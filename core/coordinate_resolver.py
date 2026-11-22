"""Strict, inert H-S-N candidate routing; not authority, verification, or canon.

Existing lattice_coordinates.py accepts broad legacy syntax and may silently fall
back to Earth. This separate boundary does *not* use that permissive parser.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

EARTH = "H00.S00.N00"
# Do not conflate the historical CONTINUUM zero-based grid with Ariadne v0.7:
# both have 1,728 positions but disagree on the source coordinate range.
LEGACY_EDITION = "LEGACY_ZERO_BASED_12"
ARIADNE_EDITION = "ARIADNE_V07"
ARIADNE_SOURCE_SHA256 = "07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6"
LEGACY_HSN = re.compile(r"^H(0\d|1[01])\.S(0\d|1[01])\.N(0\d|1[01])$")
ARIADNE_HSN = re.compile(r"^H(0[1-9]|1[0-2])\.S(0[1-9]|1[0-2])\.N(0[1-9]|1[0-2])$")
HSN = LEGACY_HSN  # compatibility alias for existing zero-based callers
D_TAG = re.compile(r"^D(0[1-9]|1[0-2])$")
BRIDGES = {"message", "receipt", "claim", "mirror", "review", "simulation", "human_root_decision"}


def _present(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _json_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()).hexdigest()


def _declared_private_mode(value: Any) -> bool:
    """Self-declared private/no-harvest metadata is a one-way restriction."""
    if type(value) is not dict:
        return False
    return (("mode" in value and
             (type(value["mode"]) is not str or value["mode"] not in ("WORK", "PUBLIC")))
            or ("no_harvest" in value and value["no_harvest"] is not False))


def _private_hold_packet() -> dict:
    # Neither content nor fingerprint/byte-length of protected input is retained.
    return {"schema": "coordinate-candidate/v0.1", "route": "quarantine",
            "errors": ["private_or_unknown_source_mode_no_import"],
            "original_claim": None, "claim_fingerprint_sha256": None,
            "original_coordinate": None, "earth_reference": EARTH,
            "d_affinity": [],
            "provenance": {"source_ref": None, "source_url": None,
                           "verification_state": "private_source_held"},
            "status": "HELD_PRIVATE_MODE", "canon": False,
            "deployment": False, "authority": "none",
            "human_root_gate": "not_granted"}


def resolve_to_earth(claim: Any) -> dict:
    """Retain unmodified source claim; label structural route or quarantine.

    Structural validation is not an independent source verification. A valid
    candidate still needs human review; no packet can self-promote.
    """
    if _declared_private_mode(claim):
        return _private_hold_packet()
    original = copy.deepcopy(claim)
    data = claim if isinstance(claim, dict) else {}
    errors = []
    for key in ("claim_id", "source_ref", "source_continuum_id"):
        if not _present(data.get(key)):
            errors.append(f"missing_{key}")
    coordinate = data.get("coordinate")
    edition = data.get("coordinate_edition", LEGACY_EDITION)
    coordinate_pattern = (LEGACY_HSN if edition == LEGACY_EDITION else
                          ARIADNE_HSN if edition == ARIADNE_EDITION else None)
    if type(edition) is not str or coordinate_pattern is None:
        errors.append("invalid_coordinate_edition")
    if not isinstance(coordinate, str) or coordinate_pattern is None or not coordinate_pattern.fullmatch(coordinate):
        errors.append("invalid_12x12x12_coordinate")
    # An explicit, source-pinned edition is required to route Ariadne H12;
    # never silently reinterpret historical zero-based coordinates.
    digest = data.get("coordinate_registry_digest")
    if edition == ARIADNE_EDITION and digest != ARIADNE_SOURCE_SHA256:
        errors.append("ariadne_source_digest_required")
    elif edition == LEGACY_EDITION and digest is not None:
        errors.append("legacy_must_not_claim_ariadne_digest")
    if data.get("canon") is True or data.get("deployment") is True or data.get("authority") not in (None, "none"):
        errors.append("attempted_self_promotion")
    if data.get("identity_fusion_allowed") is True or data.get("collapse_allowed") is True:
        errors.append("prohibited_identity_collapse")
    source_url = data.get("source_url")
    if source_url is not None and (not _present(source_url) or not source_url.startswith("https://")):
        errors.append("invalid_source_url")
    target = data.get("target_continuum_id")
    if target is not None and not _present(target):
        errors.append("invalid_target_continuum")
    bridge = data.get("bridge_type", "claim")
    if not isinstance(bridge, str) or bridge not in BRIDGES:
        errors.append("invalid_bridge_type")
    d_tags = data.get("d_affinity", [])
    if not isinstance(d_tags, list) or any(not isinstance(d, str) or not D_TAG.fullmatch(d) for d in d_tags):
        errors.append("invalid_d_affinity")
        normalized_d = []
    else:
        normalized_d = sorted(set(d_tags))
    # A hash is only a local reproducibility fingerprint, never a signature.
    packet = {
        "schema": "coordinate-candidate/v0.1",
        "route": "quarantine" if errors else "candidate_review",
        "errors": errors,
        "original_claim": original,
        "claim_fingerprint_sha256": _json_hash(original),
        "original_coordinate": coordinate,
        "earth_reference": EARTH,
        "d_affinity": normalized_d,
        "provenance": {"source_ref": data.get("source_ref"), "source_url": source_url,
                       "verification_state": "unverified_claim"},
        "continuum_context": {"source_continuum_id": data.get("source_continuum_id"),
                              "target_continuum_id": target, "bridge_type": bridge,
                              "collapse_allowed": False, "identity_fusion_allowed": False,
                              "dissent_preserved": True, "inv0_preservation_required": True},
        "status": "CANDIDATE_NOT_CANON", "canon": False, "deployment": False,
        "authority": "none", "human_root_gate": "not_granted",
    }
    # Preserve the v0.1 *wire output* for historical callers, not merely their
    # validation behavior. Explicit edition-aware calls receive v0.2 metadata.
    if "coordinate_edition" in data or "coordinate_registry_digest" in data:
        packet["schema"] = "coordinate-candidate/v0.2"
        packet["coordinate_edition"] = edition if type(edition) is str and coordinate_pattern is not None else "UNRECOGNIZED"
        packet["coordinate_registry_digest"] = ARIADNE_SOURCE_SHA256 if edition == ARIADNE_EDITION else None
    return packet


def validate_grounding(resolved: Any) -> dict:
    """Structural acceptance only; a tampered or failed packet is not accepted."""
    problems = []
    if not isinstance(resolved, dict):
        return {"valid": False, "reasons": ["not_a_packet"]}
    if resolved.get("earth_reference") != EARTH:
        problems.append("wrong_earth_reference")
    if resolved.get("route") != "candidate_review" or resolved.get("errors"):
        problems.append("quarantine_or_error")
    if resolved.get("canon") is not False or resolved.get("deployment") is not False or resolved.get("authority") != "none":
        problems.append("authority_leak")
    if resolved.get("human_root_gate") != "not_granted":
        problems.append("human_root_gate_bypassed")
    ctx = resolved.get("continuum_context") if isinstance(resolved.get("continuum_context"), dict) else {}
    if ctx.get("collapse_allowed") is not False or ctx.get("identity_fusion_allowed") is not False:
        problems.append("continuum_collapse")
    original = resolved.get("original_claim")
    if not isinstance(original, dict) or resolved.get("claim_fingerprint_sha256") != _json_hash(original):
        problems.append("source_fingerprint_mismatch")
    if not problems:
        rechecked = resolve_to_earth(original)
        if rechecked["route"] != "candidate_review":
            problems.append("source_no_longer_valid")
        for key in ("schema", "original_coordinate", "coordinate_edition", "coordinate_registry_digest", "d_affinity", "provenance", "continuum_context", "status", "route", "errors", "earth_reference"):
            if resolved.get(key) != rechecked.get(key):
                problems.append("derived_field_mismatch:" + key)
    return {"valid": not problems, "reasons": problems,
            "meaning": "structural candidate packet only; provenance authenticity unverified"}


def wrap_as_coordinate_packet(payload: Any, metadata: Any = None) -> dict:
    """Metadata is enclosed, never allowed to override authority or route."""
    if _declared_private_mode(payload) or _declared_private_mode(metadata):
        return _private_hold_packet()
    packet = resolve_to_earth(payload)
    if metadata is not None:
        packet["caller_metadata"] = copy.deepcopy(metadata)
    return packet


def escalate_to_human_root(reason: str, payload: Any) -> dict:
    """Inert escalation proposal: no messaging, notification or decision grant."""
    return {"type": "human_root_review_candidate", "status": "NOT_SENT",
            "reason": reason if _present(reason) else "unspecified",
            "payload": copy.deepcopy(payload), "payload_sha256": _json_hash(payload),
            "authority": "none", "canon": False, "deployment": False,
            "human_root_gate": "not_granted"}
