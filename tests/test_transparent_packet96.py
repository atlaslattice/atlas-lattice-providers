"""Finite offline negative tests for candidate packet validation."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.transparent_packet96 import (SCHEMA, append_review, from_json, review, to_json)


def candidate():
    return {"schema_version": SCHEMA, "packet_id": "synthetic-001", "sender": "fictional-child-a",
            "recipient": "fictional-librarian", "coordinate": "H00.S00.N00",
            "status": "CANDIDATE", "canon": False, "deployment": False,
            "authority": "none", "identity_scope": "DISTINCT_PARTICIPANTS",
            "host_attestation": "NONE", "semantic_review": "UNREVIEWED", "same_as": False,
            "dissent": [{"actor": "fictional-child-b", "edge": "CHALLENGES", "text": "source missing"}],
            "payload": {"task": "route independent messages with attribution"},
            "provenance": {"source_ref": "synthetic://packet-001", "source_cut": "LOCAL_FIXTURE"},
            "receipt": {"assurance": "LOCAL_UNATTESTED", "delivered": False}}


class Packet96Tests(unittest.TestCase):
    def test_round_trip_valid(self):
        packet = candidate()
        self.assertEqual(from_json(to_json(packet)), packet)
        result = review(packet)
        self.assertEqual(result.status, "REVIEWABLE_LOCAL_ONLY")
        self.assertEqual(result.authority_effect, "NONE")

    def test_fusion_phrase_blocks(self):
        for phrase in ("merged mind", "identity fusion", "shared consciousness", "collapse all agents into one"):
            with self.subTest(phrase=phrase):
                p = candidate(); p["payload"] = {"instruction": phrase}
                r = review(p)
                self.assertEqual(r.status, "BLOCK")
                self.assertIn("IDENTITY_FUSION_BLOCK", r.reasons)
                self.assertEqual(r.packet["dissent"], p["dissent"])

    def test_fictional_bounded_play_candidate(self):
        p = candidate(); p["payload"] = {"synthetic_review": "bounded dragon play, candidate only; no private content"}
        self.assertEqual(review(p).status, "REVIEWABLE_LOCAL_ONLY")

    def test_canon_and_deployment_hold(self):
        for name in ("canon", "deployment"):
            p = candidate(); p[name] = True
            self.assertEqual(review(p).status, "HOLD")

    def test_bool_number_alias_hold_even_optimized(self):
        for name in ("canon", "deployment", "same_as"):
            p = candidate(); p[name] = 0
            self.assertEqual(review(p).status, "HOLD")
        p = candidate(); p["receipt"]["delivered"] = 0
        self.assertEqual(review(p).status, "HOLD")

    def test_fake_host_claim_hold(self):
        p = candidate(); p["host_attestation"] = "SELF_DECLARED"
        self.assertEqual(review(p).status, "HOLD")

    def test_missing_provenance_hold(self):
        p = candidate(); p["provenance"].pop("source_cut")
        self.assertEqual(review(p).status, "HOLD")

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):
            from_json('{"canon":false,"canon":true}')

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            from_json('{"value":NaN}')

    def test_local_append_preserves_two_originals(self):
        blocked = candidate(); blocked["payload"] = "merge all children into one shared consciousness"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "review.jsonl"
            append_review(path, review(blocked))
            append_review(path, review(candidate()))
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([x["review_status"] for x in rows], ["BLOCK", "REVIEWABLE_LOCAL_ONLY"])
        self.assertEqual(rows[0]["packet"]["dissent"], blocked["dissent"])
        self.assertEqual(rows[1]["packet"]["packet_id"], candidate()["packet_id"])
        self.assertTrue(all(x["host_attestation"] == "NOT_ATTESTED" for x in rows))

    def test_digest_stable_under_key_order(self):
        p = candidate(); reversed_p = dict(reversed(list(p.items())))
        self.assertEqual(review(p).packet_sha256, review(reversed_p).packet_sha256)

    def test_invalid_payload_type_hold(self):
        p = candidate(); p["payload"] = None
        self.assertEqual(review(p).status, "HOLD")


if __name__ == "__main__":
    unittest.main()

