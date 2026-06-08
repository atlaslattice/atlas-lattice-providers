#!/usr/bin/env python3
"""One-command world-class proof runner for Atlas Lattice / Continuum OS.

This command does not promote anything to canon. It generates a candidate proof
receipt showing which operability checks passed, failed, or were skipped.

Default mode is non-destructive and CI-safe. Use --strict locally when you want
fail-fast behavior.
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

    def overall(self) -> str:
        if any(c.status == "FAIL" for c in self.checks):
            return "CANDIDATE_INCOMPLETE"
        if any(c.status == "WARN" for c in self.checks):
            return "CANDIDATE_WITH_WARNINGS"
        return "CANDIDATE_READY"

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["overall"] = self.overall()
        return data


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


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
        if not path.exists():
            missing.append(name)
            continue
        try:
            py_compile.compile(str(path), doraise=True)
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
    existing = [t for t in tests if (ROOT / t).exists()]
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
        if path.is_file():
            paths = [path]
        elif path.is_dir():
            paths = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".py", ".md", ".yaml", ".yml", ".json", ".txt"}]
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
    for root in roots:
        path = ROOT / root
        if path.is_file():
            paths = [path]
        elif path.is_dir():
            paths = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".py", ".md", ".yaml", ".yml", ".json", ".txt"}]
        else:
            continue
        for p in paths:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "Continuity OS".lower() in text.lower():
                hits.append(rel(p))
    if hits:
        return CheckResult("continuum_not_continuity_name_guard", "FAIL", "Forbidden legacy name 'Continuity OS' found", hits[:50])
    return CheckResult("continuum_not_continuity_name_guard", "PASS", "No forbidden 'Continuity OS' references found")


def openai_readiness() -> CheckResult:
    files = [
        ROOT / "providers/openai/responses_api_spine.py",
        ROOT / "providers/provider_openai.py",
        ROOT / "docs/OPENAI_INTEROP_MAP.md",
        ROOT / "AGENTS.md",
    ]
    present = [rel(f) for f in files if f.exists()]
    missing = [rel(f) for f in files if not f.exists()]
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if missing:
        return CheckResult("openai_operability_surface", "WARN", f"missing={missing}; OPENAI_API_KEY_present={has_key}", present)
    return CheckResult("openai_operability_surface", "PASS", f"OPENAI_API_KEY_present={has_key}; live requires explicit simulate=False", present)


def write_receipt(receipt: ProofReceipt, output: Optional[str]) -> None:
    if not output:
        print(json.dumps(receipt.to_dict(), indent=2, sort_keys=True))
        return
    out = ROOT / output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    if args.strict and receipt.overall() != "CANDIDATE_READY":
        return 1
    return 0 if not any(c.status == "FAIL" for c in receipt.checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
