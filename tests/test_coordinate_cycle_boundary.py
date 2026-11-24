"""Finite public-synthetic cycle rejection and acyclic sharing controls."""
import unittest

from core.coordinate_resolver import resolve_to_earth, validate_grounding, wrap_as_coordinate_packet


def claim():
    return {
        "claim_id": "synthetic-cycle-boundary",
        "source_ref": "synthetic:public:cycle",
        "source_continuum_id": "synthetic-A",
        "coordinate": "H01.S02.N03",
        "authority": "none", "canon": False, "deployment": False,
    }


class CycleBoundaryTests(unittest.TestCase):
    def test_cyclic_source_is_held_without_echo_or_input_mutation(self):
        source = claim()
        source["cycle"] = source
        packet = resolve_to_earth(source)
        self.assertEqual(packet["status"], "HELD_INVALID_INPUT")
        self.assertIsNone(packet["original_claim"])
        self.assertIsNone(packet["claim_fingerprint_sha256"])
        self.assertIs(source["cycle"], source)

    def test_received_cyclic_metadata_is_held_without_recursion_escape(self):
        packet = resolve_to_earth(claim())
        metadata = {"mode": "WORK"}
        metadata["cycle"] = metadata
        packet["caller_metadata"] = metadata
        self.assertEqual(validate_grounding(packet), {
            "valid": False, "reasons": ["not_a_plain_json_packet"]})
        self.assertIs(metadata["cycle"], metadata)

    def test_shared_acyclic_metadata_is_copied_and_remains_reviewable(self):
        shared = {"value": [1, 2, 3]}
        packet = wrap_as_coordinate_packet(claim(), {
            "mode": "WORK", "left": shared, "right": shared})
        self.assertTrue(validate_grounding(packet)["valid"])
        shared["value"].append(4)
        self.assertEqual(packet["caller_metadata"]["left"]["value"], [1, 2, 3])
        self.assertEqual(packet["caller_metadata"]["right"]["value"], [1, 2, 3])
        self.assertEqual(packet["authority"], "none")
        self.assertIs(packet["canon"], False)
        self.assertIs(packet["deployment"], False)


if __name__ == "__main__":
    unittest.main()
