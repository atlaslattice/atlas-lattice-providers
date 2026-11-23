"""Source-only collision regression; never a migration or authorization test."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from core.coordinate_lineage_gate import review_crosswalk, LEGACY, ARIADNE


def record(edition, coord, *, namespace="synthetic", registry="a"*64, revision="b"*64):
    return dict(namespace=namespace, edition=edition, coordinate=coord,
                registry_sha256=registry, record_sha256=revision)


class LineageGateTests(unittest.TestCase):
    def test_false_join_on_offset_is_review_only(self):
        old=record(LEGACY,"H00.S00.N00")
        new=record(ARIADNE,"H01.S01.N01",revision="c"*64)
        self.assertNotEqual(tuple(old.values()),tuple(new.values()))
        result=review_crosswalk(old,new)
        self.assertEqual(result["status"],"ARITHMETIC_ALIAS_REVIEW_REQUIRED")
        self.assertFalse(result["same_as"])
        self.assertFalse(result["migration_authorized"])

    def test_same_label_but_two_editions_is_not_same_as(self):
        result=review_crosswalk(record(LEGACY,"H01.S01.N01"),
                                record(ARIADNE,"H01.S01.N01"))
        self.assertEqual(result["status"],"CROSS_EDITION_OVERLAP_REVIEW_REQUIRED")
        self.assertFalse(result["same_as"])

    def test_same_label_different_revision_still_distinct(self):
        result=review_crosswalk(record(ARIADNE,"H01.S01.N01"),
                                record(ARIADNE,"H01.S01.N01",revision="c"*64))
        self.assertEqual(result["status"],"COORDINATE_COLLISION_REVIEW_REQUIRED")

    def test_same_typed_tuple_is_not_scientific_equivalence(self):
        x=record(ARIADNE,"H12.S12.N12")
        result=review_crosswalk(x,x)
        self.assertEqual(result["status"],"SAME_TYPED_REFERENCE_NOT_SEMANTIC_EQUIVALENCE")
        self.assertFalse(result["same_as"])

    def test_alternate_axes_not_alias(self):
        self.assertEqual(review_crosswalk(record(LEGACY,"H00.S00.N01"),
                                          record(ARIADNE,"H01.S01.N01"))["status"],"DISTINCT_LINEAGES")

    def test_historical_zero_only_in_legacy(self):
        self.assertEqual(review_crosswalk(record(ARIADNE,"H00.S01.N01"),
                                          record(ARIADNE,"H01.S01.N01"))["status"],"HOLD")

    def test_twelve_only_in_one_based(self):
        self.assertEqual(review_crosswalk(record(LEGACY,"H12.S01.N01"),
                                          record(ARIADNE,"H12.S01.N01"))["status"],"HOLD")

    def test_bad_hash_and_untrusted_fields_hold(self):
        for mutation in ({"registry_sha256":"bad"},{"record_sha256":42},
                         {"public":True},{"private_body":"fictional canary"},
                         {"coordinate_edition":"auto"}):
            left=record(LEGACY,"H00.S00.N00");left.update(mutation)
            with self.subTest(mutation=mutation):
                out=review_crosswalk(left,record(ARIADNE,"H01.S01.N01"))
                self.assertEqual(out["status"],"HOLD")
                self.assertNotIn("fictional canary",repr(out))

    def test_wrong_namespace_and_digest_do_not_collapse(self):
        a=record(ARIADNE,"H01.S01.N01")
        b=record(ARIADNE,"H01.S01.N01",namespace="other",registry="c"*64)
        result=review_crosswalk(a,b)
        self.assertEqual(result["status"],"COORDINATE_COLLISION_REVIEW_REQUIRED")
        self.assertFalse(result["same_as"])

    def test_forged_historical_edition_held(self):
        self.assertEqual(review_crosswalk(record("Ariadne-v0.6", "H00.S00.N00"),
                                          record(ARIADNE,"H01.S01.N01"))["status"],"HOLD")

    def test_no_input_mutation(self):
        a=record(LEGACY,"H00.S00.N00");b=record(ARIADNE,"H01.S01.N01")
        old=copy.deepcopy((a,b));review_crosswalk(a,b)
        self.assertEqual((a,b),old)

    def test_1728_grid_cardinality_and_1331_raw_overlap(self):
        old={f"H{h:02}.S{s:02}.N{n:02}" for h in range(12) for s in range(12) for n in range(12)}
        new={f"H{h:02}.S{s:02}.N{n:02}" for h in range(1,13) for s in range(1,13) for n in range(1,13)}
        self.assertEqual((len(old),len(new),len(old & new),len(old-new),len(new-old)),
                         (1728,1728,1331,397,397))

    def test_non_dict_and_non_ascii_hold(self):
        other=record(ARIADNE,"H01.S01.N01")
        for value in (None, [], "H00.S00.N00", 3, dict(other, namespace="é")):
            with self.subTest(value=value):
                self.assertEqual(review_crosswalk(value,other)["status"],"HOLD")

    def test_no_authority_from_any_positive_candidate(self):
        for a,b in ((record(LEGACY,"H00.S00.N00"),record(ARIADNE,"H01.S01.N01")),
                    (record(ARIADNE,"H01.S01.N01"),record(ARIADNE,"H01.S01.N01"))):
            result=review_crosswalk(a,b)
            self.assertFalse(result["publisher_attested"])
            self.assertFalse(result["rights_attested"])
            self.assertFalse(result["canon"])
            self.assertFalse(result["deployed"])

if __name__=="__main__": unittest.main()
