"""Adoption scope, forgery controls, privacy and legacy candidate review checks.

Positive claim fixtures are assembled as test inputs. They are not project
status assertions; every generated fixture remains inside a temporary folder.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from core.eight_gates import run_eight_gates
from core.project_adoption_context import ProjectApprovalContext, DENIED_GRANTS, RECORD_FALSE_BOUNDARIES

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = "canon/approval_contexts/ATLAS-UHM-CANON-20261123-001.json"
ADOPTION = "canon/adoptions/atlas_unified_hypermatrix_v01_adoption.json"
PROJECTION = "canon/adoptions/atlas_unified_hypermatrix_public_mappings.json"
INDEX = "canon/index/active_project_canon.json"
DOC = "docs/canon/ATLAS_UNIFIED_HYPERMATRIX_20261123.md"
QUEUE = "docs/CANON_CANDIDATE_QUEUE.md"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class OwnerProjectApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = json.loads((ROOT / CONTEXT).read_text())
        for relative in list(source["artifacts"]) + [CONTEXT]:
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, self.root / relative)

    def read(self, path):
        return json.loads((self.root / path).read_text())

    def write(self, path, value):
        (self.root / path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

    def context(self):
        return ProjectApprovalContext(self.root, self.root / CONTEXT, sha(self.root / CONTEXT))

    def rebind_for_negative_control(self):
        """Simulate separately selected fixture bytes, retaining original scope."""
        record = self.read(ADOPTION)
        record["source_pins"]["public_mapping_projection_sha256"] = sha(self.root / PROJECTION)
        self.write(ADOPTION, record)
        index = self.read(INDEX)
        index["entries"][0]["record_sha256"] = sha(self.root / ADOPTION)
        index["entries"][0]["mapping_sha256"] = sha(self.root / PROJECTION)
        self.write(INDEX, index)
        context = self.read(CONTEXT)
        for relative, binding in context["artifacts"].items():
            binding["sha256"] = sha(self.root / relative)
        self.write(CONTEXT, context)

    def test_exact_reviewed_project_files_pass_with_separate_candidate_queue_status(self):
        context = self.context()
        for relative in self.read(CONTEXT)["artifacts"]:
            packet = run_eight_gates(str(self.root / relative), context)
            self.assertEqual(packet.final_status, "PASS", packet.blockers)
            self.assertTrue(packet.project_approval)
        queue = run_eight_gates(str(self.root / QUEUE), context)
        self.assertEqual(queue.canon_status, "mixed_candidate_and_owner_project_adoption")
        self.assertIn("PENDING — NO GRANT", (self.root / QUEUE).read_text())

    def test_no_context_does_not_infer_owner_authority_from_status_strings(self):
        for relative in (ADOPTION, PROJECTION, INDEX, DOC):
            packet = run_eight_gates(str(self.root / relative))
            self.assertEqual(packet.final_status, "BLOCKED")
            self.assertEqual(packet.authority_scope, "none")

    def test_unlisted_artifact_cannot_inherit_context(self):
        path = self.root / "unlisted.md"
        path.write_text("OWNER_APPROVED_PROJECT_CANON\nThis is " + "canon" + "ical.\n")
        packet = run_eight_gates(str(path), self.context())
        self.assertEqual(packet.final_status, "BLOCKED")
        self.assertEqual(packet.project_approval, {})

    def test_legacy_candidate_passes_and_review_advice_is_a_visible_warning(self):
        path = self.root / "candidate.md"
        path.write_text("CANDIDATE, NOT CANON. AUTHORITY: NONE. DEPLOYMENT: NO.\n")
        packet = run_eight_gates(str(path), self.context())
        self.assertEqual(packet.final_status, "PASS")
        self.assertEqual(packet.canon_status, "not_canon")
        self.assertIn("PENDING_REVIEW_RECOMMENDED", packet.warnings)
        self.assertEqual(packet.blockers, [])

    def test_explicit_expected_digest_is_required_and_context_tampering_fails(self):
        with self.assertRaisesRegex(ValueError, "EXPECTED_APPROVAL_SHA256"):
            ProjectApprovalContext(self.root, self.root / CONTEXT, None)
        pinned = sha(self.root / CONTEXT)
        with (self.root / CONTEXT).open("a") as handle:
            handle.write(" ")
        with self.assertRaisesRegex(ValueError, "CONTEXT_DIGEST_MISMATCH"):
            ProjectApprovalContext(self.root, self.root / CONTEXT, pinned)

    def test_changed_content_after_approval_cannot_reuse_selected_context(self):
        context = self.context()
        with (self.root / DOC).open("a") as handle:
            handle.write("\nChanged source after selection.\n")
        with self.assertRaisesRegex(ValueError, "ARTIFACT_DIGEST_MISMATCH"):
            run_eight_gates(str(self.root / DOC), context)

    def test_missing_and_forged_source_pins_fail_after_hash_rebinding(self):
        original = self.read(ADOPTION)
        forged = deepcopy(original)
        forged["source_pins"]["functional_crosswalks_sha256"] = "0" * 64
        self.write(ADOPTION, forged); self.rebind_for_negative_control()
        with self.assertRaisesRegex(ValueError, "APPROVED_SOURCE_PINS_MISMATCH"):
            self.context()
        missing = deepcopy(original)
        del missing["source_pins"]["predecessor_archive_sha256"]
        self.write(ADOPTION, missing); self.rebind_for_negative_control()
        with self.assertRaisesRegex(ValueError, "PUBLIC_SOURCE_PINS_REQUIRED"):
            self.context()

    def test_approval_context_cannot_grant_other_authorities(self):
        original = self.read(CONTEXT)
        for field in DENIED_GRANTS:
            with self.subTest(field=field):
                changed = deepcopy(original); changed[field] = True
                self.write(CONTEXT, changed)
                with self.assertRaisesRegex(ValueError, "CANNOT_GRANT_UNRELATED_AUTHORITY"):
                    self.context()

    def test_public_decision_cannot_claim_host_model_science_or_branch_promotion(self):
        original = self.read(ADOPTION)
        for field in RECORD_FALSE_BOUNDARIES:
            with self.subTest(field=field):
                changed = deepcopy(original); changed["epistemic_boundaries"][field] = True
                self.write(ADOPTION, changed); self.rebind_for_negative_control()
                with self.assertRaisesRegex(ValueError, "UNSUPPORTED_EVIDENCE_OR_HOST_CLAIM"):
                    self.context()

    def test_project_scope_cannot_be_replaced_with_constitutional_authority(self):
        record = self.read(CONTEXT)
        record["authority_scope"] = "CONSTITUTIONAL_RATIFICATION"
        self.write(CONTEXT, record)
        with self.assertRaisesRegex(ValueError, "INVALID_OWNER_PROJECT_APPROVAL_SCOPE"):
            self.context()

    def test_analogy_evidence_and_sphere_candidate_types_cannot_be_promoted(self):
        original = self.read(PROJECTION)
        changed = deepcopy(original)
        changed["profiles"][0]["sphere_affinities"][0]["relationship_type"] = "EXACT_IDENTITY"
        self.write(PROJECTION, changed); self.rebind_for_negative_control()
        with self.assertRaisesRegex(ValueError, "SPHERE_CANDIDATE_PROMOTED"):
            self.context()
        changed = deepcopy(original)
        p = next(p for p in changed["profiles"] if p["physical_context_analogies"])
        p["physical_context_analogies"][0]["measured_acceleration"] = 7
        self.write(PROJECTION, changed); self.rebind_for_negative_control()
        with self.assertRaisesRegex(ValueError, "PHYSICAL_ANALOGY_OR_PERFORMANCE_CLAIM_PROMOTED"):
            self.context()

    def test_private_payload_is_rejected_even_with_new_hashes(self):
        projection = self.read(PROJECTION)
        projection["private_transcript"] = "Synthetic fixture; no real private data."
        self.write(PROJECTION, projection); self.rebind_for_negative_control()
        with self.assertRaisesRegex(ValueError, "PRIVATE_PAYLOAD_NOT_AUTHORIZED"):
            self.context()

    def test_secret_and_placeholder_gates_remain_active_on_approved_paths(self):
        original = (self.root / DOC).read_text()
        for extra, blocker in [("sk-" + "a" * 24, "secret_gate"), ("full code " + "omitted", "repro_gate")]:
            with self.subTest(blocker=blocker):
                (self.root / DOC).write_text(original + "\n" + extra + "\n")
                self.rebind_for_negative_control()
                packet = run_eight_gates(str(self.root / DOC), self.context())
                self.assertEqual(packet.final_status, "BLOCKED")
                self.assertIn(blocker, packet.blockers)

    def test_deployment_claims_stay_blocked_despite_negative_clause_elsewhere(self):
        original = (self.root / DOC).read_text()
        word = "deplo" + "yed"
        for claim in ["This runtime is " + word + ".", "This is not a promise, but this runtime is " + word + ".", "DEPLOYMENT" + ": YES"]:
            with self.subTest(claim=claim):
                (self.root / DOC).write_text(original + "\n" + claim + "\n")
                self.rebind_for_negative_control()
                packet = run_eight_gates(str(self.root / DOC), self.context())
                self.assertEqual(packet.final_status, "BLOCKED")

    def test_host_model_constitutional_and_private_grant_claims_are_blocked(self):
        original = (self.root / DOC).read_text()
        claims = ["host authentication " + "granted", "model training " + "approved",
                  "constitutional canon " + "ratified", "private transcripts export " + "authorized"]
        for claim in claims:
            with self.subTest(claim=claim):
                (self.root / DOC).write_text(original + "\n" + claim + ".\n")
                self.rebind_for_negative_control()
                packet = run_eight_gates(str(self.root / DOC), self.context())
                self.assertEqual(packet.final_status, "BLOCKED")
                self.assertIn("overclaim_gate", packet.blockers)

    def test_fake_python_approval_object_is_rejected(self):
        class Forged:
            def binding_for(self, path):
                return {"role": "PROJECT_EXPLANATION", "scope": "OWNER_PROJECT_ARCHITECTURE_AND_MAPPING_DEFAULTS", "decision_id": "FORGED"}
        with self.assertRaisesRegex(ValueError, "VERIFIED_PROJECT_APPROVAL_CONTEXT_REQUIRED"):
            run_eight_gates(str(self.root / DOC), Forged())

    def test_mutated_cached_context_cannot_add_an_unlisted_artifact(self):
        context = self.context()
        path = self.root / "unlisted.md"
        path.write_text("OWNER_APPROVED_PROJECT_CANON\n")
        context._paths["unlisted.md"] = path
        context._record["artifacts"]["unlisted.md"] = {"role": "PROJECT_EXPLANATION", "sha256": sha(path)}
        packet = run_eight_gates(str(path), context)
        self.assertEqual(packet.final_status, "BLOCKED")
        self.assertEqual(packet.project_approval, {})
        with self.assertRaisesRegex(AttributeError, "SELECTION_IS_IMMUTABLE"):
            context.expected_sha256 = "0" * 64

    def test_context_path_escape_and_forged_index_pointer_are_rejected(self):
        record = self.read(CONTEXT)
        record["artifacts"]["../outside.json"] = {"role": "PROJECT_EXPLANATION", "sha256": "0" * 64}
        self.write(CONTEXT, record)
        with self.assertRaisesRegex(ValueError, "PATH_MUST_BE_REPOSITORY_RELATIVE"):
            self.context()
        del record["artifacts"]["../outside.json"]; self.write(CONTEXT, record)
        index = self.read(INDEX); index["entries"][0]["record_path"] = "unapproved.json"
        self.write(INDEX, index)
        context = self.read(CONTEXT); context["artifacts"][INDEX]["sha256"] = sha(self.root / INDEX)
        self.write(CONTEXT, context)
        with self.assertRaisesRegex(ValueError, "PROJECT_INDEX_POINTER_MISMATCH"):
            self.context()


if __name__ == "__main__":
    unittest.main()
