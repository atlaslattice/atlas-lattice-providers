"""Run with PYTHONPATH including an exact PR #61 source checkout for real interop.

Without it, tests for external PR61 are explicitly skipped, never called
host-verified. The rest of the native kernel is independently testable.
"""
from __future__ import annotations
import copy
from hashlib import sha1
import importlib.util
import json
from pathlib import Path
import unittest

from native_synthesis.interop import prepare_labs_crosswalk, LAB_KIND
from native_synthesis.engine import NativeSynthesis

try:
    from labs import atlas_labs_v32 as labs
except ImportError:
    labs = None

PR61_BLOB = 'd3eb9cfe9009a23488b33f09dd1782fed93e28c3'
HSN_SHA = '07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6'


def record(lab='fusion-plasma',unit='J',kind='SYNTHETIC_MODEL'):
    q=[{'name':'energy','value':'1.250','unit':unit,'uncertainty':'0.125',
        'evidence_class':'SYNTHETIC_MODEL_ONLY'}]
    return {'schema':'atlas.labs.experiment-candidate/v0.1',
            'experiment_id':'public.synthetic.lab.001','lab_id':lab,
            'source_id':labs.CATALOG[lab][0] if labs else 'stars2-source-gateway',
            'title':'Synthetic local experiment','hypothesis':'Reproducible finite computation',
            'falsifier':'A changed seed produces a mismatching readout',
            'model_kind':kind,'model_revision':'local-no-hardware-v0.1',
            'quantities':q if kind=='SYNTHETIC_MODEL' else [],
            'ontology':{'edition':'Ariadne v0.7','registry_sha256':HSN_SHA,
                        'coordinate':'H01.S01.N01'},'origin_mode':'PUBLIC',
            'source_scope':'PUBLIC_REPORTED','authority':'none','canon':False,'deployment':False}

@unittest.skipIf(labs is None, 'PR #61 external source checkout not installed')
class AtlasLabsPR61Interop(unittest.TestCase):
    def setUp(self):
        self.e=NativeSynthesis()
        self.call=lambda x:prepare_labs_crosswalk(x,labs.prepare,labs.catalog,native=self.e)

    def test_external_source_byte_identity(self):
        p=Path(labs.__file__)
        b=p.read_bytes()
        self.assertEqual(sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),PR61_BLOB)

    def test_real_pr61_fusion_crosswalk(self):
        out=self.call(record())
        self.assertEqual(out['status'],'LINKED_LOCAL_SOURCE_ONLY')
        self.assertEqual(out['atlas_one'],'TASK_CANDIDATE_NOT_DISPATCHED')
        self.assertEqual(out['swarmchat'],'WORK_PREVIEW_NOT_POSTED')
        self.assertEqual(out['alexandria'],'GRAPH_CANDIDATE_NOT_WRITTEN')
        self.assertFalse(out['same_as'])
        self.assertFalse(out['rights_checked'])
        self.assertEqual(self.e.journal.count,1)
        self.assertTrue(self.e.journal.verify())

    def test_all_eight_lab_design_only(self):
        for lab in LAB_KIND:
            with self.subTest(lab=lab):
                self.assertEqual(prepare_labs_crosswalk(record(lab=lab,kind='DESIGN_ONLY'),
                     labs.prepare,labs.catalog)['status'],'LINKED_LOCAL_SOURCE_ONLY')

    def test_idempotent_after_replay(self):
        self.assertEqual(self.call(record())['native_local_receipt']['status'],'NEW_LOCAL_ONLY')
        self.assertEqual(self.call(record())['native_local_receipt']['status'],'DEDUPLICATED_LOCAL_ONLY')
        self.assertEqual(self.e.journal.count,1)

    def test_changed_same_request_is_hold(self):
        self.call(record())
        x=record();x['hypothesis']='different synthetic hypothesis'
        self.assertEqual(self.call(x)['status'],'HOLD')
        self.assertEqual(self.e.journal.count,1)

    def test_no_auto_ontology_mapping(self):
        x=record();x['ontology']=None
        self.assertEqual(self.call(x)['status'],'HOLD')

    def test_wrong_edition_hold(self):
        x=record();x['ontology']['edition']='historical-zero-based'
        self.assertEqual(self.call(x)['status'],'HOLD')

    def test_no_unit_coercion_bit_to_count(self):
        x=record(unit='bit');out=self.call(x)
        self.assertEqual(out['status'],'HOLD')
        self.assertEqual(out['source_count'],0)

    def test_private_and_work_sources_hold(self):
        for origin,scope in [('PLAY','PRIVATE'),('WORK','WORK_REPORTED'),('SOCIAL','PRIVATE'),('BRAIN','PRIVATE')]:
            x=record();x['origin_mode']=origin;x['source_scope']=scope
            with self.subTest(origin=origin):self.assertEqual(self.call(x)['status'],'HOLD')

    def test_lab_candidate_cannot_claim_observation(self):
        x=record();x['quantities'][0]['evidence_class']='PHYSICAL_MEASURED'
        self.assertEqual(self.call(x)['status'],'HOLD')

    def test_forged_lab_prepare_denied(self):
        def forged(_):return {'status':'PREPARED_SOURCE_ONLY','candidate':{'atlas_one':{},'swarmchat_work':{},'alexandria':{}}}
        self.assertEqual(prepare_labs_crosswalk(record(),forged,labs.catalog)['status'],'HOLD')

    def test_source_commit_mismatch(self):
        def corrupt():
            c=labs.catalog();c['fusion-plasma']['git_commit']='0'*40;return c
        self.assertEqual(prepare_labs_crosswalk(record(),labs.prepare,corrupt)['status'],'HOLD')

    def test_source_blob_mismatch(self):
        def corrupt():
            c=labs.catalog();c['fusion-plasma']['git_blob_sha1']='x'*40;return c
        self.assertEqual(prepare_labs_crosswalk(record(),labs.prepare,corrupt)['status'],'HOLD')

    def test_tampered_lab_digest(self):
        def forged(x):
            r=labs.prepare(x);r['candidate']['atlas_one']['packet']['experiment_sha256']='0'*64;return r
        self.assertEqual(prepare_labs_crosswalk(record(),forged,labs.catalog)['status'],'HOLD')

    def test_full_packet_no_raw_private_string(self):
        x=record();out=self.call(x)
        self.assertNotIn('hypothesis',json.dumps(out))
        self.assertNotIn('falsifier',json.dumps(out))
        self.assertFalse(out['hardware_verified'])

    def test_decimal_preserved_even_when_not_observed(self):
        x=record();x['quantities'][0]['value']='1.234567890123'
        self.assertEqual(self.call(x)['status'],'LINKED_LOCAL_SOURCE_ONLY')

    def test_unexpected_source_fields_fail_closed(self):
        x=record();x['secret_payload']='FAKE_CANARY_DO_NOT_ECHO'
        r=self.call(x)
        self.assertEqual(r['status'],'HOLD')
        self.assertNotIn('FAKE_CANARY_DO_NOT_ECHO',json.dumps(r))

if __name__ == '__main__':unittest.main()
