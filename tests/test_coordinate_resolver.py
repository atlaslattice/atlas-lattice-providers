"""Fail-closed boundary tests; runnable without repository imports or network."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[1] / "core" / "coordinate_resolver.py"
spec = importlib.util.spec_from_file_location("coordinate_resolver", path)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def claim():
    return {"claim_id": "synthetic-test-1", "source_ref": "test:fixture:1",
            "source_continuum_id": "test-continuum-A", "target_continuum_id": "test-continuum-B",
            "bridge_type": "claim", "coordinate": "H01.S02.N03", "d_affinity": ["D12", "D01"],
            "authority": "none", "canon": False, "deployment": False}


class ResolverTests(unittest.TestCase):
    def test_valid_references_earth_and_preserves_origin(self):
        original = claim()
        r = resolver.resolve_to_earth(original)
        self.assertEqual(r["route"], "candidate_review")
        self.assertEqual(r["earth_reference"], "H00.S00.N00")
        self.assertEqual(r["original_coordinate"], "H01.S02.N03")
        self.assertEqual(r["d_affinity"], ["D01", "D12"])
        self.assertTrue(resolver.validate_grounding(r)["valid"])
        self.assertEqual(original, claim())

    def test_legacy_fallback_is_not_accepted(self):
        for bad in ("banana", "H12.S00.N00", "H01.S12.N00", "H01.S01.N12", "H01.S02.N03 junk", "h01.s02.n03"):
            c = claim(); c["coordinate"] = bad
            self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine")

    def test_missing_provenance_is_quarantined(self):
        for field in ("claim_id", "source_ref", "source_continuum_id"):
            c = claim(); c.pop(field)
            self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine")

    def test_self_promotion_and_identity_fusion_blocked(self):
        for key, value in (("canon", True), ("deployment", True), ("authority", "system"),
                           ("identity_fusion_allowed", True), ("collapse_allowed", True)):
            c = claim(); c[key] = value
            self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine")

    def test_bad_bridge_and_d_affinity_blocked(self):
        for key, value in (("bridge_type", "fusion"), ("d_affinity", ["D13"]), ("d_affinity", "D01"),
                           ("target_continuum_id", ""), ("source_url", "file:///private")):
            c = claim(); c[key] = value
            self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine")

    def test_metadata_cannot_override_guardrails(self):
        r = resolver.wrap_as_coordinate_packet(claim(), {"canon": True, "authority": "root", "earth_reference": "wrong"})
        self.assertTrue(resolver.validate_grounding(r)["valid"])
        self.assertIs(r["canon"], False)
        self.assertEqual(r["authority"], "none")
        self.assertEqual(r["caller_metadata"]["canon"], True)

    def test_tampering_fingerprint_and_gate_is_detected(self):
        r = resolver.resolve_to_earth(claim()); r["original_claim"]["source_ref"] = "tampered"
        self.assertFalse(resolver.validate_grounding(r)["valid"])
        r = resolver.resolve_to_earth(claim()); r["human_root_gate"] = "granted"
        self.assertFalse(resolver.validate_grounding(r)["valid"])

    def test_quarantined_packet_never_validates(self):
        r = resolver.resolve_to_earth({"coordinate": "H00.S00.N00"})
        self.assertFalse(resolver.validate_grounding(r)["valid"])
        self.assertEqual(r["original_claim"], {"coordinate": "H00.S00.N00"})

    def test_non_dict_input_preserved_quarantined(self):
        r = resolver.resolve_to_earth("unsafe")
        self.assertEqual(r["route"], "quarantine")
        self.assertEqual(r["original_claim"], "unsafe")

    def test_tampering_derived_fields_detected(self):
        for key, value in (("original_coordinate", "H00.S00.N00"), ("status", "CANON"),
                           ("d_affinity", ["D02"]), ("provenance", {})):
            r = resolver.resolve_to_earth(claim()); r[key] = value
            self.assertFalse(resolver.validate_grounding(r)["valid"], key)

    def test_bad_json_shape_bridge_fails_closed(self):
        c = claim(); c["bridge_type"] = ["claim"]
        self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine")

    def test_escalation_is_inert(self):
        r = resolver.escalate_to_human_root("review missing source", {"id": "x"})
        self.assertEqual(r["status"], "NOT_SENT")
        self.assertIs(r["canon"], False)


if __name__ == "__main__":
    unittest.main()
