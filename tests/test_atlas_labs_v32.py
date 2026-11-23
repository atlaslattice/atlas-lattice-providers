import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from labs.atlas_labs_v32 import CATALOG, HSN_PIN, SCHEMA, catalog, prepare


EXAMPLE = pathlib.Path(__file__).resolve().parents[1] / 'examples' / 'atlas_labs_v32_synthetic.json'


def fixture():
    return json.loads(EXAMPLE.read_text())


class AtlasLabsTests(unittest.TestCase):
    def assert_held(self, x):
        a = prepare(x)
        self.assertEqual(a, {"status": "HOLD", "reason": "INVALID_OR_UNAUTHORIZED_PUBLIC_SOURCE",
                             "source_count": 0, "candidate": None})

    def test_all_eight_lab_roles_and_pins(self):
        self.assertEqual(len(CATALOG), 8)
        for lab, row in catalog().items():
            self.assertEqual(len(row["git_commit"]), 40)
            self.assertEqual(len(row["git_blob_sha1"]), 40)
            obj = fixture(); obj["lab_id"] = lab; obj["source_id"] = row["source_id"]
            with self.subTest(lab=lab):
                a = prepare(obj)
                self.assertEqual(a["status"], "PREPARED_SOURCE_ONLY")
                self.assertIn(row["git_commit"], a["candidate"]["atlas_one"]["packet"]["source_passport"]["url"])

    def test_success_is_three_inert_candidates(self):
        obj = fixture(); before = copy.deepcopy(obj)
        a = prepare(obj)
        self.assertEqual(obj, before)
        self.assertEqual(a["status"], "PREPARED_SOURCE_ONLY")
        out = a["candidate"]
        self.assertEqual(out["swarmchat_work"]["status"], "PREPARED_NOT_POSTED")
        self.assertEqual(out["alexandria"]["status"], "GRAPH_EDGE_CANDIDATE_NOT_WRITTEN")
        pkt = out["atlas_one"]["packet"]
        self.assertFalse(pkt["host_attested"] or pkt["verified_hardware"] or pkt["canon"] or pkt["deployment"] or pkt["same_as"])
        self.assertEqual(pkt["rights_at_return"], "NOT_CHECKED")
        self.assertEqual(len(pkt["experiment_sha256"]), 64)
        self.assertEqual(pkt["evidence_status"], "REPORTED_SYNTHETIC_NOT_REEXECUTED")

    def test_order_invariance_and_clean_json(self):
        a = fixture(); b = dict(reversed(list(a.items())))
        self.assertEqual(prepare(a)["candidate"]["atlas_one"]["packet"]["experiment_sha256"],
                         prepare(b)["candidate"]["atlas_one"]["packet"]["experiment_sha256"])
        self.assertEqual(prepare(a), prepare(json.dumps(a)))

    def test_design_only_has_no_results(self):
        x = fixture(); x["quantities"] = []; x["model_kind"] = "DESIGN_ONLY"
        r = prepare(x)
        self.assertEqual(r["status"], "PREPARED_SOURCE_ONLY")
        self.assertEqual(r["candidate"]["atlas_one"]["packet"]["evidence_status"], "UNVERIFIED_DESIGN")
        self.assert_held({**x, "quantities": fixture()["quantities"]})
        self.assert_held({**fixture(), "quantities": []})

    def test_pinned_ontology_address_not_semantics(self):
        x = fixture(); x["ontology"] = {"edition": "Ariadne v0.7", "registry_sha256": HSN_PIN,
                                           "coordinate": "H12.S12.N12"}
        r = prepare(x)
        self.assertTrue(r["candidate"]["alexandria"]["address_only"])
        self.assertFalse(r["candidate"]["alexandria"]["same_as"])
        for coordinate in ("H00.S01.N01", "H01.S00.N01", "H12.S12.N00", "H13.S01.N01", "H01.S01.N13"):
            with self.subTest(coordinate=coordinate):
                self.assert_held({**x, "ontology": {**x["ontology"], "coordinate": coordinate}})
        self.assert_held({**x, "ontology": {**x["ontology"], "edition": "legacy-zero-based"}})
        self.assert_held({**x, "ontology": {**x["ontology"], "registry_sha256": "0"*64}})

    def test_modes_and_rights_deny(self):
        for key, vals in {
            "origin_mode": ["PALACE", "PLAY", "WORK", "QUIET", "SOCIAL", "IMAGINE", None],
            "source_scope": ["PRIVATE", "WORK_REPORTED", None],
            "authority": ["owner", True],
            "canon": [True, 0, "false"],
            "deployment": [True, 0, "false"],
        }.items():
            for val in vals:
                with self.subTest(key=key, val=val):
                    self.assert_held({**fixture(), key: val})

    def test_invalid_result_types_units_evidence(self):
        for q in ([{"name":"out", "value":"1", "unit":"kWh", "uncertainty":"0", "evidence_class":"SYNTHETIC_MODEL_ONLY"}],
                  [{"name":"out", "value":"NaN", "unit":"bit", "uncertainty":"0", "evidence_class":"SYNTHETIC_MODEL_ONLY"}],
                  [{"name":"out", "value":"1e999", "unit":"bit", "uncertainty":"0", "evidence_class":"SYNTHETIC_MODEL_ONLY"}],
                  [{"name":"out", "value":"1e-999", "unit":"bit", "uncertainty":"0", "evidence_class":"SYNTHETIC_MODEL_ONLY"}],
                  [{"name":"out", "value":"1", "unit":"bit", "uncertainty":"-1", "evidence_class":"SYNTHETIC_MODEL_ONLY"}],
                  [{"name":"out", "value":"1", "unit":"bit", "uncertainty":"0", "evidence_class":"MEASURED"}]):
            self.assert_held({**fixture(), "quantities": q})
        q = fixture()["quantities"][0]
        self.assert_held({**fixture(), "quantities": [q, q]})
        self.assert_held({**fixture(), "quantities": [q]*9})
        self.assert_held({**fixture(), "quantities": [dict(q, value=1.0)]})

    def test_no_private_data_or_hidden_field_echo(self):
        x = fixture()
        for key in ("rawBody", "password", "token", "host_attested", "rights_epoch", "provider_api_key"):
            self.assert_held({**x, key: "FICTIONAL_PRIVATE_CANARY"})
        self.assertNotIn("FICTIONAL_PRIVATE_CANARY", json.dumps(prepare({**x, "token":"FICTIONAL_PRIVATE_CANARY"})))

    def test_malformed_json_and_duplicate_keys(self):
        for raw in (b"\xff", b"[]", b'{}', b'{"x":1e10000}', b'{"x":NaN}',
                    b'{"mode":"PALACE","mode":"PUBLIC"}',
                    b'{"e\\u0301":"x", "\\u00e9":"y"}',
                    b'x'*40000, b'null'):
            self.assert_held(raw)
        x = fixture(); x["quantities"][0]["value"] = float("inf")
        self.assert_held(x)
        x = fixture(); x["cycle"] = x
        self.assert_held(x)

    def test_unknown_lab_and_source_cannot_be_queried(self):
        self.assert_held({**fixture(), "lab_id": "secret-lab"})
        self.assert_held({**fixture(), "source_id": "private-palace-note"})
        self.assert_held({**fixture(), "source_id": []})
        self.assert_held({**fixture(), "lab_id": []})


if __name__ == '__main__':
    unittest.main()
