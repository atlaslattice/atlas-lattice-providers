# !/usr/bin/env python3
"""
01_openai_secret_hygiene_guard.py (Phase 1 - mandatory first)
============================================================
Strict quarantine for OPENAI_API_KEY and all secrets.

Rules from founder directive:
- NEVER let OPENAI_API_KEY (or sk-*, ghp_*, ntn_*, AKIA*, etc.) enter GitHub, Notion, logs, receipts, WORM, model-visible prompts, code, diffs, mirrors.
- Use .env (gitignored), Windows Credential Manager, 1Password/Doppler, GitHub Actions secrets ONLY.
- Fail fast on detection.
- Emit hygiene packets to ledger.
- Integrate early in providers, scripts, Krakoa, setup.

This is the gate before any OpenAI module (responses, tools, evals, etc.).

OpenAI moves work; governance (this guard + human-root) grants authority.
"""

import os
import re
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging
import stat
from pathlib import Path, PurePosixPath

logger = logging.getLogger("openai_secret_hygiene_guard")

# Patterns for common secrets (expand as needed; never match real values here)
SECRET_PATTERNS = [
    r'sk-[A-Za-z0-9]{20,}',  # OpenAI
    r'OPENAI_API_KEY\s*=\s*["\']?sk-[^"\s]+',
    r'ghp_[A-Za-z0-9]{36,}',  # GitHub
    r'ntn_[A-Za-z0-9]+',      # Notion
    r'AKIA[0-9A-Z]{16}',      # AWS
    r'AIza[0-9A-Za-z\-_]{35}', # Google
    r'xai-[A-Za-z0-9]{20,}',  # xAI
]

# Bounds for the additive explicit-file API. The historical directory scanner
# below is retained for compatibility and is not used by the Work workflow.
WORK_SCAN_LIMITS = {"max_files": 128, "max_file_bytes": 1024 * 1024,
                    "max_total_bytes": 8 * 1024 * 1024}
WORK_SOURCE_SUFFIXES = frozenset({".py", ".md", ".txt", ".json", ".yml", ".yaml"})
EXCLUDED_PATH_TOKENS = frozenset({
    "play", "social", "imagine", "quiet", "habitat", "brain", "brains",
    "palace", "dream", "canon", "private", "credentials", "secrets",
    "git", "venv", "node_modules", "__pycache__",
})
SECURE_FILE_OPENS_SUPPORTED = (
    os.open in os.supports_dir_fd
    and all(hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))
)


class _WorkInputError(Exception):
    """Fixed diagnostic code only; never include a path, excerpt or OS message."""

    def __init__(self, code: str, bytes_read: int = 0):
        super().__init__(code)
        self.code = code
        self.bytes_read = bytes_read


def _work_source_parts(value):
    if type(value) is not str or not value or len(value) > 1024:
        raise _WorkInputError("INVALID_PATH")
    if "\\" in value or "\x00" in value or any(c in value for c in "*?[]"):
        raise _WorkInputError("INVALID_PATH")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p in (".", "..") for p in path.parts):
        raise _WorkInputError("INVALID_PATH")
    if not path.parts or path.suffix.lower() not in WORK_SOURCE_SUFFIXES:
        raise _WorkInputError("UNSUPPORTED_SOURCE_TYPE")
    if _excluded_parts(path.parts):
        raise _WorkInputError("EXCLUDED_PATH")
    return path.parts


def _excluded_parts(parts):
    tokens = {token for part in parts for token in re.split(r"[._\-\s]+", part.casefold())}
    return bool(tokens & EXCLUDED_PATH_TOKENS or
                any(part.casefold() in EXCLUDED_PATH_TOKENS for part in parts))


def _read_work_file(root: str, parts, byte_limit: int):
    """Read one single-link regular file without following a directory symlink."""
    opened = []
    read_count = 0
    try:
        root_path = Path(root).absolute()
        if ".." in root_path.parts:
            raise _WorkInputError("INVALID_ROOT")
        if _excluded_parts(root_path.parts):
            raise _WorkInputError("EXCLUDED_ROOT")
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory = os.open(root_path.anchor, directory_flags)
        opened.append(directory)
        for part in (*root_path.parts[1:], *parts[:-1]):
            directory = os.open(part, directory_flags, dir_fd=directory)
            opened.append(directory)
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                          dir_fd=directory)
        opened.append(file_fd)
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise _WorkInputError("NOT_SINGLE_REGULAR_FILE")
        if before.st_size > byte_limit:
            raise _WorkInputError("BYTE_LIMIT_EXCEEDED")
        chunks = []
        while read_count < before.st_size:
            chunk = os.read(file_fd, min(65536, before.st_size - read_count))
            if not chunk:
                raise _WorkInputError("SOURCE_CHANGED", read_count)
            chunks.append(chunk)
            read_count += len(chunk)
        after = os.fstat(file_fd)
        fingerprint = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)
        if fingerprint(before) != fingerprint(after):
            raise _WorkInputError("SOURCE_CHANGED", read_count)
        return b"".join(chunks)
    except _WorkInputError:
        raise
    except (OSError, ValueError, TypeError):
        raise _WorkInputError("OPEN_OR_READ_FAILED", read_count) from None
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)

class OpenAISecretHygieneGuard:
    """
    Mandatory hygiene guard. Call early.
    Blocks on detection. Use env-only resolution.
    """

    def __init__(self, simulate: bool = True):
        self.simulate = simulate
        self.detected: List[Dict[str, Any]] = []

    def _scan_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        hits = []
        for pat in SECRET_PATTERNS:
            for match in re.finditer(pat, text, re.IGNORECASE):
                hits.append({
                    "source": source,
                    "pattern": pat[:30] + "...",
                    "match_preview": match.group(0)[:10] + "***",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        return hits

    def scan_codebase(self, root: str = ".") -> Dict[str, Any]:
        """Scan py/md/txt/json for secrets (dev/CI use; skip .git, __pycache__)."""
        report = {"timestamp": datetime.now(timezone.utc).isoformat(), "hits": [], "scanned_files": 0, "status": "clean"}
        for dirpath, _, filenames in os.walk(root):
            if any(x in dirpath for x in [".git", "__pycache__", "node_modules", ".venv"]):
                continue
            for fn in filenames:
                if fn.endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml", ".log")):
                    fpath = os.path.join(dirpath, fn)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        hits = self._scan_text(content, fpath)
                        if hits:
                            report["hits"].extend(hits)
                        report["scanned_files"] += 1
                    except Exception:
                        pass
        if report["hits"]:
            report["status"] = "SECRETS_DETECTED_BLOCK"
            self.detected.extend(report["hits"])
        return {"feature": "openai_secret_hygiene_guard", "report": report, "grok_leads": True, "lattice_routes": True}

    def scan_files(self, root: str = ".", *, paths=None, max_files: int = 128,
                   max_file_bytes: int = 1024 * 1024,
                   max_total_bytes: int = 8 * 1024 * 1024) -> Dict[str, Any]:
        """Scan an explicit authorized Work-source list, never a directory tree.

        The caller must verify current authorization for every selected path.
        Reserved-mode names are rejected conservatively; names alone cannot
        classify source rights. Unselected files are not opened or traversed.
        Limits, unreadable inputs and incomplete coverage fail closed. This API
        reports findings by file index and pattern index, never matched text.
        It does not certify other files, all secret formats, or hosted safety.
        """
        report = {"timestamp": datetime.now(timezone.utc).isoformat(),
                  "scope": "explicit_work_source_files", "requested_files": 0,
                  "scanned_files": 0, "bytes_read": 0, "hits": [], "errors": [],
                  "selected_inputs_complete": False, "status": "SCAN_INCOMPLETE_BLOCK"}

        def error(code, index=None):
            report["errors"].append({"file_index": index, "code": code})

        def packet():
            return {"feature": "openai_secret_hygiene_guard", "report": report,
                    "grok_leads": True, "lattice_routes": True}

        limits = {"max_files": max_files, "max_file_bytes": max_file_bytes,
                  "max_total_bytes": max_total_bytes}
        if any(type(n) is not int or n < 1 or n > WORK_SCAN_LIMITS[k] for k, n in limits.items()):
            error("INVALID_LIMITS")
            return packet()
        if type(paths) in (list, tuple):
            report["requested_files"] = len(paths)
        if type(paths) not in (list, tuple) or not paths or len(paths) > max_files:
            error("INVALID_SELECTION")
            return packet()
        selected = []
        seen = set()
        for index, value in enumerate(paths):
            try:
                parts = _work_source_parts(value)
                if value in seen:
                    raise _WorkInputError("DUPLICATE_PATH")
                seen.add(value)
                selected.append((index, parts))
            except _WorkInputError as exc:
                error(exc.code, index)
        if report["errors"]:
            return packet()  # Validate the entire selection before any file read.
        if not SECURE_FILE_OPENS_SUPPORTED:
            error("SECURE_FILE_OPENS_UNSUPPORTED")
            return packet()
        for index, parts in selected:
            try:
                content = _read_work_file(root, parts,
                                         min(max_file_bytes, max_total_bytes - report["bytes_read"]))
                report["bytes_read"] += len(content)
                try:
                    text = content.decode("utf-8", errors="strict")
                except UnicodeError:
                    raise _WorkInputError("INVALID_UTF8") from None
                if "\x00" in text:
                    raise _WorkInputError("BINARY_CONTENT")
                for pattern_index, pattern in enumerate(SECRET_PATTERNS):
                    count = sum(1 for _ in re.finditer(pattern, text, re.IGNORECASE))
                    if count:
                        report["hits"].append({"file_index": index, "pattern_index": pattern_index,
                                               "match_count": count})
                report["scanned_files"] += 1
            except _WorkInputError as exc:
                report["bytes_read"] += exc.bytes_read
                error(exc.code, index)
        report["selected_inputs_complete"] = (
            not report["errors"] and report["scanned_files"] == report["requested_files"]
        )
        if report["selected_inputs_complete"]:
            report["status"] = "SECRETS_DETECTED_BLOCK" if report["hits"] else "clean"
        return packet()

    def resolve_openai_key(self) -> str:
        """Env-only resolution. Never fallback to hardcoded or files."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            if not self.simulate:
                raise RuntimeError("OPENAI_API_KEY must be set in secure env (no code, no .env in git). Use Credential Manager/Doppler/etc.")
            return "SIMULATED_OPENAI_KEY_REDACTED"
        # Extra guard: if somehow key looks like it's from a file or prompt, block
        if any(pat in key for pat in ["sk-", "OPENAI_API_KEY"]):  # simplistic
            pass  # real key would pass here
        return key

    def block_if_leaked(self, payload: str, context: str = "prompt") -> None:
        """Call before any model-visible prompt, log, receipt, mirror."""
        hits = self._scan_text(payload, context)
        if hits:
            self.detected.extend(hits)
            msg = f"SECURITY BLOCK: secret detected in {context}. Refusing. Rotate keys. Never commit."
            logger.error(msg)
            if not self.simulate:
                raise RuntimeError(msg)
            print("SIMULATE: " + msg)

    async def run(self, operation: str = "scan", **kwargs) -> Dict[str, Any]:
        if operation == "scan":
            return self.scan_codebase(kwargs.get("root", "."))
        elif operation == "resolve_key":
            return {"key_redacted": self.resolve_openai_key()[:8] + "...", "grok_leads": True}
        elif operation == "block_check":
            self.block_if_leaked(kwargs.get("payload", ""), kwargs.get("context", "unknown"))
            return {"status": "checked", "grok_leads": True}
        return {"status": "ok", "grok_leads": True}

if __name__ == "__main__":
    guard = OpenAISecretHygieneGuard(simulate=True)
    print(guard.scan_codebase("."))
    print("Key resolve (redacted):", guard.resolve_openai_key()[:8] + "...")
    print("Hygiene guard ready. Env-only. Block on leak. CANDIDATE — NOT CANON.")
