"""Candidate-only JSON Schema negative tests; no external services or production grants.

Run with:
    python -m pip install 'jsonschema>=4.18,<5'
    python -m unittest discover -s tests -p 'test_continuum_schemas.py' -v
Without the optional validator dependency, tests are explicitly SKIPPED.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

try:
    from jsonschema import Draft202012Validator
except ImportError:  # optional developer dependency; never silently claim a pass
    Draft202012Validator = None

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


@unittest.skipIf(Draft202012Validator is None, "jsonschema optional dependency not installed; no validation performed")
class ContinuumSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.continuum_schema = load("schemas/continuum/continuum.schema.json")
        cls.link_schema = load("schemas/continuum/continuum_link.schema.json")
        cls.candidate = load("examples/continuum_candidate.json")
        cls.bridge = load("examples/continuum_link_candidate.json")
        Draft202012Validator.check_schema(cls.continuum_schema)
        Draft202012Validator.check_schema(cls.link_schema)

    def valid(self, schema, payload):
        return not list(Draft202012Validator(schema).iter_errors(payload))

    def test_candidate_fixture_valid(self):
        self.assertTrue(self.valid(self.continuum_schema, self.candidate))

    def test_bridge_fixture_valid(self):
        self.assertTrue(self.valid(self.link_schema, self.bridge))

    def test_candidate_canon_rejected(self):
        p = copy.deepcopy(self.candidate); p["canon"] = True
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_candidate_deployment_rejected(self):
        p = copy.deepcopy(self.candidate); p["deployment"] = True
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_authority_escalation_rejected(self):
        p = copy.deepcopy(self.candidate); p["authority"] = "human-root"
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_missing_source_rejected(self):
        p = copy.deepcopy(self.candidate); del p["source_ref"]
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_outside_1728_coordinate_rejected(self):
        p = copy.deepcopy(self.candidate); p["coordinate"] = "H12.S00.N00"
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_duplicate_affinity_rejected(self):
        p = copy.deepcopy(self.candidate); p["d_affinity"] = ["D01", "D01"]
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_bad_raw_status_rejected(self):
        p = copy.deepcopy(self.candidate); p["raw_export_status"] = "verified_complete"
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_human_root_self_grant_rejected(self):
        p = copy.deepcopy(self.candidate); p["human_root_gate"]["state"] = "approved"
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_missing_preservation_path_rejected(self):
        p = copy.deepcopy(self.candidate); p["preservation"]["source_fossil_ref"] = ""
        self.assertFalse(self.valid(self.continuum_schema, p))

    def test_bridge_identity_fusion_rejected(self):
        p = copy.deepcopy(self.bridge); p["identity_fusion_allowed"] = True
        self.assertFalse(self.valid(self.link_schema, p))

    def test_bridge_collapse_rejected(self):
        p = copy.deepcopy(self.bridge); p["collapse_allowed"] = True
        self.assertFalse(self.valid(self.link_schema, p))

    def test_bridge_raw_content_transfer_rejected(self):
        p = copy.deepcopy(self.bridge); p["raw_content_transferred"] = True
        self.assertFalse(self.valid(self.link_schema, p))

    def test_bridge_absent_human_root_gate_rejected(self):
        p = copy.deepcopy(self.bridge); del p["human_root_gate"]
        self.assertFalse(self.valid(self.link_schema, p))

    def test_unknown_fields_rejected_for_scope_control(self):
        p = copy.deepcopy(self.bridge); p["host_authenticated"] = True
        self.assertFalse(self.valid(self.link_schema, p))


if __name__ == "__main__":
    unittest.main()
