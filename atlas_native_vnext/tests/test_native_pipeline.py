"""Use real exact PR61 source from PYTHONPATH; missing dependency is skipped."""
from __future__ import annotations
from pathlib import Path
from hashlib import sha1
import json
import tempfile
import unittest
from native_synthesis.pipeline import OfflineAtlasPipeline
from native_synthesis.offline_receipts import OfflinePreparationStore
from native_synthesis.engine import ARIADNE_SHA
try:
    from labs import atlas_labs_v32 as labs
except ImportError:
    labs=None

@unittest.skipIf(labs is None, 'PR61 exact external source absent')
class OfflinePipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=OfflinePreparationStore(str(Path(self.tmp.name)/'source-only.db'),scope_key=b'a-private-local-key-32-bytes-0123456789')
        self.pipe=OfflineAtlasPipeline(labs.prepare,labs.catalog,self.store)
        self.x={'schema':'atlas.labs.experiment-candidate/v0.1',
            'experiment_id':'PR61.native.integration.001','lab_id':'fusion-plasma',
            'source_id':'stars2-source-gateway','title':'Synthetic source-only trial',
            'hypothesis':'Local computations have reproducible outputs',
            'falsifier':'A fixed negative control changes unexpectedly',
            'model_kind':'SYNTHETIC_MODEL','model_revision':'no-hardware-v1',
            'quantities':[{'name':'energy','value':'2.5','unit':'J','uncertainty':'0.1',
                           'evidence_class':'SYNTHETIC_MODEL_ONLY'}],
            'ontology':{'edition':'Ariadne v0.7','registry_sha256':ARIADNE_SHA,
                        'coordinate':'H01.S01.N01'},
            'origin_mode':'PUBLIC','source_scope':'PUBLIC_REPORTED','authority':'none',
            'canon':False,'deployment':False}
        self.ctx={'tenant':'test-tenant','account':'test-account','principal':'test-user','room':'offline-work'}
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def test_real_cross_repo_pipeline_stages_no_side_effects(self):
        o=self.pipe.prepare(self.x,**self.ctx)
        self.assertEqual(o['status'],'LOCAL_REVIEW_PREPARED_NOT_SENT')
        self.assertEqual(o['atlas_one'],'TASK_NOT_DISPATCHED')
        self.assertEqual(o['swarmchat'],'WORK_MESSAGE_NOT_POSTED')
        self.assertEqual(o['alexandria'],'GRAPH_NOT_WRITTEN')
        self.assertFalse(o['host_attested']);self.assertFalse(o['delivery_ack'])
        self.assertEqual(self.store.report()['prepared_records'],1)
    def test_idempotent_local_replay(self):
        a=self.pipe.prepare(self.x,**self.ctx)
        b=self.pipe.prepare(self.x,**self.ctx)
        self.assertEqual(a['local_sqlite_state'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertEqual(b['local_sqlite_state'],'DEDUPLICATED_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.store.report()['prepared_records'],1)
    def test_withdraw_between_prepare_and_duplicate(self):
        a=self.pipe.prepare(self.x,**self.ctx)
        self.pipe.withdraw_local(**self.ctx,source_sha256=a['lab_receipt_sha256'])
        b=self.pipe.prepare(self.x,**self.ctx)
        self.assertEqual(b['status'],'HOLD')
    def test_wrong_scope_not_replayed_as_peer(self):
        a=self.pipe.prepare(self.x,**self.ctx)
        b=self.pipe.prepare(self.x,tenant='different-tenant',account=self.ctx['account'],principal=self.ctx['principal'],room=self.ctx['room'])
        self.assertEqual(a['status'],b['status'])
        self.assertFalse(b['peer_read'])
        self.assertEqual(self.store.report()['prepared_records'],2)
    def test_account_switch_same_tenant_principal_is_distinct(self):
        a=self.pipe.prepare(self.x,**self.ctx)
        b=self.pipe.prepare(self.x,**{**self.ctx,'account':'another-account'})
        self.assertEqual(a['status'],'LOCAL_REVIEW_PREPARED_NOT_SENT')
        self.assertEqual(b['status'],'LOCAL_REVIEW_PREPARED_NOT_SENT')
        self.assertEqual(self.store.report()['prepared_records'],2)
        self.pipe.withdraw_local(**self.ctx,source_sha256=a['lab_receipt_sha256'])
        fresh=self.pipe.prepare(self.x,**{**self.ctx,'account':'another-account'})
        self.assertEqual(fresh['status'],'LOCAL_REVIEW_PREPARED_NOT_SENT')
        self.assertEqual(fresh['local_sqlite_state'],'DEDUPLICATED_PREPARED_LOCAL_ONLY')

    def test_invalid_private_mode_has_no_preparation(self):
        x=dict(self.x);x['origin_mode']='PALACE'
        r=self.pipe.prepare(x,**self.ctx)
        self.assertEqual(r['status'],'HOLD')
        self.assertEqual(self.store.report()['prepared_records'],0)
    def test_no_invented_ontology(self):
        x=dict(self.x);x['ontology']=None
        self.assertEqual(self.pipe.prepare(x,**self.ctx)['status'],'HOLD')
    def test_no_silent_bit_conversion(self):
        x=dict(self.x);x['quantities']=[dict(self.x['quantities'][0],unit='bit')]
        self.assertEqual(self.pipe.prepare(x,**self.ctx)['status'],'HOLD')
    def test_changed_same_identifier_rejected(self):
        self.pipe.prepare(self.x,**self.ctx)
        x=dict(self.x);x['hypothesis']='A different local result'
        self.assertEqual(self.pipe.prepare(x,**self.ctx)['status'],'HOLD')
        self.assertEqual(self.store.report()['prepared_records'],1)

if __name__=='__main__':unittest.main()
