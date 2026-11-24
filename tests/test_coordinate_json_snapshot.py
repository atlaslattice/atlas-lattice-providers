"""Adversarial caller-object and JSON snapshot tests; no hosted permissions."""
import importlib.util
import math
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "core" / "coordinate_resolver.py"
spec = importlib.util.spec_from_file_location("coordinate_resolver_snap", path)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def claim():
    return {
        "claim_id": "synthetic-frozen", "source_ref": "synthetic:public:1",
        "source_continuum_id": "continuum-A", "coordinate": "H01.S02.N03",
        "authority": "none", "canon": False, "deployment": False,
    }


class SideEffectStr(str):
    def __str__(self):
        raise AssertionError("untrusted __str__ must not execute")

    def __deepcopy__(self, _memo):
        raise AssertionError("untrusted __deepcopy__ must not execute")


class SideEffectObject:
    def __str__(self):
        raise AssertionError("must not coerce custom object")

    def __deepcopy__(self, _memo):
        raise AssertionError("must not deepcopy custom object")


class CoordinateSnapshotTests(unittest.TestCase):
    def test_safe_claim_is_frozen_and_legacy_wire_shape_preserved(self):
        source = claim()
        source["nested"] = {"epoch": 0, "notes": ["synthetic"]}
        packet = resolver.resolve_to_earth(source)
        self.assertEqual(packet["route"], "candidate_review")
        self.assertEqual(packet["schema"], "coordinate-candidate/v0.1")
        self.assertTrue(resolver.validate_grounding(packet)["valid"])
        source["nested"]["epoch"] = 9
        self.assertEqual(packet["original_claim"]["nested"]["epoch"], 0)
        self.assertTrue(resolver.validate_grounding(packet)["valid"])

    def test_ariadne_coordinate_edition_still_requires_registry_pin(self):
        source = claim()
        source.update({
            "coordinate_edition": resolver.ARIADNE_EDITION,
            "coordinate_registry_digest": resolver.ARIADNE_SOURCE_SHA256,
            "coordinate": "H12.S12.N12",
        })
        packet = resolver.resolve_to_earth(source)
        self.assertEqual(packet["schema"], "coordinate-candidate/v0.2")
        self.assertTrue(resolver.validate_grounding(packet)["valid"])

    def test_unsafe_objects_and_ambiguous_json_are_constant_shape_holds(self):
        sentinel = "SYNTHETIC_UNTRUSTED_BODY_DO_NOT_ECHO"
        samples = [
            SideEffectObject(), SideEffectStr(sentinel),
            {"nested": SideEffectObject()},
            {"nested": SideEffectStr(sentinel)},
            {"nested": float("nan")}, {"nested": float("inf")},
            {"nested": (1, 2)}, {"nested": {1, 2}},
            {"nested": {False: "not a JSON string key"}},
            {"nested": sentinel * 80000}, {"nested": "\\ud800".encode().decode("unicode_escape")},
        ]
        expected = None
        for sample in samples:
            with self.subTest(sample_type=type(sample).__name__):
                source = claim()
                source["other"] = sample
                packet = resolver.resolve_to_earth(source)
                self.assertEqual(packet["status"], "HELD_INVALID_INPUT")
                self.assertEqual(packet["route"], "quarantine")
                self.assertIsNone(packet["original_claim"])
                self.assertIsNone(packet["claim_fingerprint_sha256"])
                self.assertNotIn(sentinel, repr(packet))
                self.assertFalse(resolver.validate_grounding(packet)["valid"])
                if expected is None:
                    expected = packet
                self.assertEqual(packet, expected)

    def test_declared_private_mode_holds_without_snapshot_echo(self):
        source = claim()
        source.update({"mode": "PALACE", "private_body": SideEffectObject()})
        packet = resolver.resolve_to_earth(source)
        self.assertEqual(packet["status"], "HELD_PRIVATE_MODE")
        self.assertIsNone(packet["original_claim"])

    def test_invalid_metadata_is_not_copied_into_packet(self):
        packet = resolver.wrap_as_coordinate_packet(claim(), {"caller": SideEffectObject()})
        self.assertEqual(packet["status"], "HELD_INVALID_INPUT")
        self.assertNotIn("caller_metadata", packet)

    def test_tampered_packet_with_unsafe_original_is_not_valid(self):
        packet = resolver.resolve_to_earth(claim())
        packet["original_claim"]["other"] = SideEffectObject()
        verdict = resolver.validate_grounding(packet)
        self.assertFalse(verdict["valid"])
        # Whole-packet admission now rejects unsafe values before field diagnostics.
        self.assertEqual(verdict, {"valid": False,
                                   "reasons": ["not_a_plain_json_packet"]})

    def test_non_dict_string_still_quarantined_compatibly(self):
        packet = resolver.resolve_to_earth("unsafe")
        self.assertEqual(packet["route"], "quarantine")
        self.assertEqual(packet["original_claim"], "unsafe")

    def test_private_escalation_never_echoes_opaque_payload(self):
        sentinel = "SYNTHETIC_PALACE_BODY_NO_EXPORT"
        result = resolver.escalate_to_human_root("disclose " + sentinel,
                    {"mode": "PALACE", "body": sentinel, "secret": SideEffectObject()})
        self.assertEqual(result["status"], "HELD_PRIVATE_MODE")
        self.assertIsNone(result["payload"])
        self.assertIsNone(result["payload_sha256"])
        self.assertNotIn(sentinel, repr(result))

    def test_unsafe_escalation_holds_and_safe_remains_inert(self):
        held = resolver.escalate_to_human_root("review", {"x": SideEffectObject()})
        self.assertEqual(held["status"], "HELD_INVALID_INPUT")
        self.assertIsNone(held["payload_sha256"])
        safe = resolver.escalate_to_human_root("review", {"id": "synthetic:1"})
        self.assertEqual(safe["status"], "NOT_SENT")
        self.assertEqual(safe["payload"], {"id": "synthetic:1"})
        self.assertEqual(len(safe["payload_sha256"]), 64)
        self.assertEqual(safe["authority"], "none")


if __name__ == "__main__":
    unittest.main()
