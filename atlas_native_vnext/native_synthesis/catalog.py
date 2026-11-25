"""Version-pinned discovery. Repository visibility or license label is not trust.

Catalog entries are *instructions for review*, not package imports. No network,
no subprocesses, no transitive dependency installation or automatic tool calls.
"""
from __future__ import annotations
from importlib import resources
import json
from .wire import WireError, IDENT, HEX40, clean_text, keys_exact

ALLOWED_STATES = {'SOURCE_PINNED', 'REVIEW_LICENSE', 'REVIEW_SECURITY', 'HOLD_SOURCE', 'HOST_GATED'}
ALLOWED_APPROACH = {'WRAP_READ_ONLY', 'REVIEW_ONLY', 'OPTIONAL_PLUGIN', 'DO_NOT_VENDOR', 'HOST_INTEGRATION'}

class CapabilityCatalog:
    def __init__(self, obj=None):
        if obj is None:
            raw = resources.files('native_synthesis').joinpath('catalog.json').read_text(encoding='utf-8')
            obj = json.loads(raw)
        keys_exact(obj, {'schema', 'assets'})
        if obj['schema'] != 'atlas.native.capabilities/v0.1' or type(obj['assets']) is not list:
            raise WireError('INVALID_CATALOG')
        entries = {}
        for item in obj['assets']:
            keys_exact(item, {'id','name','family','upstream','local_ref','revision','license','license_gate','strategy','state','proof','host_state'})
            aid = item['id']
            if type(aid) is not str or not IDENT.fullmatch(aid) or aid in entries:
                raise WireError('INVALID_CATALOG')
            for x in ('name','family','upstream','local_ref','license','license_gate','proof','host_state'):
                clean_text(item[x], 400)
            if item['state'] not in ALLOWED_STATES or item['strategy'] not in ALLOWED_APPROACH:
                raise WireError('INVALID_CATALOG')
            if item['revision'] is not None and not (type(item['revision']) is str and HEX40.fullmatch(item['revision'])):
                raise WireError('INVALID_CATALOG')
            entries[aid] = item.copy()
        self._entries = entries

    def list(self, family='all'):
        if type(family) is not str or len(family) > 60: raise WireError('INVALID_QUERY')
        return [{k:v for k,v in x.items() if k not in ('proof',)} for x in self._entries.values()
                if family == 'all' or x['family'] == family]

    def get(self, asset_id):
        if type(asset_id) is not str or asset_id not in self._entries:
            raise WireError('NOT_FOUND')
        return self._entries[asset_id].copy()

    @property
    def count(self):
        return len(self._entries)
