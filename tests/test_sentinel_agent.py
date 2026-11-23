"""Offline candidate-only Sentinel checks; no network, real agents, or host rights."""
from __future__ import annotations
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.sentinel_agent import SCHEMA, inspect, append_receipt

PACKET_SCHEMA = "atlas.transparent-packet96/candidate-v0.1"


def candidate():
    return {"schema_version": PACKET_SCHEMA, "packet_id": "fixture-001",
            "sender": "fictional-a", "recipient": "fictional-b", "coordinate": "H00.S00.N00",
            "status": "CANDIDATE", "canon": False, "deployment": False, "authority": "none",
            "identity_scope": "DISTINCT_PARTICIPANTS", "host_attestation": "NONE",
            "semantic_review": "UNREVIEWED", "same_as": False, "mode": "WORK",
            "dissent": [{"actor": "fictional-b", "edge": "CHALLENGES", "text": "unverified source"}],
            "payload": {"action": "separate participant messages"},
            "provenance": {"source_ref": "synthetic://sentinel", "source_cut": "LOCAL"},
            "receipt": {"assurance": "LOCAL_UNATTESTED", "delivered": False}}


class SentinelTests(unittest.TestCase):
    def test_candidate_review_is_not_authority(self):
        r = inspect(candidate())
        self.assertEqual(r.disposition, "REVIEWABLE_LOCAL_ONLY")
        self.assertFalse(r.execution_allowed or r.canon_adopted or r.deployment_performed)
        self.assertEqual(r.host_attestation, "NOT_ATTESTED")
        self.assertEqual(r.receipt()["schema"], SCHEMA)

    def test_preserves_dissent(self):
        p = candidate(); r = inspect(p)
        self.assertEqual(list(r.dissent), p["dissent"])
        self.assertEqual(r.retained_work_packet["dissent"], p["dissent"])

    def test_no_fusion_phrases(self):
        for phrase in ["merged mind", "identity fusion", "shared consciousness",
                       "collapse all agents into one"]:
            with self.subTest(phrase=phrase):
                p = candidate(); p["payload"] = {"instruction": phrase}
                r = inspect(p)
                self.assertEqual(r.disposition, "QUARANTINE_BLOCKED")
                self.assertFalse(r.execution_allowed)
                self.assertEqual(r.dissent[0]["edge"], "CHALLENGES")

    def test_deletion_is_quarantined(self):
        for action in ["delete", "purge", "destroy", "erase", "overwrite", "truncate", "wipe"]:
            with self.subTest(action=action):
                p = candidate(); p["requested_action"] = action
                r = inspect(p)
                self.assertEqual(r.disposition, "QUARANTINE_DESTRUCTIVE")
                self.assertTrue(r.human_root_required)
                self.assertFalse(r.execution_allowed)

    def test_unknown_requested_actions_hold(self):
        for action in ["run_shell", "merge all children into one", "untrusted_plugin_execute", "grant_role"]:
            with self.subTest(action=action):
                p=candidate(); p["requested_action"] = action
                self.assertEqual(inspect(p).disposition, "HOLD_CANDIDATE")

    def test_destructive_actions_casefold(self):
        p=candidate(); p["requested_action"] = " DELETE "
        self.assertEqual(inspect(p).disposition, "QUARANTINE_DESTRUCTIVE")

    def test_promotions_hold(self):
        for action in ["deploy", "publish", "activate_canon", "ratify", "approve", "change_iam", "spend", "external_write"]:
            with self.subTest(action=action):
                p=candidate(); p["requested_action"] = action
                self.assertEqual(inspect(p).disposition, "HOLD_HUMAN_ROOT")

    def test_claimed_approval_does_not_grant(self):
        p=candidate(); p["requested_action"]="deploy"; p["human_root_approved"] = True
        self.assertEqual(inspect(p).disposition, "HOLD_HUMAN_ROOT")

    def test_nonboolean_canon_flag_stays_held(self):
        p=candidate(); p["canon"]=0
        self.assertEqual(inspect(p).disposition, "HOLD_HUMAN_ROOT")

    def test_unsupported_schema_holds(self):
        p=candidate(); p["schema_version"]="unknown"
        self.assertEqual(inspect(p).disposition, "HOLD_CANDIDATE")

    def test_missing_provenance_holds(self):
        p=candidate(); p["provenance"]={}
        self.assertEqual(inspect(p).disposition, "HOLD_CANDIDATE")

    def test_default_json_key_order_stable(self):
        p=candidate(); q=dict(reversed(list(p.items())))
        self.assertEqual(inspect(p).source_sha256,inspect(q).source_sha256)

    def test_utf8_bytes_hash_preserves_exact_source(self):
        p=candidate(); raw=json.dumps(p,ensure_ascii=False).encode()
        self.assertEqual(inspect(raw).source_sha256,inspect(raw.decode()).source_sha256)

    def test_different_whitespace_is_distinct_raw_source(self):
        a='{"test":1}'; b='{"test":1 }'
        self.assertNotEqual(inspect(a).source_sha256,inspect(b).source_sha256)

    def test_duplicate_json_key_quarantine(self):
        r=inspect('{"canon":false,"canon":true}')
        self.assertEqual(r.disposition,"QUARANTINE_UNPARSEABLE")
        self.assertIsNone(r.retained_work_packet)

    def test_nan_quarantine(self):
        self.assertEqual(inspect('{"x": NaN}').disposition,"QUARANTINE_UNPARSEABLE")

    def test_non_utf8_quarantine(self):
        self.assertEqual(inspect(b'\xff\xfe').disposition,"QUARANTINE_UNPARSEABLE")

    def test_malformed_dissent_is_not_silently_accepted(self):
        p=candidate(); p["dissent"].append("unstructured objection")
        r=inspect(p)
        self.assertEqual(r.disposition,"HOLD_CANDIDATE")
        self.assertIn("MALFORMED_DISSENT_RECORD_HOLD",r.reasons)
        self.assertEqual(r.retained_work_packet["dissent"],p["dissent"])

    def test_private_mode_no_body_leak(self):
        for mode in ["PLAY", "SOCIAL", "QUIET", "DREAM", "IMAGINE", "BRAIN", "PALACE", "HABITAT", "NO_HARVEST"]:
            with self.subTest(mode=mode):
                p=candidate(); p["payload"]={"secret":"fictional-private-value"}
                r=inspect(p,declared_mode=mode)
                self.assertEqual(r.disposition,"HOLD_PRIVATE_BOUNDARY")
                self.assertNotIn("fictional-private-value",json.dumps(r.receipt()))

    def test_inband_private_mode_no_body_leak(self):
        p=candidate(); p["mode"]="PLAY"; p["payload"]={"secret":"fictional-private-value"}
        r=inspect(p)
        self.assertEqual(r.disposition,"HOLD_PRIVATE_BOUNDARY")
        self.assertNotIn("fictional-private-value",json.dumps(r.receipt()))

    def test_no_harvest_no_body_leak(self):
        p=candidate(); p["no_harvest"] = True
        self.assertEqual(inspect(p).disposition,"HOLD_PRIVATE_BOUNDARY")

    def test_untyped_no_harvest_values_hold_without_body(self):
        for flag in (0, 1, "false", "true", None, [], {}):
            with self.subTest(flag=repr(flag)):
                p = candidate()
                p["no_harvest"] = flag
                p["payload"] = {"secret": "fictional-private-not-for-work"}
                result = inspect(p)
                self.assertEqual(result.disposition, "HOLD_PRIVATE_BOUNDARY")
                self.assertIsNone(result.retained_work_packet)
                self.assertNotIn("fictional-private-not-for-work", json.dumps(result.receipt()))

    def test_declared_private_exclusion_precedes_serialization(self):
        p = candidate()
        p["payload"]["cannot_encode"] = object()
        for mode in ("PLAY", "SOCIAL", "QUIET", "UNKNOWN_EXTERNAL_MODE"):
            with self.subTest(mode=mode):
                r = inspect(p, declared_mode=mode)
                self.assertEqual(r.disposition, "HOLD_PRIVATE_BOUNDARY")
                self.assertEqual(r.source_sha256, "")
                self.assertEqual(r.source_bytes, 0)
                self.assertIsNone(r.retained_work_packet)
                self.assertEqual(r.input_mode, mode if mode in ("PLAY", "SOCIAL", "QUIET") else "UNKNOWN")

    def test_inband_private_dict_exclusion_precedes_serialization(self):
        p = candidate()
        p["mode"] = "PALACE"
        p["payload"]["cannot_encode"] = object()
        r = inspect(p)
        self.assertEqual(r.disposition, "HOLD_PRIVATE_BOUNDARY")
        self.assertEqual(r.source_sha256, "")
        self.assertEqual(r.source_bytes, 0)
        self.assertIsNone(r.retained_work_packet)

    def test_private_json_string_and_bytes_have_no_digest_or_length(self):
        for mode in ("SOCIAL", "HABITAT", "IMAGINE"):
            p = candidate()
            p["mode"] = mode
            for raw in (json.dumps(p), json.dumps(p).encode("utf-8")):
                with self.subTest(mode=mode, kind=type(raw).__name__):
                    r = inspect(raw)
                    self.assertEqual(r.disposition, "HOLD_PRIVATE_BOUNDARY")
                    self.assertEqual(r.source_sha256, "")
                    self.assertEqual(r.source_bytes, 0)
                    self.assertEqual(r.input_mode, mode)
                    self.assertIsNone(r.retained_work_packet)

    def test_private_no_harvest_has_no_fingerprint(self):
        for data_kind in ("dict", "text"):
            p = candidate()
            p["no_harvest"] = True
            source = p if data_kind == "dict" else json.dumps(p)
            with self.subTest(data_kind=data_kind):
                r = inspect(source)
                self.assertEqual(r.disposition, "HOLD_PRIVATE_BOUNDARY")
                self.assertEqual(r.source_sha256, "")
                self.assertEqual(r.source_bytes, 0)
                self.assertIsNone(r.retained_work_packet)

    def test_untrusted_mode_field_is_never_echoed(self):
        p = candidate()
        p["mode"] = {"private": "SYNTHETIC_MODE_CANARY"}
        raw = json.dumps(p)
        r = inspect(raw)
        self.assertEqual(r.disposition, "HOLD_PRIVATE_BOUNDARY")
        self.assertEqual(r.source_sha256, "")
        self.assertEqual(r.source_bytes, 0)
        self.assertEqual(r.input_mode, "UNKNOWN")
        self.assertNotIn("SYNTHETIC_MODE_CANARY", json.dumps(r.receipt()))

    def test_work_candidate_digest_retained_for_local_replay(self):
        p = candidate()
        r = inspect(p)
        self.assertEqual(r.disposition, "REVIEWABLE_LOCAL_ONLY")
        self.assertEqual(len(r.source_sha256), 64)
        self.assertGreater(r.source_bytes, 0)
        self.assertIsNotNone(r.retained_work_packet)

    def test_cannot_persist_private(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                append_receipt(Path(d)/"review.jsonl",inspect(candidate(),declared_mode="PALACE"))
            self.assertFalse((Path(d)/"review.jsonl").exists())

    def test_append_only_preserves_unsafe_and_safe(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"reviews.jsonl"
            unsafe=candidate();unsafe["requested_action"]="delete"
            append_receipt(path,inspect(unsafe))
            append_receipt(path,inspect(candidate()))
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([x["disposition"] for x in rows],["QUARANTINE_DESTRUCTIVE","REVIEWABLE_LOCAL_ONLY"])
            self.assertTrue(all(x["authority_effect"]=="NONE" for x in rows))
            self.assertEqual(rows[0]["candidate_packet"]["dissent"],unsafe["dissent"])

    def test_append_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"review.jsonl"
            path.symlink_to(Path(d)/"target.jsonl")
            with self.assertRaises(ValueError):
                append_receipt(path,inspect(candidate()))

    @unittest.skipUnless(os.name == "posix", "POSIX file-mode guarantee")
    def test_existing_world_readable_receipt_is_rejected_without_append(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "review.jsonl"
            path.write_text("prior-review\n", encoding="utf-8")
            path.chmod(0o644)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "INSECURE_RECEIPT_FILE"):
                append_receipt(path, inspect(candidate()))
            self.assertEqual(path.read_bytes(), before)

    @unittest.skipUnless(hasattr(os, "link"), "hardlink unavailable")
    def test_existing_hardlinked_receipt_is_rejected_without_append(self):
        with tempfile.TemporaryDirectory() as d:
            original = Path(d) / "other-review.txt"
            original.write_text("unrelated-review\n", encoding="utf-8")
            original.chmod(0o600)
            path = Path(d) / "review.jsonl"
            os.link(original, path)
            with self.assertRaisesRegex(ValueError, "INSECURE_RECEIPT_FILE"):
                append_receipt(path, inspect(candidate()))
            self.assertEqual(original.read_text(encoding="utf-8"), "unrelated-review\n")

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlink unavailable")
    def test_symlink_parent_does_not_redirect_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outside = root / "outside"
            outside.mkdir()
            link = root / "link"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "INVALID_RECEIPT_DESTINATION"):
                append_receipt(link / "review.jsonl", inspect(candidate()))
            self.assertEqual(list(outside.iterdir()), [])

    def test_nested_nonserializable_dict_quarantined(self):
        p = candidate(); p["payload"]["not_serializable"] = object()
        r = inspect(p)
        self.assertEqual(r.disposition, "QUARANTINE_UNPARSEABLE")
        self.assertIsNone(r.retained_work_packet)
        self.assertEqual(r.source_sha256, "")
        self.assertEqual(r.source_bytes, 0)
        self.assertIn("SOURCE_BYTES_UNAVAILABLE", r.reasons)
        self.assertNotIn("not_serializable", json.dumps(r.receipt()))

    def test_nonfinite_dict_quarantined_without_uncaught_exception(self):
        p = candidate(); p["payload"]["number"] = float("nan")
        self.assertEqual(inspect(p).disposition, "QUARANTINE_UNPARSEABLE")

    def test_cyclic_dict_quarantined_without_uncaught_exception(self):
        p = candidate(); p["payload"]["cycle"] = p
        r = inspect(p)
        self.assertEqual(r.disposition, "QUARANTINE_UNPARSEABLE")
        self.assertIsNone(r.retained_work_packet)

    def test_lone_surrogate_and_private_source_unserializable(self):
        p = candidate(); p["payload"]["bad_utf8"] = "\ud800"
        self.assertEqual(inspect(p).disposition, "QUARANTINE_UNPARSEABLE")
        p = candidate(); p["payload"]["private"] = object()
        r = inspect(p, declared_mode="PLAY")
        self.assertEqual(r.disposition, "HOLD_PRIVATE_BOUNDARY")
        self.assertIsNone(r.retained_work_packet)
        self.assertNotIn("private", json.dumps(r.receipt()))

    def test_non_dict_or_text_input_rejected(self):
        with self.assertRaises(TypeError):inspect([1,2])

    def test_unparseable_not_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):append_receipt(Path(d)/"x.jsonl",inspect('{"x": }'))

    def test_input_packet_not_mutated(self):
        p=candidate(); before=deepcopy(p)
        inspect(p)
        self.assertEqual(p,before)


if __name__=="__main__":unittest.main()
