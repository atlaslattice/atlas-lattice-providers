"""Adapter descriptions and safe source-only planning.

Neither actual MCP/A2A/SDK service bindings nor external tool executions are
created here. Host must inject current permission checks and real endpoints.
"""
from __future__ import annotations
import re
from .wire import WireError, IDENT, HEX40, clean_text, keys_exact, strict_json, digest
from .responses import function_tools
from .engine import LAB_FAMILIES, generic_hold

_ALLOWED_PROVIDERS={'github','google_drive','notion','microsoft_graph'}
_QPU_SOLVERS={'qiskit','cirq','openmc','warpx','reefcore'}

def mcp_tools_preview():
    """MCP tool descriptions, not server registration, transport, or rights."""
    return {'status':'MANIFEST_ONLY_NOT_REGISTERED','mcp_version_policy':'NEGOTIATE_ON_HOST',
            'tools':[{'name':t['name'],'description':t['description'],
                      'inputSchema':t['parameters'],
                      'annotations':{'readOnlyHint':True,'destructiveHint':False}}
                     for t in function_tools()],
            'host_auth':'NOT_ATTESTED','endpoint':None}

def a2a_card_preview():
    """Inert A2A skill proposal; not a discoverable authenticated agent card."""
    return {'status':'DRAFT_AGENT_SKILLS_NOT_ADVERTISED',
            'issuer_principal':'NOT_ATTESTED','service_url':None,
            'skills':[{'id':'public_source_intake','name':'Public source candidate review'},
                      {'id':'cross_domain_falsifier','name':'A+B=C with alternatives and falsifier'},
                      {'id':'capability_registry','name':'Versioned open-source inventory'}],
            'push_notifications':False,'external_identity_verified':False,
            'host_authorization':'REQUIRED'}

def uws_read_plan(value):
    """Normalizes a *requested* UWS metadata read, NEVER executes a CLI."""
    try:
        x=strict_json(value)
        keys_exact(x,{'schema','provider','operation','resource','revision'})
        if x['schema']!='atlas.native.uws-plan/v0.1':raise WireError('INVALID_SCHEMA')
        if x['provider'] not in _ALLOWED_PROVIDERS or x['operation']!='source.metadata.read':
            raise WireError('INVALID_PROVIDER')
        if type(x['resource']) is not str or not re.fullmatch(r'[A-Za-z0-9_./:-]{1,160}',x['resource']):
            raise WireError('INVALID_RESOURCE')
        if type(x['revision']) is not str or not HEX40.fullmatch(x['revision']):
            raise WireError('INVALID_REVISION')
        return {'status':'UWS_READ_PLAN_NOT_EXECUTED','provider':x['provider'],
                'resource_sha256':digest({'resource':x['resource']}),
                'source_revision':x['revision'],'trusted_principal':False,
                'permissions_checked':False,'cli_spawned':False,'remote_called':False,
                'provider_spend_usd':0}
    except (WireError,KeyError,TypeError,ValueError):return generic_hold()

def numerical_backend_plan(value):
    """Selects a bounded backend as a proposal. Hardware and real physics stay off."""
    try:
        x=strict_json(value)
        keys_exact(x,{'schema','backend','lab_id','model_revision','evidence_kind','budget_usd'})
        if (x['schema']!='atlas.native.solver-plan/v0.1' or x['backend'] not in _QPU_SOLVERS
                or x['lab_id'] not in LAB_FAMILIES or x['evidence_kind']!='SYNTHETIC'):
            raise WireError('INVALID_SOLVER')
        clean_text(x['model_revision'],100)
        if type(x['budget_usd']) is not int or x['budget_usd']!=0:
            raise WireError('NO_SPEND_GATE')
        if x['backend'] in ('qiskit','cirq') and x['lab_id']!='quantum':
            raise WireError('WRONG_DOMAIN')
        if x['backend'] in ('openmc','warpx') and x['lab_id']!='fusion':
            raise WireError('WRONG_DOMAIN')
        return {'status':'SOLVER_PLAN_NOT_EXECUTED','backend':x['backend'],
                'lab_id':x['lab_id'],'model_revision':x['model_revision'],
                'model_verified':False,'scientific_calibration':False,'physical_hardware':False,
                'provider_called':False,'rights_checked':False,'spend_usd':0,
                'host_permission':'UNVERIFIED'}
    except (WireError,KeyError,TypeError,ValueError):return generic_hold()

def graph_view_plan(value):
    """Neutral typed 3D/2D view payload; not an interactive or hosted scene."""
    try:
        x=strict_json(value)
        keys_exact(x,{'schema','nodes','edges'})
        if x['schema']!='atlas.native.graph-view/v0.1' or type(x['nodes']) is not list or type(x['edges']) is not list:
            raise WireError('INVALID_VIEW')
        if len(x['nodes'])>16 or len(x['edges'])>32:raise WireError('INVALID_VIEW')
        nodes=set()
        for n in x['nodes']:
            keys_exact(n,{'id','kind','edition'})
            if type(n['id']) is not str or not IDENT.fullmatch(n['id']) or n['id'] in nodes:
                raise WireError('INVALID_VIEW')
            if n['kind'] not in ('source','claim','hypothesis','review','lab'):
                raise WireError('INVALID_VIEW')
            if n['edition'] not in ('source-v0.1','Ariadne v0.7'):
                raise WireError('INVALID_VIEW')
            nodes.add(n['id'])
        for edge in x['edges']:
            keys_exact(edge,{'from','to','relation','review_status'})
            if (edge['from'] not in nodes or edge['to'] not in nodes or edge['from']==edge['to']
                or edge['relation'] not in ('SOURCE_OF','PROPOSED_RELATED','REVIEWED_BY')
                or edge['review_status']!='UNREVIEWED'):
                raise WireError('INVALID_VIEW')
        return {'status':'GRAPH_VIEW_SOURCE_ONLY','nodes':len(nodes),'edges':len(x['edges']),
                'source_sha256':digest(x),'scene_created':False,'hosted_3d':False,
                'semantic_edges_accepted':0,'canon':False}
    except (WireError,KeyError,TypeError,ValueError):return generic_hold()
