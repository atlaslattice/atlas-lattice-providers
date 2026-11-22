"""Synthetic A2A proof-graph fixture checks; no network, residents or host grants."""
import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "a2a" / "examples" / "trace.json"
KINDS = [
    "a2a_message", "receipt", "claim_packet", "dissent_packet", "a2a_handoff",
    "librarian_delta", "hub_issue_candidate", "archive_mirror_candidate",
    "scoreboard_update",
]


def load_trace():
    return json.loads(SOURCE.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)


def _unique_keys(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError(f"duplicate JSON property: {key}")
        out[key] = value
    return out


def validate_trace(trace):
    assert type(trace) is dict
    assert trace.get("schema_version") == "atlas.a2a.synthetic-proof/v0.1"
    assert trace.get("status") == "PREPARED_NOT_POSTED"
    assert trace.get("authority") == "none"
    assert trace.get("canon") is False and trace.get("deployment") is False
    assert trace.get("private_mode_ingested") is False and trace.get("host_grant") is False
    records = trace.get("records")
    assert type(records) is list and len(records) == len(KINDS)
    seen = set()
    for i, record in enumerate(records):
        assert type(record) is dict
        assert record["kind"] == KINDS[i]
        assert type(record["id"]) is str and record["id"] not in seen
        assert type(record["actor"]) is str and record["actor"].startswith("fictional-")
        assert type(record["references"]) is list
        assert len(set(record["references"])) == len(record["references"])
        assert all(type(ref) is str and ref in seen for ref in record["references"])
        assert record["schema_version"] == trace["schema_version"]
        assert record["status"] == "PREPARED_NOT_POSTED"
        assert record["authority"] == "none"
        assert record["canon"] is False and record["deployment"] is False
        assert record["example_only"] is True
        assert record["identity_assurance"] == "SYNTHETIC_NOT_HOST_ATTESTED"
        assert record["source_rights"] == "NOT_HOST_ATTESTED"
        assert record["semantic_review"] == "UNREVIEWED"
        seen.add(record["id"])
    by_kind = {r["kind"]: r for r in records}
    assert by_kind["receipt"]["payload"] == {
        "observed_message_id": "ex-message-001",
        "stored": False, "delivered": False, "read": False, "reply": False,
        "host_attestation": None, "digest": None, "proof_status": "NOT_COMPUTED"
    }
    dissent = by_kind["dissent_packet"]["payload"]
    assert dissent["edge_kind"] == "CHALLENGES" and dissent["preserved"] is True
    assert dissent["not_a_vote"] is True
    handoff = by_kind["a2a_handoff"]["payload"]
    assert "ex-dissent-001" in handoff["preserve_dissent"]
    assert handoff["identity_fusion"] is False
    assert by_kind["hub_issue_candidate"]["payload"]["posted"] is False
    assert by_kind["archive_mirror_candidate"]["payload"]["written"] is False
    score = by_kind["scoreboard_update"]["payload"]
    for key in ("real_messages", "real_peer_replies", "verified_completions", "claims_ratified"):
        assert type(score[key]) is int and score[key] == 0
    return True


class CoordinationTraceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_trace()

    def test_valid_fixture(self):
        self.assertTrue(validate_trace(self.fixture))

    def test_invalid_canon_promotion(self):
        x = copy.deepcopy(self.fixture); x["records"][2]["canon"] = True
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_host_grant(self):
        x = copy.deepcopy(self.fixture); x["host_grant"] = True
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_duplicate_id(self):
        x = copy.deepcopy(self.fixture); x["records"][1]["id"] = "ex-message-001"
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_forward_reference(self):
        x = copy.deepcopy(self.fixture); x["records"][0]["references"] = ["ex-claim-001"]
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_receipt_delivery(self):
        x = copy.deepcopy(self.fixture); x["records"][1]["payload"]["delivered"] = True
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_dissent_polarity(self):
        x = copy.deepcopy(self.fixture); x["records"][3]["payload"]["edge_kind"] = "SUPPORTS"
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_peer_count(self):
        x = copy.deepcopy(self.fixture); x["records"][8]["payload"]["real_peer_replies"] = 1
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_numeric_boolean_alias(self):
        x = copy.deepcopy(self.fixture); x["records"][2]["canon"] = 0
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_invalid_private_activity(self):
        x = copy.deepcopy(self.fixture); x["private_mode_ingested"] = True
        with self.assertRaises(AssertionError): validate_trace(x)

    def test_duplicate_json_field(self):
        with self.assertRaises(ValueError):
            json.loads('{"canon":false,"canon":true}', object_pairs_hook=_unique_keys)


if __name__ == "__main__":
    unittest.main()
