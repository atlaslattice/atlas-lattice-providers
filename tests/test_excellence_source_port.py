"""Source reference integration tests; synthetic controls plus the pinned publication."""
import asyncio
import hashlib
import json
import unittest
from pathlib import Path
from core.excellence_reference import (read_reference, describe_reference, prepare_task_reference,
    ReferenceError, PROGRAM_ID, ARIADNE_SHA256, CANON_REFERENCE)

def fixture():
    """Synthetic source-reference fixture; no live publication is claimed."""
    return {
        "schema": "atlas.excellence.source-reference.v1", "status": "PLANNED", "canon_status": "NOT CANON", "review_status": "CANDIDATE",
        "program_id": PROGRAM_ID, "revision": 1, "engineering_namespace": "EX1728",
        "source_repository": "atlaslattice/Atlas-Intelligence", "source_commit": "a" * 40,
        "source_files": {"programs/excellence1728/catalog/capabilities.json": "b" * 64}, "plan_sha256": "c" * 64,
        "counts": {"workstreams": 12, "capabilities": 144, "phases": 12, "steps": 1728},
        "coverage": {"ariadne_source_sha256": ARIADNE_SHA256, "houses": 12, "spheres": 144, "nodes": 1728,
                     "ordinal_identity_implied": False, "semantic_crosswalk_status": "SOURCE_REVIEW_REQUIRED"},
        "canon_reference": {"decision_id": CANON_REFERENCE, "new_canon_changes": False},
        "completion": {"implemented": 0, "verified": 0, "integrated": 0, "genuine_macroturns": 0},
        "authority": "none", "deployment": False, "runtime_status": "SOURCE_PORT_ONLY",
    }


def encoded(record=None):
    raw = json.dumps(fixture() if record is None else record, sort_keys=True).encode()
    return raw, hashlib.sha256(raw).hexdigest()


class SourceReferenceTests(unittest.TestCase):
    def test_bundled_reference_is_the_selected_source_publication(self):
        raw = (Path(__file__).resolve().parents[1] / 'config/excellence1728/source_reference.json').read_bytes()
        selected = read_reference(raw, 'e8471ea75fa6fc9abfc48b849ad60399d5378ff2d181891e9e811141e1f6066c')
        self.assertEqual(selected['source_commit'], 'dcb3de996e798ab5d96c77e91690bbc06a56f966')
        self.assertEqual(selected['plan_sha256'], '47084b895a6317db16275a92c3878a340d31af15fb9ab479db7101953c18e49c')
        self.assertEqual(len(selected['source_files']), 31)
        self.assertEqual(sum(selected['completion'].values()), 0)

    def test_describe_selected_reference_without_execution_claim(self):
        d = describe_reference(*encoded())
        self.assertEqual(d["counts"]["steps"], 1728)
        self.assertTrue(d["canonical_runtime_required"])
        self.assertEqual(sum(d["completion"].values()), 0)
        self.assertFalse(d["host_permissions_verified"])

    def test_exact_byte_pin_required(self):
        raw, pin = encoded()
        with self.assertRaises(ReferenceError): read_reference(raw + b" ", pin)
        with self.assertRaises(ReferenceError): read_reference(raw, None)

    def test_duplicate_keys_fail_even_with_recomputed_digest(self):
        raw, _ = encoded()
        raw = raw[:-1] + b', "deployment": false}'
        with self.assertRaisesRegex(ReferenceError, "duplicate_reference_key"):
            read_reference(raw, hashlib.sha256(raw).hexdigest())

    def test_reference_cannot_self_promote(self):
        for field, value in [("status", "VERIFIED"), ("authority", "owner"), ("deployment", True), ("canon_status", "CANON")]:
            record = fixture(); record[field] = value
            with self.subTest(field=field), self.assertRaises(ReferenceError): read_reference(*encoded(record))
        record = fixture(); record["completion"]["verified"] = 1
        with self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_immutable_source_ref_and_safe_paths(self):
        for commit in ["main", "a"*39, "https://example.invalid"]:
            record=fixture();record["source_commit"]=commit
            with self.subTest(commit=commit), self.assertRaises(ReferenceError): read_reference(*encoded(record))
        for path in ["../secret", "/private/file", "path//file", "path/./file", "path\\file"]:
            record=fixture();record["source_files"]={path:"b"*64}
            with self.subTest(path=path), self.assertRaises(ReferenceError): read_reference(*encoded(record))

    def test_source_and_engineering_namespaces_not_collapsed(self):
        raw, pin = encoded()
        for task in ["H01.S01.N01", "H00.S00.N00", "EX.W00.C01.P01", "EX.W12.C12.P13"]:
            with self.subTest(task=task), self.assertRaises(ReferenceError):
                prepare_task_reference(raw,pin,task_id=task,room_id="work-test")
        p=prepare_task_reference(raw,pin,task_id="EX.W12.C12.P12",room_id="work-test")
        self.assertFalse(p["ordinal_identity_implied"])
        self.assertFalse(p["execution_authorized"])

    def test_mutable_return_cannot_expand_next_reference(self):
        raw,pin=encoded();r=read_reference(raw,pin);r["completion"]["verified"]=1728
        self.assertEqual(read_reference(raw,pin)["completion"]["verified"],0)

    def test_protected_mode_and_ambiguous_room_fail(self):
        raw,pin=encoded()
        for kwargs in [{"mode":"PLAY","room_id":"work-test"},{"mode":"WORK","room_id":"bad room"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ReferenceError):
                prepare_task_reference(raw,pin,task_id="EX.W01.C01.P01",**kwargs)

    def test_existing_goal_decomposer_preserves_legacy_and_source_paths(self):
        from core.hierarchical_goal_decomposer import HierarchicalGoalDecompositionEngine
        raw,pin=encoded(); engine=HierarchicalGoalDecompositionEngine()
        out=asyncio.run(engine.decompose('Review source pin',excellence_reference_bytes=raw,expected_reference_sha256=pin,task_id='EX.W01.C01.P01',room_id='work-test'))
        self.assertEqual(out['status'],'SOURCE_PROGRAM_REFERENCE_PREPARED')
        self.assertIs(out['execution_authorized'],False)
        legacy=asyncio.run(engine.decompose('Existing path'))
        self.assertEqual(legacy['goal_tree']['root'],'Existing path')
        with self.assertRaises(ReferenceError):
            asyncio.run(engine.decompose('Invalid mode',excellence_reference_bytes=raw,expected_reference_sha256=pin,task_id='EX.W01.C01.P01',room_id='work-test',mode='PLAY'))


if __name__=='__main__': unittest.main()
