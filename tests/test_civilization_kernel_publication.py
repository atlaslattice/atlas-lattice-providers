"""Verify bundled selected-reference bytes; this is not a source retrieval test."""
import unittest
from pathlib import Path
from core.civilization_kernel_reference import read_reference

class PublicationReferenceTests(unittest.TestCase):
    def test_selected_immutable_reference_bytes(self):
        raw = (Path(__file__).resolve().parents[1] / 'config/civilization-r01/source_reference.json').read_bytes()
        record = read_reference(raw, 'f1002f1eb4a88aaf9db5239aa3ecc3b4dd54aa3a8dfeeefe1950c40eb9b37038')
        self.assertEqual(record["source_commit"], 'fe8f24033ea307b6ecb29d561479cbe24f9c816d')
        self.assertEqual(len(record["source_files"]), 33)
        self.assertEqual(record["dispatch"]["H02"], "REFERENCE_QUERY")
        self.assertEqual(record["benchmark"]["original_1728_primary_metric_credit"], 0)
        self.assertIs(record["deployment"], False)

if __name__ == "__main__":
    unittest.main()
