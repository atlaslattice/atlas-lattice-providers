#!/usr/bin/env python3
"""
Eight Gates Enforcement Core — CANDIDATE, NOT CANON.

Mechanical checks for source/status/secret/overclaim/repro/review/human-root gates.
This module is intentionally conservative: it blocks or warns rather than promoting.
"""
from __future__ import annotations

import argparse
import ast
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

try:
    from .project_adoption_context import ProjectApprovalContext
except ImportError:  # Direct invocation: python core/eight_gates.py
    from project_adoption_context import ProjectApprovalContext

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

ESCALATION_PATTERNS = [
    r"\b(?:host authentication|host consent|runtime permissions?)\s*(?:is|are|:)?\s*(?:granted|verified|approved)\b",
    r"\b(?:model training|autonomous agents?|personhood)\s*(?:is|are|:)?\s*(?:granted|verified|approved|established)\b",
    r"\b(?:constitutional|scientific|cultural|fiction)\s+canon\s*(?:is|:)?\s*(?:ratified|approved|replaced)\b",
    r"\bprivate\s+(?:content|transcripts?|corpora)\s*(?:export|publication|release)\s*(?:is|:)?\s*(?:granted|approved|authorized)\b",
]

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
    warnings: List[str] = field(default_factory=list)
    project_approval: Dict[str, Any] = field(default_factory=dict)

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

def status_gate(path: Path, text: str, project_binding=None) -> GateResult:
    if project_binding is not None:
        return GateResult(True, "exact reviewed project decision and artifact hash selected by caller; original candidate records retain their status", [])
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

def _policy_evidence_text(path: Path, text: str) -> str:
    """Do not treat this scanner's rule tables or guard literals as artifact claims.

    All other text is scanned. Secret scanning always sees the entire file.
    The exclusion is confined to this exact implementation path and AST nodes.
    """
    if path.resolve() != Path(__file__).resolve():
        return text
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text  # Repro gate will report syntax failure.
    lines = text.splitlines(keepends=True)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {"OVERCLAIM_PATTERNS", "ESCALATION_PATTERNS", "PLACEHOLDER_PATTERNS"} for t in node.targets):
            for i in range(node.value.lineno - 1, node.value.end_lineno):
                lines[i] = "\n" if lines[i].endswith("\n") else ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in {"CANON: YES", "DEPLOYMENT: YES"}:
            for i in range(node.lineno - 1, node.end_lineno):
                lines[i] = "\n" if lines[i].endswith("\n") else ""
    return "".join(lines)


def _negative_clause(text: str, start: int) -> bool:
    """Limited negative-claim recognition only inside exact approved artifacts.

    A new contrast or sentence resets the scope. This is not a general proof
    of prose truth; current bytes still require the caller's reviewed hash.
    """
    prefix = text[max(0, start - 700):start]
    prefix = re.split(r"[.!?;:\n]|\b(?:but|however|yet)\b", prefix, flags=re.I)[-1]
    return bool(re.search(r"\b(?:no\s+item\s+below\s+is|(?:does|do|did|is|are|was|were|has|have|can|will)\s+not)\b", prefix, re.I))


def overclaim_gate(path: Path, text: str, project_binding=None) -> GateResult:
    hits = []
    text = _policy_evidence_text(path, text)
    for pattern in OVERCLAIM_PATTERNS:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if project_binding is not None and pattern in {r"\bcanonical\b", r"\bcanonized\b"}:
            matches = []  # Exact owner project scope; never inferred from text.
        if project_binding is not None and pattern == r"\bdeployed\b":
            matches = [m for m in matches if not _negative_clause(text, m.start())]
        if matches:
            hits.append(f"overclaim:{pattern}")
    if project_binding is not None:
        for pattern in ESCALATION_PATTERNS:
            if any(not _negative_clause(text, m.start()) for m in re.finditer(pattern, text, re.I)):
                hits.append("outside_project_approval_scope:" + pattern)
    return GateResult(not hits, "overclaim scan complete", hits)

def repro_gate(path: Path, text: str) -> GateResult:
    findings = []
    lower = _policy_evidence_text(path, text).lower()
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

def human_root_gate(path: Path, text: str, project_binding=None) -> GateResult:
    text = _policy_evidence_text(path, text)
    if project_binding is not None:
        if "DEPLOYMENT: YES" in text.upper():
            return GateResult(False, "project adoption supplies no runtime deployment approval", ["SEPARATE_DEPLOYMENT_APPROVAL_REQUIRED"])
        return GateResult(True, "explicit caller-selected owner project record and source pins checked; no host, model, constitutional or private-source grant", [])
    # Human-root approval is only required for promotion. Candidate artifacts pass by staying candidate.
    if "CANON: YES" in text.upper() or "DEPLOYMENT: YES" in text.upper():
        return GateResult(False, "promotion requires explicit human-root packet", ["HUMAN_ROOT_REQUIRED"])
    return GateResult(True, "no promotion detected; remains candidate/not-canon", [])

def run_eight_gates(path_str: str, project_approval=None) -> EightGatesPacket:
    path = Path(path_str)
    text = read_text(path)
    if project_approval is not None and type(project_approval) is not ProjectApprovalContext:
        raise ValueError("VERIFIED_PROJECT_APPROVAL_CONTEXT_REQUIRED")
    binding = ProjectApprovalContext.binding_for(project_approval, path) if project_approval is not None else None
    gates = {
        "source_gate": source_gate(path, text),
        "hash_gate": hash_gate(path, text),
        "status_gate": status_gate(path, text, binding),
        "secret_gate": secret_gate(path, text),
        "overclaim_gate": overclaim_gate(path, text, binding),
        "repro_gate": repro_gate(path, text),
        "review_gate": review_gate(path, text),
        "human_root_gate": human_root_gate(path, text, binding),
    }
    blockers = []
    warnings = []
    for name, result in gates.items():
        if not result.pass_:
            blockers.append(name)
            blockers.extend(result.findings)
        else:
            warnings.extend(result.findings)
    final_status = "PASS" if not blockers else "BLOCKED"
    next_action = "No promotion; retain candidate state." if final_status == "PASS" else "Resolve blockers before merge/promotion."
    if binding and final_status == "PASS":
        next_action = "Retain the exact scoped owner project decision and original candidate/evidence statuses; amendments need a new authorized decision."
    if project_approval is not None:
        # Check the same selected bytes again before returning the decision.
        if ProjectApprovalContext.binding_for(project_approval, path) != binding:
            raise ValueError("PROJECT_APPROVAL_CHANGED_DURING_SCAN")
    return EightGatesPacket(
        artifact_id=hashlib.sha256(str(path).encode()).hexdigest()[:16],
        artifact_path=str(path),
        artifact_type=path.suffix.lstrip(".") or "unknown",
        gate_results={name: result.to_packet() for name, result in gates.items()},
        final_status=final_status,
        blockers=blockers,
        next_action=next_action,
        generated_at=datetime.now(timezone.utc).isoformat(),
        canon_status=("mixed_candidate_and_owner_project_adoption" if binding and binding["role"] == "MIXED_HISTORICAL_QUEUE" else "owner_project_approval_context" if binding and binding["role"] == "VALIDATION_CONTEXT" else "owner_project_adopted" if binding else "not_canon"),
        authority_scope=binding["scope"] if binding else "none",
        warnings=warnings,
        project_approval=binding or {},
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="Run Eight Gates scan against files.")
    parser.add_argument("paths", nargs="+", help="Files to scan")
    parser.add_argument("--out", default="archive/reports/eight_gates_packet.json", help="Output JSON path")
    parser.add_argument("--repo-root", default=".", help="Repository containing the selected approval context")
    parser.add_argument("--project-approval", help="Explicit owner-approved project context; never auto-discovered")
    parser.add_argument("--expected-project-approval-sha256", help="Independently selected digest of that context")
    args = parser.parse_args()
    if bool(args.project_approval) != bool(args.expected_project_approval_sha256):
        parser.error("Project approval requires both an explicit context and its expected digest.")
    try:
        approval = ProjectApprovalContext(args.repo_root, args.project_approval, args.expected_project_approval_sha256) if args.project_approval else None
        packets = [run_eight_gates(p, approval).to_dict() for p in args.paths]
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"blocked": True, "approval_error": str(error)}, indent=2))
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"packets": packets}, indent=2), encoding="utf-8")
    blocked = any(p["final_status"] == "BLOCKED" for p in packets)
    print(json.dumps({"out": str(out), "blocked": blocked, "count": len(packets)}, indent=2))
    return 1 if blocked else 0

if __name__ == "__main__":
    raise SystemExit(main())
