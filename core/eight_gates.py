#!/usr/bin/env python3
"""
Eight Gates Enforcement Core — CANDIDATE, NOT CANON.

Mechanical checks for source/status/secret/overclaim/repro/review/human-root gates.
This module is intentionally conservative: it blocks or warns rather than promoting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

SECRET_PATTERNS = [
    r"OPENAI_API_KEY\s*=\s*['\"]?sk-[^'\"\s]+",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"ntn_[A-Za-z0-9_-]{10,}",
    r"AKIA[0-9A-Z]{16}",
    r"AIza[0-9A-Za-z\-_]{20,}",
    r"xai-[A-Za-z0-9_-]{20,}",
]

OVERCLAIM_PATTERNS = [
    r"\bcanonical\b",
    r"\bcanonized\b",
    r"official OpenAI",
    r"official xAI",
    r"\bdeployed\b",
    r"production ready",
    r"supersedes all prior",
    r"first true unification",
    r"proven complete",
    r"fully mirrored",
    r"all archives complete",
    r"clean-clone verified",
]

PLACEHOLDER_PATTERNS = [
    "full code omitted",
    "assume local content",
    "from temp_",
    "abbrev in payload",
    "[FULL CONTENT OF",
    "full enhanced code",
]

STATUS_TERMS = ["CANDIDATE", "NOT CANON", "AUTHORITY", "DEPLOYMENT"]

@dataclass
class GateResult:
    pass_: bool
    notes: str
    findings: List[str] = field(default_factory=list)

    def to_packet(self) -> Dict[str, Any]:
        return {"pass": self.pass_, "notes": self.notes, "findings": self.findings}

@dataclass
class EightGatesPacket:
    artifact_id: str
    artifact_path: str
    artifact_type: str
    gate_results: Dict[str, Dict[str, Any]]
    final_status: str
    blockers: List[str]
    next_action: str
    generated_at: str
    generated_by: str = "core/eight_gates.py"
    canon_status: str = "not_canon"
    authority_scope: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def source_gate(path: Path, text: str) -> GateResult:
    # Files in git paths have at least a declared artifact path; source passports can improve this later.
    if path.exists():
        return GateResult(True, "artifact path exists; source passport recommended", [])
    return GateResult(False, "artifact path missing", ["RAW_SOURCE_MISSING"])

def hash_gate(path: Path, text: str) -> GateResult:
    if path.exists() and path.is_file():
        return GateResult(True, f"sha256:{sha256_file(path)}", [])
    return GateResult(False, "hash unavailable", ["HASH_MISSING"])

def status_gate(path: Path, text: str) -> GateResult:
    if path.suffix.lower() in {".md", ".txt", ".yaml", ".yml", ".json"}:
        missing = [term for term in STATUS_TERMS if term not in text.upper()]
        if missing:
            return GateResult(False, "candidate/status banner incomplete", [f"missing:{m}" for m in missing])
    return GateResult(True, "status gate passed or not applicable", [])

def secret_gate(path: Path, text: str) -> GateResult:
    hits = []
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(f"secret_pattern:{pattern[:24]}")
    return GateResult(not hits, "secret scan complete", hits)

def overclaim_gate(path: Path, text: str) -> GateResult:
    hits = []
    for pattern in OVERCLAIM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(f"overclaim:{pattern}")
    return GateResult(not hits, "overclaim scan complete", hits)

def repro_gate(path: Path, text: str) -> GateResult:
    findings = []
    lower = text.lower()
    for phrase in PLACEHOLDER_PATTERNS:
        if phrase.lower() in lower:
            findings.append(f"placeholder:{phrase}")
    if path.suffix == ".py" and path.exists():
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
        if proc.returncode != 0:
            findings.append("py_compile_failed:" + (proc.stderr or proc.stdout)[:200])
    return GateResult(not findings, "repro/placeholder scan complete", findings)

def review_gate(path: Path, text: str) -> GateResult:
    # Candidate-friendly: warn only. Review packets can be attached later.
    if "REVIEWED" in text.upper() or "REVIEW" in text.upper():
        return GateResult(True, "review language present", [])
    return GateResult(True, "review gate pending but non-blocking for candidate artifacts", ["PENDING_REVIEW_RECOMMENDED"])

def human_root_gate(path: Path, text: str) -> GateResult:
    # Human-root approval is only required for promotion. Candidate artifacts pass by staying candidate.
    if "CANON: YES" in text.upper() or "DEPLOYMENT: YES" in text.upper():
        return GateResult(False, "promotion requires explicit human-root packet", ["HUMAN_ROOT_REQUIRED"])
    return GateResult(True, "no promotion detected; remains candidate/not-canon", [])

def run_eight_gates(path_str: str) -> EightGatesPacket:
    path = Path(path_str)
    text = read_text(path)
    gates = {
        "source_gate": source_gate(path, text),
        "hash_gate": hash_gate(path, text),
        "status_gate": status_gate(path, text),
        "secret_gate": secret_gate(path, text),
        "overclaim_gate": overclaim_gate(path, text),
        "repro_gate": repro_gate(path, text),
        "review_gate": review_gate(path, text),
        "human_root_gate": human_root_gate(path, text),
    }
    blockers = []
    for name, result in gates.items():
        if not result.pass_:
            blockers.append(name)
        blockers.extend(result.findings)
    final_status = "PASS" if not blockers else "BLOCKED"
    next_action = "No promotion; retain candidate state." if final_status == "PASS" else "Resolve blockers before merge/promotion."
    return EightGatesPacket(
        artifact_id=hashlib.sha256(str(path).encode()).hexdigest()[:16],
        artifact_path=str(path),
        artifact_type=path.suffix.lstrip(".") or "unknown",
        gate_results={name: result.to_packet() for name, result in gates.items()},
        final_status=final_status,
        blockers=blockers,
        next_action=next_action,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="Run Eight Gates scan against files.")
    parser.add_argument("paths", nargs="+", help="Files to scan")
    parser.add_argument("--out", default="archive/reports/eight_gates_packet.json", help="Output JSON path")
    args = parser.parse_args()

    packets = [run_eight_gates(p).to_dict() for p in args.paths]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"packets": packets}, indent=2), encoding="utf-8")
    blocked = any(p["final_status"] == "BLOCKED" for p in packets)
    print(json.dumps({"out": str(out), "blocked": blocked, "count": len(packets)}, indent=2))
    return 1 if blocked else 0

if __name__ == "__main__":
    raise SystemExit(main())
