"""Synthetic non-Work metadata review boundary; no private source content used."""
import importlib.util
import pathlib
import unittest

module_path = pathlib.Path(__file__).resolve().parents[1] / "core" / "coordinate_resolver.py"
spec = importlib.util.spec_from_file_location("coordinate_resolver", module_path)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def claim():
    return {
        "claim_id": "fixture:synthetic-only",
        "source_ref": "test:synthetic",
        "source_continuum_id": "synthetic-A",
        "target_continuum_id": "synthetic-B",
        "bridge_type": "claim",
        "coordinate": "H01.S02.N03",
        "authority": "none",
        "canon": False,
        "deployment": False,
    }


class MetadataModeBoundaryTests(unittest.TestCase):
    def test_existing_wrapper_denies_protected_modes_without_echo(self):
        marker = "SYNTHETIC_DO_NOT_ECHO"
        for protected in ({"mode": "IMAGINE", "marker": marker},
                          {"mode": "QUIET", "marker": marker},
                          {"no_harvest": True, "marker": marker}):
            with self.subTest(protected=list(protected)):
                result = resolver.wrap_as_coordinate_packet(claim(), protected)
                self.assertEqual(result["status"], "HELD_PRIVATE_MODE")
                self.assertNotIn(marker, repr(result))

    def test_validator_cannot_accept_added_nonwork_caller_metadata(self):
        # A packet received from outside wrap_as_coordinate_packet must not
        # bypass the wrapper's pre-existing mode exclusion by appending metadata.
        for private_mode in ("IMAGINE", "QUIET", "SOCIAL", None, 17):
            with self.subTest(mode=repr(private_mode)):
                received = resolver.resolve_to_earth(claim())
                received["caller_metadata"] = {"mode": private_mode}
                review = resolver.validate_grounding(received)
                self.assertFalse(review["valid"])
                self.assertIn("caller_metadata_private_mode_no_import", review["reasons"])

    def test_validator_cannot_accept_postwrap_no_harvest_mutation(self):
        for excluded in (True, None, "false", 0):
            with self.subTest(flag=repr(excluded)):
                packet = resolver.wrap_as_coordinate_packet(claim(), {"mode": "WORK", "no_harvest": False})
                self.assertTrue(resolver.validate_grounding(packet)["valid"])
                packet["caller_metadata"]["no_harvest"] = excluded
                review = resolver.validate_grounding(packet)
                self.assertFalse(review["valid"])
                self.assertIn("caller_metadata_private_mode_no_import", review["reasons"])

    def test_allowed_work_and_public_metadata_remain_compatible(self):
        for metadata in ({"mode": "WORK"}, {"mode": "PUBLIC", "no_harvest": False},
                         {"ticket": "synthetic"}):
            with self.subTest(metadata=metadata):
                packet = resolver.wrap_as_coordinate_packet(claim(), metadata)
                review = resolver.validate_grounding(packet)
                self.assertTrue(review["valid"], review["reasons"])


if __name__ == "__main__":
    unittest.main()
