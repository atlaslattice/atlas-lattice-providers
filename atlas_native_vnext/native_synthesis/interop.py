"""Additive local Atlas Labs v32 <-> Atlas Native candidate crosswalk.

Neither side is an authenticated source, host operation, accepted graph relation,
scientific calibration or real Work delivery.  The independent Atlas Labs v32
prepare function and public catalog are injected only by trusted local tests
or operator code; no network, dynamic imports, provider spends or permissions.
"""
from __future__ import annotations
from hashlib import sha256
import json
from .engine import NativeSynthesis, generic_hold, ARIADNE_SHA
from .wire import WireError, HEX40, HEX64, keys_exact, strict_json

# A syntactic review crosswalk is NOT a semantic ontology crosswalk.
LAB_KIND = {
    'quantum-labs': ('quantum', 'orcs'),
    'physics-mathematics': ('mathematics', 'foundation'),
    'fusion-plasma': ('fusion', 'orcs'),
    'materials-manufacturing': ('materials', 'foundation'),
    'biological-systems': ('biology', 'orcs'),
    'space-aerospace': ('aerospace', 'orcs'),
    'regenerative-infrastructure': ('regenerative', 'orcs'),
    'knowledge-evidence': ('evidence', 'manus'),
}
LAB_FIELDS = {'schema','experiment_id','lab_id','source_id','title','hypothesis',
              'falsifier','model_kind','model_revision','quantities','ontology',
              'origin_mode','source_scope','authority','canon','deployment'}


def prepare_labs_crosswalk(lab_input, labs_prepare, labs_catalog, native=None):
    """Run two separately reviewed *local* source-only preparers and link receipts.

    Required: an explicitly supplied PR61-style `prepare` and `catalog` from a
    local operator-pinned checkout. This injection cannot grant host authority.
    Unpinned/missing ontology and unit changes HOLD; no auto-picked coordinates.
    """
    try:
        x = strict_json(lab_input)
        keys_exact(x, LAB_FIELDS)
        if (x['schema']!='atlas.labs.experiment-candidate/v0.1' or
                x['origin_mode']!='PUBLIC' or x['source_scope']!='PUBLIC_REPORTED' or
                x['canon'] is not False or x['deployment'] is not False or
                x['authority']!='none'):
            raise WireError('INVALID_PUBLIC_LAB')
        kind = x['lab_id']
        if type(kind) is not str or kind not in LAB_KIND:
            raise WireError('LAB_NOT_REVIEWED')
        if type(x['ontology']) is not dict:
            raise WireError('UNPINNED_HSN')
        keys_exact(x['ontology'], {'edition','registry_sha256','coordinate'})
        if (x['ontology']['edition']!='Ariadne v0.7' or
                x['ontology']['registry_sha256']!=ARIADNE_SHA):
            raise WireError('UNPINNED_HSN')
        if not callable(labs_prepare) or not callable(labs_catalog):
            raise WireError('NO_LOCAL_REFERENCE')
        lab_review = labs_prepare(x)
        sources = labs_catalog()
        if (type(sources) is not dict or type(lab_review) is not dict or
                lab_review.get('status')!='PREPARED_SOURCE_ONLY' or
                type(lab_review.get('candidate')) is not dict):
            raise WireError('LAB_REJECTED')
        source=sources.get(kind)
        if type(source) is not dict or set(source)!={'source_id','repo','path',
                'git_blob_sha1','git_commit','review_status'}:
            raise WireError('UNPINNED_SOURCE')
        if source['source_id']!=x['source_id']:
            raise WireError('SOURCE_ID_MISMATCH')
        native_id, asset_id = LAB_KIND[kind]
        engine = native if native is not None else NativeSynthesis()
        catalog = engine.catalog
        asset = catalog.get(asset_id)
        if (type(source['repo']) is not str or source['repo']!=asset['local_ref'] or
                type(source['git_commit']) is not str or
                not HEX40.fullmatch(source['git_commit']) or
                source['git_commit']!=asset['revision'] or
                type(source['git_blob_sha1']) is not str or
                not HEX40.fullmatch(source['git_blob_sha1']) or
                type(source['path']) is not str or not source['path'] or
                source['path'].startswith('/') or '..' in source['path'].split('/')):
            raise WireError('SOURCE_REVISION_MISMATCH')
        source_url='https://github.com/'+source['repo']+'/blob/'+source['git_commit']+'/'+source['path']
        expected_lab_sha=sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,
                                    separators=(',',':')).encode('utf-8')).hexdigest()
        c=lab_review['candidate']
        if type(c.get('atlas_one')) is not dict or type(c.get('swarmchat_work')) is not dict or type(c.get('alexandria')) is not dict:
            raise WireError('INVALID_LAB_HANDOFF')
        p=c['atlas_one'].get('packet')
        if (type(p) is not dict or p.get('experiment_sha256')!=expected_lab_sha or
                p.get('lab_id')!=kind or p.get('experiment_id')!=x['experiment_id'] or
                p.get('host_attested') is not False or p.get('verified_hardware') is not False or
                p.get('canon') is not False or p.get('deployment') is not False or
                p.get('same_as') is not False or p.get('rights_at_return')!='NOT_CHECKED' or
                type(p.get('source_passport')) is not dict or
                p['source_passport'].get('url')!=source_url or
                p['source_passport'].get('git_blob_sha1')!=source['git_blob_sha1'] or
                c['atlas_one'].get('status')!='TASK_INTAKE_CANDIDATE_NOT_DISPATCHED' or
                c['swarmchat_work'].get('status')!='PREPARED_NOT_POSTED' or
                c['swarmchat_work'].get('experiment_sha256')!=expected_lab_sha or
                c['swarmchat_work'].get('source_ref')!=source_url or
                c['alexandria'].get('status')!='GRAPH_EDGE_CANDIDATE_NOT_WRITTEN' or
                c['alexandria'].get('experiment_sha256')!=expected_lab_sha or
                c['alexandria'].get('same_as') is not False):
            raise WireError('INCONSISTENT_LAB_RECEIPTS')
        if p.get('model_kind')!=x['model_kind'] or p.get('model_revision')!=x['model_revision']:
            raise WireError('MODEL_MISMATCH')
        measurements = p.get('measurements')
        if type(measurements) is not list or measurements!=x['quantities']:
            raise WireError('UNREPRODUCED_QUANTITIES')
        # Native units deliberately have a *narrower* meaning than Labs v32.
        # No conversion of bit->count, ratio->1, or other silent metric changes.
        metrics=[]
        for q in measurements:
            if type(q) is not dict or set(q)!={'name','value','unit','uncertainty','evidence_class'}:
                raise WireError('INVALID_QUANTITY')
            if q['evidence_class']!='SYNTHETIC_MODEL_ONLY':
                raise WireError('UNVERIFIED_MEASUREMENTS')
            metrics.append({'name':q['name'],'value':q['value'],'unit':q['unit']})
        if x['model_kind'] not in ('DESIGN_ONLY','SYNTHETIC_MODEL'):
            raise WireError('UNVERIFIED_MEASUREMENTS')
        n_packet={
            'schema':'atlas.native.experiment/v0.1','request_id':x['experiment_id'],
            'lab_id':native_id,
            'source':{'asset_id':asset_id,'url':source_url,'commit':source['git_commit'],
                      'blob_sha':source['git_blob_sha1'],'origin_mode':'PUBLIC','visibility':'PUBLIC'},
            'ontology':{'edition':x['ontology']['edition'],'address':x['ontology']['coordinate'],
                        'registry_sha256':x['ontology']['registry_sha256']},
            'claim':{'hypothesis':x['hypothesis'],'falsifier':x['falsifier'],'dissent_ids':[]},
            'model':{'kind':x['model_kind'],'backend':'ATLAS_LABS_V32_LOCAL_CANDIDATE',
                     'revision':x['model_revision'],'quantities':metrics,
                     'uncertainty_status':'SYNTHETIC_UNCALIBRATED' if metrics else 'NOT_EVALUATED'},
        }
        result=engine.prepare_experiment(n_packet)
        if result.get('status')!='SOURCE_PREPARED_ONLY' or result['permission']['read_rights']!='NOT_CHECKED':
            raise WireError('NATIVE_REJECTED')
        return {
            'status':'LINKED_LOCAL_SOURCE_ONLY',
            'schema':'atlas.native.labs-crosswalk/v0.1',
            'labs_experiment_sha256':expected_lab_sha,
            'native_experiment_sha256':result['source_sha256'],
            'native_local_receipt':result['local_receipt'],
            'atlas_one':'TASK_CANDIDATE_NOT_DISPATCHED',
            'swarmchat':'WORK_PREVIEW_NOT_POSTED',
            'alexandria':'GRAPH_CANDIDATE_NOT_WRITTEN',
            'semantic_mapping':'UNADJUDICATED', 'same_as':False,
            'scientifically_validated':False, 'hardware_verified':False,
            'host_identity_attested':False, 'rights_checked':False,
            'peer_returned':False,'authority_effect':'NONE', 'provider_spend_usd':0,
        }
    except (WireError,ValueError,TypeError,KeyError,AttributeError,OverflowError,UnicodeError,RecursionError):
        return generic_hold()