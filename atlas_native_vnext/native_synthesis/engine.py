"""Atlas-native source-only synthesis kernel.

Novel boundary: typed federated capability inventory + public experiment packet
+ version-scoped A+B=C challenge + deterministic non-delivered handoff set.
It does not import third-party code, call models, execute tools, touch the broker,
write evidence graphs, ratify CANON, authenticate a host or drive lab hardware.
"""
from __future__ import annotations
from hashlib import sha256
import re
from .catalog import CapabilityCatalog
from .journal import CandidateJournal
from .wire import WireError, HEX40, HEX64, HSN, REPO_URI, IDENT, keys_exact, \
                  strict_json, clean_text, exact_quantity, digest, canonical_json

ARIADNE_SHA='07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6'
LAB_FAMILIES={
    'quantum': 'Quantum Computing and QPU Methods',
    'mathematics': 'Mathematics and Numerical Physics',
    'fusion': 'Fusion, Plasma and Neutronics',
    'materials': 'Materials and Manufacturing',
    'biology': 'Biological and Environmental Systems',
    'aerospace': 'Space, Aerospace and Habitats',
    'regenerative': 'Regenerative Infrastructure and Supply Chains',
    'evidence': 'Source Provenance and Causal Evaluation',
}
LAB_SOURCE_ALLOW={'atlas-providers','atlas-labs-v32','orcs','manus', 'foundation', 'element145'}
GENERIC_HOLD={'status':'HOLD','reason':'REVIEW_OR_RIGHTS_REQUIRED',
              'authority_effect':'NONE','host_attested':False,
              'source_count':0,'payload':None}

def generic_hold(): return dict(GENERIC_HOLD)

class NativeSynthesis:
    def __init__(self, catalog=None, journal=None):
        self.catalog=catalog or CapabilityCatalog()
        self.journal=journal or CandidateJournal()

    @staticmethod
    def _source(item, catalog):
        keys_exact(item,{'asset_id','url','commit','blob_sha','origin_mode','visibility'})
        if item['origin_mode']!='PUBLIC' or item['visibility']!='PUBLIC':
            raise WireError('NOT_PUBLIC')
        for k in ('asset_id','url','commit','blob_sha'):
            clean_text(item[k], 400)
        if not (HEX40.fullmatch(item['commit']) and HEX40.fullmatch(item['blob_sha']) and
                REPO_URI.fullmatch(item['url'])):
            raise WireError('SOURCE_NOT_PINNED')
        asset=catalog.get(item['asset_id'])
        if (asset['id'] not in LAB_SOURCE_ALLOW or asset['revision']!=item['commit']
                or not item['url'].startswith('https://github.com/'+asset['local_ref']+'/blob/'+item['commit']+'/')):
            raise WireError('SOURCE_NOT_PINNED')
        if asset['state'] not in ('SOURCE_PINNED','REVIEW_LICENSE'):
            raise WireError('SOURCE_NOT_PINNED')
        # GitHub paths must have unambiguous canonical segments.  Accepting
        # ../, ./ or repeated separators lets a later URL reader fetch a
        # different object than the review packet appears to pin.
        path=item['url'].split('/blob/'+item['commit']+'/',1)[-1]
        if not path or any(part in ('', '.', '..') for part in path.split('/')):
            raise WireError('SOURCE_NOT_PINNED')
        # We validate *structural source pins*; source contents are not fetched here.
        return {'asset_id':asset['id'],'commit':item['commit'], 'blob_sha':item['blob_sha'],
                'source_pointer_sha256':sha256(item['url'].encode()).hexdigest(),
                'source_contents_read':False,'source_rights_verified':False}

    @staticmethod
    def _ontology(o):
        keys_exact(o,{'edition','address','registry_sha256'})
        if (o['edition']!='Ariadne v0.7' or type(o['address']) is not str or
            not HSN.fullmatch(o['address']) or o['registry_sha256']!=ARIADNE_SHA):
            raise WireError('ONTOLOGY_MISMATCH')
        return {'edition':o['edition'],'address':o['address'],
                'registry_sha256':o['registry_sha256'],
                'semantic_mapping':'UNADJUDICATED','same_as':False}

    @staticmethod
    def _claim(c):
        keys_exact(c,{'hypothesis','falsifier','dissent_ids'})
        clean_text(c['hypothesis'],800)
        clean_text(c['falsifier'],800)
        if type(c['dissent_ids']) is not list or len(c['dissent_ids'])>8:
            raise WireError('INVALID_CLAIM')
        if any(type(x) is not str or not IDENT.fullmatch(x) for x in c['dissent_ids']):
            raise WireError('INVALID_CLAIM')
        return {'claim_sha256':digest(c),'dissent_count':len(c['dissent_ids']),
                'falsifier_sha256':sha256(c['falsifier'].encode('utf-8')).hexdigest(),
                'peer_reviewed':False,'authority_effect':'NONE'}

    @staticmethod
    def _model(m):
        keys_exact(m,{'kind','backend','revision','quantities','uncertainty_status'})
        if m['kind'] not in ('DESIGN_ONLY','SYNTHETIC_MODEL'):
            raise WireError('SCIENTIFIC_EVIDENCE_UNVERIFIED')
        clean_text(m['backend'],80);clean_text(m['revision'],100)
        if m['uncertainty_status'] not in ('NOT_EVALUATED','SYNTHETIC_UNCALIBRATED'):
            raise WireError('SCIENTIFIC_EVIDENCE_UNVERIFIED')
        if type(m['quantities']) is not list or len(m['quantities'])>8:
            raise WireError('INVALID_QUANTITY')
        if (m['kind']=='DESIGN_ONLY' and m['quantities']) or (m['kind']=='SYNTHETIC_MODEL' and not m['quantities']):
            raise WireError('INVALID_QUANTITY')
        for v in m['quantities']:
            keys_exact(v,{'name','value','unit'})
            clean_text(v['name'],60)
            exact_quantity(v['value'],v['unit'])
        # Hash the model/quantities rather than advertise as measured science.
        return {'kind':m['kind'],'model_sha256':digest(m),'numeric_records':len(m['quantities']),
                'status':'LOCAL_SOURCE_ONLY','experimentally_validated':False,
                'scientific_uncertainty':m['uncertainty_status']}

    def prepare_experiment(self, value):
        """Public source -> three UNPOSTED candidate envelopes; errors generic."""
        try:
            x=strict_json(value)
            keys_exact(x,{'schema','request_id','lab_id','source','ontology','claim','model'})
            if x['schema']!='atlas.native.experiment/v0.1': raise WireError('INVALID_SCHEMA')
            if type(x['request_id']) is not str or not IDENT.fullmatch(x['request_id']):
                raise WireError('INVALID_REQUEST')
            if x['lab_id'] not in LAB_FAMILIES: raise WireError('UNKNOWN_LAB')
            source=self._source(x['source'],self.catalog)
            ontology=self._ontology(x['ontology'])
            claim=self._claim(x['claim'])
            model=self._model(x['model'])
            public_receipt=digest(x)
            out={
                'status':'SOURCE_PREPARED_ONLY','schema':'atlas.native.handoffs/v0.1',
                'request_id':x['request_id'],'source_sha256':public_receipt,
                'evidence':{'source':source,'ontology':ontology,'claim':claim,'model':model},
                'atlas_one':{'state':'TASK_CANDIDATE_NOT_DISPATCHED','lab':x['lab_id'],
                             'effect':'NONE','source_sha256':public_receipt},
                'swarmchat':{'state':'WORK_PREVIEW_NOT_POSTED','source_sha256':public_receipt,
                             'origin':'PUBLIC_ONLY','room':None,'seq':None,'peer_returned':False},
                'alexandria':{'state':'GRAPH_CANDIDATE_NOT_WRITTEN','source_sha256':public_receipt,
                              'relation':'RELATED_HYPOTHESIS_UNREVIEWED','same_as':False},
                'permission':{'host_principal':'NOT_ATTESTED','read_rights':'NOT_CHECKED',
                              'return_rights':'NOT_CHECKED','authority_effect':'NONE'},
                'publisher_gate':'HUMAN_ROOT_REQUIRED','canonical':False,
                'host_deployed':False,'provider_spend_usd':0,
            }
            jr=self.journal.append(x['request_id'],'prepare_experiment',
                                   {'source_sha256':public_receipt,'lab':x['lab_id']})
            out['local_receipt']=jr
            return out
        except (WireError, KeyError, TypeError, ValueError, AttributeError):
            return generic_hold()

    def propose_fusion(self, value):
        """Novel typed A+B=C hypothesis candidate; no causal claim auto-accepted."""
        try:
            x=strict_json(value)
            keys_exact(x,{'schema','request_id','hypothesis','falsifier','alternatives','sources'})
            if x['schema']!='atlas.native.crossdomain/v0.1':raise WireError('INVALID_SCHEMA')
            if type(x['request_id']) is not str or not IDENT.fullmatch(x['request_id']):
                raise WireError('INVALID_REQUEST')
            clean_text(x['hypothesis'],800);clean_text(x['falsifier'],800)
            if type(x['alternatives']) is not list or not 1<=len(x['alternatives'])<=6:
                raise WireError('INVALID_CLAIM')
            for alt in x['alternatives']:clean_text(alt,250)
            if type(x['sources']) is not list or not 2<=len(x['sources'])<=4:
                raise WireError('INVALID_SOURCE_SET')
            normalized=[]; lab_set=set(); source_set=set()
            for item in x['sources']:
                keys_exact(item,{'lab_id','source'})
                if item['lab_id'] not in LAB_FAMILIES: raise WireError('UNKNOWN_LAB')
                src=self._source(item['source'],self.catalog)
                key=(src['asset_id'],src['commit'],src['blob_sha'])
                if key in source_set:raise WireError('DUPLICATE_SOURCE')
                source_set.add(key);lab_set.add(item['lab_id']);normalized.append(src)
            if len(lab_set)<2: raise WireError('NOT_CROSS_DOMAIN')
            fp=digest(x)
            receipt=self.journal.append(x['request_id'],'propose_fusion',
                                        {'source_sha256':fp,'source_count':len(source_set)})
            return {'status':'CROSS_DOMAIN_REVIEW_CANDIDATE','schema':'atlas.native.crossdomain.result/v0.1',
                    'source_count':len(source_set),'lab_count':len(lab_set),
                    'source_sha256':fp,'falsifier_recorded':True,
                    'alternative_count':len(x['alternatives']),
                    'graph_edge':'RELATED_METHOD_TRANSFER_PROPOSED','same_as':False,
                    'causal_verified':False,'scientifically_validated':False,
                    'all_source_contents_read':False,'peer_verified':False,
                    'authority_effect':'NONE','atlas_one_dispatch':False,
                    'swarmchat_posted':False,'alexandria_written':False,
                    'local_receipt':receipt}
        except (WireError, ValueError, KeyError, TypeError, AttributeError):
            return generic_hold()

    def readiness(self):
        return {'schema':'atlas.native.readiness/v0.1','source_assets':self.catalog.count,
                'laboratory_families':len(LAB_FAMILIES),'openai_responses_adapter':'OFFLINE_ONLY',
                'atlas_one':'NOT_DISPATCHED','swarmchat':'NOT_POSTED',
                'alexandria':'NOT_WRITTEN','uws':'HOST_GATED',
                'qpu':'NOT_CONNECTED','physical_research':'NOT_VALIDATED',
                'real_host_principal':'NOT_AVAILABLE','ci':'NOT_VERIFIED',
                'provider_calls':0,'new_spend_usd':0,'canon':'NOT_RATIFIED',
                'ledger':self.journal.report()}
