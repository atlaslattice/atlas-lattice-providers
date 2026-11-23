import copy
import json
import pathlib
import threading
import unittest

from native_synthesis import NativeSynthesis, CapabilityCatalog, WireError, strict_json, digest
from native_synthesis.wire import exact_quantity, canonical_json, HEX40, HSN
from native_synthesis.journal import CandidateJournal
from native_synthesis.authority import SyntheticHostAuthority, UnavailableAuthority
from native_synthesis.responses import function_tools, handle_function_call

ROOT=pathlib.Path(__file__).resolve().parents[1]
EX=json.loads((ROOT/'examples/experiment-stub.json').read_text())
FUS=json.loads((ROOT/'examples/cross-domain-stub.json').read_text())


def changed(**kwargs):
    x=copy.deepcopy(EX)
    for key,value in kwargs.items():
        if '.' in key:
            pos=key.split('.')
            tgt=x
            for k in pos[:-1]:tgt=tgt[k]
            tgt[pos[-1]]=value
        else:x[key]=value
    return x

class TestWire(unittest.TestCase):
    def test_strict_baseline(self):self.assertEqual(strict_json('{"x":1}'),{'x':1})
    def test_duplicate_key(self):
        with self.assertRaises(WireError):strict_json('{"a":1,"a":2}')
    def test_unicode_equivalent_alias(self):
        with self.assertRaises(WireError):strict_json('{"e\\u0301":1,"\\u00e9":2}')
    def test_unicode_equivalent_alias_python_dict(self):
        with self.assertRaises(WireError):strict_json({'e\u0301':1,'\u00e9':2})
    def test_nested_unicode_alias(self):
        with self.assertRaises(WireError):strict_json('{"a":{"e\\u0301":1,"\\u00e9":2}}')
    def test_float_json_rejected(self):
        for literal in ('1.25','1e10000','1e-10000','NaN','Infinity','-Infinity'):
            with self.subTest(literal=literal),self.assertRaises(WireError):strict_json('{"v":'+literal+'}')
    def test_deep_json_rejected(self):
        with self.assertRaises(WireError):strict_json('{"v":'+'['*32+'0'+']'*32+'}')
    def test_large_json_rejected(self):
        with self.assertRaises(WireError):strict_json('{"body":"'+'x'*48001+'"}')
    def test_invalid_utf8(self):
        with self.assertRaises(WireError):strict_json(b'\xff')
    def test_root_list_disallowed(self):
        with self.assertRaises(WireError):strict_json('[1]')
    def test_decimal_small_nonzero_survives(self):self.assertTrue(exact_quantity('1e-100','J')!=0)
    def test_decimal_loses_no_mantissa(self):self.assertEqual(str(exact_quantity('1.234567890123456789','J')),'1.234567890123456789')
    def test_large_exponent_rejected(self):
        for v in ('1e+999','1e-999','NaN','1.0.2'):
            with self.subTest(v=v),self.assertRaises(WireError):exact_quantity(v,'J')
    def test_units_required(self):
        with self.assertRaises(WireError):exact_quantity('1.2','madeup')
    def test_hash_stable(self):self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
    def test_canonical_rejects_float_nan(self):
        with self.assertRaises(WireError):canonical_json({'a':float('nan')})
    def test_one_based_ontology(self):
        self.assertTrue(HSN.fullmatch('H12.S12.N12'))
        self.assertFalse(HSN.fullmatch('H00.S01.N01'))

class TestCatalog(unittest.TestCase):
    def setUp(self):self.c=CapabilityCatalog()
    def test_catalog_contains_core(self):
        self.assertGreaterEqual(self.c.count,30)
        for x in ('uws','atlas-one','noosphere','atlas-labs-v32','swarmchat','openai-agents'):
            self.c.get(x)
    def test_restricted_licenses_not_vendored(self):
        for x in ('n8n','dify'):
            self.assertEqual(self.c.get(x)['strategy'],'DO_NOT_VENDOR')
    def test_private_broker_locator_not_exported(self):
        s=self.c.get('swarmchat')
        self.assertEqual(s['upstream'],'ACCOUNT_PRIVATE_WORK_BROKER_REFERENCE_WITHHELD')
        self.assertNotIn('.chatgpt.site',json.dumps(self.c._entries))
    def test_source_only_metadata(self):
        self.assertTrue(all(x['host_state']=='NOT_HOST_VERIFIED' for x in self.c._entries.values()))
    def test_catalog_mutation_safe(self):
        x=self.c.get('n8n');x['name']='X'
        self.assertNotEqual(self.c.get('n8n')['name'],'X')
    def test_catalog_duplicate_rejected(self):
        item=self.c.get('uws')
        with self.assertRaises(WireError):CapabilityCatalog({'schema':'atlas.native.capabilities/v0.1','assets':[item,item]})
    def test_catalog_revision_40_hex(self):
        for x in self.c._entries.values():
            if x['revision'] is not None:self.assertTrue(HEX40.fullmatch(x['revision']))

class TestExperiment(unittest.TestCase):
    def setUp(self):self.engine=NativeSynthesis()
    def test_public_synthetic_prepares_three_inert_outputs(self):
        out=self.engine.prepare_experiment(EX)
        self.assertEqual(out['status'],'SOURCE_PREPARED_ONLY')
        self.assertEqual(out['atlas_one']['state'],'TASK_CANDIDATE_NOT_DISPATCHED')
        self.assertEqual(out['swarmchat']['state'],'WORK_PREVIEW_NOT_POSTED')
        self.assertEqual(out['alexandria']['state'],'GRAPH_CANDIDATE_NOT_WRITTEN')
        self.assertFalse(out['canonical'])
        self.assertEqual(out['permission']['read_rights'],'NOT_CHECKED')
        self.assertFalse(out['evidence']['source']['source_contents_read'])
    def test_request_id_replay_is_idempotent(self):
        self.assertEqual(self.engine.prepare_experiment(EX)['local_receipt']['status'],'NEW_LOCAL_ONLY')
        self.assertEqual(self.engine.prepare_experiment(EX)['local_receipt']['status'],'DEDUPLICATED_LOCAL_ONLY')
        self.assertEqual(self.engine.journal.count,1)
    def test_conflicting_same_request_id_holds(self):
        self.engine.prepare_experiment(EX)
        self.assertEqual(self.engine.prepare_experiment(changed(**{'claim.hypothesis':'new synthetic hypothesis'}))['status'],'HOLD')
    def test_wrong_edition_holds(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'ontology.edition':'Historical Zero Based'}))['status'],'HOLD')
    def test_overlap_false_friends_rejected(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'ontology.registry_sha256':'0'*64}))['status'],'HOLD')
    def test_H00_rejected(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'ontology.address':'H00.S01.N01'}))['status'],'HOLD')
    def test_H12_accepted_syntactically(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'ontology.address':'H12.S12.N12'}))['status'],'SOURCE_PREPARED_ONLY')
    def test_private_origin_suppressed(self):
        for private in ('PALACE','BRAIN','WORK','PLAY','SOCIAL','QUIET','IMAGINE','DREAM'):
            with self.subTest(private=private):
                res=self.engine.prepare_experiment(changed(**{'source.origin_mode':private}))
                self.assertEqual(res['status'],'HOLD')
                self.assertEqual(res['source_count'],0)
                self.assertIsNone(res['payload'])
    def test_public_claim_does_not_grant_rights(self):
        res=self.engine.prepare_experiment(EX)
        self.assertEqual(res['permission']['host_principal'],'NOT_ATTESTED')
        self.assertEqual(res['permission']['return_rights'],'NOT_CHECKED')
    def test_non_public_visibility_holds(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'source.visibility':'PRIVATE'}))['status'],'HOLD')
    def test_mismatched_source_commit_holds(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'source.commit':'a'*40}))['status'],'HOLD')
    def test_invalid_blob_sha_holds(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'source.blob_sha':'0'*39}))['status'],'HOLD')
    def test_source_url_canonical_segments_required(self):
        valid=EX['source']['url']; prefix=valid.rsplit('/',1)[0]
        for relative in ('../unknown.md','./source.md','a//b.md','a/../b.md',
                         'a/./b.md','a//../b.md'):
            with self.subTest(path=relative):
                x=changed(**{'source.url':prefix+'/'+relative})
                r=self.engine.prepare_experiment(x)
                self.assertEqual(r['status'],'HOLD')
                self.assertIsNone(r['payload'])
                self.assertEqual(r['source_count'],0)
        self.assertEqual(self.engine.prepare_experiment(EX)['status'],
                         'SOURCE_PREPARED_ONLY')

    def test_unlicensed_fork_not_experiment_source(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'source.asset_id':'n8n'}))['status'],'HOLD')
    def test_unknown_field_no_source_fingerprint(self):
        x=copy.deepcopy(EX);x['source']['privateMemo']='DO_NOT_ECHO'
        res=self.engine.prepare_experiment(x)
        self.assertEqual(res['status'],'HOLD')
        self.assertNotIn('DO_NOT_ECHO',json.dumps(res))
    def test_unverified_physical_result_rejected(self):
        self.assertEqual(self.engine.prepare_experiment(changed(**{'model.kind':'PHYSICAL_MEASUREMENT'}))['status'],'HOLD')
    def test_design_only_requires_zero_numbers(self):
        x=changed(**{'model.kind':'DESIGN_ONLY','model.uncertainty_status':'NOT_EVALUATED','model.quantities':[]})
        self.assertEqual(self.engine.prepare_experiment(x)['status'],'SOURCE_PREPARED_ONLY')
        self.assertEqual(self.engine.prepare_experiment(changed(**{'model.kind':'DESIGN_ONLY'}))['status'],'HOLD')
    def test_float_number_rejected(self):
        x=changed(**{'model.quantities':[{'name':'x','value':1.2,'unit':'J'}]})
        self.assertEqual(self.engine.prepare_experiment(x)['status'],'HOLD')
    def test_mutation_does_not_affect_original(self):
        x=copy.deepcopy(EX);snap=copy.deepcopy(x);self.engine.prepare_experiment(x)
        self.assertEqual(x,snap)
    def test_false_claim_kind_not_promoted(self):
        r=self.engine.prepare_experiment(EX)
        self.assertFalse(r['alexandria']['same_as']);self.assertFalse(r['evidence']['claim']['peer_reviewed'])
    def test_large_private_data_not_logged(self):
        x=copy.deepcopy(EX);x['claim']['hypothesis']='x'*900
        r=self.engine.prepare_experiment(x)
        self.assertEqual(r['status'],'HOLD');self.assertNotIn('x'*100,json.dumps(r))

class TestFusion(unittest.TestCase):
    def setUp(self):self.e=NativeSynthesis()
    def test_candidate_requires_two_distinct_sources(self):
        r=self.e.propose_fusion(FUS)
        self.assertEqual(r['status'],'CROSS_DOMAIN_REVIEW_CANDIDATE')
        self.assertEqual(r['source_count'],2)
        self.assertFalse(r['causal_verified'])
    def test_duplicate_sources_fail(self):
        x=copy.deepcopy(FUS);x['sources'][1]['source']=copy.deepcopy(x['sources'][0]['source'])
        self.assertEqual(self.e.propose_fusion(x)['status'],'HOLD')
    def test_same_lab_not_cross_domain(self):
        x=copy.deepcopy(FUS);x['sources'][1]['lab_id']='fusion'
        self.assertEqual(self.e.propose_fusion(x)['status'],'HOLD')
    def test_missing_alternative_holds(self):
        x=copy.deepcopy(FUS);x['alternatives']=[]
        self.assertEqual(self.e.propose_fusion(x)['status'],'HOLD')
    def test_fusion_no_publication(self):
        r=self.e.propose_fusion(FUS)
        self.assertFalse(r['swarmchat_posted']);self.assertFalse(r['alexandria_written'])
        self.assertFalse(r['atlas_one_dispatch']);self.assertFalse(r['scientifically_validated'])

class TestJournal(unittest.TestCase):
    def test_replay(self):
        j=CandidateJournal();a=j.append('x','op',{'status':'PUBLIC_ONLY'});b=j.append('x','op',{'status':'PUBLIC_ONLY'})
        self.assertEqual(a['seq'],b['seq']);self.assertEqual(j.count,1);self.assertTrue(j.verify())
    def test_changed_same_request_holds(self):
        j=CandidateJournal();j.append('x','op',{'a':1})
        with self.assertRaises(WireError):j.append('x','op',{'a':2})
    def test_forbidden_private_field_holds(self):
        with self.assertRaises(WireError):CandidateJournal().append('x','op',{'secret':'leak'})
    def test_concurrent_duplicate_one_receipt(self):
        j=CandidateJournal();out=[]
        ts=[threading.Thread(target=lambda:out.append(j.append('key','op',{'v':1}))) for i in range(20)]
        for t in ts:t.start()
        for t in ts:t.join()
        self.assertEqual(j.count,1);self.assertEqual(len(out),20);self.assertTrue(j.verify())
    def test_chain_tamper_detected(self):
        j=CandidateJournal();j.append('one','op',{'v':1});j.append('two','op',{'v':2})
        j._entries[0]['previous_sha256']='x'*64
        self.assertFalse(j.verify())

class TestHostFake(unittest.TestCase):
    def setUp(self):
        self.a=SyntheticHostAuthority(b'X'*32)
        self.params=('tenant-A','human-A','room-work','read','sha-source-A')
        self.token=self.a.issue(*self.params,deadline=200)
    def test_correct_grant(self):self.assertTrue(self.a.check(self.token,*self.params,now=100))
    def test_wrong_scope(self):
        for index in range(5):
            x=list(self.params);x[index]='other'
            self.assertFalse(self.a.check(self.token,*x,now=100))
    def test_withdraw_at_return(self):
        self.assertTrue(self.a.check(self.token,*self.params,now=100))
        self.a.withdraw(*self.params)
        self.assertFalse(self.a.check(self.token,*self.params,now=100))
    def test_regrant_does_not_resurrect_old(self):
        self.a.withdraw(*self.params);new=self.a.issue(*self.params,deadline=200)
        self.assertFalse(self.a.check(self.token,*self.params,now=100))
        self.assertTrue(self.a.check(new,*self.params,now=100))
    def test_expiration(self):self.assertFalse(self.a.check(self.token,*self.params,now=200))
    def test_token_forgery(self):self.assertFalse(self.a.check(self.token[:-1]+'0',*self.params,now=100))
    def test_unavailable_host_fails_closed(self):self.assertFalse(UnavailableAuthority().return_fence({},None,100))

class TestResponses(unittest.TestCase):
    def test_strict_tool_specs(self):
        for t in function_tools():
            self.assertTrue(t['strict']);self.assertEqual(t['type'],'function')
            self.assertEqual(set(t['parameters']['required']),set(t['parameters']['properties']))
            self.assertFalse(t['parameters']['additionalProperties'])
    def test_offline_status_tool_call(self):
        r=handle_function_call({'type':'function_call','name':'atlas_native_readiness','call_id':'call-1',
                                'arguments':json.dumps({'query':'status'})})
        self.assertEqual(r['type'],'function_call_output');self.assertEqual(r['call_id'],'call-1')
        self.assertEqual(json.loads(r['output'])['provider_calls'],0)
    def test_packet_source_only(self):
        r=handle_function_call({'type':'function_call','name':'atlas_native_experiment','call_id':'call-2',
                                'arguments':json.dumps({'packet_json':json.dumps(EX)})})
        self.assertEqual(json.loads(r['output'])['status'],'SOURCE_PREPARED_ONLY')
    def test_model_cannot_call_undeclared_function(self):
        r=handle_function_call({'type':'function_call','name':'start_uws_shell','call_id':'call-3',
                                'arguments':'{}'})
        self.assertEqual(json.loads(r['output'])['status'],'HOLD')
    def test_model_cannot_force_tool_args(self):
        r=handle_function_call({'type':'function_call','name':'atlas_native_catalog','call_id':'call-4',
                                'arguments':'{"family":"all","host_approved":true}'})
        self.assertEqual(json.loads(r['output'])['status'],'HOLD')
    def test_duplicate_model_keys_hold(self):
        r=handle_function_call({'type':'function_call','name':'atlas_native_readiness','call_id':'call-5',
                                'arguments':'{"query":"status","query":"deploy"}'})
        self.assertEqual(json.loads(r['output'])['status'],'HOLD')
    def test_invalid_call_id_fails_before_reply(self):
        with self.assertRaises(WireError):handle_function_call({'type':'function_call','name':'atlas_native_readiness','arguments':'{}'})

if __name__=='__main__':unittest.main()
