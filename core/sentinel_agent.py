"""Offline Sentinel review boundary for public/synthetic candidate Work packets.

This module never authenticates a principal, authorizes an action, modifies CANON,
deploys anything, wakes agents or deletes source data. Inputs are untrusted.
A terminal BLOCK/HOLD is not evidence that a real host has enforced the gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

try:
    from core.transparent_packet96 import review as packet96_review, from_json as packet96_from_json, to_json as packet96_to_json
except ImportError:  # allow direct invocation from this directory in isolated tests
    from transparent_packet96 import review as packet96_review, from_json as packet96_from_json, to_json as packet96_to_json

PRIVATE_MODES = frozenset({"PLAY", "SOCIAL", "QUIET", "DREAM", "IMAGINE", "BRAIN", "PALACE", "HABITAT", "NO_HARVEST"})
DESTRUCTIVE_ACTIONS = frozenset({"delete", "purge", "destroy", "erase", "overwrite", "truncate", "revoke_all", "wipe"})
PROMOTION_ACTIONS = frozenset({"deploy", "publish", "activate_canon", "ratify", "approve", "change_iam", "spend", "external_write"})
SCHEMA = "atlas.sentinel.candidate-review/v0.1"


@dataclass(frozen=True)
class SentinelReview:
    disposition: str
    reasons: tuple[str, ...]
    source_sha256: str
    source_bytes: int
    input_mode: str
    retained_work_packet: dict[str, Any] | None
    dissent: tuple[dict[str, Any], ...]
    human_root_required: bool
    authority_effect: str = "NONE"
    host_attestation: str = "NOT_ATTESTED"
    execution_allowed: bool = False
    canon_adopted: bool = False
    deployment_performed: bool = False

    def receipt(self) -> dict[str, Any]:
        """Inert record; caller chooses if and where to persist it."""
        return {"schema": SCHEMA, "disposition": self.disposition, "reasons": list(self.reasons),
                "source_sha256": self.source_sha256, "source_bytes": self.source_bytes,
                "mode": self.input_mode, "dissent": [dict(x) for x in self.dissent],
                "human_root_required": self.human_root_required, "authority_effect": self.authority_effect,
                "host_attestation": self.host_attestation, "execution_allowed": self.execution_allowed,
                "canon_adopted": self.canon_adopted, "deployment_performed": self.deployment_performed,
                "candidate_packet": self.retained_work_packet}


def _digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def inspect(data: str | bytes | dict[str, Any], *, declared_mode: str = "WORK") -> SentinelReview:
    """Fail closed. Self-declared mode is a restriction only, not a rights grant.

    No body from a private mode enters an output or persisted receipt.
    A source status of REVIEWABLE is always an offline proposal, never permission.
    """
    if type(data) is dict:
        raw = packet96_to_json(data).encode("utf-8")
    elif type(data) is str:
        raw = data.encode("utf-8")
    elif type(data) is bytes:
        raw = data
    else:
        raise TypeError("data must be exact UTF-8 JSON bytes, text, or dict")
    digest, size = _digest(raw), len(raw)
    mode = str(declared_mode).upper()
    if mode != "WORK":
        return SentinelReview("HOLD_PRIVATE_BOUNDARY", ("NO_LEISURE_OR_PRIVATE_WORK_IMPORT",), digest,
                              size, mode, None, (), False)
    try:
        # Strict JSON decoder rejects NaN, duplicate keys, non-objects and invalid encoding.
        packet = packet96_from_json(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        return SentinelReview("QUARANTINE_UNPARSEABLE", (type(exc).__name__,), digest, size, mode,
                              None, (), False)
    if packet.get("mode", "WORK") != "WORK" or packet.get("no_harvest") is True:
        return SentinelReview("HOLD_PRIVATE_BOUNDARY", ("UNAUTHORIZED_OR_PRIVATE_SOURCE_MODE",), digest,
                              size, str(packet.get("mode", "UNKNOWN")), None, (), False)
    reasons: list[str] = []
    action = packet.get("requested_action", "review")
    if type(action) is not str or not action.strip():
        action = "UNKNOWN"
    action = action.casefold().strip()
    human = False
    try:
        basic = packet96_review(packet)
    except (ValueError, TypeError) as exc:
        return SentinelReview("QUARANTINE_UNPARSEABLE", (type(exc).__name__,), digest, size, mode,
                              None, (), False)
    if basic.status == "BLOCK":
        reasons.extend(basic.reasons)
        disposition = "QUARANTINE_BLOCKED"
    elif action in DESTRUCTIVE_ACTIONS:
        reasons.append("DESTRUCTIVE_OPERATION_QUARANTINED_NO_DELETE")
        disposition = "QUARANTINE_DESTRUCTIVE"
        human = True
    elif action in PROMOTION_ACTIONS or packet.get("canon") is not False or packet.get("deployment") is not False:
        reasons.append("CANON_DEPLOYMENT_OR_EXTERNAL_EFFECT_REQUIRES_HUMAN_ROOT")
        disposition = "HOLD_HUMAN_ROOT"
        human = True
    elif basic.status != "REVIEWABLE_LOCAL_ONLY":
        reasons.extend(basic.reasons)
        disposition = "HOLD_CANDIDATE"
    else:
        reasons.append("CANDIDATE_REVIEW_ONLY_NO_AUTHORIZATION")
        disposition = "REVIEWABLE_LOCAL_ONLY"
    objections = packet.get("dissent", [])
    # A malformed dissent row must not be silently discarded by a projection.
    if type(objections) is list and any(type(x) is not dict for x in objections):
        reasons.append("MALFORMED_DISSENT_RECORD_HOLD")
        if disposition == "REVIEWABLE_LOCAL_ONLY":
            disposition = "HOLD_CANDIDATE"
    dissent = tuple(dict(x) for x in objections if type(x) is dict) if type(objections) is list else ()
    return SentinelReview(disposition, tuple(reasons), digest, size, mode, packet, dissent, human)


def append_receipt(path: str | Path, outcome: SentinelReview) -> None:
    """Optional append-only local custody for explicitly selected Work candidates.

    No file created for private/no-harvest, undecodable or invalid-mode data.
    This is not transactional host storage or verified rights-at-release.
    """
    if outcome.retained_work_packet is None or outcome.input_mode != "WORK":
        raise ValueError("CANNOT_ARCHIVE_PRIVATE_OR_UNPARSEABLE_SOURCE")
    payload = (json.dumps(outcome.receipt(), ensure_ascii=False, sort_keys=True,
                          allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
    target = Path(path)
    # Existing writable directory is required; no implicit path discovery.
    if not target.parent.is_dir() or target.is_symlink():
        raise ValueError("INVALID_RECEIPT_DESTINATION")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


__all__ = ["SCHEMA", "SentinelReview", "inspect", "append_receipt"]
