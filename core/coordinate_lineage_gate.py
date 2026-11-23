"""Offline review-only guard for 0-based vs Ariadne v0.7 coordinate aliases.

Inputs are caller assertions, never trust anchors. No source retrieval, rights
verification, network, graph join, migration, publishing, or CANON effect.
"""
from __future__ import annotations

import re

SCHEMA = "atlas.coordinate-lineage-review/candidate-v0.1"
LEGACY = "LEGACY_ZERO_BASED_UNVERIFIED"
ARIADNE = "ARIADNE_V07_ONE_BASED"
_ALLOWED = frozenset({"namespace", "edition", "coordinate", "registry_sha256", "record_sha256"})
_DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_NAMESPACE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}\Z", re.ASCII)
_COORD = re.compile(r"H(\d\d)\.S(\d\d)\.N(\d\d)\Z", re.ASCII)


def _held(reason: str) -> dict:
    return {"schema": SCHEMA, "status": "HOLD", "reason": reason,
            "same_as": False, "authority_effect": "NONE", "source_custody": False}


def _parse(record: object) -> tuple | None:
    # No arbitrary caller fields (body, private URLs, permissions, tokens).
    if type(record) is not dict or set(record) != _ALLOWED:
        return None
    namespace = record["namespace"]
    edition = record["edition"]
    coordinate = record["coordinate"]
    registry = record["registry_sha256"]
    revision = record["record_sha256"]
    if (type(namespace) is not str or not _NAMESPACE.fullmatch(namespace)
            or type(edition) is not str or edition not in (LEGACY, ARIADNE)
            or type(coordinate) is not str or not _COORD.fullmatch(coordinate)
            or type(registry) is not str or not _DIGEST.fullmatch(registry)
            or type(revision) is not str or not _DIGEST.fullmatch(revision)):
        return None
    axes = tuple(int(n) for n in _COORD.fullmatch(coordinate).groups())
    permitted = range(0, 12) if edition == LEGACY else range(1, 13)
    if not all(n in permitted for n in axes):
        return None
    # The full typed tuple must survive archival storage. A coordinate label
    # (even after arithmetic translation) is never a scientific identity.
    key = (namespace, edition, registry, coordinate, revision)
    return key, axes


def review_crosswalk(original: object, target: object) -> dict:
    """Describe a candidate alias while forbidding semantic equivalence.

    All hashes, namespace and editions are caller-claimed and UNVERIFIED.
    This deliberately does not produce an importable mapping or SAME_AS edge.
    """
    left = _parse(original)
    right = _parse(target)
    if left is None or right is None:
        return _held("INVALID_OR_UNPINNED_TYPED_IDENTITY")
    lkey, laxes = left
    rkey, raxes = right
    if lkey == rkey:
        status = "SAME_TYPED_REFERENCE_NOT_SEMANTIC_EQUIVALENCE"
    elif lkey[0] != rkey[0]:
        # Coordinate labels are only comparable within the same claimed namespace.
        # Cross-namespace axis matches are not candidate edition aliases.
        status = "DISTINCT_LINEAGES"
    elif lkey[1] == LEGACY and rkey[1] == ARIADNE and tuple(n + 1 for n in laxes) == raxes:
        status = "ARITHMETIC_ALIAS_REVIEW_REQUIRED"
    elif lkey[1] != rkey[1] and lkey[3] == rkey[3]:
        status = "CROSS_EDITION_OVERLAP_REVIEW_REQUIRED"
    elif lkey[1] == rkey[1] and lkey[3] == rkey[3]:
        status = "COORDINATE_COLLISION_REVIEW_REQUIRED"
    else:
        status = "DISTINCT_LINEAGES"
    return {"schema": SCHEMA, "status": status,
            "same_as": False, "authority_effect": "NONE", "source_custody": False,
            "publisher_attested": False, "rights_attested": False,
            "migration_authorized": False, "canon": False, "deployed": False}
