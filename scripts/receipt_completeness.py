#!/usr/bin/env python3
"""Offline, candidate-only receipt-completeness rubric (not a truth verifier).

A field score is evidence *documentation* quality, not evidence authenticity.
No network, account, disk writes, canon promotion, or agent execution.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict

FIELDS = (
    "source_link", "commit_sha", "lifecycle_status", "authority_label",
    "canon_deployment", "verification", "tests", "human_root_gate",
    "inv0_preservation", "dissent_path",
)
LIFECYCLE = {"RAW", "PARSED", "CLAIM", "CANDIDATE", "REVIEWED", "CONTRADICTED", "SUPERSEDED", "QUARANTINED", "RATIFIED", "CANON", "DEPLOYED"}
VERIFICATION = {"visible", "reported", "local-only", "branch-only", "needs-fetch", "missing"}
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")


def filled(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def https_link(value: Any) -> bool:
    return filled(value) and value.startswith("https://") and " " not in value


def score(record: Dict[str, Any]) -> Dict[str, Any]:
    """Score 10 named fields 0/1/2; preserve reasons and cap evidence claims."""
    if not isinstance(record, dict):
        raise ValueError("A receipt must be a JSON object")
    results = {}

    def mark(field: str, points: int, reason: str) -> None:
        results[field] = {"points": points, "max": 2, "reason": reason}

    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    url = source.get("url")
    state = source.get("verification")
    if https_link(url):
        if state == "visible" and https_link(source.get("readback_url")) and filled(source.get("checked_at")):
            mark("source_link", 2, "URL plus declared visible readback reference; existence not independently checked by this tool")
        else:
            mark("source_link", 1, "Source URL declared; independent readback not documented")
    else:
        mark("source_link", 0, "No usable source URL")

    commit = record.get("commit") if isinstance(record.get("commit"), dict) else {}
    sha = commit.get("sha")
    curl = commit.get("url")
    if isinstance(sha, str) and SHA40.fullmatch(sha):
        if https_link(curl) and sha.lower() in curl.lower():
            mark("commit_sha", 2, "40-hex SHA and matching commit URL documented")
        else:
            mark("commit_sha", 1, "40-hex SHA given without matching link")
    else:
        mark("commit_sha", 0, "Missing or invalid full commit SHA (blob SHA is not a commit SHA)")

    lifecycle = record.get("lifecycle")
    recognized_lifecycle = isinstance(lifecycle, str) and lifecycle in LIFECYCLE
    mark("lifecycle_status", 2 if recognized_lifecycle else 1 if filled(lifecycle) else 0,
         "Known lifecycle label" if recognized_lifecycle else "Unrecognized or missing lifecycle label")

    authority = record.get("authority")
    recognized_authority = isinstance(authority, str) and authority in {"none", "human-root", "delegated-explicit"}
    mark("authority_label", 2 if recognized_authority else 1 if filled(authority) else 0,
         "Explicit authority scope" if recognized_authority else "Missing or unclear authority scope")

    canon, deployment = record.get("canon"), record.get("deployment")
    if isinstance(canon, bool) and isinstance(deployment, bool):
        mark("canon_deployment", 2, "Both flags explicitly Boolean; values are claims, not authorization")
    elif isinstance(canon, bool) or isinstance(deployment, bool):
        mark("canon_deployment", 1, "Only one explicit Boolean flag")
    else:
        mark("canon_deployment", 0, "Canon/deployment flags missing or non-Boolean")

    verification = record.get("verification") if isinstance(record.get("verification"), dict) else {}
    vstate = verification.get("state")
    if vstate == "visible" and https_link(verification.get("receipt_url")) and filled(verification.get("checked_at")):
        mark("verification", 2, "Visible verification declared with dated receipt link; no network lookup performed")
    elif vstate in VERIFICATION:
        mark("verification", 1, "Verification state disclosed; not independently evidenced")
    else:
        mark("verification", 0, "Missing/unknown verification state")

    tests = record.get("tests") if isinstance(record.get("tests"), dict) else {}
    tstate = tests.get("state")
    if tstate == "passed" and filled(tests.get("command")) and https_link(tests.get("receipt_url")):
        mark("tests", 2, "Pass declared with command and linked output; execution not repeated")
    elif tstate == "not_testable" and filled(tests.get("reason")):
        mark("tests", 2, "Explicit non-testable rationale")
    elif (tstate == "not_run" and filled(tests.get("reason"))) or (tstate == "reported_passed" and filled(tests.get("command"))):
        mark("tests", 1, "Unverified/unfinished testing disclosed")
    else:
        mark("tests", 0, "No qualifying test evidence or reason")

    gate = record.get("human_root_gate") if isinstance(record.get("human_root_gate"), dict) else {}
    if gate.get("required") is True and filled(gate.get("decision_route")) and gate.get("state") in {"pending", "not_granted"}:
        mark("human_root_gate", 2, "Human decision route stated; gate remains ungranted")
    elif "required" in gate and isinstance(gate.get("required"), bool):
        mark("human_root_gate", 1, "Gate requirement declared without a complete ungranted decision route")
    else:
        mark("human_root_gate", 0, "Human-root gate omitted")

    inv0 = record.get("inv0_preservation") if isinstance(record.get("inv0_preservation"), dict) else {}
    if filled(inv0.get("path")) and filled(inv0.get("method")):
        mark("inv0_preservation", 2, "Specific preservation path and method described; no write verified")
    elif filled(inv0.get("statement")):
        mark("inv0_preservation", 1, "Preservation principle stated without an executable path")
    else:
        mark("inv0_preservation", 0, "Preservation path not described")

    dissent = record.get("dissent") if isinstance(record.get("dissent"), dict) else {}
    if filled(dissent.get("review_route")) and filled(dissent.get("preservation_route")):
        mark("dissent_path", 2, "Dissent review and retention routes explicitly described")
    elif filled(dissent.get("statement")):
        mark("dissent_path", 1, "Dissent mentioned without a retention route")
    else:
        mark("dissent_path", 0, "No dissent/contradiction path")

    total = sum(x["points"] for x in results.values())
    assert tuple(results) == FIELDS
    evidence_fields = ("source_link", "commit_sha", "verification", "tests")
    evidence_ready = all(results[f]["points"] == 2 for f in evidence_fields)
    return {
        "artifact_id": record.get("artifact_id", "unspecified"),
        "points": total, "max_points": 20,
        "percent": round(total * 100 / 20, 1),
        "rubric_version": "candidate-v0.1",
        "evidence_gate": "documented-not-authenticated" if evidence_ready else "blocked-missing-or-unverified-receipts",
        "dimensions": results,
        "limitation": "DOCUMENTATION COMPLETENESS ONLY; no live verification, authenticity, truth, canon, or deployment inference",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="one JSON receipt, or an array of receipts")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    records = payload if isinstance(payload, list) else [payload]
    print(json.dumps([score(x) for x in records], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
