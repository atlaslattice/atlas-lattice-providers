"""Offline negative tests: candidate only, no live identities or outbound calls."""
import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from core.continuum_bridge_candidate import propose
from core.transparent_packet96 import from_json, review, to_json


def good():
    return {"claim_id": "synthetic1", "source_ref": "synthetic://do-not-export-payload",
            "source_continuum_id": "synthetic.alpha", "target_continuum_id": "synthetic.beta",
            "coordinate": "H02.S03.N04", "bridge_type": "review", "source_scope": "WORK_REPORTED",
            "rights_status": "UNVERIFIED", "mode": "WORK", "no_harvest": False,
            "canon": False, "deployment": False, "collapse_allowed": False,
            "identity_fusion_allowed": False, "authority": "none", "d_affinity": ["D12", "D01"],
            "dissent_refs": ["private:objection1"]}


class CandidateBridgeTests(unittest.TestCase):
    def test_bounded_candidate(self):
        r = propose(good()); self.assertEqual(r["status"], "REVIEWABLE_LOCAL_ONLY")
        self.assertFalse(r["execution_allowed"])
        self.assertFalse(r["link"]["raw_content_transferred"])
        self.assertEqual(r["link"]["human_root_gate"]["state"], "not_granted")
        self.assertFalse(r["packet96"]["receipt"]["delivered"])

    def test_original_not_mutated(self):
        obj=good();old=copy.deepcopy(obj);propose(obj);self.assertEqual(obj,old)

    def test_no_plain_source_or_dissent_transfer(self):
        r=json.dumps(propose(good()))
        self.assertNotIn("synthetic://do-not-export-payload",r)
        self.assertNotIn("private:objection1",r)

    def test_malformed_modes_hold(self):
        for scope in ["PLAY", "DREAM", "QUIET", "IMAGINE", "SOCIAL", "BRAIN", None]:
            obj=good();obj["source_scope"]=scope
            with self.subTest(scope=scope): self.assertEqual(propose(obj)["status"],"HOLD")

    def test_explicit_private_mode_holds(self):
        for val in ["PLAY", "DREAM", "SOCIAL", "IMAGINE", None]:
            obj=good();obj["mode"]=val
            with self.subTest(val=val):self.assertEqual(propose(obj)["status"],"HOLD")

    def test_fake_rights_or_canon_hold(self):
        for field,value in [("rights_status","VERIFIED"),("canon",True),("canon",0),
                            ("deployment",True),("collapse_allowed",True),("identity_fusion_allowed",True),
                            ("authority","root"),("requested_action","deploy"),("no_harvest",True)]:
            obj=good();obj[field]=value
            with self.subTest(field=field):self.assertEqual(propose(obj)["status"],"HOLD")

    def test_coordinate_bounds(self):
        for coordinate in ["H12.S00.N00","H00.S12.N00","H00.S00.N12","garbage","H0.S0.N0"]:
            obj=good();obj["coordinate"]=coordinate
            with self.subTest(coordinate=coordinate):self.assertEqual(propose(obj)["status"],"HOLD")

    def test_ariadne_v07_one_based_coordinate_range(self):
        # All 1,728 canonical coordinates are H/S/N = 01..12, never 00.
        for coordinate in ("H01.S01.N01", "H12.S12.N12", "H12.S01.N12",
                           "H01.S12.N01"):
            obj = good(); obj["coordinate"] = coordinate
            with self.subTest(valid=coordinate):
                self.assertEqual(propose(obj)["status"], "REVIEWABLE_LOCAL_ONLY")
        for coordinate in ("H00.S01.N01", "H01.S00.N01", "H01.S01.N00",
                           "H13.S12.N12", "H12.S13.N12", "H12.S12.N13"):
            obj = good(); obj["coordinate"] = coordinate
            with self.subTest(invalid=coordinate):
                result = propose(obj)
                self.assertEqual(result["status"], "HOLD")
                self.assertIsNone(result["source_sha256"])
                self.assertIsNone(result["packet96"])

    def test_missing_source_identity_hold(self):
        for field in ["claim_id", "source_ref", "source_continuum_id", "target_continuum_id"]:
            obj=good();obj.pop(field)
            with self.subTest(field=field):self.assertEqual(propose(obj)["status"],"HOLD")

    def test_no_same_continuum_cross_bridge(self):
        obj=good();obj["target_continuum_id"]="synthetic.alpha"
        self.assertEqual(propose(obj)["status"],"HOLD")

    def test_d_affinity_and_dissent_validation(self):
        for field,value in [("d_affinity",["D13"]),("d_affinity","D01"),("dissent_refs",[None]),("bridge_type","mind-merge")]:
            obj=good();obj[field]=value
            with self.subTest(field=field):self.assertEqual(propose(obj)["status"],"HOLD")

    def test_stable_for_key_order(self):
        obj=good();rev=dict(reversed(list(obj.items())))
        self.assertEqual(propose(obj)["source_sha256"], propose(rev)["source_sha256"])

    def test_duplicate_json_key_rejected(self):
        self.assertEqual(propose('{"canon":false,"canon":true}')["status"],"HOLD")

    def test_nan_unserializable_and_cyclic_hold(self):
        obj=good();obj["payload"]={"a":float('nan')}
        self.assertEqual(propose(obj)["status"],"HOLD")
        obj=good();obj["payload"] = obj
        self.assertEqual(propose(obj)["status"],"HOLD")

    def test_nonzero_float_underflow_holds_without_rounding(self):
        base=json.dumps(good())[:-1]
        for tiny in ("1e-9999", "-1e-9999", "2e-400"):
            with self.subTest(tiny=tiny):
                raw=base+', "synthetic_weight":'+tiny+'}'
                result=propose(raw)
                self.assertEqual(result["status"], "HOLD")
                self.assertIn("UNPARSEABLE_JSON", result["reason_codes"])
        # A literal zero or a representable subnormal is not underflow.
        for allowed in ("0e-9999", "5e-324"):
            with self.subTest(allowed=allowed):
                raw=base+', "synthetic_weight":'+allowed+'}'
                self.assertEqual(propose(raw)["status"], "REVIEWABLE_LOCAL_ONLY")

    def test_non_utf8_bytes_hold(self):
        self.assertEqual(propose(b'\xff\xfe')["status"],"HOLD")

    def test_wrong_types_hold(self):
        for obj in [1, ["x"],None, "[]"]:
            self.assertEqual(propose(obj)["status"],"HOLD")

    def test_oversize_hold(self):
        obj=good();obj["big"]="x"*65536
        self.assertEqual(propose(obj)["status"],"HOLD")


    def test_packet96_contract_with_existing_local_module(self):
        from core.transparent_packet96 import review
        p = propose(good())
        outcome = review(p["packet96"])
        self.assertEqual(outcome.status, "REVIEWABLE_LOCAL_ONLY")
        self.assertEqual(outcome.reasons, ())

    def test_missing_optional_arrays_fail_closed_not_keyerror(self):
        for name in ("d_affinity", "dissent_refs"):
            candidate = good(); candidate.pop(name)
            self.assertEqual(propose(candidate)["status"], "HOLD")

    def test_private_mode_holds_without_fingerprint_or_length(self):
        for key, value in (("mode", "PLAY"), ("source_scope", "QUIET"),
                           ("no_harvest", True)):
            candidate = good(); candidate[key] = value
            r = propose(candidate)
            self.assertEqual(r["status"], "HOLD")
            self.assertIsNone(r["source_sha256"])
            self.assertIsNone(r["source_bytes"])

    def test_continuum_ids_do_not_encode_tokens_or_urls(self):
        for bad_id in ("secret?token=abc", "https://example.com/path", "a b", "💫"):
            candidate = good(); candidate["source_continuum_id"] = bad_id
            self.assertEqual(propose(candidate)["status"], "HOLD")

    def test_official_link_schema_with_jsonschema_when_installed(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema optional dependency not installed")
        schema_path = pathlib.Path(__file__).resolve().parents[1] / "schemas" / "continuum" / "continuum_link.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(propose(good())["link"])

    def test_packet96_review_contract(self):
        proposal = propose(good())
        packet = from_json(to_json(proposal["packet96"]))
        outcome = review(packet)
        self.assertEqual(outcome.status, "REVIEWABLE_LOCAL_ONLY")
        self.assertEqual(outcome.reasons, ())
        self.assertEqual(outcome.authority_effect, "NONE")
        self.assertEqual(outcome.host_attestation, "NOT_ATTESTED")
        self.assertFalse(packet["receipt"]["delivered"])
        self.assertFalse(packet["canon"] or packet["deployment"] or packet["same_as"])

    def test_plural_context_is_explicit_and_nonfusing(self):
        packet = propose(good())["packet96"]
        self.assertEqual(packet["continuum_context"], {
            "source_continuum_id": "synthetic.alpha",
            "target_continuum_id": "synthetic.beta",
            "bridge_type": "review",
            "collapse_allowed": False, "identity_fusion_allowed": False,
            "dissent_preserved": True, "inv0_preservation_required": True,
        })
        self.assertNotEqual(packet["continuum_context"]["source_continuum_id"],
                            packet["continuum_context"]["target_continuum_id"])

    def test_json_exponent_overflow_holds(self):
        raw = json.dumps(good(), separators=(",", ":"))[:-1] + ',"unexpected":1e10000}'
        proposal = propose(raw)
        self.assertEqual(proposal["status"], "HOLD")
        self.assertIsNone(proposal["packet96"])
        self.assertIsNone(proposal["link"])


    def test_invalid_caller_labeled_work_never_fingerprinted(self):
        # Mode/rights strings are untrusted. Invalid data can originate
        # from any protected surface despite a self-reported Work label.
        for key, value in (("coordinate", "wrong"),
                           ("source_continuum_id", "https://invalid.test/path"),
                           ("rights_status", "VERIFIED")):
            obj = good()
            obj[key] = value
            with self.subTest(field=key):
                out = propose(obj)
                self.assertEqual(out["status"], "HOLD")
                self.assertIsNone(out["source_sha256"])
                self.assertIsNone(out["source_bytes"])

    def test_unreviewed_extra_body_fields_cannot_enter_digest(self):
        for extra in ("private_body", "privateMemo", "sourceText", "unreviewed"):
            obj = good()
            obj[extra] = "FICTIONAL_PRIVATE_CANARY"
            with self.subTest(extra=extra):
                out = propose(obj)
                self.assertEqual(out["status"], "HOLD")
                self.assertIn("UNRECOGNIZED_SOURCE_FIELDS", out["reason_codes"])
                self.assertIsNone(out["source_sha256"])
                self.assertIsNone(out["source_bytes"])
                self.assertIsNone(out["packet96"])
                self.assertIsNone(out["link"])

    def test_valid_declared_review_candidate_retains_source_digest(self):
        out = propose(good())
        self.assertEqual(out["status"], "REVIEWABLE_LOCAL_ONLY")
        self.assertRegex(out["source_sha256"], r"^[a-f0-9]{64}$")

if __name__=="__main__": unittest.main()
