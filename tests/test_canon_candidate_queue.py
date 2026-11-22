"""No-authority candidate queue negative tests; local fixture only."""
import json
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "docs" / "canon_candidate_queue.v0.1.json"

def no_duplicate_keys(pairs):
    result = {}
    for k,v in pairs:
        if k in result:
            raise ValueError("duplicate key")
        result[k] = v
    return result

def load():
    return json.loads(FILE.read_text("utf-8"), object_pairs_hook=no_duplicate_keys)

def validate(d):
    if type(d) is not dict or d.get("schema_version") != "atlas.canon.candidate-queue/v0.1":
        raise ValueError("schema")
    if d.get("canon") is not False or d.get("deployment") is not False:
        raise ValueError("promotion")
    if d.get("authority") != "none" or type(d.get("adopted_count")) is not int or d["adopted_count"] != 0:
        raise ValueError("authority")
    if d.get("decision_source") != "AUTHENTICATED_HUMAN_ROOT_NOT_PRESENT":
        raise ValueError("host decision")
    records = d.get("candidates")
    if type(records) is not list or len(records) != 4:
        raise ValueError("count")
    ids = set()
    for row in records:
        if type(row) is not dict or type(row.get("id")) is not str or row["id"] in ids:
            raise ValueError("id")
        ids.add(row["id"])
        if not (type(row.get("source")) is str and row["source"].startswith("https://github.com/atlaslattice/")):
            raise ValueError("source")
        if row.get("human_root_decision") is not None or row.get("canonical_status") != "NOT_ADOPTED":
            raise ValueError("decision")
        if row.get("rights_at_return") != "NOT_ATTESTED" or row.get("semantic_review") != "UNREVIEWED":
            raise ValueError("rights")
        if row.get("dissent_preserved") is not True or not (type(row.get("contradiction")) is str and row["contradiction"]):
            raise ValueError("dissent")
    return True

class CandidateQueueTests(unittest.TestCase):
    def setUp(self): self.data = load()
    def test_valid(self): self.assertTrue(validate(self.data))
    def test_reject_canon(self):
        self.data["canon"]=True
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_bool_number(self):
        self.data["canon"]=0
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_decision(self):
        self.data["candidates"][0]["human_root_decision"]={"approved":True}
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_adoption(self):
        self.data["candidates"][0]["canonical_status"]="ADOPTED"
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_missing_source(self):
        self.data["candidates"][1]["source"]=""
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_missing_dissent(self):
        self.data["candidates"][1]["dissent_preserved"]=False
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_rights_claim(self):
        self.data["candidates"][2]["rights_at_return"]="VERIFIED"
        with self.assertRaises(ValueError): validate(self.data)
    def test_reject_duplicate_json(self):
        with self.assertRaises(ValueError):
            json.loads('{"canon":false,"canon":true}',object_pairs_hook=no_duplicate_keys)
if __name__ == "__main__": unittest.main()

