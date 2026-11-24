"""Explicit-file scanner checks using disposable synthetic files only.

The source module is loaded directly, bypassing provider package initializers.
No real repository scan, credentials, network, provider operation or corpus read.
"""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "providers/openai/openai_secret_hygiene_guard.py"
spec = importlib.util.spec_from_file_location("work_guard_source", SOURCE)
guard_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard_source)


class ExplicitWorkSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="work-source-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.guard = guard_source.OpenAISecretHygieneGuard(simulate=True)

    def write(self, path, content=b"synthetic clean source\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def scan(self, paths, **kwargs):
        return self.guard.scan_files(str(self.root), paths=paths, **kwargs)["report"]

    def test_only_explicit_selected_file_is_read(self):
        self.write("work/selected.py")
        self.write("Brain/unused.py", b"deliberately unselected synthetic content")
        with patch.object(guard_source.os, "walk", side_effect=AssertionError("directory traversal forbidden")):
            result = self.scan(["work/selected.py"])
        self.assertEqual(result["status"], "clean")
        self.assertTrue(result["selected_inputs_complete"])
        self.assertEqual((result["requested_files"], result["scanned_files"]), (1, 1))
        self.assertEqual(result["scope"], "explicit_work_source_files")

    def test_detection_is_counted_without_excerpt(self):
        synthetic = "sk-" + "SYNTHETIC" * 3
        self.write("work/example.py", synthetic.encode())
        result = self.scan(["work/example.py"])
        self.assertEqual(result["status"], "SECRETS_DETECTED_BLOCK")
        self.assertTrue(result["selected_inputs_complete"])
        self.assertEqual(result["hits"], [{"file_index": 0, "pattern_index": 0, "match_count": 1}])
        self.assertNotIn(synthetic, json.dumps(result))
        self.assertNotIn("match_preview", json.dumps(result))

    def test_missing_selected_file_marks_partial_coverage(self):
        self.write("work/first.py")
        self.write("work/third.py")
        result = self.scan(["work/first.py", "work/missing.py", "work/third.py"])
        self.assertEqual((result["requested_files"], result["scanned_files"]), (3, 2))
        self.assertEqual(result["status"], "SCAN_INCOMPLETE_BLOCK")
        self.assertFalse(result["selected_inputs_complete"])
        self.assertEqual(result["errors"], [{"file_index": 1, "code": "OPEN_OR_READ_FAILED"}])

    def test_read_error_is_recorded_and_exception_text_redacted(self):
        self.write("work/selected.py")
        marker = "SYNTHETIC_PRIVATE_EXCEPTION"
        with patch.object(guard_source.os, "read", side_effect=PermissionError(marker)):
            result = self.scan(["work/selected.py"])
        self.assertEqual(result["scanned_files"], 0)
        self.assertFalse(result["selected_inputs_complete"])
        self.assertEqual(result["errors"][0]["code"], "OPEN_OR_READ_FAILED")
        self.assertNotIn(marker, json.dumps(result))

    def test_partial_read_error_accounts_for_consumed_bytes(self):
        self.write("work/selected.py", b"a" * 70000)
        read = os.read
        count = 0
        def interrupt_after_first(descriptor, limit):
            nonlocal count
            count += 1
            if count > 1:
                raise OSError("SYNTHETIC_READ_INTERRUPTED")
            return read(descriptor, limit)
        with patch.object(guard_source.os, "read", side_effect=interrupt_after_first):
            result = self.scan(["work/selected.py"])
        self.assertEqual(result["bytes_read"], 65536)
        self.assertEqual(result["scanned_files"], 0)
        self.assertEqual(result["status"], "SCAN_INCOMPLETE_BLOCK")

    def test_utf8_errors_and_binary_content_are_not_silently_skipped(self):
        for content, code in ((b"bad\xff", "INVALID_UTF8"), (b"embedded\x00nul", "BINARY_CONTENT")):
            with self.subTest(code=code):
                self.write("work/selected.py", content)
                result = self.scan(["work/selected.py"])
                self.assertEqual(result["errors"][0]["code"], code)
                self.assertEqual(result["bytes_read"], len(content))
                self.assertEqual(result["scanned_files"], 0)

    def test_invalid_selection_is_rejected_before_open(self):
        choices = (None, [], "work/file.py", iter(["work/file.py"]),
                   ["work/file.py"] * 129, ["work/file.py", "work/file.py"])
        with patch.object(guard_source.os, "open", side_effect=AssertionError("must not open")) as opened:
            for choice in choices:
                with self.subTest(kind=type(choice).__name__):
                    result = self.scan(choice)
                    self.assertEqual(result["status"], "SCAN_INCOMPLETE_BLOCK")
            opened.assert_not_called()

    def test_invalid_paths_reject_entire_selection_before_open(self):
        invalid = ("/tmp/file.py", "../file.py", "work/../file.py", "./file.py",
                   "work//file.py", "work\\file.py", "work/*.py", "work/file[0].py",
                   "work", "work/file.log", "work/file.py\x00", 7, ["work/file.py"])
        self.write("work/selected.py")
        with patch.object(guard_source.os, "open", side_effect=AssertionError("must not open")) as opened:
            for value in invalid:
                with self.subTest(value=value):
                    result = self.scan(["work/selected.py", value])
                    self.assertEqual(result["scanned_files"], 0)
                    self.assertFalse(result["selected_inputs_complete"])
            opened.assert_not_called()

    def test_reserved_paths_are_rejected_before_open(self):
        names = ("Play", "Social", "Imagine", "Quiet", "Habitat", "Brain", "Palace",
                 "Dream", "CANON", "private", ".git", ".venv", "node_modules", "__pycache__")
        with patch.object(guard_source.os, "open", side_effect=AssertionError("must not open")) as opened:
            for name in names:
                with self.subTest(name=name):
                    result = self.scan([name + "/entry.py"])
                    self.assertEqual(result["errors"][0]["code"], "EXCLUDED_PATH")
            opened.assert_not_called()

    def test_reserved_root_and_parent_escape_are_rejected_before_open(self):
        with patch.object(guard_source.os, "open", side_effect=AssertionError("must not open")) as opened:
            for root in (self.root / "Brain", self.root / ".." / "outside"):
                result = self.guard.scan_files(str(root), paths=["entry.py"])["report"]
                self.assertEqual(result["status"], "SCAN_INCOMPLETE_BLOCK")
            opened.assert_not_called()

    def test_symlink_file_directory_and_root_are_rejected(self):
        self.write("work/selected.py")
        (self.root / "linked.py").symlink_to(self.root / "work/selected.py")
        (self.root / "linked-directory").symlink_to(self.root / "work", target_is_directory=True)
        for root, path in ((self.root, "linked.py"), (self.root, "linked-directory/selected.py"),
                           (self.root / "linked-directory", "selected.py")):
            with self.subTest(path=path), patch.object(guard_source.os, "read") as read:
                result = self.guard.scan_files(str(root), paths=[path])["report"]
                self.assertEqual(result["status"], "SCAN_INCOMPLETE_BLOCK")
                read.assert_not_called()

    def test_hardlinked_file_is_not_read(self):
        source = self.write("work/selected.py")
        os.link(source, self.root / "linked.py")
        with patch.object(guard_source.os, "read") as read:
            result = self.scan(["work/selected.py"])
        self.assertEqual(result["errors"][0]["code"], "NOT_SINGLE_REGULAR_FILE")
        read.assert_not_called()

    def test_directory_and_fifo_are_not_read(self):
        (self.root / "directory.py").mkdir()
        os.mkfifo(self.root / "pipe.py")
        for path in ("directory.py", "pipe.py"):
            with self.subTest(path=path), patch.object(guard_source.os, "read") as read:
                result = self.scan([path])
                self.assertEqual(result["errors"][0]["code"], "NOT_SINGLE_REGULAR_FILE")
                read.assert_not_called()

    def test_per_file_limit_rejects_before_content_read(self):
        self.write("work/selected.py", b"a" * 33)
        with patch.object(guard_source.os, "read") as read:
            result = self.scan(["work/selected.py"], max_file_bytes=32)
        self.assertEqual(result["errors"][0]["code"], "BYTE_LIMIT_EXCEEDED")
        self.assertEqual(result["bytes_read"], 0)
        read.assert_not_called()

    def test_total_limit_records_partial_coverage_without_overread(self):
        self.write("work/first.py", b"a" * 24)
        self.write("work/second.py", b"b" * 24)
        result = self.scan(["work/first.py", "work/second.py"], max_total_bytes=40)
        self.assertEqual(result["bytes_read"], 24)
        self.assertEqual(result["scanned_files"], 1)
        self.assertEqual(result["errors"], [{"file_index": 1, "code": "BYTE_LIMIT_EXCEEDED"}])
        self.assertFalse(result["selected_inputs_complete"])

    def test_invalid_or_unbounded_limits_fail_before_open(self):
        with patch.object(guard_source.os, "open", side_effect=AssertionError("must not open")) as opened:
            for name, maximum in guard_source.WORK_SCAN_LIMITS.items():
                for value in (True, False, 0, -1, "4", 1.0, maximum + 1):
                    with self.subTest(name=name, value=value):
                        result = self.scan(["work/file.py"], **{name: value})
                        self.assertEqual(result["errors"][0]["code"], "INVALID_LIMITS")
            opened.assert_not_called()

    def test_changed_input_is_reported(self):
        self.write("work/selected.py")
        original = os.fstat
        count = 0
        def changed_stat(descriptor):
            nonlocal count
            count += 1
            info = original(descriptor)
            if count == 1:
                return info
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
            data = {name: getattr(info, name) for name in fields}
            data["st_mtime_ns"] += 1
            return SimpleNamespace(**data)
        with patch.object(guard_source.os, "fstat", side_effect=changed_stat):
            result = self.scan(["work/selected.py"])
        self.assertEqual(result["errors"][0]["code"], "SOURCE_CHANGED")
        self.assertEqual(result["scanned_files"], 0)
        self.assertGreater(result["bytes_read"], 0)

    def test_unsupported_secure_open_platform_fails_before_open(self):
        with patch.object(guard_source, "SECURE_FILE_OPENS_SUPPORTED", False), \
             patch.object(guard_source.os, "open") as opened:
            result = self.scan(["work/file.py"])
        self.assertEqual(result["errors"][0]["code"], "SECURE_FILE_OPENS_UNSUPPORTED")
        opened.assert_not_called()

    def test_empty_selected_regular_file_is_complete(self):
        self.write("work/selected.py", b"")
        result = self.scan(["work/selected.py"])
        self.assertEqual(result["status"], "clean")
        self.assertEqual(result["scanned_files"], 1)
        self.assertEqual(result["bytes_read"], 0)
        self.assertTrue(result["selected_inputs_complete"])


if __name__ == "__main__":
    unittest.main()
