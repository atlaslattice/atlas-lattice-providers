"""Synthetic reference controls; no synthetic commit is a publication claim."""
import asyncio
import hashlib
import json
import unittest

from core.civilization_kernel_reference import (
    ASSESSMENT_SHA256, CANDIDATE_NOTICE, HOUSES, PROTOCOL_SHA256, RAW_SHA256, RELEASE_ID,
    REQUIRED_FILES, SOURCE_ROOT, ReferenceError, prepare_kernel_reference, read_reference,
)


def fixture():
    files = {path: "b" * 64 for path in REQUIRED_FILES}
    files[SOURCE_ROOT + "/benchmarks/SUPPORTING_KERNEL_PROTOCOL.json"] = PROTOCOL_SHA256
    files[SOURCE_ROOT + "/outputs/SUPPORTING_KERNEL_RAW.jsonl"] = RAW_SHA256
    files[SOURCE_ROOT + "/outputs/SUPPORTING_KERNEL_ASSESSMENT.json"] = ASSESSMENT_SHA256
    return {
        "schema": "atlas.civilization.kernel-source-reference.v1",
        "release_id": RELEASE_ID, "status": "SUPPORTING_CAPABILITY_SOURCE_REFERENCE",
        "source_repository": "atlaslattice/Atlas-Intelligence", "source_commit": "a" * 40,
        "source_root": SOURCE_ROOT, "source_files": files, "kernel_houses": list(HOUSES),
        "dispatch": {h: "REFERENCE_QUERY" if h == "H02" else "INDEXED_QUERY" for h in HOUSES},
        "benchmark": {"scope": "LOCAL_SYNTHETIC_SUPPORTING_KERNEL_COMPARISON",
            "protocol_sha256": PROTOCOL_SHA256, "raw_sha256": RAW_SHA256,
            "assessment_sha256": ASSESSMENT_SHA256, "registered_kernel_hypotheses": 12,
            "local_gain_candidates": 11, "observed_regressions": ["H02"],
            "original_1728_primary_metric_credit": 0, "production_gains_verified": 0,
            "whole_system_gain_claimed": False},
        "authority": "none", "canon": False, "deployment": False,
        "source_bodies_included": False, "specialized_node_contracts_complete": 0,
        "ordinal_identity_implied": False,
    }


def encoded(record=None):
    raw = json.dumps(fixture() if record is None else record, sort_keys=True).encode()
    return raw, hashlib.sha256(raw).hexdigest()


class KernelSourceReferenceTests(unittest.TestCase):
    def test_optional_providers_notice_accepts_legacy_and_exact_annotation_only(self):
        legacy_bytes, legacy_pin = encoded()
        legacy = prepare_kernel_reference(legacy_bytes, legacy_pin, house_id="H02", room_id="work-test")
        self.assertNotIn("candidate_notice", read_reference(legacy_bytes, legacy_pin))
        record = fixture(); record["candidate_notice"] = CANDIDATE_NOTICE
        annotated_bytes, annotated_pin = encoded(record)
        self.assertEqual(read_reference(annotated_bytes, annotated_pin)["candidate_notice"], CANDIDATE_NOTICE)
        annotated = prepare_kernel_reference(annotated_bytes, annotated_pin, house_id="H02", room_id="work-test")
        legacy["source"].pop("reference_sha256"); annotated["source"].pop("reference_sha256")
        self.assertEqual(legacy, annotated)
        for notice in ("edited notice", None, True, {"text": CANDIDATE_NOTICE}):
            record = fixture(); record["candidate_notice"] = notice
            with self.subTest(notice=notice), self.assertRaisesRegex(ReferenceError, "candidate_notice_mismatch"):
                read_reference(*encoded(record))
        record = fixture(); record["candidate_notice"] = CANDIDATE_NOTICE; record["unlisted_host_metadata"] = "value"
        with self.assertRaisesRegex(ReferenceError, "reference_fields_mismatch"):
            read_reference(*encoded(record))

    def test_known_candidate_retains_scope_source_and_h02_fallback(self):
        raw, pin = encoded()
        packet = prepare_kernel_reference(raw, pin, house_id="H02", room_id="work-test")
        self.assertEqual(packet["release_id"], "ATLAS-CIVILIZATION-R01-20261123-1")
        self.assertEqual(packet["dispatch_candidate"], "REFERENCE_QUERY")
        self.assertEqual(packet["source"]["commit"], "a" * 40)
        self.assertEqual(packet["source"]["reference_sha256"], pin)
        self.assertEqual(packet["benchmark"]["local_gain_candidates"], 11)
        self.assertEqual(packet["benchmark"]["observed_regressions"], ["H02"])
        self.assertEqual(packet["specialized_node_contracts_complete"], 0)
        self.assertEqual(packet["status"], "REFERENCE_BYTES_VERIFIED_SOURCE_COMMIT_UNCHECKED")
        for field in ("source_files_retrieved", "host_permissions_verified", "current_return_fence_verified",
                      "execution_authorized", "work_posted", "source_bodies_included", "canon", "deployment"):
            self.assertIs(packet[field], False, field)
        self.assertIn("current_return_fence", packet["required_next_checks"])

    def test_exact_byte_pin_is_required_on_every_call(self):
        raw, pin = encoded()
        for body, selected in [(raw + b" ", pin), (raw, None), (raw, "A" * 64), (bytearray(raw), pin)]:
            with self.subTest(selected=selected), self.assertRaises(ReferenceError):
                read_reference(body, selected)

    def test_duplicate_json_keys_rejected_with_matching_digest(self):
        raw, _ = encoded()
        raw = raw[:-1] + b', "authority": "none"}'
        with self.assertRaisesRegex(ReferenceError, "duplicate_reference_key"):
            read_reference(raw, hashlib.sha256(raw).hexdigest())

    def test_malformed_nonfinite_and_oversized_references_rejected(self):
        for raw in (b"{broken}", b"\xff", b"NaN", b"1e400", b"[" * 40 + b"]" * 40, b" " * 131073):
            with self.subTest(raw=raw[:15]), self.assertRaises(ReferenceError):
                read_reference(raw, hashlib.sha256(raw).hexdigest())

    def test_reference_cannot_expand_authority_completion_or_coordinates(self):
        for field, value in (("canon", True), ("deployment", True), ("authority", "owner"),
                             ("source_bodies_included", True), ("ordinal_identity_implied", True),
                             ("specialized_node_contracts_complete", 144),
                             ("specialized_node_contracts_complete", False)):
            record = fixture(); record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ReferenceError):
                read_reference(*encoded(record))

    def test_evidence_cannot_be_upgraded_to_whole_system_or_node_credit(self):
        for field, value in (("original_1728_primary_metric_credit", 1), ("production_gains_verified", True),
                             ("registered_kernel_hypotheses", 1728), ("whole_system_gain_claimed", True),
                             ("observed_regressions", []), ("local_gain_candidates", 12)):
            record = fixture(); record["benchmark"][field] = value
            with self.subTest(field=field), self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_exact_source_repository_root_release_and_commit_required(self):
        for field, value in (("source_commit", "main"), ("source_commit", "a" * 39),
                             ("source_repository", "atlaslattice/fork"), ("source_root", "programs/excellence1728"),
                             ("release_id", "future-release")):
            record = fixture(); record[field] = value
            with self.subTest(field=field), self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_source_fingerprints_cannot_be_missing_unsafe_or_mismatched(self):
        record = fixture(); del record["source_files"][SOURCE_ROOT + "/kernels/H02.mjs"]
        with self.assertRaises(ReferenceError): read_reference(*encoded(record))
        for path in ("../private", "/absolute", SOURCE_ROOT + "/../secret", SOURCE_ROOT + "//index.mjs",
                     SOURCE_ROOT + "/./index.mjs", "programs/excellence1728/README.md"):
            record = fixture(); record["source_files"][path] = "b" * 64
            with self.subTest(path=path), self.assertRaises(ReferenceError): read_reference(*encoded(record))
        record = fixture(); record["source_files"][SOURCE_ROOT + "/outputs/SUPPORTING_KERNEL_RAW.jsonl"] = "d" * 64
        with self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_release_dispatch_cannot_select_the_regressed_candidate(self):
        record = fixture(); record["dispatch"]["H02"] = "INDEXED_QUERY"
        with self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_no_ordinal_mapping_from_ex1728_or_original_hsn(self):
        for house in ("H01.S01.N01", "EX.W01.C01.P01", "H00", "H13", 1, None):
            with self.subTest(house=house), self.assertRaises(ReferenceError):
                prepare_kernel_reference(*encoded(), house_id=house, room_id="work-test")
        packet = prepare_kernel_reference(*encoded(), house_id="H01", room_id="work-test")
        self.assertEqual(packet["implementation_scope"], "SUPPORTING_CAPABILITY")
        self.assertIs(packet["ordinal_identity_implied"], False)
        self.assertNotIn("node_id", packet)
        self.assertNotIn("task_id", packet)

    def test_current_work_room_and_mode_are_rechecked(self):
        raw, pin = encoded()
        prepare_kernel_reference(raw, pin, house_id="H01", room_id="work-first")
        for mode, room in (("PLAY", "work-first"), ("WORK", "bad room"), ("WORK", "ab"), (None, "work-first")):
            with self.subTest(mode=mode, room=room), self.assertRaises(ReferenceError):
                prepare_kernel_reference(raw, pin, house_id="H01", room_id=room, mode=mode)
        self.assertEqual(prepare_kernel_reference(raw, pin, house_id="H01", room_id="work-next")["room_id"], "work-next")

    def test_unknown_fields_are_not_smuggled_through(self):
        record = fixture(); record["private_source_body"] = "synthetic forbidden payload"
        with self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_caller_edits_do_not_change_later_source_scope(self):
        raw, pin = encoded()
        first = prepare_kernel_reference(raw, pin, house_id="H03", room_id="work-test")
        first["source"]["files"].clear(); first["benchmark"]["local_gain_candidates"] = 1728
        next_packet = prepare_kernel_reference(raw, pin, house_id="H03", room_id="work-test")
        self.assertTrue(next_packet["source"]["files"])
        self.assertEqual(next_packet["benchmark"]["local_gain_candidates"], 11)

    def test_optional_decomposer_prepares_metadata_and_preserves_legacy(self):
        from core.hierarchical_goal_decomposer import HierarchicalGoalDecompositionEngine
        engine = HierarchicalGoalDecompositionEngine()
        raw, pin = encoded()
        options = dict(civilization_kernel_reference_bytes=raw,
                       expected_civilization_kernel_reference_sha256=pin,
                       kernel_house_id="H02", room_id="work-test")
        result = asyncio.run(engine.decompose("Synthetic local candidate", **options))
        self.assertEqual(result["status"], "SUPPORTING_KERNEL_REFERENCE_PREPARED")
        self.assertEqual(result["goal_tree"]["source_kernel"]["dispatch_candidate"], "REFERENCE_QUERY")
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["goal_tree"]["source_kernel"]["current_return_fence_verified"])
        legacy = asyncio.run(engine.decompose("Existing path"))
        self.assertEqual(legacy["goal_tree"]["subgoals"], ["sub1", "sub2 with checkpoints"])
        with self.assertRaises(ReferenceError):
            asyncio.run(engine.decompose("Wrong mode", **options, mode="PLAY"))
        with self.assertRaisesRegex(ReferenceError, "ambiguous_source_reference"):
            asyncio.run(engine.decompose("Ambiguous reference", **options, excellence_reference_bytes=b"{}"))


if __name__ == "__main__":
    unittest.main()
