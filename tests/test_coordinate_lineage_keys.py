"""Synthetic Python key-boundary regression, not a hosted JSON exploit."""
import copy
import unittest

from core.coordinate_lineage_gate import ARIADNE, review_crosswalk


class HostileKey(str):
    __hash__ = str.__hash__

    def __eq__(self, _other):
        raise AssertionError("caller key equality must not execute")


def record():
    return {"namespace": "synthetic.keys", "edition": ARIADNE,
            "coordinate": "H01.S01.N01", "registry_sha256": "a" * 64,
            "record_sha256": "b" * 64}


def hostile_record():
    return {HostileKey(key) if key == "namespace" else key: value
            for key, value in record().items()}


class LineageKeyTests(unittest.TestCase):
    def assert_held_without_authority(self, result):
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "INVALID_OR_UNPINNED_TYPED_IDENTITY")
        self.assertFalse(result["same_as"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["source_custody"])

    def test_original_subclass_key_held_before_caller_equality(self):
        self.assert_held_without_authority(review_crosswalk(hostile_record(), record()))

    def test_target_subclass_key_held_before_caller_equality(self):
        self.assert_held_without_authority(review_crosswalk(record(), hostile_record()))

    def test_plain_key_reference_remains_reviewable_without_mutation(self):
        left, right = record(), record()
        original = copy.deepcopy((left, right))
        result = review_crosswalk(left, right)
        self.assertEqual(result["status"], "SAME_TYPED_REFERENCE_NOT_SEMANTIC_EQUIVALENCE")
        self.assertFalse(result["same_as"])
        self.assertFalse(result["migration_authorized"])
        self.assertEqual((left, right), original)

    def test_same_namespace_different_digest_still_requires_collision_review(self):
        left, right = record(), record()
        right["registry_sha256"] = "c" * 64
        result = review_crosswalk(left, right)
        self.assertEqual(result["status"], "COORDINATE_COLLISION_REVIEW_REQUIRED")
        self.assertFalse(result["same_as"])
        self.assertFalse(result["migration_authorized"])


if __name__ == "__main__":
    unittest.main()
