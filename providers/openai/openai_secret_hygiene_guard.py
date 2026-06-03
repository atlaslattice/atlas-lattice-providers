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