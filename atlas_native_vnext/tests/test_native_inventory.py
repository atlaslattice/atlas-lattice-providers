import copy
import json
import unittest
from native_synthesis.inventory import triage_public_inventory

def sample():
    return {'schema':'atlas.public-repository-registry/v0.1','public_only':True,
            'excluded_nonpublic_count':1,'records_count':2,'records':[
              {'repo_full_name':'atlaslattice/A2A','url':'https://github.com/atlaslattice/A2A',
               'repository_id':'1001','visibility':'public',
               'readiness':'HOLD_FOR_SOURCE_AND_RIGHTS_REVIEW','canon_status':'NOT_CANON',
               'sphere144_tags':[],'related_core_repos':[]},
              {'repo_full_name':'atlaslattice/noosphere-archive','url':'https://github.com/atlaslattice/noosphere-archive',
               'repository_id':'1002','visibility':'public',
               'readiness':'HOLD_FOR_SOURCE_AND_RIGHTS_REVIEW','canon_status':'NOT_CANON',
               'sphere144_tags':[],'related_core_repos':[]} ]}
class RegistryTests(unittest.TestCase):
    def test_raw_source_json_accepted(self):
        r=triage_public_inventory(json.dumps(sample()))
        self.assertEqual(r['status'],'PUBLIC_METADATA_TRIAGE_ONLY')
    def test_root_duplicate_json_refused(self):
        self.assertEqual(triage_public_inventory('{"schema":"x","schema":"atlas.public-repository-registry/v0.1"}')['status'],'HOLD')
    def test_public_inventory_accepted_as_metadata_only(self):
        r=triage_public_inventory(sample())
        self.assertEqual(r['status'],'PUBLIC_METADATA_TRIAGE_ONLY')
        self.assertEqual(r['records_count'],2);self.assertEqual(r['host_integrated_rows'],0)
    def test_private_row_refuses_all(self):
        x=sample();x['records'][1]['visibility']='private'
        r=triage_public_inventory(x)
        self.assertEqual(r['status'],'HOLD');self.assertEqual(r['public_repo_names'],[])
    def test_duplicate_row_refuses(self):
        x=sample();x['records'][1]=copy.deepcopy(x['records'][0])
        self.assertEqual(triage_public_inventory(x)['status'],'HOLD')
    def test_self_promoted_canon_refuses(self):
        x=sample();x['records'][0]['canon_status']='RATIFIED'
        self.assertEqual(triage_public_inventory(x)['status'],'HOLD')
    def test_name_heuristics_not_semantics(self):
        r=triage_public_inventory(sample());self.assertEqual(r['source_reviewed_rows'],0)
    def test_source_tags_not_accepted_from_caller(self):
        x=sample();x['records'][0]['sphere144_tags']=['H01']
        self.assertEqual(triage_public_inventory(x)['status'],'HOLD')
    def test_count_mismatch_refuses(self):
        x=sample();x['records_count']=272
        self.assertEqual(triage_public_inventory(x)['status'],'HOLD')
    def test_no_nonpublic_name_on_denial(self):
        x=sample();x['records'][1]['repo_full_name']='atlaslattice/private-secret-thing';x['records'][1]['visibility']='private'
        self.assertNotIn('private-secret-thing',str(triage_public_inventory(x)))
if __name__=='__main__':unittest.main()
