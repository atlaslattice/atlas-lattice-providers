"""Explicit, hash-bound owner project approval context for Eight Gates.

The caller supplies the context and expected hash independently. Reading a
status string from a repository never supplies an approval or access right.
This is a source-integrity check, not identity authentication or truth proof.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re


SCOPE = "OWNER_PROJECT_ARCHITECTURE_AND_MAPPING_DEFAULTS"
SCHEMA = "atlas.eight-gates.owner-project-approval.v1"
DENIED_GRANTS = (
    "scientific_validation_granted", "host_authentication_or_consent_granted",
    "hosted_runtime_deployment_granted", "model_training_or_personhood_granted",
    "unrelated_constitutional_or_fiction_ratification_granted", "private_content_export_granted",
)
RECORD_FALSE_BOUNDARIES = (
    "project_adoption_is_scientific_validation", "physical_properties_transfer_across_analogy",
    "relation_types_changed_by_approval", "hosted_deployment_verified",
    "host_authentication_or_consent_granted", "autonomous_agents_or_personhood_established",
    "draft_prs_merged_by_this_record",
)
ROLES = {"ADOPTION_RECORD", "MAPPING_PROJECTION", "ACTIVE_INDEX", "MIXED_HISTORICAL_QUEUE", "PROJECT_EXPLANATION"}
PRIVATE_PAYLOAD_FIELDS = {"approval_quote", "private_transcript", "private_content", "private_corpora",
                          "recovery_transcript", "raw_ariadne_registry", "original_source_corpus",
                          "private_mode_content", "credentials", "access_token"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _relative_file(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("APPROVAL_PATH_MUST_BE_REPOSITORY_RELATIVE")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("APPROVAL_SOURCE_MISSING_OR_OUTSIDE_REPOSITORY")
    return path


def _public_fields_only(value):
    if isinstance(value, dict):
        if set(value) & PRIVATE_PAYLOAD_FIELDS:
            raise ValueError("PRIVATE_PAYLOAD_NOT_AUTHORIZED_BY_PROJECT_ADOPTION")
        for child in value.values():
            _public_fields_only(child)
    elif isinstance(value, list):
        for child in value:
            _public_fields_only(child)


class ProjectApprovalContext:
    """Only the supplied decision's exact reviewed artifacts receive its scope."""
    __slots__ = ("root", "context_path", "expected_sha256", "_record", "_paths", "_sealed")

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise AttributeError("APPROVAL_CONTEXT_SELECTION_IS_IMMUTABLE")
        object.__setattr__(self, name, value)

    def __init__(self, repo_root, context_path, expected_sha256):
        self.root = Path(repo_root).resolve()
        self.context_path = Path(context_path).resolve()
        if not _sha(expected_sha256):
            raise ValueError("EXPLICIT_EXPECTED_APPROVAL_SHA256_REQUIRED")
        if not self.context_path.is_relative_to(self.root) or not self.context_path.is_file():
            raise ValueError("APPROVAL_CONTEXT_MISSING_OR_OUTSIDE_REPOSITORY")
        self.expected_sha256 = expected_sha256
        if sha256(self.context_path) != expected_sha256:
            raise ValueError("APPROVAL_CONTEXT_DIGEST_MISMATCH")
        self._record = json.loads(self.context_path.read_text(encoding="utf-8"))
        r = self._record
        if r.get("schema") != SCHEMA or r.get("approval_kind") != "EXPLICIT_PROJECT_OWNER_INSTRUCTION" or r.get("authority_scope") != SCOPE:
            raise ValueError("INVALID_OWNER_PROJECT_APPROVAL_SCOPE")
        if not isinstance(r.get("decision_id"), str) or not r["decision_id"].strip() or not _sha(r.get("recorded_approval_sha256")):
            raise ValueError("APPROVAL_DECISION_SOURCE_REQUIRED")
        if any(r.get(key) is not False for key in DENIED_GRANTS):
            raise ValueError("PROJECT_APPROVAL_CANNOT_GRANT_UNRELATED_AUTHORITY")
        artifacts = r.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts:
            raise ValueError("HASH_BOUND_APPROVAL_ARTIFACTS_REQUIRED")
        self._paths = {}
        for relative, binding in artifacts.items():
            if not isinstance(binding, dict) or set(binding) != {"role", "sha256"} or binding["role"] not in ROLES or not _sha(binding["sha256"]):
                raise ValueError("INVALID_APPROVAL_ARTIFACT_BINDING")
            self._paths[relative] = _relative_file(self.root, relative)
        self._assert_current()
        self._validate_public_records()
        self._sealed = True

    def _assert_current(self):
        if sha256(self.context_path) != self.expected_sha256:
            raise ValueError("APPROVAL_CONTEXT_CHANGED_AFTER_SELECTION")
        for relative, path in self._paths.items():
            if not path.is_file() or sha256(path) != self._record["artifacts"][relative]["sha256"]:
                raise ValueError("APPROVED_ARTIFACT_DIGEST_MISMATCH:" + relative)

    def _one(self, role):
        found = [(relative, self._paths[relative]) for relative, b in self._record["artifacts"].items() if b["role"] == role]
        if len(found) != 1:
            raise ValueError("ONE_APPROVAL_RECORD_PER_ROLE_REQUIRED:" + role)
        return found[0][0], json.loads(found[0][1].read_text(encoding="utf-8"))

    def _validate_public_records(self):
        record_path, record = self._one("ADOPTION_RECORD")
        projection_path, projection = self._one("MAPPING_PROJECTION")
        _, index = self._one("ACTIVE_INDEX")
        for public_record in (record, projection, index):
            _public_fields_only(public_record)
        decision = self._record["decision_id"]
        if record.get("schema") != "atlas.project-canon-public-adoption.v1" or record.get("decision_id") != decision or record.get("status") != "OWNER_APPROVED_PROJECT_CANON":
            raise ValueError("PUBLIC_PROJECT_DECISION_MISMATCH")
        boundaries = record.get("epistemic_boundaries", {})
        if any(boundaries.get(k) is not False for k in RECORD_FALSE_BOUNDARIES):
            raise ValueError("UNSUPPORTED_EVIDENCE_OR_HOST_CLAIM")
        for key in ("historical_lexical_remaps_automatically_accepted", "hypothetical_elements_confirmed"):
            if type(boundaries.get(key)) is not int or boundaries[key] != 0:
                raise ValueError("UNSUPPORTED_SEMANTIC_OR_PHYSICAL_RATIFICATION")
        if record.get("approval_quote_published") is not False or record.get("independent_peer_consensus_claimed") is not False or record.get("cryptographic_identity_attestation") is not False:
            raise ValueError("UNSUPPORTED_IDENTITY_PEER_OR_PRIVATE_SOURCE_CLAIM")
        pins = record.get("source_pins", {})
        required_pins = {"ariadne_original_v07_sha256", "functional_crosswalks_sha256", "predecessor_archive_sha256", "public_mapping_projection_sha256"}
        if set(pins) != required_pins or any(not _sha(pins[k]) for k in required_pins):
            raise ValueError("PUBLIC_SOURCE_PINS_REQUIRED")
        projection_sha = self._record["artifacts"][projection_path]["sha256"]
        approved_sources = self._record.get("approved_source_pins", {})
        if set(approved_sources) != required_pins - {"public_mapping_projection_sha256"} or any(not _sha(v) for v in approved_sources.values()):
            raise ValueError("APPROVED_SOURCE_PINS_REQUIRED")
        if any(pins[k] != value for k, value in approved_sources.items()):
            raise ValueError("APPROVED_SOURCE_PINS_MISMATCH")
        if pins["public_mapping_projection_sha256"] != projection_sha:
            raise ValueError("PUBLIC_PROJECTION_SOURCE_DIGEST_MISMATCH")
        if projection.get("schema") != "atlas.hypermatrix-public-mapping-projection.v1":
            raise ValueError("PUBLIC_PROJECTION_SCHEMA_MISMATCH")
        if projection.get("decision_id") != decision or projection.get("project_adoption") != "OWNER_APPROVED_PROJECT_CANON":
            raise ValueError("PUBLIC_PROJECTION_DECISION_MISMATCH")
        if projection.get("source_file_sha256") != pins["functional_crosswalks_sha256"] or projection.get("original_ariadne_source_sha256") != pins["ariadne_original_v07_sha256"]:
            raise ValueError("PUBLIC_PROJECTION_ORIGIN_MISMATCH")
        profiles = projection.get("profiles")
        if not isinstance(profiles, list) or not profiles:
            raise ValueError("PUBLIC_PROFILES_REQUIRED")
        counts = {"functional_profiles": len(profiles),
                  "operator_assignments": sum(len(p["operator_assignments"]) for p in profiles),
                  "sphere_affinities": sum(len(p["sphere_affinities"]) for p in profiles),
                  "physical_context_analogies": sum(len(p["physical_context_analogies"]) for p in profiles),
                  "profiles_without_default_element": sum(not p["physical_context_analogies"] for p in profiles),
                  "public_sources": len(projection.get("public_sources", []))}
        if projection.get("counts") != counts or record.get("adopted_scope", {}).get("functional_mapping_counts") != counts:
            raise ValueError("PUBLIC_MAPPING_COUNTS_MISMATCH")
        for profile in profiles:
            if profile.get("mapping_status_in_source") != "PROPOSED_FUNCTIONAL_ANALOGY" or profile.get("capability_authority") != "NONE_FROM_MYTHOLOGY":
                raise ValueError("MAPPING_APPROVAL_CANNOT_GRANT_EVIDENCE_OR_AUTHORITY")
            if any(x.get("relationship_type") != "COMPUTATIONAL_OPERATOR" for x in profile["operator_assignments"]):
                raise ValueError("OPERATOR_RELATION_TYPE_CHANGED")
            if any(x.get("relationship_type") != "SEMANTIC_CANDIDATE" for x in profile["sphere_affinities"]):
                raise ValueError("SPHERE_CANDIDATE_PROMOTED_BY_APPROVAL")
            for prop in profile["physical_context_analogies"]:
                if prop.get("relationship_type") != "GENERATIVE_ANALOGY" or prop.get("property_relationship_type") != "PHYSICAL_PROPERTY" or prop.get("association_evidence_status") != "PROPOSED_FUNCTIONAL_ANALOGY" or prop.get("measured_acceleration") is not None:
                    raise ValueError("PHYSICAL_ANALOGY_OR_PERFORMANCE_CLAIM_PROMOTED")
        if index.get("schema") != "atlas.active-project-canon-index.v1":
            raise ValueError("PROJECT_INDEX_SCHEMA_MISMATCH")
        entries = [x for x in index.get("entries", []) if x.get("decision_id") == decision]
        if len(entries) != 1:
            raise ValueError("EXACT_PROJECT_INDEX_ENTRY_REQUIRED")
        entry = entries[0]
        for key, expected in {"record_path": record_path, "record_sha256": self._record["artifacts"][record_path]["sha256"],
                              "mapping_path": projection_path, "mapping_sha256": projection_sha,
                              "status": "OWNER_APPROVED_PROJECT_CANON"}.items():
            if entry.get(key) != expected:
                raise ValueError("PROJECT_INDEX_POINTER_MISMATCH:" + key)

    def binding_for(self, path):
        # Reload the caller-selected bytes. Mutable nested cache data supplies
        # no approval, even when a caller alters it after construction.
        fresh = ProjectApprovalContext(self.root, self.context_path, self.expected_sha256)
        path = Path(path).resolve()
        if path == fresh.context_path:
            return {"decision_id": fresh._record["decision_id"], "scope": SCOPE,
                    "role": "VALIDATION_CONTEXT", "sha256": fresh.expected_sha256}
        for relative, target in fresh._paths.items():
            if path == target:
                return {"decision_id": fresh._record["decision_id"], "scope": SCOPE,
                        **deepcopy(fresh._record["artifacts"][relative])}
        return None
