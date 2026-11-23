"""Atlas Labs v32: inert, public-source-only experiment -> review packet adapter.

No execution, retrieval, Work posting, Graph writes, rights or CANON authority.
The registered public GitHub files are review entrypoints, not scientific proof.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
import unicodedata
from typing import Any

SCHEMA = "atlas.labs.experiment-candidate/v0.1"
HSN_PIN = "07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6"
HSN = re.compile(r"^H(0[1-9]|1[0-2])\.S(0[1-9]|1[0-2])\.N(0[1-9]|1[0-2])$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,12})?(?:[eE][+-]?[0-9]{1,3})?$")
UNITS = frozenset({"1", "bit", "Hz", "Pa", "s", "m", "kg", "K", "W", "J", "eV", "m/s", "ratio"})
EXPERIMENT_FIELDS = frozenset({"schema", "experiment_id", "lab_id", "source_id", "title",
    "hypothesis", "falsifier", "model_kind", "model_revision", "quantities",
    "ontology", "origin_mode", "source_scope", "authority", "canon", "deployment"})
QUANTITY_FIELDS = frozenset({"name", "value", "unit", "uncertainty", "evidence_class"})

# Explicit public-source passport pins. No source bodies or private account details.
# Blob hashes were read from GitHub for the repository revisions below.
CATALOG = {
 "quantum-labs": ("qpu-grid-design", "open-regenerative-compute-standard", "research/orcs/manufacturing/T4_S50_DC_OCP_MT_DIABLO_800VDC_STANDARDS_AND_QPU_INTEGRATION_SPEC_v0_4_2026-11-01.md", "6be14024f4950c016a3948fc757de159e7958dd3", "ea2ba0133338b316b01c62f83c97bd845c61a9f0"),
 "physics-mathematics": ("acoustic-model-spec", "atlas-lattice-foundation", "spec_modules/18_volumetric_acoustic_printing_spec.md", "28b1c82a4a0935654ba7096abe5a512a06fb2477", "d72e7f161a514d63bd03946e8ed6885bfe66eb89"),
 "fusion-plasma": ("stars2-source-gateway", "open-regenerative-compute-standard", "GPTWORK_START_HERE_STARS_2_0.md", "ef51e2a526e27119b9504ba8a13eabf80b975f01", "ea2ba0133338b316b01c62f83c97bd845c61a9f0"),
 "materials-manufacturing": ("acoustic-model-spec", "atlas-lattice-foundation", "spec_modules/18_volumetric_acoustic_printing_spec.md", "28b1c82a4a0935654ba7096abe5a512a06fb2477", "d72e7f161a514d63bd03946e8ed6885bfe66eb89"),
 "biological-systems": ("maui-fermentation-feasibility", "open-regenerative-compute-standard", "research/maui-yeast-myoglobin-local-precision-fermentation-feasibility-v0.7-2026-10-16.md", "0c27cdd730c2c466e88df6f835bef25675dd609a", "ea2ba0133338b316b01c62f83c97bd845c61a9f0"),
 "space-aerospace": ("moon-mars-habitat-candidate", "open-regenerative-compute-standard", "research/beyond_q/addenda/BQ_MOON_MARS_CLOSED_LOOP_HABITAT_TESTBED_MISSION_AND_LEDGER_v0_1_2026-10-30.md", "cc64e40b4990769347b37527d49a8029f9729779", "ea2ba0133338b316b01c62f83c97bd845c61a9f0"),
 "regenerative-infrastructure": ("beyondq-electrical-options", "open-regenerative-compute-standard", "research/beyond_q/power/BQ_ELEC_01_MINIMUM_CONVERSION_ARCHITECTURE_v0_1.md", "9b7a77fb66e7344c0d6a32876fc72c80e7a98368", "ea2ba0133338b316b01c62f83c97bd845c61a9f0"),
 "knowledge-evidence": ("public-graph-candidate", "manus-artifacts", "public_candidate_bundle_0001/START_HERE.md", "1171dde2dc2d6394572fe5719299bcc568aec5bd", "476901f06b9685dfa63b2f796806b5d181595463"),
}

DENIED = {"status": "HOLD", "reason": "INVALID_OR_UNAUTHORIZED_PUBLIC_SOURCE",
          "source_count": 0, "candidate": None}


def _pairs_unique(pairs: list[tuple[str, Any]]) -> dict:
    obj: dict[str, Any] = {}
    seen: set[str] = set()
    for k, v in pairs:
        normalized = unicodedata.normalize("NFC", k)
        if normalized in seen:
            raise ValueError("ambiguous key")
        seen.add(normalized)
        obj[k] = v
    return obj


def _reject_numeric(value: str) -> None:
    raise ValueError("numeric literals disallowed: use bounded decimal strings")


def _decode(raw: Any) -> dict:
    if type(raw) is dict:
        # Reparse to reject nested non-JSON objects and Python float values.
        raw = json.dumps(raw, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if type(raw) is str:
        raw = raw.encode("utf-8")
    if type(raw) is not bytes or len(raw) > 32768:
        raise ValueError("unacceptable source")
    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_unique,
                     parse_constant=_reject_numeric, parse_float=_reject_numeric)
    if type(obj) is not dict:
        raise ValueError("root must be an object")
    return obj


# Reject spoof-prone directional marks and invisible line/paragraph control
# characters in review-facing text, without excluding ordinary Unicode science.
# Explicitly exclude invisible format operators in human-facing review fields.
# Keep U+200C (ZWNJ) and U+200D (ZWJ): both carry legitimate multilingual
# shaping/emoji meaning. This is not an input-language or Unicode ban.
REVIEW_VISUAL_CONTROLS = frozenset(
    {0x00AD, 0x034F, 0x061C, 0x180E, 0x200B, 0x200E, 0x200F,
     0x2028, 0x2029, 0xFEFF}
    | set(range(0x202A, 0x202F)) | set(range(0x2060, 0x2070)))


def _text(x: Any, limit: int = 240) -> bool:
    return (type(x) is str and bool(x.strip()) and len(x) <= limit
            and all(ord(c) >= 32 and not 0x7F <= ord(c) <= 0x9F
                    and ord(c) not in REVIEW_VISUAL_CONTROLS for c in x))


def _quantity(q: Any) -> dict:
    if type(q) is not dict or set(q) != QUANTITY_FIELDS:
        raise ValueError("bad quantity fields")
    if not _text(q["name"], 48) or not IDENT.fullmatch(q["name"]):
        raise ValueError("bad metric name")
    if type(q["unit"]) is not str or q["unit"] not in UNITS:
        raise ValueError("unsupported unit")
    if q["evidence_class"] != "SYNTHETIC_MODEL_ONLY":
        raise ValueError("measurements not independently observed")
    for key in ("value", "uncertainty"):
        s = q[key]
        if type(s) is not str or not DECIMAL.fullmatch(s):
            raise ValueError("bad decimal")
        try:
            v = Decimal(s)
        except InvalidOperation as e:
            raise ValueError("bad decimal") from e
        if not v.is_finite() or abs(v) > Decimal("1e12"):
            raise ValueError("out of bounded range")
        if v != 0 and abs(v) < Decimal("1e-12"):
            raise ValueError("below numerical reporting floor")
        if key == "uncertainty" and v < 0:
            raise ValueError("negative uncertainty")
    return dict(q)


def catalog() -> dict:
    """Read-only public-scoped sources; returns fresh objects, never authority."""
    return {lab: {"source_id": s[0], "repo": "atlaslattice/" + s[1],
                  "path": s[2], "git_blob_sha1": s[3], "git_commit": s[4],
                  "review_status": "SOURCE_POINTER_NOT_SCIENCE_VALIDATION"}
            for lab, s in CATALOG.items()}


def prepare(raw: Any) -> dict:
    """Prepare inert Atlas ONE, Alexandria and SwarmChat review candidates.

    Neither verifies source rights nor calls a lab, graph, model or broker.
    Every untrusted denial is intentionally the same shallow scalar response.
    """
    try:
        x = _decode(raw)
        if set(x) != EXPERIMENT_FIELDS or x["schema"] != SCHEMA:
            raise ValueError("unsupported schema")
        lab = x["lab_id"]
        if type(lab) is not str or lab not in CATALOG or x["source_id"] != CATALOG[lab][0]:
            raise ValueError("unknown source")
        if not _text(x["experiment_id"], 80) or not IDENT.fullmatch(x["experiment_id"]):
            raise ValueError("bad id")
        if any(not _text(x[f], limit) for f, limit in (("title", 100), ("hypothesis", 300),
                                                       ("falsifier", 300), ("model_revision", 80))):
            raise ValueError("bad texts")
        if x["origin_mode"] != "PUBLIC" or x["source_scope"] != "PUBLIC_REPORTED":
            raise ValueError("no private modes")
        if x["authority"] != "none" or x["canon"] is not False or x["deployment"] is not False:
            raise ValueError("no promotion")
        kind = x["model_kind"]
        if type(kind) is not str or kind not in ("DESIGN_ONLY", "SYNTHETIC_MODEL"):
            raise ValueError("no measured lab claims")
        q = x["quantities"]
        if type(q) is not list or len(q) > 8 or (kind == "DESIGN_ONLY" and q) or (kind == "SYNTHETIC_MODEL" and not q):
            raise ValueError("invalid result class")
        metrics = [_quantity(m) for m in q]
        if len(set(m["name"] for m in metrics)) != len(metrics):
            raise ValueError("duplicate metric")
        ontology = x["ontology"]
        if ontology is not None:
            if type(ontology) is not dict or set(ontology) != {"edition", "registry_sha256", "coordinate"}:
                raise ValueError("invalid ontology passport")
            if ontology["edition"] != "Ariadne v0.7" or ontology["registry_sha256"] != HSN_PIN:
                raise ValueError("unversioned or legacy ontology")
            if type(ontology["coordinate"]) is not str or not HSN.fullmatch(ontology["coordinate"]):
                raise ValueError("invalid HSN coordinate")
        # Fingerprint only an entirely validated, known public-source candidate.
        canonical = json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        digest = sha256(canonical.encode("utf-8")).hexdigest()
        source = catalog()[lab]
        url = ("https://github.com/" + source["repo"] + "/blob/" + source["git_commit"]
               + "/" + source["path"])
        packet = {"schema": "atlas.labs.packet/v0.1", "experiment_id": x["experiment_id"],
                  "lab_id": lab, "model_kind": kind, "model_revision": x["model_revision"],
                  "measurements": metrics, "ontology": ontology,
                  "source_passport": {"url": url, "git_blob_sha1": source["git_blob_sha1"],
                                      "edition": ontology["edition"] if ontology else None,
                                      "rights": "PUBLIC_REPORTED_NOT_HOST_ATTESTED"},
                  "evidence_status": "UNVERIFIED_DESIGN" if kind == "DESIGN_ONLY" else "REPORTED_SYNTHETIC_NOT_REEXECUTED",
                  "hypothesis": x["hypothesis"], "falsifier": x["falsifier"],
                  "experiment_sha256": digest, "authority_effect": "NONE", "canon": False,
                  "deployment": False, "verified_hardware": False, "host_attested": False,
                  "same_as": False, "rights_at_return": "NOT_CHECKED"}
        return {"status": "PREPARED_SOURCE_ONLY", "reason": None, "source_count": 1,
                "candidate": {"atlas_one": {"status": "TASK_INTAKE_CANDIDATE_NOT_DISPATCHED", "packet": packet},
                              "swarmchat_work": {"status": "PREPARED_NOT_POSTED", "parentSeq": None,
                                                 "source_ref": url, "experiment_sha256": digest,
                                                 "message": "Review lab candidate " + x["experiment_id"] + "; independent source, units, method and rights checks required"},
                              "alexandria": {"status": "GRAPH_EDGE_CANDIDATE_NOT_WRITTEN", "source_ref": url,
                                             "address_only": ontology is not None,
                                             "experiment_sha256": digest,
                                             "same_as": False}}}
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError, UnicodeError):
        return dict(DENIED)


def main() -> None:
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "--catalog":
        result = {"status": "SOURCE_POINTERS_ONLY", "labs": catalog()}
    elif len(sys.argv) == 2 and sys.argv[1] == "--stdin":
        result = prepare(sys.stdin.buffer.read(32769))
    else:
        raise SystemExit("Usage: python -m labs.atlas_labs_v32 --catalog|--stdin")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
