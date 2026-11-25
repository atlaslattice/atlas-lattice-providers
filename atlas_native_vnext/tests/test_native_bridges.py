import json
import unittest
from native_synthesis.bridges import (mcp_tools_preview,a2a_card_preview,uws_read_plan,
                                      numerical_backend_plan,graph_view_plan)

def uws():return {'schema':'atlas.native.uws-plan/v0.1','provider':'github',
                  'operation':'source.metadata.read','resource':'atlaslattice/manus-artifacts',
                  'revision':'476901f06b9685dfa63b2f796806b5d181595463'}
def backend():return {'schema':'atlas.native.solver-plan/v0.1','backend':'qiskit',
                     'lab_id':'quantum','model_revision':'offline-0.1',
                     'evidence_kind':'SYNTHETIC','budget_usd':0}
def graph():return {'schema':'atlas.native.graph-view/v0.1',
                    'nodes':[{'id':'source-one','kind':'source','edition':'source-v0.1'},
                             {'id':'claim-one','kind':'claim','edition':'source-v0.1'}],
                    'edges':[{'from':'source-one','to':'claim-one','relation':'SOURCE_OF',
                              'review_status':'UNREVIEWED'}]}
class AdapterTests(unittest.TestCase):
    def test_mcp_is_only_manifest(self):
        v=mcp_tools_preview()
        self.assertIsNone(v['endpoint']);self.assertFalse(v['host_auth']=='VERIFIED')
        self.assertGreaterEqual(len(v['tools']),4)
        for t in v['tools']:self.assertTrue(t['annotations']['readOnlyHint'])
    def test_a2a_not_advertised(self):
        v=a2a_card_preview();self.assertFalse(v['push_notifications']);self.assertIsNone(v['service_url'])
    def test_uws_plan_inert(self):
        v=uws_read_plan(uws());self.assertEqual(v['status'],'UWS_READ_PLAN_NOT_EXECUTED')
        self.assertFalse(v['remote_called'])
    def test_uws_injection_denied(self):
        x=uws();x['resource']='x; rm -rf /'
        self.assertEqual(uws_read_plan(x)['status'],'HOLD')
    def test_uws_no_post(self):
        x=uws();x['operation']='source.write'
        self.assertEqual(uws_read_plan(x)['status'],'HOLD')
    def test_uws_missing_credential_denied(self):
        x=uws();x['access_token']='secret'
        self.assertEqual(uws_read_plan(x)['status'],'HOLD')
    def test_quantum_no_spend(self):
        self.assertFalse(numerical_backend_plan(backend())['provider_called'])
        x=backend();x['budget_usd']=100
        self.assertEqual(numerical_backend_plan(x)['status'],'HOLD')
    def test_quantum_no_hardware(self):self.assertFalse(numerical_backend_plan(backend())['physical_hardware'])
    def test_wrong_solver_lab(self):
        x=backend();x['lab_id']='biology'
        self.assertEqual(numerical_backend_plan(x)['status'],'HOLD')
    def test_unverified_solver_read(self):
        x=backend();x['evidence_kind']='MEASURED'
        self.assertEqual(numerical_backend_plan(x)['status'],'HOLD')
    def test_graph_only_preview(self):
        v=graph_view_plan(graph());self.assertFalse(v['hosted_3d'])
        self.assertEqual(v['semantic_edges_accepted'],0)
    def test_graph_requires_explicit_unreviewed_edge(self):
        x=graph();x['edges'][0]['review_status']='CANON'
        self.assertEqual(graph_view_plan(x)['status'],'HOLD')
    def test_graph_rejects_nonexistent_node(self):
        x=graph();x['edges'][0]['to']='missing'
        self.assertEqual(graph_view_plan(x)['status'],'HOLD')
    def test_graph_rejects_external_script(self):
        x=graph();x['nodes'][1]['id']='<script>'
        self.assertEqual(graph_view_plan(x)['status'],'HOLD')
if __name__=='__main__':unittest.main()
