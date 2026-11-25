"""OpenAI Responses API native function-call envelope adapter.

Uses the published Responses API `function_call` / `function_call_output`
shape. This module NEVER calls the API; client/SDK belongs to the host.
No model-supplied arguments can create authority, enable external tools or post.
"""
from __future__ import annotations
import json
from .engine import NativeSynthesis, generic_hold
from .wire import strict_json, WireError, clean_text

_TOOL_FIELDS = {
    'atlas_native_catalog': ('family', 'List available, reviewed capability candidates by family.'),
    'atlas_native_experiment': ('packet_json', 'Prepare an unposted, public-only Atlas experiment for review.'),
    'atlas_native_fusion': ('packet_json', 'Prepare an unposted cross-domain A+B=C falsifiable candidate.'),
    'atlas_native_readiness': ('query', 'Read the source-only integration status; query must equal status.'),
}

def function_tools():
    """Strict function-tool definitions, flat required fields per OpenAI docs."""
    result=[]
    for name,(field,description) in _TOOL_FIELDS.items():
        result.append({'type':'function','name':name,'description':description,'strict':True,
                       'parameters':{'type':'object','properties':{field:{'type':'string'}},
                                     'required':[field],'additionalProperties':False}})
    return result

def handle_function_call(call, engine=None):
    """Accept only an actual structured Responses `function_call` payload."""
    e=engine or NativeSynthesis()
    if type(call) is not dict: raise WireError('INVALID_CALL')
    callid=call.get('call_id')
    if type(callid) is not str or not callid or len(callid)>120:
        raise WireError('INVALID_CALL')
    try:
        if call.get('type')!='function_call' or call.get('name') not in _TOOL_FIELDS:
            raise WireError('INVALID_CALL')
        name=call['name'];key=_TOOL_FIELDS[name][0]
        obj=strict_json(call.get('arguments'))
        if set(obj)!={key} or type(obj[key]) is not str:
            raise WireError('INVALID_CALL')
        if name=='atlas_native_catalog':
            out={'status':'SOURCE_CATALOG_ONLY','entries':e.catalog.list(obj[key]),
                 'host_proof':False}
        elif name=='atlas_native_readiness':
            out=e.readiness() if obj[key]=='status' else generic_hold()
        elif name=='atlas_native_experiment':
            out=e.prepare_experiment(obj[key])
        elif name=='atlas_native_fusion':
            out=e.propose_fusion(obj[key])
        else:
            out=generic_hold()
    except (ValueError, WireError, TypeError, KeyError):
        out=generic_hold()
    return {'type':'function_call_output','call_id':callid,
            'output':json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':'))}
