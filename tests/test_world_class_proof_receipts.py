"""Local regression checks for the candidate receipt writer (no network or private data)."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from scripts import world_class_proof as proof


class TestProofReceiptCustody(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.old_root = proof.ROOT
        proof.ROOT = Path(self.scratch.name)
        self.receipt = proof.ProofReceipt()

    def tearDown(self):
        proof.ROOT = self.old_root
        self.scratch.cleanup()

    def write(self, path):
        with contextlib.redirect_stdout(io.StringIO()):
            proof.write_receipt(self.receipt, path)

    def test_fresh_receipt_written(self):
        self.write("receipts/result.json")
        data = json.loads((proof.ROOT / "receipts/result.json").read_text())
        self.assertEqual(data["status"], "CANDIDATE_NOT_CANON")
        self.assertFalse(data["canon"])

    def test_existing_receipt_never_overwritten(self):
        target = proof.ROOT / "receipts/result.json"
        target.parent.mkdir()
        target.write_text("prior evidence")
        with self.assertRaises(FileExistsError):
            self.write("receipts/result.json")
        self.assertEqual(target.read_text(), "prior evidence")

    def test_existing_hardlink_never_overwritten(self):
        target = proof.ROOT / "target.json"
        target.write_text("preserve")
        (proof.ROOT / "receipts").mkdir()
        os.link(target, proof.ROOT / "receipts/result.json")
        with self.assertRaises(FileExistsError):
            self.write("receipts/result.json")
        self.assertEqual(target.read_text(), "preserve")

    def test_final_symlink_rejected(self):
        target = proof.ROOT / "target"
        target.write_text("preserve")
        (proof.ROOT / "receipts").mkdir()
        (proof.ROOT / "receipts/result.json").symlink_to(target)
        with self.assertRaises(ValueError):
            self.write("receipts/result.json")
        self.assertEqual(target.read_text(), "preserve")

    def test_symlink_parent_rejected(self):
        outside = proof.ROOT / "outside"
        outside.mkdir()
        (proof.ROOT / "receipts").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.write("receipts/result.json")
        self.assertFalse((outside / "result.json").exists())

    def test_nested_symlink_parent_rejected(self):
        (proof.ROOT / "receipts").mkdir()
        (proof.ROOT / "outside").mkdir()
        (proof.ROOT / "receipts/nested").symlink_to(proof.ROOT / "outside", target_is_directory=True)
        with self.assertRaises(ValueError):
            self.write("receipts/nested/result.json")

    def test_parent_traversal_rejected(self):
        for name in ("receipts/../target", "receipts/deep/../../target"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.write(name)

    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError):
            self.write(str(proof.ROOT / "receipts/result.json"))

    def test_writes_outside_receipts_rejected(self):
        for name in ("README.md", "docs/result.json", "receipts"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.write(name)

    def test_posix_receipt_permissions(self):
        self.write("receipts/result.json")
        if os.name == "posix":
            self.assertEqual((proof.ROOT / "receipts/result.json").stat().st_mode & 0o077, 0)

    def test_nested_directory_creation(self):
        self.write("receipts/nested/result.json")
        self.assertTrue((proof.ROOT / "receipts/nested/result.json").is_file())

    def test_empty_output_prints_only(self):
        self.write("")
        self.assertFalse((proof.ROOT / "receipts").exists())

    def test_non_directory_parent_rejected(self):
        (proof.ROOT / "receipts").write_text("not a directory")
        with self.assertRaises(ValueError):
            self.write("receipts/result.json")

    def test_core_syntax_check_creates_no_bytecode(self):
        source = proof.ROOT / "scripts/world_class_proof.py"
        source.parent.mkdir(parents=True)
        source.write_text("x=1\n")
        result = proof.compile_targets()
        self.assertIn(result.status, ("WARN", "PASS"))
        self.assertFalse((source.parent / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
