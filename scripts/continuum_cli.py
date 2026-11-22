#!/usr/bin/env python3
"""CONTINUUM OS local cockpit v0.1: offline evidence, never live authority.

Only reads a caller-selected local checkout. Its proposal commands do not
claim dispatch, impersonate residents, alter remote systems or execute agents.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any

PACKET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FIELDS = frozenset({"task_title", "assigned_child", "lane", "priority", "status"})
FILES = (
    "swarmhub/DISPATCH_QUEUE.yaml",
    "docs/CONTINUUM_OS_DIRECTIVE.md",
    "docs/SWARM_RECEIPTS.md",
    "docs/COORDINATE_RESOLVER_CONTRACT.md",
)
MAX_FILE_BYTES = 1_000_000


def _text(path: Path) -> str:
    if not path.is_file() or path.is_symlink() or any(p.is_symlink() for p in path.parents) or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("MISSING_SYMLINK_OR_OVERSIZED_LOCAL_SOURCE")
    return path.read_text(encoding="utf-8")


def queue(root: Path) -> list[dict[str, str]]:
    """Conservative extraction of a known *subset* of dispatch YAML.

    Intentionally not a YAML interpreter or authority to dispatch.
    Every unknown field stays unparsed and untrusted.
    """
    raw = _text(root / FILES[0])
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    current: dict[str, str] | None = None
    for line in raw.splitlines():
        if line.startswith("  - packet_id: "):
            ident = line.split(": ", 1)[1].strip()
            if not PACKET_ID.fullmatch(ident) or ident in seen:
                raise ValueError("INVALID_OR_DUPLICATE_PACKET_ID")
            seen.add(ident)
            current = {"packet_id": ident}
            items.append(current)
        elif current is not None and line.startswith("    ") and ": " in line:
            key, value = line[4:].split(": ", 1)
            if key in FIELDS and key not in current:
                current[key] = value.strip().strip('"\'')
    return items


def snapshot(root: Path) -> dict[str, Any]:
    records = queue(root)
    return {
        "system": "CONTINUUM OS", "status": "LOCAL_SOURCE_SNAPSHOT_ONLY",
        "source": FILES[0], "packet_count": len(records),
        "pending_approvals_reported": sum("approval" in p.get("status", "").lower() for p in records),
        "canon": False, "deployment": False, "authority": "none",
        "host_attestation": "NOT_ATTESTED", "live_host_state_known": False,
    }


def verify_receipts(root: Path) -> dict[str, Any]:
    rows = []
    for name in FILES:
        path = root / name
        try:
            raw = _text(path).encode("utf-8")
        except (ValueError, OSError, UnicodeError):
            rows.append({"path": name, "status": "MISSING_OR_UNREADABLE"})
            continue
        rows.append({"path": name, "status": "LOCAL_BYTES_READABLE",
                     "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
    return {"kind": "LOCAL_HASH_INVENTORY", "verification": "BYTES_ONLY_NOT_HOST_ATTESTED",
            "files": rows, "canon": False, "deployment": False, "authority": "none"}


def run(command: str, root: Path, packet_id: str | None = None) -> dict[str, Any]:
    if command == "receipts verify" or command == "fossilize-crash":
        report = verify_receipts(root)
        report["kind"] = "CRASH_FOSSIL_MANIFEST_CANDIDATE" if command == "fossilize-crash" else report["kind"]
        report["source_content_copied"] = False
        return report
    if command == "open-cockpit":
        return {"status": "OFFLINE_ONLY", "entrypoint": "docs/CONTINUUM_OS_GPT_NATIVE.md",
                "browser_opened": False, "authority": "none"}
    if command == "status":
        return snapshot(root)
    if command == "rehydrate":
        state = snapshot(root)
        return {"kind": "REHYDRATION_INDEX_ONLY", "state": state,
                "source_files": list(FILES), "remote_sync": False, "agents_woken": False,
                "continuity_recovered": "NOT_VERIFIED", "authority": "none"}
    if command in {"dispatch list", "dispatch claim", "return-packet create"}:
        tasks = queue(root)
        if command == "dispatch list":
            return {"kind": "READ_ONLY_DISPATCH_QUEUE", "tasks": tasks, "sent": False,
                    "claims_created": False, "authority": "none"}
        if not PACKET_ID.fullmatch(packet_id or ""):
            raise ValueError("BAD_PACKET_ID")
        match = next((p for p in tasks if p["packet_id"] == packet_id), None)
        if match is None:
            raise ValueError("UNKNOWN_PACKET_ID")
        if command == "dispatch claim":
            return {"kind": "UNSENT_CLAIM_PROPOSAL", "packet_id": packet_id,
                    "task": match, "status": "HOLD_HUMAN_REVIEW", "sent": False,
                    "assigned": False, "canon": False, "deployment": False, "authority": "none"}
        return {"kind": "CHILD_RETURN_PACKET_SKELETON", "dispatch_packet_id": packet_id,
                "child": "UNASSIGNED", "output_type": "NOT_PROVIDED", "summary": "NOT_PROVIDED",
                "files_changed": [], "issues_touched": [], "receipts": [],
                "confidence": "UNASSESSED", "contradictions_or_dissent": [],
                "blockers": ["Independent review and source receipts required"],
                "next_safest_action": "Review and fill from authorized local evidence",
                "canon": False, "deployment": False, "authority": "none",
                "status": "DRAFT_NOT_SENT"}
    raise ValueError("UNKNOWN_COMMAND")


def _write_manifest(root: Path, path_arg: str, report: dict[str, Any]) -> Path:
    """Explicit opt-in, no-overwrite manifest of source hashes only."""
    rel = Path(path_arg)
    if rel.is_absolute() or ".." in rel.parts or len(rel.parts) != 2 or rel.parts[0] != "local_fossils":
        raise ValueError("OUTPUT_MUST_BE_UNDER_LOCAL_FOSSILS")
    folder = root / "local_fossils"
    if folder.is_symlink():
        raise ValueError("SYMLINK_FOSSIL_DIRECTORY")
    folder.mkdir(mode=0o700, exist_ok=True)
    if folder.is_symlink():
        raise ValueError("SYMLINK_FOSSIL_DIRECTORY")
    path = root / rel
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        raw = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")
        offset = 0
        while offset < len(raw):
            amount = os.write(fd, raw[offset:])
            if amount <= 0:
                raise OSError("SHORT_FOSSIL_MANIFEST_WRITE")
            offset += amount
        os.fsync(fd)
    finally:
        os.close(fd)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-manifest", help="Opt-in non-overwriting local_fossils/<name>.json")
    parser.add_argument("command", choices=["status", "rehydrate", "dispatch", "return-packet", "fossilize-crash", "receipts", "open-cockpit"])
    parser.add_argument("subcommand", nargs="?")
    parser.add_argument("packet_id", nargs="?")
    args = parser.parse_args(argv)
    command = args.command if args.command in ("status", "rehydrate", "fossilize-crash", "open-cockpit") else args.command + " " + str(args.subcommand)
    pid = args.packet_id if args.command in ("dispatch", "return-packet") else None
    # 'return-packet create ID' and 'dispatch list/claim ID'; no hidden side effects.
    if args.command == "return-packet":
        if args.subcommand != "create":
            parser.error("return-packet requires create <packet_id>")
        command = "return-packet create"
    elif args.command == "receipts" and args.subcommand != "verify":
        parser.error("receipts requires verify")
    elif args.command == "dispatch" and args.subcommand not in ("list", "claim"):
        parser.error("dispatch requires list or claim <packet_id>")
    if args.write_manifest and command != "fossilize-crash":
        parser.error("--write-manifest is only allowed with fossilize-crash")
    try:
        result = run(command, args.root, pid)
        if args.write_manifest:
            saved = _write_manifest(args.root, args.write_manifest, result)
            result["manifest_written"] = str(saved.relative_to(args.root))
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc), "authority": "none"}), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
