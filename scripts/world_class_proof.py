#!/usr/bin/env python3
"""One-command world-class proof runner for Atlas Lattice / Continuum OS.

This command does not promote anything to canon. It generates a candidate proof
receipt showing which operability checks passed, failed, or were skipped.

The broad command reads checkout sources and can invoke optional interop tests;
run it only with an independently authorized source and execution scope. CI runs
explicit synthetic regression modules instead. --strict also fails on warnings.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
LEGACY_NAME_ALLOWED_CONTEXT = {"docs/CONTINUUM_OS_DIRECTIVE.md", "docs/WORLD_CLASS_PROOF.md", "scripts/world_class_proof.py"}
REQUIRED_CHECK_NAMES = (
    "py_compile_core_surfaces",
    "openai_operability_surface",
    "continuum_os_plural_continuums_directive",
    "continuum_not_continuity_name_guard",
    "a2a_no_merged_mind_invariant",
    "inv0_preservation_invariant",
    "candidate_not_canon_boundary",
    "pytest_openai_interop",
)


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ""
    files: List[str] = field(default_factory=list)


@dataclass
class ProofReceipt:
    receipt_type: str = "WorldClassProofReceipt"
    system_name: str = "CONTINUUM OS"
    continuum_model: str = "multiple_continuums"
    status: str = "CANDIDATE_NOT_CANON"
    canon: bool = False
    authority: str = "none"
    human_root_required: bool = True
    invariants: List[str] = field(default_factory=lambda: ["INV-0", "NO_MERGED_MIND", "CANDIDATE_NOT_CANON", "A2A_BUS_NOT_FUSION", "CONTINUUM_OS", "MULTIPLE_CONTINUUMS"])
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    checks: List[CheckResult] = field(default_factory=list)

    def evidence_errors(self) -> List[str]:
        """Check coverage and result shape before interpreting status labels."""
        if type(self.checks) is not list or not self.checks:
            return ["NO_CHECK_EVIDENCE"]
        names = []
        errors = []
        for check in self.checks:
            if not isinstance(check, CheckResult) or type(check.name) is not str or not check.name.strip():
                errors.append("MALFORMED_CHECK")
                continue
            names.append(check.name)
            if type(check.status) is not str or check.status not in {"PASS", "WARN", "FAIL"}:
                errors.append("UNKNOWN_CHECK_STATUS")
        if len(names) != len(set(names)):
            errors.append("DUPLICATE_CHECK_NAME")
        if not set(REQUIRED_CHECK_NAMES).issubset(names):
            errors.append("MISSING_REQUIRED_CHECKS")
        return sorted(set(errors))

    def overall(self) -> str:
        if self.evidence_errors():
            return "CANDIDATE_INCOMPLETE"
        if any(c.status == "FAIL" for c in self.checks):
            return "CANDIDATE_INCOMPLETE"
        if any(c.status == "WARN" for c in self.checks):
            return "CANDIDATE_WITH_WARNINGS"
        return "CANDIDATE_READY"

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["required_check_names"] = list(REQUIRED_CHECK_NAMES)
        data["evidence_errors"] = self.evidence_errors()
        data["overall"] = self.overall()
        return data


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def in_repo_file(path: Path) -> bool:
    """Accept only files whose resolved content stays within this checkout.

    A candidate proof must not read or execute external symlink targets.
    This is a source-only boundary, not a defense against concurrent
    filesystem replacement by an adversarial host.
    """
    try:
        return path.is_file() and path.resolve(strict=True).is_relative_to(ROOT.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return False


def compile_targets() -> CheckResult:
    candidates = [
        "scripts/world_class_proof.py",
        "scripts/openai_interop_check.py",
        "providers/openai/responses_api_spine.py",
        "providers/openai/structured_output_schema_spine.py",
        "providers/openai/tool_passport_function_calling.py",
        "providers/openai/openai_tracing_to_golden_trace.py",
        "providers/openai/evals_bullshit_olympics_bridge.py",
        "providers/openai/workload_identity_secrets_hygiene.py",
        "providers/provider_openai.py",
        "providers/openai/agents_sdk_adapter.py",
        "core/orchestrator_prime.py",
        "core/sentinel_agent.py",
        "core/transparent_packet96.py",
    ]
    compiled: List[str] = []
    missing: List[str] = []
    failures: List[str] = []
    for name in candidates:
        path = ROOT / name
        if not in_repo_file(path):
            missing.append(name)
            continue
        try:
            # Syntax-check without producing __pycache__ or changing tracked worktrees.
            compile(path.read_bytes(), str(path), "exec")
            compiled.append(name)
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    if failures:
        return CheckResult("py_compile_core_surfaces", "FAIL", "; ".join(failures), compiled)
    if missing:
        return CheckResult("py_compile_core_surfaces", "WARN", f"compiled={len(compiled)} missing={missing}", compiled)
    return CheckResult("py_compile_core_surfaces", "PASS", f"compiled={len(compiled)}", compiled)


def run_optional_pytest() -> CheckResult:
    tests = ["tests/test_openai_interop.py"]
    existing = [t for t in tests if in_repo_file(ROOT / t)]
    if not existing:
        return CheckResult("pytest_openai_interop", "WARN", "tests/test_openai_interop.py not present yet")
    try:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q", *existing], cwd=ROOT, text=True, capture_output=True, timeout=120)
    except Exception as exc:
        return CheckResult("pytest_openai_interop", "WARN", f"pytest unavailable or timed out: {exc}", existing)
    if proc.returncode != 0:
        return CheckResult("pytest_openai_interop", "FAIL", (proc.stdout + proc.stderr)[-2000:], existing)
    return CheckResult("pytest_openai_interop", "PASS", proc.stdout.strip()[-500:], existing)


def scan_terms(name: str, required_terms: List[str], roots: List[str]) -> CheckResult:
    corpus = ""
    seen_files: List[str] = []
    for root in roots:
        path = ROOT / root
        if in_repo_file(path):
            paths = [path]
        elif path.is_dir() and not path.is_symlink():
            paths = [p for p in path.rglob("*") if in_repo_file(p) and p.suffix.lower() in {".py", ".md", ".yaml", ".yml", ".json", ".txt"}]
        else:
            continue
        for p in paths:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if any(term.lower() in text.lower() for term in required_terms):
                seen_files.append(rel(p))
            corpus += "\n" + text[:200000]
    missing = [term for term in required_terms if term.lower() not in corpus.lower()]
    if missing:
        return CheckResult(name, "WARN", f"missing_terms={missing}", seen_files[:30])
    return CheckResult(name, "PASS", f"terms_present={required_terms}", seen_files[:30])


def scan_for_forbidden_term() -> CheckResult:
    roots = ["docs", "scripts", "core", "providers", "a2a", "AGENTS.md"]
    hits: List[str] = []
    checked = 0
    unreadable = 0
    for root in roots:
        path = ROOT / root
        if in_repo_file(path):
            paths = [path]
        elif path.is_dir() and not path.is_symlink():
            paths = [p for p in path.rglob("*") if in_repo_file(p) and p.suffix.lower() in {".py", ".md", ".yaml", ".yml", ".json", ".txt"}]
        else:
            continue
        for p in paths:
            rp = rel(p)
            if rp in LEGACY_NAME_ALLOWED_CONTEXT:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="strict")
            except (OSError, UnicodeError):
                unreadable += 1
                continue
            checked += 1
            if "Continuity OS".lower() in text.lower():
                hits.append(rp)
    if hits:
        return CheckResult("continuum_not_continuity_name_guard", "FAIL",
                           f"Forbidden legacy name found outside directive docs; checked_files={checked}; unreadable_files={unreadable}", hits[:50])
    if not checked or unreadable:
        return CheckResult("continuum_not_continuity_name_guard", "WARN",
                           f"Name-check evidence incomplete; checked_files={checked}; unreadable_files={unreadable}")
    return CheckResult("continuum_not_continuity_name_guard", "PASS",
                       f"No forbidden legacy name references in the readable source selection; checked_files={checked}; unreadable_files=0")


def openai_readiness() -> CheckResult:
    files = [
        ROOT / "providers/openai/responses_api_spine.py",
        ROOT / "providers/provider_openai.py",
        ROOT / "docs/OPENAI_INTEROP_MAP.md",
        ROOT / "AGENTS.md",
    ]
    present = [rel(f) for f in files if in_repo_file(f)]
    missing = [rel(f) for f in files if not in_repo_file(f)]
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if missing:
        return CheckResult("openai_operability_surface", "WARN", f"missing={missing}; OPENAI_API_KEY_present={has_key}", present)
    return CheckResult("openai_operability_surface", "PASS", f"OPENAI_API_KEY_present={has_key}; live requires explicit simulate=False", present)


def write_receipt(receipt: ProofReceipt, output: Optional[str]) -> None:
    if not output:
        print(json.dumps(receipt.to_dict(), indent=2, sort_keys=True))
        return
    # Owner-private receipts must not overwrite evidence or redirect to arbitrary files.
    relative = Path(output)
    if (relative.is_absolute() or ".." in relative.parts or
            len(relative.parts) < 2 or relative.parts[0] != "receipts"):
        raise ValueError("Receipt output must be a relative path under receipts/ without traversal")
    parent = ROOT
    for part in relative.parts[:-1]:
        parent = parent / part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError("Receipt parent must be a real directory, not a symlink")
    out = parent / relative.name
    if out.is_symlink():
        raise ValueError("Receipt destination must not be a symlink")
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(out, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt.to_dict(), indent=2, sort_keys=True))
    print(f"\nreceipt_written={rel(out)}")


def build_receipt() -> ProofReceipt:
    receipt = ProofReceipt()
    receipt.checks.append(compile_targets())
    receipt.checks.append(openai_readiness())
    receipt.checks.append(scan_terms("continuum_os_plural_continuums_directive", ["CONTINUUM OS", "multiple continuums"], ["docs", "scripts", "README.md"]))
    receipt.checks.append(scan_for_forbidden_term())
    receipt.checks.append(scan_terms("a2a_no_merged_mind_invariant", ["NO MERGED MIND", "merged mind"], ["a2a", "core", "docs"]))
    receipt.checks.append(scan_terms("inv0_preservation_invariant", ["INV-0", "NOTHING DIES"], ["core", "docs", "canon", "archive"]))
    receipt.checks.append(scan_terms("candidate_not_canon_boundary", ["CANDIDATE", "NOT CANON", "human-root"], ["docs", "canon", "archive", "AGENTS.md"]))
    receipt.checks.append(run_optional_pytest())
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a candidate world-class proof receipt.")
    parser.add_argument("--output", default="receipts/world_class_proof_receipt.json", help="Receipt path relative to repo root. Use empty string to print only.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on FAIL/WARN.")
    args = parser.parse_args()
    receipt = build_receipt()
    write_receipt(receipt, args.output)
    overall = receipt.overall()
    if overall == "CANDIDATE_INCOMPLETE":
        return 1
    if args.strict and overall != "CANDIDATE_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
