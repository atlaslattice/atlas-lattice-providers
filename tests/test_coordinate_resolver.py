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
    def test_self_declared_private_sources_and_metadata_never_echo(self):
        secret = "FICTIONAL_PRIVACY_SENTINEL_DO_NOT_ECHO"
        for mode in ("PLAY", "SOCIAL", "QUIET", "IMAGINE", "DREAM", None, 1):
            with self.subTest(mode=repr(mode)):
                c = claim()
                c["mode"] = mode
                c["payload"] = {"secret": secret}
                result = resolver.resolve_to_earth(c)
                self.assertEqual(result["status"], "HELD_PRIVATE_MODE")
                self.assertEqual(result["route"], "quarantine")
                self.assertIsNone(result["original_claim"])
                self.assertNotIn(secret, repr(result))
                self.assertFalse(resolver.validate_grounding(result)["valid"])
        for flag in (True, None, "false", 0):
            with self.subTest(no_harvest=repr(flag)):
                c = claim()
                c["no_harvest"] = flag
                c["body"] = secret
                result = resolver.resolve_to_earth(c)
                self.assertEqual(result["status"], "HELD_PRIVATE_MODE")
                self.assertNotIn(secret, repr(result))
        wrapped = resolver.wrap_as_coordinate_packet(
            claim(), {"mode": "IMAGINE", "secret": secret})
        self.assertEqual(wrapped["status"], "HELD_PRIVATE_MODE")
        self.assertNotIn(secret, repr(wrapped))
        self.assertNotIn("caller_metadata", wrapped)
        normal = resolver.resolve_to_earth(dict(claim(), mode="WORK", no_harvest=False))
        self.assertEqual(normal["route"], "candidate_review")

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

    def test_full_ariadne_v07_1728_coordinate_lattice(self):
        # All twelve houses, spheres and nodes must be available when opted-in.
        valid = 0
        for h in range(1, 13):
            for sphere in range(1, 13):
                for node in range(1, 13):
                    c = claim()
                    c["coordinate"] = f"H{h:02d}.S{sphere:02d}.N{node:02d}"
                    c["coordinate_edition"] = resolver.ARIADNE_EDITION
                    c["coordinate_registry_digest"] = resolver.ARIADNE_SOURCE_SHA256
                    resolved = resolver.resolve_to_earth(c)
                    self.assertEqual(resolved["route"], "candidate_review", c["coordinate"])
                    self.assertEqual(resolved["earth_reference"], "H00.S00.N00")
                    self.assertEqual(resolved["coordinate_edition"], resolver.ARIADNE_EDITION)
                    self.assertEqual(resolved["schema"], "coordinate-candidate/v0.2")
                    self.assertTrue(resolver.validate_grounding(resolved)["valid"], c["coordinate"])
                    valid += 1
        self.assertEqual(valid, 1728)

    def test_legacy_wire_shape_preserved_and_explicit_edition_gets_v02(self):
        legacy = resolver.resolve_to_earth(claim())
        self.assertEqual(legacy["schema"], "coordinate-candidate/v0.1")
        self.assertNotIn("coordinate_edition", legacy)
        self.assertNotIn("coordinate_registry_digest", legacy)
        explicit_legacy_claim = claim()
        explicit_legacy_claim["coordinate_edition"] = resolver.LEGACY_EDITION
        explicit = resolver.resolve_to_earth(explicit_legacy_claim)
        self.assertEqual(explicit["schema"], "coordinate-candidate/v0.2")
        self.assertEqual(explicit["coordinate_edition"], resolver.LEGACY_EDITION)
        self.assertTrue(resolver.validate_grounding(explicit)["valid"])
        # A v0.1 packet may not be falsely relabeled as v0.2 or vice versa.
        forged = resolver.resolve_to_earth(claim())
        forged["schema"] = "coordinate-candidate/v0.2"
        self.assertFalse(resolver.validate_grounding(forged)["valid"])

    def test_full_legacy_zero_based_1728_coordinate_lattice_unchanged(self):
        valid = 0
        for h in range(12):
            for sphere in range(12):
                for node in range(12):
                    c = claim(); c["coordinate"] = f"H{h:02d}.S{sphere:02d}.N{node:02d}"
                    resolved = resolver.resolve_to_earth(c)
                    self.assertEqual(resolved["route"], "candidate_review", c["coordinate"])
                    self.assertNotIn("coordinate_edition", resolved)
                    self.assertNotIn("coordinate_registry_digest", resolved)
                    self.assertEqual(resolved["schema"], "coordinate-candidate/v0.1")
                    self.assertTrue(resolver.validate_grounding(resolved)["valid"])
                    valid += 1
        self.assertEqual(valid, 1728)

    def test_earth_sentinel_is_not_an_ariadne_knowledge_coordinate(self):
        for invalid in ("H00.S00.N00", "H00.S01.N01", "H01.S00.N01",
                        "H01.S01.N00", "H00.S12.N12"):
            c = claim(); c["coordinate"] = invalid
            c["coordinate_edition"] = resolver.ARIADNE_EDITION
            c["coordinate_registry_digest"] = resolver.ARIADNE_SOURCE_SHA256
            r = resolver.resolve_to_earth(c)
            self.assertEqual(r["route"], "quarantine", invalid)
            self.assertEqual(r["original_claim"], c)
            self.assertEqual(r["earth_reference"], "H00.S00.N00")
            self.assertFalse(resolver.validate_grounding(r)["valid"], invalid)

    def test_ariadne_and_legacy_edition_boundaries_are_not_silently_aliased(self):
        valid_ariadne = claim(); valid_ariadne.update({
            "coordinate": "H12.S12.N12", "coordinate_edition": resolver.ARIADNE_EDITION,
            "coordinate_registry_digest": resolver.ARIADNE_SOURCE_SHA256,
        })
        self.assertEqual(resolver.resolve_to_earth(valid_ariadne)["route"], "candidate_review")
        without_edition = dict(valid_ariadne)
        without_edition.pop("coordinate_edition")
        self.assertEqual(resolver.resolve_to_earth(without_edition)["route"], "quarantine")
        without_digest = dict(valid_ariadne)
        without_digest.pop("coordinate_registry_digest")
        self.assertEqual(resolver.resolve_to_earth(without_digest)["route"], "quarantine")
        wrong_digest = dict(valid_ariadne)
        wrong_digest["coordinate_registry_digest"] = "0" * 64
        self.assertEqual(resolver.resolve_to_earth(wrong_digest)["route"], "quarantine")
        bad_edition = dict(valid_ariadne)
        bad_edition["coordinate_edition"] = "ARIADNE_V0"
        self.assertEqual(resolver.resolve_to_earth(bad_edition)["route"], "quarantine")
        legacy_earth = claim(); legacy_earth["coordinate"] = "H00.S00.N00"
        self.assertEqual(resolver.resolve_to_earth(legacy_earth)["route"], "candidate_review")
        self.assertNotIn("coordinate_edition", resolver.resolve_to_earth(legacy_earth))

    def test_reject_edition_and_digest_tampering(self):
        c = claim(); c.update({
            "coordinate": "H12.S12.N12", "coordinate_edition": resolver.ARIADNE_EDITION,
            "coordinate_registry_digest": resolver.ARIADNE_SOURCE_SHA256,
        })
        for key, bad in (("coordinate_edition", resolver.LEGACY_EDITION),
                         ("coordinate_registry_digest", None),
                         ("coordinate_registry_digest", "1" * 64)):
            with self.subTest(key=key, bad=bad):
                receipt = resolver.resolve_to_earth(c)
                receipt[key] = bad
                self.assertFalse(resolver.validate_grounding(receipt)["valid"])

    def test_out_of_range_and_malformed_coordinates_are_quarantined(self):
        for invalid in ("H13.S12.N12", "H12.S13.N12", "H12.S12.N13",
                        "H99.S01.N01", "H01.S99.N01", "H01.S01.N99",
                        "H001.S01.N01", "H12.S012.N12", "H12.S12.N012",
                        "H-1.S01.N01", "H12.S12.N12 ", "h12.s12.n12"):
            c = claim(); c.update({"coordinate": invalid,
                                   "coordinate_edition": resolver.ARIADNE_EDITION,
                                   "coordinate_registry_digest": resolver.ARIADNE_SOURCE_SHA256})
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
