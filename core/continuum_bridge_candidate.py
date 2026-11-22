"""Offline continuum-to-Packet96 candidate adapter; never a transport or grant.

Public source code only. No network, file writes, sessions, real agent actions,
rights authentication or canonical promotion. Deliberately omits raw source text.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

SCHEMA = "atlas.continuum-link/candidate-v0.1"
PACKET96 = "atlas.transparent-packet96/candidate-v0.1"
COORD = re.compile(r"^H(0[0-9]|1[01])\.S(0[0-9]|1[01])\.N(0[0-9]|1[01])$")
D = re.compile(r"^D(0[1-9]|1[0-2])$")
BRIDGES = frozenset({"message", "receipt", "claim", "mirror", "review", "simulation", "human_root_decision"})
SCOPES = frozenset({"PUBLIC_REPORTED", "WORK_REPORTED"})
MAX_BYTES = 65536


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("duplicate JSON key")
        result[k] = v
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError("nonfinite JSON constant: " + value)


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _text(v: Any) -> bool:
    return type(v) is str and bool(v.strip())


def propose(source: dict | str | bytes) -> dict:
    """Return a sanitized, non-delivered review proposal or an inert HOLD.

    Input labels and byte hashes are claims, not independently verified rights.
    Returned payloads never embed source_ref, source body or dissent prose.
    """
    reasons: list[str] = []
    if type(source) is dict:
        try:
            raw = json.dumps(source, ensure_ascii=False, allow_nan=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError, OverflowError, UnicodeEncodeError, RecursionError):
            return {"status": "HOLD", "reason_codes": ["UNSERIALIZABLE_SOURCE"],
                    "source_sha256": None, "source_bytes": None, "packet96": None, "link": None}
    elif type(source) is str:
        try:
            raw = source.encode("utf-8")
        except UnicodeEncodeError:
            raw = b""
            reasons.append("INVALID_UTF8")
    elif type(source) is bytes:
        raw = source
    else:
        return {"status": "HOLD", "reason_codes": ["UNSUPPORTED_SOURCE_TYPE"],
                "source_sha256": None, "source_bytes": None, "packet96": None, "link": None}
    digest = _digest(raw)
    if len(raw) > MAX_BYTES:
        reasons.append("SOURCE_TOO_LARGE")
    obj = {}
    if not reasons:
        try:
            obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate,
                             parse_constant=_reject_constant)
            if type(obj) is not dict:
                reasons.append("NOT_AN_OBJECT")
                obj = {}
        except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
            reasons.append("UNPARSEABLE_JSON")
    if not reasons:
        for key in ("claim_id", "source_ref", "source_continuum_id", "target_continuum_id"):
            if not _text(obj.get(key)):
                reasons.append("MISSING_" + key.upper())
        if not (type(obj.get("coordinate")) is str and COORD.fullmatch(obj["coordinate"])):
            reasons.append("INVALID_12X12X12_COORDINATE")
        if obj.get("bridge_type") not in BRIDGES if type(obj.get("bridge_type")) is str else True:
            reasons.append("INVALID_BRIDGE_TYPE")
        if obj.get("source_scope") not in SCOPES if type(obj.get("source_scope")) is str else True:
            reasons.append("PRIVATE_OR_UNKNOWN_SCOPE")
        if obj.get("rights_status") != "UNVERIFIED":
            reasons.append("UNSUPPORTED_RIGHTS_ATTESTATION")
        if obj.get("source_continuum_id") == obj.get("target_continuum_id"):
            reasons.append("SAME_CONTINUUM_NOT_A_CROSS_BRIDGE")
        for key in ("canon", "deployment", "collapse_allowed", "identity_fusion_allowed"):
            if obj.get(key) is not False:
                reasons.append("NONFALSE_" + key.upper())
        if obj.get("authority") != "none" or obj.get("requested_action", "review") != "review":
            reasons.append("AUTHORITY_OR_ACTION_REQUEST")
        if obj.get("no_harvest") is not False or obj.get("mode") not in ("WORK", "PUBLIC"):
            reasons.append("PRIVATE_MODE_OR_UNKNOWN_HARVEST")
        affinities = obj.get("d_affinity", [])
        if type(affinities) is not list or any(type(x) is not str or not D.fullmatch(x) for x in affinities):
            reasons.append("BAD_D_AFFINITY")
        dissent = obj.get("dissent_refs", [])
        if type(dissent) is not list or any(not _text(x) for x in dissent):
            reasons.append("BAD_DISSENT_REFS")
    if reasons:
        return {"status": "HOLD", "reason_codes": sorted(set(reasons)),
                "source_sha256": digest, "source_bytes": len(raw),
                "packet96": None, "link": None, "authority_effect": "NONE"}

    # Source pointer and dissent references are hashed to prevent accidental
    # transfer of private identifiers; this is not long-term archival custody.
    source_pointer = "sha256:" + _digest(obj["source_ref"].encode("utf-8"))
    dissent_hashes = ["sha256:" + _digest(x.encode("utf-8")) for x in obj["dissent_refs"]]
    link_id = "candidate.bridge." + digest[:24]
    link = {
        "schema_version": SCHEMA, "link_id": link_id,
        "source_continuum_id": obj["source_continuum_id"],
        "target_continuum_id": obj["target_continuum_id"],
        "bridge_type": obj["bridge_type"], "source_ref": source_pointer,
        "status": "CANDIDATE", "canon": False, "deployment": False,
        "authority": "none", "collapse_allowed": False,
        "identity_fusion_allowed": False, "dissent_preserved": True,
        "inv0_preservation_required": True, "raw_content_transferred": False,
        "provenance_refs": ["sha256:" + digest], "dissent_refs": dissent_hashes,
        "human_root_gate": {"required": True, "state": "not_granted", "decision_route": "independent-human-review"},
        "notes": "Pointer-only local candidate; scope and rights self-declared, no source custody or external verification",
    }
    packet = {
        "schema_version": PACKET96, "packet_id": link_id,
        "sender": "offline-bridge-proposer", "recipient": "offline-review-queue",
        "coordinate": obj["coordinate"], "status": "CANDIDATE",
        "canon": False, "deployment": False, "authority": "none",
        "identity_scope": "DISTINCT_PARTICIPANTS", "host_attestation": "NONE",
        "semantic_review": "UNREVIEWED", "same_as": False,
        "dissent": [{"ref_hash": h} for h in dissent_hashes],
        "provenance": {"source_ref": source_pointer, "source_cut": "SELF_DECLARED_UNVERIFIED"},
        "receipt": {"assurance": "LOCAL_UNATTESTED", "delivered": False},
        "payload": {"link_id": link_id, "bridge_type": obj["bridge_type"],
                    "source_continuum_id": obj["source_continuum_id"],
                    "target_continuum_id": obj["target_continuum_id"],
                    "source_sha256": digest, "d_affinity": sorted(set(obj["d_affinity"]))},
    }
    return {"status": "REVIEWABLE_LOCAL_ONLY", "reason_codes": [],
            "source_sha256": digest, "source_bytes": len(raw),
            "packet96": packet, "link": link, "authority_effect": "NONE",
            "execution_allowed": False, "host_attestation": "NOT_ATTESTED"}
