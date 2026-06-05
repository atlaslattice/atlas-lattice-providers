#!/usr/bin/env python3
"""Clean-clone style reproducibility check — CANDIDATE, NOT CANON."""
from __future__ import annotations

import json
import py_compile
from datetime import datetime, timezone
from pathlib import Path

PLACEHOLDERS = [
    "full code omitted",
    "assume local content",
    "from temp_",
    "abbrev in payload",
    "[FULL CONTENT OF",
    "full enhanced code",
]

CHECK_PATHS = [
    "core/eight_gates.py",
    "schemas/eight_gates_packet.schema.yaml",
    "docs/EIGHT_GATES_ENFORCEMENT_ARCHITECTURE_V1.0.md",
]


def scan_placeholders(root: Path) -> list[str]:
    hits = []
    for path in root.rglob("*"):
        if path.is_dir() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for phrase in PLACEHOLDERS:
            if phrase.lower() in lower:
                hits.append(f"{path}:{phrase}")
    return hits


def compile_python(root: Path) -> list[str]:
    failures = []
    for path in root.rglob("*.py"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"{path}:{str(exc)[:200]}")
    return failures


def main() -> int:
    root = Path.cwd()
    missing = [p for p in CHECK_PATHS if not (root / p).exists()]
    placeholders = scan_placeholders(root)
    compile_failures = compile_python(root)
    report = {
        "status": "PASS" if not (missing or placeholders or compile_failures) else "BLOCKED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "missing_required_paths": missing,
        "placeholder_hits": placeholders,
        "py_compile_failures": compile_failures,
        "canon_status": "not_canon",
        "authority_scope": "none",
    }
    out = root / "archive" / "reports" / "clean_clone_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
