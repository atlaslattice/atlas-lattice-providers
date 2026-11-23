"""Offline candidate-packet extension guards. Synthetic/public-safe only."""
import importlib.util
from pathlib import Path
import unittest

module_path = Path(__file__).resolve().parents[1] / "core" / "coordinate_resolver.py"
spec = importlib.util.spec_from_file_location("coordinate_packet_field_guard", module_path)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def claim():
    return {
        "claim_id": "synthetic-packet-fields",
        "source_ref": "test:public-fixture",
        "source_continuum_id": "synthetic-A",
        "coordinate": "H01.S02.N03",
        "authority": "none", "canon": False, "deployment": False,
    }


class HostileDict(dict):
    def get(self, *_args, **_kwargs):
        raise AssertionError("untrusted dict subclass .get must not run")


class PacketFieldGuardTests(unittest.TestCase):
    def test_legacy_unmodified_packet_still_valid(self):
        packet = resolver.resolve_to_earth(claim())
        self.assertEqual(packet["schema"], "coordinate-candidate/v0.1")
        self.assertTrue(resolver.validate_grounding(packet)["valid"])

    def test_ariadne_explicit_packet_still_valid(self):
        source = claim()
        source.update({"coordinate_edition": resolver.ARIADNE_EDITION,
                       "coordinate_registry_digest": resolver.ARIADNE_SOURCE_SHA256,
                       "coordinate": "H12.S12.N12"})
        packet = resolver.resolve_to_earth(source)
        self.assertEqual(packet["schema"], "coordinate-candidate/v0.2")
        self.assertTrue(resolver.validate_grounding(packet)["valid"])

    def test_unverified_extra_attestation_is_rejected(self):
        packet = resolver.resolve_to_earth(claim())
        packet["host_approved"] = True
        verdict = resolver.validate_grounding(packet)
        self.assertFalse(verdict["valid"])
        self.assertIn("unexpected_packet_fields", verdict["reasons"])

    def test_opaque_caller_metadata_is_rejected(self):
        packet = resolver.resolve_to_earth(claim())
        packet["caller_metadata"] = object()
        verdict = resolver.validate_grounding(packet)
        self.assertFalse(verdict["valid"])
        self.assertIn("caller_metadata_not_plain_json", verdict["reasons"])

    def test_plain_caller_metadata_remains_inert(self):
        packet = resolver.wrap_as_coordinate_packet(claim(),
            {"source": "public-synthetic", "review_status": "NOT_VERIFIED"})
        self.assertTrue(resolver.validate_grounding(packet)["valid"])
        self.assertEqual(packet["authority"], "none")
        self.assertIs(packet["deployment"], False)

    def test_dict_subclass_with_behavior_never_read(self):
        packet = HostileDict(resolver.resolve_to_earth(claim()))
        self.assertEqual(resolver.validate_grounding(packet),
                         {"valid": False, "reasons": ["not_a_packet"]})


if __name__ == "__main__":
    unittest.main()
