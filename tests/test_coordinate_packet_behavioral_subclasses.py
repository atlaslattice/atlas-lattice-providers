"""Public-synthetic packet hardening: behavioral Python caller objects never execute.

Source-only regression. No private Work/Play bodies, host rights, CANON or
independent CI claim. Run: python -m unittest discover -s tests
-p 'test_coordinate_packet_behavioral_subclasses.py' -v
"""
import unittest

from core.coordinate_resolver import (
    ARIADNE_EDITION, ARIADNE_SOURCE_SHA256,
    resolve_to_earth, validate_grounding,
)


def claim():
    return {
        "claim_id": "synthetic-packet-boundary",
        "source_ref": "synthetic:public:packet",
        "source_continuum_id": "synthetic-A",
        "coordinate": "H01.S02.N03",
        "authority": "none",
        "canon": False,
        "deployment": False,
    }


class ExplodingContext(dict):
    def get(self, *_args, **_kwargs):
        raise AssertionError("untrusted nested dict.get must not be called")


class ExplodingString(str):
    def __eq__(self, _other):
        raise AssertionError("untrusted nested str.__eq__ must not be called")


class PacketBehavioralSubclassTests(unittest.TestCase):
    def assert_hold(self, packet):
        verdict = validate_grounding(packet)
        self.assertEqual(
            verdict,
            {"valid": False, "reasons": ["not_a_plain_json_packet"]},
        )

    def test_plain_legacy_packet_remains_reviewable(self):
        self.assertTrue(validate_grounding(resolve_to_earth(claim()))["valid"])

    def test_plain_explicit_ariadne_packet_remains_reviewable(self):
        item = claim()
        item.update({
            "coordinate_edition": ARIADNE_EDITION,
            "coordinate_registry_digest": ARIADNE_SOURCE_SHA256,
            "coordinate": "H12.S12.N12",
        })
        self.assertTrue(validate_grounding(resolve_to_earth(item))["valid"])

    def test_nested_context_subclass_held_without_executing_get(self):
        packet = resolve_to_earth(claim())
        packet["continuum_context"] = ExplodingContext(packet["continuum_context"])
        self.assert_hold(packet)

    def test_derived_coordinate_subclass_held_without_executing_eq(self):
        packet = resolve_to_earth(claim())
        packet["original_coordinate"] = ExplodingString("H01.S02.N03")
        self.assert_hold(packet)

    def test_caller_metadata_behavioral_subclass_held(self):
        packet = resolve_to_earth(claim())
        packet["caller_metadata"] = {"payload": ExplodingString("public")}
        self.assert_hold(packet)

    def test_plain_caller_metadata_remains_inert_and_allowed(self):
        packet = resolve_to_earth(claim())
        packet["caller_metadata"] = {"origin": "public-synthetic", "tags": ["test"]}
        self.assertTrue(validate_grounding(packet)["valid"])


if __name__ == "__main__":
    unittest.main()
