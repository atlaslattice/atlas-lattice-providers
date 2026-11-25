"""HOLD-first source-only triage for the existing Noosphere PUBLIC registry.

Designed for `registry/public_repo_inventory_2026-11-22.json` at Git blob
8c03e455a45971f3be8782095c748f64416dc114. No automatic fetching,
ontology mapping, license inference, source code ingestion, or private rows.
"""
from __future__ import annotations
import re
import json
import unicodedata
from .wire import WireError

REGISTRY_SCHEMA = 'atlas.public-repository-registry/v0.1'
PUBLIC_REPO = re.compile(r'^atlaslattice/[A-Za-z0-9_.-]{1,100}$')
PUBLIC_REPO_URL = re.compile(r'^https://github\.com/atlaslattice/[A-Za-z0-9_.-]{1,100}$')
# NAME hints only. Not accepted source identities, reviewed semantics, or canon.
HINTS={
    'atlas-lattice-providers':'provider-candidate',
    'Atlas-Intelligence':'atlas-one-candidate',
    'noosphere-archive':'registry-candidate',
    'continuum-os':'alexandria-candidate',
    'manus-artifacts':'archive-candidate',
    'sheldonbrain-rag-api':'memory-candidate',
    'uws':'workspace-candidate',
    'open-regenerative-compute-standard':'science-candidate',
    'element-145':'ontology-candidate',
    'A2A':'upstream-protocol-reference',
    'langchain':'upstream-agent-reference',
    'OpenHands':'upstream-developer-reference',
    'browser-use':'upstream-browser-reference',
    'dify':'restricted-license-reference',
    'n8n':'restricted-license-reference',
    'three.js':'3d-upstream-reference',
    'godot':'3d-upstream-reference',
}

def triage_public_inventory(value):
    """All-or-nothing metadata-only triage; refuses mixed/private inventory."""
    try:
        if type(value) in (str,bytes):
            if type(value) is bytes:
                if len(value)>500_000:raise WireError('INVALID_REGISTRY')
                value=value.decode('utf-8')
            if len(value.encode('utf-8'))>500_000:raise WireError('INVALID_REGISTRY')
            def pairs_hook(pairs):
                result={};seen=set()
                for k,v in pairs:
                    nk=unicodedata.normalize('NFC',k)
                    if nk in seen:raise WireError('INVALID_REGISTRY')
                    seen.add(nk);result[k]=v
                return result
            def reject_num(_):raise WireError('INVALID_REGISTRY')
            source=json.loads(value,object_pairs_hook=pairs_hook,
                              parse_float=reject_num,parse_constant=reject_num)
        else:
            source=value
        if type(source) is not dict or source.get('schema')!=REGISTRY_SCHEMA:
            raise WireError('INVALID_REGISTRY')
        if source.get('public_only') is not True or type(source.get('records')) is not list:
            raise WireError('INVALID_REGISTRY')
        rows=source['records']
        if not rows or len(rows)>500:raise WireError('INVALID_REGISTRY')
        if type(source.get('records_count')) is not int or source['records_count'] != len(rows):
            raise WireError('INVALID_REGISTRY')
        if type(source.get('excluded_nonpublic_count')) is not int or source['excluded_nonpublic_count']<0:
            raise WireError('INVALID_REGISTRY')
        out=[];seen=set();fork_hints=0
        for row in rows:
            if type(row) is not dict or row.get('visibility')!='public':
                raise WireError('NOT_PUBLIC')
            repo=row.get('repo_full_name');url=row.get('url');id=row.get('repository_id')
            if (type(repo) is not str or not PUBLIC_REPO.fullmatch(repo)
                    or type(url) is not str or not PUBLIC_REPO_URL.fullmatch(url)
                    or url!='https://github.com/'+repo
                    or type(id) is not str or not id.isdecimal()
                    or repo in seen):
                raise WireError('INVALID_REGISTRY')
            seen.add(repo)
            if row.get('readiness')!='HOLD_FOR_SOURCE_AND_RIGHTS_REVIEW' or row.get('canon_status')!='NOT_CANON':
                raise WireError('FALSE_AUTHORITY')
            if row.get('sphere144_tags')!=[] or row.get('related_core_repos')!=[]:
                raise WireError('UNREVIEWED_SEMANTICS')
            hint=HINTS.get(repo.split('/',1)[1],'UNCLASSIFIED_NAME_ONLY')
            if hint.startswith('upstream-'):fork_hints+=1
            out.append({'repo_full_name':repo,'url':url,'name_hint':hint,
                        'source_review':'NOT_PERFORMED','rights':'NOT_VERIFIED',
                        'semantic_mapping':'NONE','host_integration':'NOT_VERIFIED'})
        return {'status':'PUBLIC_METADATA_TRIAGE_ONLY','records_count':len(out),
                'excluded_nonpublic_count':source['excluded_nonpublic_count'],
                'known_name_hint_count':len(out)-sum(x['name_hint']=='UNCLASSIFIED_NAME_ONLY' for x in out),
                'upstream_name_hints':fork_hints,
                'source_registry_blob_sha1':'8c03e455a45971f3be8782095c748f64416dc114',
                'public_repo_names':[r['repo_full_name'] for r in out],
                'source_reviewed_rows':0,'host_integrated_rows':0,
                'private_records_ever_copied':0,'canon_promotions':0}
    except (WireError,TypeError,KeyError,ValueError,AttributeError,UnicodeError,RecursionError):
        return {'status':'HOLD','records_count':0,'public_repo_names':[],
                'private_records_ever_copied':0,'canon_promotions':0}
