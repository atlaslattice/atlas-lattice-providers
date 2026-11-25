"""Source-custody tests for the optional, offline PR61 import.

All fixtures are synthetic. No broker, real agent, tool, network or private
data is touched; a hash match is not a runtime rights grant.
"""
from hashlib import sha1
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import unittest

from scripts import run_local_pipeline as importer

GOOD = b'STATUS = "VERIFIED_SYNTHETIC_SOURCE"\n'
SWAPPED = b'STATUS = "SWAPPED_AFTER_DIGEST"\n'


def git_blob(raw):
    return sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


class PinnedSourceCustodyTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'public_fixture.py'
        self.path.write_bytes(GOOD)

    def test_exact_verified_buffer_executes(self):
        with patch.object(importer, 'LABS_PR61_SOURCE_GIT_BLOB', git_blob(GOOD)):
            self.assertEqual(importer.import_pinned_labs_source(self.path).STATUS,
                             'VERIFIED_SYNTHETIC_SOURCE')

    def test_swap_after_digest_does_not_change_executed_bytes(self):
        original_read = Path.read_bytes
        path = self.path

        def read_then_swap(target):
            data = original_read(target)
            if target == path:
                path.write_bytes(SWAPPED)
            return data

        with patch.object(importer, 'LABS_PR61_SOURCE_GIT_BLOB', git_blob(GOOD)), \
             patch.object(Path, 'read_bytes', read_then_swap):
            result = importer.import_pinned_labs_source(path)
        self.assertEqual(result.STATUS, 'VERIFIED_SYNTHETIC_SOURCE')
        self.assertEqual(path.read_bytes(), SWAPPED)

    def test_tampered_first_read_refused(self):
        self.path.write_bytes(SWAPPED)
        with patch.object(importer, 'LABS_PR61_SOURCE_GIT_BLOB', git_blob(GOOD)):
            with self.assertRaisesRegex(ValueError, 'not the reviewed'):
                importer.import_pinned_labs_source(self.path)

    def test_oversized_source_refused(self):
        self.path.write_bytes(b' ' * 250001)
        with patch.object(importer, 'LABS_PR61_SOURCE_GIT_BLOB', git_blob(GOOD)):
            with self.assertRaises(ValueError):
                importer.import_pinned_labs_source(self.path)

    def test_verified_invalid_python_still_fails_closed(self):
        invalid = b'def unclosed(:\n'
        self.path.write_bytes(invalid)
        with patch.object(importer, 'LABS_PR61_SOURCE_GIT_BLOB', git_blob(invalid)):
            with self.assertRaises(SyntaxError):
                importer.import_pinned_labs_source(self.path)


if __name__ == '__main__':
    unittest.main()
