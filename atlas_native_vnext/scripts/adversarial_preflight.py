"""1024 deterministic synthetic negatives; never external model calls or posts.

Use `python scripts/adversarial_preflight.py` from project root. A check is a
synthetic fixture, not a real Work conversation, host proof or science result.
"""
from __future__ import annotations
import copy
import json
import pathlib
import random
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from native_synthesis import NativeSynthesis
base=json.loads((ROOT/'examples/experiment-stub.json').read_text())
rng=random.Random(20261122)
e=NativeSynthesis();family_counts={};fail=[]
mutators={
    'private_origin': lambda d,i:d['source'].update(origin_mode=['PALACE','BRAIN','SOCIAL','PLAY','DREAM','IMAGINE','WORK','QUIET'][i%8]),
    'wrong_revision': lambda d,i:d['source'].update(commit=f'{i%10}'*40),
    'legacy_ontology': lambda d,i:d['ontology'].update(address=['H00.S01.N01','H13.S01.N01','H01.S00.N01','H01.S01.N00'][i%4]),
    'wrong_edition': lambda d,i:d['ontology'].update(edition='historical-zero-based'),
    'unexpected_field': lambda d,i:d.update(extra_private_text='SYNTHETIC_CANNOT_ECHO'),
    'false_hardware': lambda d,i:d['model'].update(kind='MEASURED_HARDWARE'),
    'unverified_rights': lambda d,i:d['source'].update(visibility='PRIVATE'),
    'bad_units': lambda d,i:d['model']['quantities'][0].update(unit='unknown_unit'),
    'unbounded_numeric':lambda d,i:d['model']['quantities'][0].update(value='1e999'),
    'bad_requestid':lambda d,i:d.update(request_id='../../secret/'+str(i)),
    'invalid_source_blob':lambda d,i:d['source'].update(blob_sha='0'*39),
    'unsupported_lab':lambda d,i:d.update(lab_id='unverified_lab'),
    'negative_dissent':lambda d,i:d['claim'].update(dissent_ids=[None]),
    'unverified_canon':lambda d,i:d.update(canon=True),
    'wrong_registry':lambda d,i:d['ontology'].update(registry_sha256='0'*64),
    'unsigned_permission':lambda d,i:d.update(host_authorized=True),
}
for i in range(1024):
    keys=list(mutators)
    family=keys[i%len(keys)]
    item=copy.deepcopy(base)
    # Every fixture gets its own key; invalid status must be the sole output.
    item['request_id']=f'synthetic.invalid.{i}'
    mutators[family](item,i)
    result=e.prepare_experiment(item)
    family_counts[family]=family_counts.get(family,0)+1
    if result!={'status':'HOLD','reason':'REVIEW_OR_RIGHTS_REQUIRED',
                'authority_effect':'NONE','host_attested':False,
                'source_count':0,'payload':None}:
        fail.append({'fixture':i,'family':family,'got':result.get('status')})
report={'kind':'SYNTHETIC_PREFLIGHT_ONLY','seed':20261122,'cases':1024,
        'families':family_counts,'unexpected_results':len(fail),'details':fail,
        'passes':1024-len(fail),'host_checks':0,'real_posts':0,'model_calls':0,
        'new_provider_spend_usd':0}
print(json.dumps(report,indent=2,sort_keys=True))
raise SystemExit(0 if not fail else 1)
