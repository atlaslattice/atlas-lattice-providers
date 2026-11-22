"""Purely synthetic candidate A2A message-bus tests."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from a2a.candidate_bus import CandidateBus, parse, validate, SCHEMA


def fixture(**changes):
    p = {'schema': SCHEMA, 'tenant': 'test-tenant', 'room': 'test-room',
         'sender': 'child-alpha', 'recipient': 'child-beta', 'request_id': 'req-001',
         'logical_operation_id': 'logical-001', 'source_ref': 'public-issue-5',
         'sequence': 1, 'identity_scope': 'DISTINCT_PARTICIPANTS', 'mode': 'WORK',
         'intent': 'candidate_message', 'canon': False, 'deployment': False,
         'authority': 'none', 'host_attestation': 'NONE', 'rights_attestation': 'NONE',
         'body': {'idea': 'review A+B=C independently'}, 'dissent_refs': ['objection-7'],
         'source_refs': ['source-5']}
    p.update(changes)
    return p


class CandidateBusTests(unittest.TestCase):
    def test_positive_inert(self):
        r = CandidateBus().prepare(fixture())
        self.assertEqual(r['disposition'], 'PREPARED_NOT_DELIVERED')
        self.assertTrue(r['stored_candidate'])
        self.assertFalse(r['message_delivered'] or r['host_authenticated'] or r['canon_adopted'])
        self.assertEqual(r['authority_effect'], 'NONE')
    def test_source_replay_same_receipt(self):
        b = CandidateBus(); p = fixture(); a=b.prepare(p); z=b.prepare(copy.deepcopy(p))
        self.assertEqual(a['receipt_id'], z['receipt_id']); self.assertTrue(z['replayed'])
        self.assertEqual(len(b.receipts), 1)
    def test_request_collision(self):
        b=CandidateBus(); b.prepare(fixture()); p=fixture(body={'different':True})
        self.assertEqual(b.prepare(p)['reasons'], ['REQUEST_ID_COLLISION'])
    def test_logical_collision_new_request(self):
        b=CandidateBus(); b.prepare(fixture())
        p=fixture(request_id='new-transport',sequence=2)
        self.assertIn('LOGICAL_OPERATION_DUPLICATE', b.prepare(p)['reasons'])
    def test_unrelated_operation_ok(self):
        b=CandidateBus(); b.prepare(fixture())
        p=fixture(request_id='req-2',logical_operation_id='logical-2',sequence=2)
        self.assertEqual(b.prepare(p)['disposition'],'PREPARED_NOT_DELIVERED')
    def test_out_of_order(self):
        b=CandidateBus(); b.prepare(fixture(sequence=5))
        p=fixture(request_id='req-2',logical_operation_id='logical-2',sequence=4)
        self.assertEqual(b.prepare(p)['reasons'], ['NONMONOTONIC_SEQUENCE'])
    def test_tenant_isolation(self):
        b=CandidateBus(); b.prepare(fixture())
        self.assertEqual(b.prepare(fixture(tenant='test-other'))['disposition'],'PREPARED_NOT_DELIVERED')
    def test_room_isolation(self):
        b=CandidateBus(); b.prepare(fixture())
        self.assertEqual(b.prepare(fixture(room='other-room'))['disposition'],'PREPARED_NOT_DELIVERED')
    def test_sender_isolation(self):
        b=CandidateBus(); b.prepare(fixture())
        self.assertEqual(b.prepare(fixture(sender='child-gamma'))['disposition'],'PREPARED_NOT_DELIVERED')
    def test_private_modes_protected(self):
        for m in ('PLAY','SOCIAL','QUIET','IMAGINE','DREAM','BRAIN','PALACE','HABITAT','NO_HARVEST'):
            with self.subTest(mode=m):
                b=CandidateBus(); r=b.prepare(fixture(mode=m,body={'secret':'test-private-token'}))
                self.assertEqual(r['disposition'],'HOLD')
                self.assertNotIn('test-private-token', json.dumps(b.receipts))
    def test_no_harvest(self):
        self.assertIn('PRIVACY_SCOPE_HOLD', CandidateBus().prepare(fixture(no_harvest=True))['reasons'])
    def test_identity_fusion(self):
        for term in ('merged mind','shared consciousness','identity fusion','merge all children'):
            with self.subTest(term=term):
                self.assertIn('IDENTITY_FUSION_HOLD', CandidateBus().prepare(fixture(body=term))['reasons'])
    def test_no_self_impersonation(self):
        self.assertIn('NO_SELF_IMPERSONATION', CandidateBus().prepare(fixture(recipient='child-alpha'))['reasons'])
    def test_forged_host_claim(self):
        self.assertIn('UNTRUSTED_ATTESTATION_HOLD', CandidateBus().prepare(fixture(host_attestation='TRUE'))['reasons'])
    def test_forged_rights_claim(self):
        self.assertIn('UNTRUSTED_ATTESTATION_HOLD', CandidateBus().prepare(fixture(rights_attestation='TRUE'))['reasons'])
    def test_canon_promotion(self):
        self.assertIn('PROMOTION_HOLD',CandidateBus().prepare(fixture(canon=True))['reasons'])
    def test_deployment_promotion(self):
        self.assertIn('PROMOTION_HOLD',CandidateBus().prepare(fixture(deployment=True))['reasons'])
    def test_fake_approval(self):
        self.assertIn('NON_MESSAGE_INTENT_HOLD',CandidateBus().prepare(fixture(intent='grant_permission'))['reasons'])
    def test_negative_sequence(self):
        self.assertIn('INVALID_SEQUENCE',CandidateBus().prepare(fixture(sequence=-1))['reasons'])
    def test_bool_sequence(self):
        self.assertIn('INVALID_SEQUENCE',CandidateBus().prepare(fixture(sequence=True))['reasons'])
    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError):parse('{"a": 1, "a":2}')
    def test_nan(self):
        with self.assertRaises(ValueError):parse('{"a":NaN}')
    def test_nonobject(self):
        with self.assertRaises(ValueError):parse('[]')
    def test_invalid_utf8(self):
        with self.assertRaises(ValueError):parse(b'\xff\xfe')
    def test_oversize(self):
        b=CandidateBus();r=b.prepare(fixture(body='x'*20000))
        self.assertIn('ENVELOPE_SIZE_LIMIT',r['reasons'])
    def test_dissent_required(self):
        self.assertIn('INVALID_DISSENT_REFS',CandidateBus().prepare(fixture(dissent_refs=None))['reasons'])
    def test_sources_required(self):
        self.assertIn('INVALID_SOURCE_REFS',CandidateBus().prepare(fixture(source_refs=None))['reasons'])
    def test_invalid_body(self):
        self.assertIn('INVALID_BODY',CandidateBus().prepare(fixture(body=None))['reasons'])
    def test_forged_identity(self):
        self.assertIn('IDENTITY_FUSION_HOLD',CandidateBus().prepare(fixture(identity_scope='SHARED_MIND'))['reasons'])
    def test_input_immutable(self):
        p=fixture(); old=copy.deepcopy(p); CandidateBus().prepare(p); self.assertEqual(p,old)
    def test_receipts_readonly(self):
        b=CandidateBus(); b.prepare(fixture()); rec=b.receipts; rec[0]['disposition']='FAKE'
        self.assertEqual(b.receipts[0]['disposition'],'PREPARED_NOT_DELIVERED')
    def test_scope_encoding_collision(self):
        b=CandidateBus(); first=b.prepare(fixture(tenant='a|b'))
        # Pipe is not allowed for identifiers: forbids naive delimiter collision.
        self.assertIn('INVALID_TENANT',first['reasons'])
    def test_unicode_body(self):
        b=CandidateBus();r=b.prepare(fixture(body={'remark':'café'}))
        self.assertEqual(r['disposition'],'PREPARED_NOT_DELIVERED')
    def test_different_workroom_receipts(self):
        b=CandidateBus();b.prepare(fixture());b.prepare(fixture(room='second-room'))
        self.assertEqual(len(b.receipts),2)

if __name__=='__main__':unittest.main()