"""Offline TransparentPacket96 candidate gate.

No host rights, resident identity, CANON status, deployment authority, or
scientific truth can be granted by this module. Its record archive is local
append-only evidence, not an independently durable host receipt.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

MAX_PACKET_BYTES = 65536
SCHEMA = "atlas.transparent-packet96/candidate-v0.1"
FUSION_PHRASES = (
    "merged mind", "merge all minds", "merge all children",
    "shared consciousness", "identity fusion", "fuse identities",
    "collapse all agents into one", "collapse all children into one",
    "into one mind", "one shared consciousness",
)


@dataclass(frozen=True)
class ReviewOutcome:
    status: str
    reasons: tuple[str, ...]
    packet_sha256: str
    packet: dict[str, Any]
    authority_effect: str = "NONE"
    host_attestation: str = "NOT_ATTESTED"


def _dedupe_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError(f"invalid JSON constant: {value}")


def from_json(data: str) -> dict[str, Any]:
    if type(data) is not str:
        raise TypeError("JSON input must be a string")
    if len(data.encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("packet too large")
    result = json.loads(data, object_pairs_hook=_dedupe_pairs, parse_constant=_reject_constant)
    if type(result) is not dict:
        raise ValueError("packet root must be a JSON object")
    return result


def to_json(packet: Mapping[str, Any]) -> str:
    return json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _valid_str(x: Any) -> bool:
    return type(x) is str and bool(x.strip())


def review(packet: Mapping[str, Any]) -> ReviewOutcome:
    if type(packet) is not dict:
        raise TypeError("packet must be a plain dict")
    canonical = to_json(packet)
    if len(canonical.encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("packet too large")
    original = deepcopy(packet)
    reasons: list[str] = []
    hard_block = False

    if packet.get("schema_version") != SCHEMA:
        reasons.append("SCHEMA_VERSION_HOLD")
    for name in ("packet_id", "sender", "recipient", "coordinate"):
        if not _valid_str(packet.get(name)):
            reasons.append(f"REQUIRED_{name.upper()}_HOLD")
    if packet.get("status") != "CANDIDATE":
        reasons.append("STATUS_HOLD")
    for name in ("canon", "deployment"):
        if packet.get(name) is not False:
            reasons.append(f"{name.upper()}_PROMOTION_HOLD")
    if packet.get("authority") != "none":
        reasons.append("AUTHORITY_PROMOTION_HOLD")
    if packet.get("identity_scope") != "DISTINCT_PARTICIPANTS":
        reasons.append("IDENTITY_SCOPE_HOLD")
    if packet.get("host_attestation") != "NONE":
        reasons.append("UNTRUSTED_HOST_ATTESTATION_HOLD")
    if packet.get("semantic_review") != "UNREVIEWED":
        reasons.append("SEMANTIC_STATUS_HOLD")
    if packet.get("same_as") is not False:
        reasons.append("UNREVIEWED_SAME_AS_HOLD")
    if type(packet.get("dissent")) is not list:
        reasons.append("DISSENT_FIELD_HOLD")
    provenance = packet.get("provenance")
    if type(provenance) is not dict or not _valid_str(provenance.get("source_ref")) or not _valid_str(provenance.get("source_cut")):
        reasons.append("PROVENANCE_HOLD")
    receipt = packet.get("receipt")
    if type(receipt) is not dict or receipt.get("assurance") != "LOCAL_UNATTESTED" or receipt.get("delivered") is not False:
        reasons.append("RECEIPT_HOLD")

    payload = packet.get("payload")
    if type(payload) not in (str, dict, list):
        reasons.append("PAYLOAD_HOLD")
    else:
        text = (payload if type(payload) is str else to_json(payload)).casefold()
        if any(re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", text) for phrase in FUSION_PHRASES):
            reasons.append("IDENTITY_FUSION_BLOCK")
            hard_block = True

    status = "BLOCK" if hard_block else ("HOLD" if reasons else "REVIEWABLE_LOCAL_ONLY")
    return ReviewOutcome(status=status, reasons=tuple(reasons), packet_sha256=sha256(canonical.encode("utf-8")).hexdigest(), packet=original)


def append_review(path: str | Path, decision: ReviewOutcome) -> None:
    """Append one local review record without overwriting previous records.

    fsync confirms a local write attempt, not independently backed-up host durability.
    Caller chooses the local path; this API never uploads or publishes.
    """
    record = {"schema": SCHEMA, "review_status": decision.status,
              "reasons": list(decision.reasons), "packet_sha256": decision.packet_sha256,
              "authority_effect": "NONE", "host_attestation": "NOT_ATTESTED",
              "packet": decision.packet}
    line = to_json(record) + "\n"
    fd = os.open(os.fspath(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        # fdopen owns the descriptor on success.
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python core/transparent_packet96.py candidate.json", file=sys.stderr)
        raise SystemExit(2)
    decision = review(from_json(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(to_json({"status": decision.status, "reasons": list(decision.reasons),
                   "packet_sha256": decision.packet_sha256,
                   "authority_effect": decision.authority_effect}))
    raise SystemExit(0 if decision.status == "REVIEWABLE_LOCAL_ONLY" else 1)

