#!/usr/bin/env python3
"""Operator status console — tells what is real, blocked, candidate, and next."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = [
    "docs/EIGHT_GATES_ENFORCEMENT_ARCHITECTURE_V1.0.md",
    "schemas/eight_gates_packet.schema.yaml",
    "core/eight_gates.py",
    ".github/workflows/eight_gates_check.yml",
    ".github/ISSUE_TEMPLATE/eight_gates_failure.yml",
    "public_candidate_bundle_0001/README.md",
]


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}


def main() -> int:
    root = Path.cwd()
    missing = [p for p in REQUIRED if not (root / p).exists()]
    py = run([sys.executable, "-m", "py_compile", "core/eight_gates.py"])
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "OPERATOR_STATUS",
        "canon_status": "not_canon",
        "deployment_status": "not_deployed",
        "authority_scope": "none",
        "required_paths_missing": missing,
        "eight_gates_py_compile": py,
        "next_safest_task": "Resolve missing required paths, then run core/eight_gates.py over public_candidate_bundle_0001.",
        "keeper": "The gate is not a crown. The receipt is not approval. NOTHING DIES.",
    }
    out_json = root / "archive" / "reports" / "operator_status.json"
    out_md = root / "docs" / "OPERATOR_STATUS.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(status, indent=2), encoding="utf-8")
    out_md.write_text("# OPERATOR_STATUS\n\n```json\n" + json.dumps(status, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0 if not missing and py["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
