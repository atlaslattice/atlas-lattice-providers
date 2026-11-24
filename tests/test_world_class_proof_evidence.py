"""Synthetic evidence checks only; no real aggregator, credential or provider run."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts import world_class_proof as proof


def complete_receipt():
    return proof.ProofReceipt(checks=[proof.CheckResult(name, "PASS")
                                     for name in proof.REQUIRED_CHECK_NAMES])


class TestProofEvidence(unittest.TestCase):
    def test_empty_receipt_is_incomplete(self):
        receipt = proof.ProofReceipt()
        self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")
        self.assertIn("NO_CHECK_EVIDENCE", receipt.to_dict()["evidence_errors"])

    def test_partial_check_coverage_is_incomplete(self):
        receipt = complete_receipt(); receipt.checks.pop()
        self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")
        self.assertIn("MISSING_REQUIRED_CHECKS", receipt.evidence_errors())

    def test_all_required_passes_are_ready_without_authority(self):
        data = complete_receipt().to_dict()
        self.assertEqual(data["overall"], "CANDIDATE_READY")
        self.assertEqual(data["evidence_errors"], [])
        self.assertFalse(data["canon"])
        self.assertEqual(data["authority"], "none")

    def test_additive_named_check_can_extend_complete_coverage(self):
        receipt = complete_receipt(); receipt.checks.append(proof.CheckResult("synthetic_extra", "PASS"))
        self.assertEqual(receipt.overall(), "CANDIDATE_READY")

    def test_unknown_status_is_incomplete(self):
        for value in ("UNKNOWN", "SKIP", "pass", "", None, []):
            with self.subTest(value=value):
                receipt = complete_receipt(); receipt.checks[0].status = value
                self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")

    def test_duplicate_check_identity_is_incomplete(self):
        receipt = complete_receipt(); receipt.checks.append(receipt.checks[0])
        self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")
        self.assertIn("DUPLICATE_CHECK_NAME", receipt.evidence_errors())

    def test_malformed_check_identity_is_incomplete(self):
        for value in (None, "", " ", []):
            with self.subTest(value=value):
                receipt = complete_receipt(); receipt.checks[0].name = value
                self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")

    def test_malformed_check_object_is_incomplete(self):
        receipt = complete_receipt(); receipt.checks[0] = {"status": "PASS"}
        self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")

    def test_known_warning_and_failure_keep_their_meaning(self):
        receipt = complete_receipt(); receipt.checks[0].status = "WARN"
        self.assertEqual(receipt.overall(), "CANDIDATE_WITH_WARNINGS")
        receipt.checks[1].status = "FAIL"
        self.assertEqual(receipt.overall(), "CANDIDATE_INCOMPLETE")

    def cli(self, receipt, strict=False):
        argv = ["proof", "--output", ""] + (["--strict"] if strict else [])
        with patch.object(sys, "argv", argv), patch.object(proof, "build_receipt", return_value=receipt), \
             patch.object(proof, "write_receipt"), patch.object(proof.os, "getenv", side_effect=AssertionError("no credential inspection")), \
             patch.object(proof.subprocess, "run", side_effect=AssertionError("no subprocess")):
            return proof.main()

    def test_default_cli_rejects_empty_or_unknown_evidence(self):
        self.assertEqual(self.cli(proof.ProofReceipt()), 1)
        receipt = complete_receipt(); receipt.checks[0].status = "UNKNOWN"
        self.assertEqual(self.cli(receipt), 1)

    def test_cli_preserves_default_warning_and_strict_behavior(self):
        receipt = complete_receipt()
        self.assertEqual(self.cli(receipt), 0)
        self.assertEqual(self.cli(receipt, strict=True), 0)
        receipt.checks[0].status = "WARN"
        self.assertEqual(self.cli(receipt), 0)
        self.assertEqual(self.cli(receipt, strict=True), 1)


class TestNameCheckCoverage(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="name-guard-fixture-")
        self.addCleanup(self.scratch.cleanup)
        self.old_root = proof.ROOT
        proof.ROOT = Path(self.scratch.name)
        self.addCleanup(setattr, proof, "ROOT", self.old_root)
        (proof.ROOT / "docs").mkdir()

    def test_zero_readable_inputs_warns(self):
        result = proof.scan_for_forbidden_term()
        self.assertEqual(result.status, "WARN")
        self.assertIn("checked_files=0", result.detail)

    def test_only_exempt_context_does_not_clear_guard(self):
        (proof.ROOT / "docs/WORLD_CLASS_PROOF.md").write_text("synthetic exempt text")
        self.assertEqual(proof.scan_for_forbidden_term().status, "WARN")

    def test_unreadable_input_warns_without_exception_content(self):
        (proof.ROOT / "docs/fixture.md").write_text("synthetic clean text")
        marker = "SYNTHETIC_EXCEPTION_DETAIL"
        with patch.object(Path, "read_text", side_effect=PermissionError(marker)):
            result = proof.scan_for_forbidden_term()
        self.assertEqual(result.status, "WARN")
        self.assertIn("unreadable_files=1", result.detail)
        self.assertNotIn(marker, result.detail)

    def test_unreadable_peer_prevents_an_all_clear(self):
        (proof.ROOT / "docs/clean.md").write_text("synthetic clean text")
        (proof.ROOT / "docs/denied.md").write_text("synthetic input")
        read = Path.read_text
        def selective(path, *args, **kwargs):
            if path.name == "denied.md":
                raise PermissionError("synthetic denial")
            return read(path, *args, **kwargs)
        with patch.object(Path, "read_text", selective):
            result = proof.scan_for_forbidden_term()
        self.assertEqual(result.status, "WARN")
        self.assertIn("checked_files=1", result.detail)

    def test_invalid_utf8_is_coverage_warning(self):
        (proof.ROOT / "docs/fixture.md").write_bytes(b"synthetic invalid utf8\xff")
        self.assertEqual(proof.scan_for_forbidden_term().status, "WARN")

    def test_clean_readable_positive_control(self):
        (proof.ROOT / "docs/fixture.md").write_text("synthetic clean text")
        result = proof.scan_for_forbidden_term()
        self.assertEqual(result.status, "PASS")
        self.assertIn("checked_files=1", result.detail)

    def test_detected_name_still_fails(self):
        (proof.ROOT / "docs/fixture.md").write_text("Continuity OS")
        result = proof.scan_for_forbidden_term()
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.files, ["docs/fixture.md"])


if __name__ == "__main__":
    unittest.main()
