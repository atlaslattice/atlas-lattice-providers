"""Verify bundled selected-reference bytes; this is not a source retrieval test."""
import unittest
from pathlib import Path
from core.civilization_kernel_reference import read_reference

class PublicationReferenceTests(unittest.TestCase):
    def test_selected_immutable_reference_bytes(self):
        raw = (Path(__file__).resolve().parents[1] / 'config/civilization-r01/source_reference.json').read_bytes()
        record = read_reference(raw, 'c58306da892927b60e2c2f98e868a5ee9a176ea10b5ecb37851782df770128a9')
        self.assertEqual(record["source_commit"], 'fe8f24033ea307b6ecb29d561479cbe24f9c816d')
        self.assertEqual(len(record["source_files"]), 33)
        self.assertEqual(record["dispatch"]["H02"], "REFERENCE_QUERY")
        self.assertEqual(record["benchmark"]["original_1728_primary_metric_credit"], 0)
        self.assertIs(record["deployment"], False)

if __name__ == "__main__":
    unittest.main()
