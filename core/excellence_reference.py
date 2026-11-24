"""Read-only source reference port for the Atlas engineering program.

CANDIDATE, NOT CANON. This port validates selected reference bytes and prepares
metadata for the primary runtime. It has no network, execution or write API.
The expected digest identifies a selected reference, not an authenticated owner.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

PROGRAM_ID = "ATLAS-EXCELLENCE-1728-20261123"
ARIADNE_SHA256 = "07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6"
CANON_REFERENCE = "ATLAS-UHM-CANON-20261123-001"
SHA = re.compile(r"[a-f0-9]{64}\Z")
GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
TASK = re.compile(r"EX\.W(0[1-9]|1[0-2])\.C(0[1-9]|1[0-2])\.P(0[1-9]|1[0-2])\Z")
ROOM = re.compile(r"[A-Za-z0-9_-]{3,80}\Z")


class ReferenceError(ValueError):
    """The selected reference or requested source task is invalid."""


def _require(value: bool, reason: str) -> None:
    if not value:
        raise ReferenceError(reason)


def _digest(value: Any, pattern=SHA) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result, "duplicate_reference_key")
        result[key] = value
    return result


def _path(value: Any) -> bool:
    return (type(value) is str and 1 <= len(value) <= 500
            and not value.startswith("/") and re.fullmatch(r"[A-Za-z0-9_./-]+", value) is not None
            and all(part not in ("", ".", "..") for part in value.split("/")))


def read_reference(raw: bytes, expected_reference_sha256: str) -> dict:
    """Revalidate bytes on every call; caller edits cannot extend cached scope."""
    _require(type(raw) is bytes and len(raw) <= 1024 * 1024, "bounded_reference_bytes_required")
    _require(_digest(expected_reference_sha256), "expected_reference_digest_required")
    _require(hashlib.sha256(raw).hexdigest() == expected_reference_sha256, "reference_digest_mismatch")
    try:
        record = json.loads(raw, object_pairs_hook=_pairs,
                            parse_constant=lambda _: (_ for _ in ()).throw(ReferenceError("nonfinite_reference_number")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ReferenceError("invalid_reference_json") from exc
    _require(type(record) is dict, "reference_object_required")
    keys = {"schema", "status", "canon_status", "review_status", "program_id", "revision", "engineering_namespace",
            "source_repository", "source_commit", "source_files", "plan_sha256", "counts", "coverage",
            "canon_reference", "completion", "authority", "deployment", "runtime_status"}
    _require(set(record) == keys, "reference_fields_mismatch")
    _require(record["schema"] == "atlas.excellence.source-reference.v1" and record["program_id"] == PROGRAM_ID, "reference_identity_mismatch")
    _require(type(record["revision"]) is int and record["revision"] >= 1, "reference_revision_invalid")
    _require(record["status"] == "PLANNED" and record["canon_status"] == "NOT CANON" and record["review_status"] == "CANDIDATE"
             and record["engineering_namespace"] == "EX1728", "plan_state_required")
    _require(record["source_repository"] == "atlaslattice/Atlas-Intelligence" and _digest(record["source_commit"], GIT_SHA), "immutable_source_commit_required")
    _require(_digest(record["plan_sha256"]), "plan_digest_required")
    files = record["source_files"]
    _require(type(files) is dict and 1 <= len(files) <= 256
             and all(_path(path) and _digest(sha) for path, sha in files.items()), "source_file_pins_required")
    expected_counts = {"workstreams": 12, "capabilities": 144, "phases": 12, "steps": 1728}
    _require(type(record["counts"]) is dict and record["counts"] == expected_counts
             and all(type(n) is int for n in record["counts"].values()), "engineering_counts_invalid")
    _require(record["coverage"] == {"ariadne_source_sha256": ARIADNE_SHA256, "houses": 12, "spheres": 144,
                                     "nodes": 1728, "ordinal_identity_implied": False,
                                     "semantic_crosswalk_status": "SOURCE_REVIEW_REQUIRED"}, "knowledge_scope_invalid")
    _require(record["coverage"]["ordinal_identity_implied"] is False
             and all(type(record["coverage"][key]) is int for key in ("houses", "spheres", "nodes")), "knowledge_scope_types_invalid")
    _require(record["canon_reference"] == {"decision_id": CANON_REFERENCE, "new_canon_changes": False}, "canon_reference_invalid")
    _require(record["canon_reference"]["new_canon_changes"] is False, "canon_reference_types_invalid")
    _require(record["completion"] == {"implemented": 0, "verified": 0, "integrated": 0, "genuine_macroturns": 0}
             and all(type(n) is int for n in record["completion"].values()), "reference_cannot_assert_completed_work")
    _require(record["authority"] == "none" and record["deployment"] is False
             and record["runtime_status"] == "SOURCE_PORT_ONLY", "source_port_boundary_invalid")
    return copy.deepcopy(record)


def describe_reference(raw: bytes, expected_reference_sha256: str) -> dict:
    record = read_reference(raw, expected_reference_sha256)
    return {"schema": "atlas.excellence.source-port-status.v1", "program_id": PROGRAM_ID,
            "status": "REFERENCE_BYTES_VERIFIED_PLAN_EXECUTION_UNOBSERVED", "reference_sha256": expected_reference_sha256,
            "plan_sha256": record["plan_sha256"], "source_commit": record["source_commit"],
            "counts": record["counts"], "completion": record["completion"], "engineering_namespace": "EX1728",
            "canon_reference": record["canon_reference"], "canonical_runtime_required": True,
            "authority": "none", "canon": False, "deployment": False, "host_permissions_verified": False}


def prepare_task_reference(raw: bytes, expected_reference_sha256: str, *, task_id: str,
                           room_id: str, mode: str = "WORK") -> dict:
    record = read_reference(raw, expected_reference_sha256)
    _require(type(task_id) is str and TASK.fullmatch(task_id) is not None, "engineering_task_id_required")
    _require(type(room_id) is str and ROOM.fullmatch(room_id) is not None and mode == "WORK", "work_scope_required")
    return {"kind": "ActionPacket", "schema": "atlas.excellence.source-task-candidate.v1",
            "requested_action": "PREPARE", "status": "SOURCE_REFERENCE_REQUIRES_CANONICAL_TASK_VALIDATOR",
            "source_class": "Work", "room_id": room_id, "mode": mode, "task_id_candidate": task_id,
            "program_id": PROGRAM_ID, "engineering_namespace": "EX1728",
            "source": {"repository": record["source_repository"], "commit": record["source_commit"],
                       "files": record["source_files"], "plan_sha256": record["plan_sha256"],
                       "reference_sha256": expected_reference_sha256},
            "ariadne_source_sha256": ARIADNE_SHA256, "ordinal_identity_implied": False,
            "canon": False, "deployment": False, "authority": "none", "work_posted": False,
            "execution_authorized": False, "source_bodies_included": False,
            "required_next_checks": ["canonical_plan_task_exists", "current_dependency_ledger",
                                     "current_source_pins", "current_work_host_permission"]}
