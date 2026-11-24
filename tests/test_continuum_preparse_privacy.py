"""Regression: malformed or oversized source bodies are unknown/private by default."""
import json
import unittest

from core.continuum_bridge_candidate import propose


def good():
    return {"claim_id":"synthetic1","source_ref":"synthetic://x",
            "source_continuum_id":"synthetic.a","target_continuum_id":"synthetic.b",
            "coordinate":"H02.S03.N04","bridge_type":"review",
            "source_scope":"WORK_REPORTED","rights_status":"UNVERIFIED",
            "mode":"WORK","no_harvest":False,"canon":False,
            "deployment":False,"collapse_allowed":False,
            "identity_fusion_allowed":False,"authority":"none",
            "d_affinity":["D01"],"dissent_refs":[]}


class PreparsePrivacyTests(unittest.TestCase):
    def test_unparseable_private_or_unknown_has_no_fingerprint(self):
        for raw in (b'{"mode":"PLAY","source_scope":"PLAY"',
                    b'{"mode":"QUIET","mode":"WORK"}',
                    b'\xffprivate-content', b'not-json'):
            with self.subTest(size=len(raw)):
                result=propose(raw)
                self.assertEqual(result["status"],"HOLD")
                self.assertIsNone(result["source_sha256"])
                self.assertIsNone(result["source_bytes"])
    def test_oversize_unparseable_has_no_fingerprint(self):
        result=propose(b'private'*(65536//7 + 1))
        self.assertEqual(result["status"],"HOLD")
        self.assertIsNone(result["source_sha256"])
        self.assertIsNone(result["source_bytes"])
    def test_valid_play_and_unknown_scope_no_fingerprint(self):
        for field,value in (("mode","PLAY"),("source_scope","PRIVATE"),
                            ("no_harvest",True)):
            obj=good();obj[field]=value
            result=propose(obj)
            self.assertEqual(result["status"],"HOLD")
            self.assertIsNone(result["source_sha256"])
            self.assertIsNone(result["source_bytes"])
    def test_nonstring_scope_is_generic_hold_without_unhashable_crash(self):
        for scope in ([], ["WORK_REPORTED"], {}, {"private": "synthetic"}):
            with self.subTest(scope=type(scope).__name__):
                obj=good();obj["source_scope"]=scope
                result=propose(obj)
                self.assertEqual(result["status"],"HOLD")
                self.assertIsNone(result["source_sha256"])
                self.assertIsNone(result["source_bytes"])

    def test_nonstring_mode_is_unknown_not_source_verified(self):
        for mode in (["WORK"], {"mode": "WORK"}, None):
            with self.subTest(mode=type(mode).__name__):
                obj=good();obj["mode"]=mode
                result=propose(obj)
                self.assertEqual(result["status"],"HOLD")
                self.assertIsNone(result["source_sha256"])
                self.assertIsNone(result["source_bytes"])

    def test_one_based_h12_allowed_and_h00_withheld(self):
        # Ariadne v0.7 is one-based: H12 is valid; H00 is legacy-only.
        valid = good(); valid["coordinate"] = "H12.S01.N02"
        accepted = propose(json.dumps(valid))
        self.assertEqual(accepted["status"], "REVIEWABLE_LOCAL_ONLY")
        self.assertEqual(accepted["source_bytes"], len(json.dumps(valid).encode()))
        self.assertEqual(len(accepted["source_sha256"]), 64)
        invalid = good(); invalid["coordinate"] = "H00.S01.N02"
        denied = propose(json.dumps(invalid))
        self.assertEqual(denied["status"], "HOLD")
        self.assertIsNone(denied["source_sha256"])
        self.assertIsNone(denied["source_bytes"])
    def test_valid_work_candidate_is_still_local_only(self):
        result=propose(good())
        self.assertEqual(result["status"],"REVIEWABLE_LOCAL_ONLY")
        self.assertFalse(result["execution_allowed"])
        self.assertEqual(result["authority_effect"],"NONE")

if __name__=="__main__": unittest.main()
