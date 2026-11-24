"""Optional metadata reference to the canonical Atlas R01 software kernels.

This module validates caller-selected bytes and prepares Work candidates. It has
no network, model, kernel-execution, room-posting, storage, or promotion API. A
digest selects bytes; it does not authenticate the caller or retrieve the source.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re

RELEASE_ID = "ATLAS-CIVILIZATION-R01-20261123-1"
REPOSITORY = "atlaslattice/Atlas-Intelligence"
SOURCE_ROOT = "programs/civilization-r01"
HOUSES = tuple(f"H{i:02}" for i in range(1, 13))
SHA = re.compile(r"[a-f0-9]{64}\Z")
COMMIT = re.compile(r"[a-f0-9]{40}\Z")
ROOM = re.compile(r"[A-Za-z0-9_-]{3,80}\Z")
REQUIRED_FILES = frozenset(SOURCE_ROOT + "/" + path for path in (
    "index.mjs", "runtime/json.mjs", "runtime/dispatch-policy.mjs",
    "integrations/kernel-actions.mjs", "kernels/a-common.mjs", "kernels/b-support.mjs",
    "benchmarks/SUPPORTING_KERNEL_PROTOCOL.json", "outputs/SUPPORTING_KERNEL_RAW.jsonl",
    "outputs/SUPPORTING_KERNEL_ASSESSMENT.json", *(f"kernels/{h}.mjs" for h in HOUSES),
))
PROTOCOL_SHA256 = "e7895c7f39549706eb1e377ebdd2d3c9ae8904d7d492b96f1f9433c286bb2d38"
RAW_SHA256 = "ed03acd0bacd3990d90051e01a9552faadb49bcbea05723d7eed8f59fd45cef6"
ASSESSMENT_SHA256 = "dfcbb79f6b2d531e5220ccba45fb7aff01868211bc2de9fc51d5e4d7793b638b"


class ReferenceError(ValueError):
    """The selected reference or current candidate scope is invalid."""


def _require(ok, reason):
    if not ok:
        raise ReferenceError(reason)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate_reference_key")
        result[key] = value
    return result


def _bounded_json(value, depth=0, budget=None):
    budget = [0] if budget is None else budget
    budget[0] += 1
    _require(depth <= 20 and budget[0] <= 8192, "reference_structure_bound")
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        _require(math.isfinite(value) and abs(value) <= 2**53 - 1, "reference_number_invalid")
    elif type(value) is str:
        _require(len(value) <= 4096, "reference_string_bound")
    elif type(value) is list:
        for item in value:
            _bounded_json(item, depth + 1, budget)
    elif type(value) is dict:
        for key, item in value.items():
            _bounded_json(key, depth + 1, budget)
            _bounded_json(item, depth + 1, budget)
    else:
        raise ReferenceError("reference_json_required")


def _sha(value, pattern=SHA):
    return type(value) is str and pattern.fullmatch(value) is not None


def _source_path(value):
    return (type(value) is str and len(value) <= 300
            and value.startswith(SOURCE_ROOT + "/")
            and re.fullmatch(r"[A-Za-z0-9_./-]+", value) is not None
            and all(part not in ("", ".", "..") for part in value.split("/")))


def read_reference(raw: bytes, expected_reference_sha256: str) -> dict:
    """Revalidate a bounded exact-byte reference; never cache caller authority."""
    _require(type(raw) is bytes and 0 < len(raw) <= 131072, "bounded_reference_bytes_required")
    _require(_sha(expected_reference_sha256), "expected_reference_digest_required")
    _require(hashlib.sha256(raw).hexdigest() == expected_reference_sha256, "reference_digest_mismatch")
    try:
        record = json.loads(raw, object_pairs_hook=_pairs)
        _bounded_json(record)
    except (ValueError, OverflowError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, ReferenceError):
            raise
        raise ReferenceError("invalid_reference_json") from exc
    fields = {"schema", "release_id", "status", "source_repository", "source_commit", "source_root",
              "source_files", "kernel_houses", "dispatch", "benchmark", "authority", "canon",
              "deployment", "source_bodies_included", "specialized_node_contracts_complete",
              "ordinal_identity_implied"}
    _require(type(record) is dict and set(record) == fields, "reference_fields_mismatch")
    _require(record["schema"] == "atlas.civilization.kernel-source-reference.v1"
             and record["release_id"] == RELEASE_ID and record["status"] == "SUPPORTING_CAPABILITY_SOURCE_REFERENCE",
             "release_identity_mismatch")
    _require(record["source_repository"] == REPOSITORY and record["source_root"] == SOURCE_ROOT
             and _sha(record["source_commit"], COMMIT), "immutable_canonical_source_required")
    files = record["source_files"]
    _require(type(files) is dict and REQUIRED_FILES <= set(files) and len(files) <= 128
             and all(_source_path(path) and _sha(pin) for path, pin in files.items()), "source_fingerprints_required")
    _require(files[SOURCE_ROOT + "/benchmarks/SUPPORTING_KERNEL_PROTOCOL.json"] == PROTOCOL_SHA256
             and files[SOURCE_ROOT + "/outputs/SUPPORTING_KERNEL_RAW.jsonl"] == RAW_SHA256
             and files[SOURCE_ROOT + "/outputs/SUPPORTING_KERNEL_ASSESSMENT.json"] == ASSESSMENT_SHA256,
             "benchmark_source_fingerprints_mismatch")
    _require(record["kernel_houses"] == list(HOUSES), "kernel_ids_required")
    _require(record["dispatch"] == {h: "REFERENCE_QUERY" if h == "H02" else "INDEXED_QUERY" for h in HOUSES},
             "release_dispatch_mismatch")
    evidence = record["benchmark"]
    _require(evidence == {
        "scope": "LOCAL_SYNTHETIC_SUPPORTING_KERNEL_COMPARISON",
        "protocol_sha256": PROTOCOL_SHA256, "raw_sha256": RAW_SHA256,
        "assessment_sha256": ASSESSMENT_SHA256, "registered_kernel_hypotheses": 12,
        "local_gain_candidates": 11, "observed_regressions": ["H02"],
        "original_1728_primary_metric_credit": 0, "production_gains_verified": 0,
        "whole_system_gain_claimed": False,
    }, "benchmark_scope_mismatch")
    _require(all(type(evidence[k]) is int for k in ("registered_kernel_hypotheses", "local_gain_candidates",
                 "original_1728_primary_metric_credit", "production_gains_verified"))
             and evidence["whole_system_gain_claimed"] is False, "benchmark_types_invalid")
    _require(record["authority"] == "none" and record["canon"] is False and record["deployment"] is False
             and record["source_bodies_included"] is False and record["ordinal_identity_implied"] is False
             and type(record["specialized_node_contracts_complete"]) is int
             and record["specialized_node_contracts_complete"] == 0, "source_reference_cannot_self_promote")
    return copy.deepcopy(record)


def prepare_kernel_reference(raw: bytes, expected_reference_sha256: str, *, house_id: str,
                             room_id: str, mode: str = "WORK") -> dict:
    """Prepare metadata for an explicit supporting-kernel ID; never infer an HSN."""
    record = read_reference(raw, expected_reference_sha256)
    _require(type(house_id) is str and house_id in HOUSES, "supporting_kernel_house_required")
    _require(type(mode) is str and mode == "WORK" and type(room_id) is str
             and ROOM.fullmatch(room_id) is not None, "current_work_scope_required")
    return {
        "kind": "ActionPacket", "schema": "atlas.civilization.kernel-reference-candidate.v1",
        "requested_action": "PREPARE", "status": "REFERENCE_BYTES_VERIFIED_SOURCE_COMMIT_UNCHECKED",
        "source_class": "Work", "room_id": room_id, "mode": mode, "release_id": RELEASE_ID,
        "supporting_kernel_house": house_id, "dispatch_candidate": record["dispatch"][house_id],
        "implementation_scope": "SUPPORTING_CAPABILITY",
        "source": {"repository": REPOSITORY, "commit": record["source_commit"], "root": SOURCE_ROOT,
                   "files": record["source_files"], "reference_sha256": expected_reference_sha256},
        "benchmark": record["benchmark"], "ordinal_identity_implied": False,
        "specialized_node_contracts_complete": 0, "source_files_retrieved": False,
        "host_permissions_verified": False, "current_return_fence_verified": False,
        "execution_authorized": False, "work_posted": False, "source_bodies_included": False,
        "canon": False, "deployment": False, "authority": "none",
        "required_next_checks": ["canonical_release_and_source_fingerprints", "current_work_read_permission",
                                 "current_return_fence", "canonical_kernel_input_and_output_bounds"],
    }
