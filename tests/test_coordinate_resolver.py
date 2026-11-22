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
        for bad in ("banana", "H12.S00.N00", "H01.S12.N00", "H01.S01.N00", "H01.S02.N03 junk", "h01.s02.n03"):
            c = claim(); c["coordinate"] = bad
            self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine")

    def test_full_ariadne_v07_1728_coordinate_lattice(self):
        # All twelve houses, twelve spheres and twelve nodes must be reachable.
        valid = 0
        for h in range(1, 13):
            for sphere in range(1, 13):
                for node in range(1, 13):
                    c = claim()
                    c["coordinate"] = f"H{h:02d}.S{sphere:02d}.N{node:02d}"
                    resolved = resolver.resolve_to_earth(c)
                    self.assertEqual(resolved["route"], "candidate_review", c["coordinate"])
                    self.assertEqual(resolved["earth_reference"], "H00.S00.N00")
                    self.assertTrue(resolver.validate_grounding(resolved)["valid"], c["coordinate"])
                    valid += 1
        self.assertEqual(valid, 1728)

    def test_earth_sentinel_is_output_only_not_a_knowledge_coordinate(self):
        for invalid in ("H00.S00.N00", "H00.S01.N01", "H01.S00.N01",
                        "H01.S01.N00", "H00.S12.N12"):
            c = claim(); c["coordinate"] = invalid
            r = resolver.resolve_to_earth(c)
            self.assertEqual(r["route"], "quarantine", invalid)
            self.assertEqual(r["original_claim"], c)
            self.assertEqual(r["earth_reference"], "H00.S00.N00")
            self.assertFalse(resolver.validate_grounding(r)["valid"], invalid)

    def test_out_of_range_and_malformed_coordinates_are_quarantined(self):
        for invalid in ("H13.S12.N12", "H12.S13.N12", "H12.S12.N13",
                        "H99.S01.N01", "H01.S99.N01", "H01.S01.N99",
                        "H001.S01.N01", "H12.S012.N12", "H12.S12.N012",
                        "H-1.S01.N01", "H12.S12.N12 ", "h12.s12.n12"):
            c = claim(); c["coordinate"] = invalid
            self.assertEqual(resolver.resolve_to_earth(c)["route"], "quarantine", invalid)

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