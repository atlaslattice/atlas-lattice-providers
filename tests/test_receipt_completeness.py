"""Positive, negative and overclaim tests for candidate receipt rubric."""
import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "receipt_completeness.py"
SPEC = importlib.util.spec_from_file_location("receipt_completeness", MODULE)
rubric = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rubric)
SHA = "a" * 40


def complete():
    return {
        "artifact_id": "synthetic-demo-only",
        "source": {"url": "https://github.com/example/repo/blob/main/packet.json", "verification": "visible", "readback_url": "https://github.com/example/repo/blob/main/packet.json", "checked_at": "2026-11-22"},
        "commit": {"sha": SHA, "url": "https://github.com/example/repo/commit/" + SHA},
        "lifecycle": "CANDIDATE", "authority": "none", "canon": False, "deployment": False,
        "verification": {"state": "visible", "receipt_url": "https://github.com/example/repo/actions/runs/1", "checked_at": "2026-11-22"},
        "tests": {"state": "passed", "command": "python -m unittest", "receipt_url": "https://github.com/example/repo/actions/runs/1"},
        "human_root_gate": {"required": True, "decision_route": "owner review", "state": "not_granted"},
        "inv0_preservation": {"path": "fossils/original", "method": "append-only, never delete"},
        "dissent": {"review_route": "issues/review", "preservation_route": "fossils/dissent"},
    }


class RubricTests(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(rubric.score({})["points"], 0)

    def test_synthetic_complete_caps_at_twenty(self):
        result = rubric.score(complete())
        self.assertEqual(result["points"], 20)
        self.assertIn("ONLY", result["limitation"])

    def test_local_only_fails_full_verification(self):
        r = complete()
        r["verification"] = {"state": "local-only"}
        r["source"]["verification"] = "reported"
        r["tests"] = {"state": "reported_passed", "command": "pytest"}
        s = rubric.score(r)
        self.assertEqual(s["dimensions"]["verification"]["points"], 1)
        self.assertEqual(s["dimensions"]["source_link"]["points"], 1)
        self.assertEqual(s["dimensions"]["tests"]["points"], 1)

    def test_stub_cannot_get_sha_credit(self):
        r = complete()
        r["commit"] = {"sha": "61613e60c7ad654174aa48f6f1396b2ec026b2f7", "url": "https://github.com/example/repo/blob/main/file.md"}
        self.assertEqual(rubric.score(r)["dimensions"]["commit_sha"]["points"], 1)

    def test_bogus_sha_rejected(self):
        r = complete()
        r["commit"]["sha"] = "not-a-sha"
        self.assertEqual(rubric.score(r)["dimensions"]["commit_sha"]["points"], 0)

    def test_unlinked_pass_is_not_counted(self):
        r = complete()
        r["tests"] = {"state": "passed", "command": "pytest"}
        self.assertEqual(rubric.score(r)["dimensions"]["tests"]["points"], 0)

    def test_non_testable_reason_is_accepted(self):
        r = complete()
        r["tests"] = {"state": "not_testable", "reason": "This is narrative-only."}
        self.assertEqual(rubric.score(r)["dimensions"]["tests"]["points"], 2)

    def test_unrun_reason_gets_partial(self):
        r = complete()
        r["tests"] = {"state": "not_run", "reason": "No CI configured"}
        self.assertEqual(rubric.score(r)["dimensions"]["tests"]["points"], 1)

    def test_gate_cannot_claim_approved_by_default(self):
        r = complete()
        r["human_root_gate"]["state"] = "approved"
        self.assertEqual(rubric.score(r)["dimensions"]["human_root_gate"]["points"], 1)

    def test_canon_flags_must_be_boolean(self):
        r = complete()
        r["canon"] = "false"
        r["deployment"] = "false"
        self.assertEqual(rubric.score(r)["dimensions"]["canon_deployment"]["points"], 0)

    def test_dissent_needs_retention(self):
        r = complete()
        r["dissent"] = {"statement": "Allow challenge"}
        self.assertEqual(rubric.score(r)["dimensions"]["dissent_path"]["points"], 1)

    def test_inv0_requires_path(self):
        r = complete()
        r["inv0_preservation"] = {"statement": "NOTHING DIES"}
        self.assertEqual(rubric.score(r)["dimensions"]["inv0_preservation"]["points"], 1)

    def test_bad_json_shapes_are_missing_not_crashes(self):
        r = complete()
        r["lifecycle"] = {"status": "CANDIDATE"}
        r["authority"] = ["none"]
        result = rubric.score(r)
        self.assertEqual(result["dimensions"]["lifecycle_status"]["points"], 0)
        self.assertEqual(result["dimensions"]["authority_label"]["points"], 0)

    def test_missing_evidence_blocks_gate_even_with_many_labels(self):
        r = complete()
        r["commit"] = {}
        self.assertEqual(rubric.score(r)["evidence_gate"], "blocked-missing-or-unverified-receipts")

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            rubric.score([1])


if __name__ == "__main__":
    unittest.main()
