"""Fail-closed wire format. No other package or network dependency.

Numbers in scientific fields MUST be exact decimal strings with declared units.
The strict JSON parser rejects all floating-point JSON literals to avoid
implicit overflow, underflow and scientific quantization. Original spelling
of ordinary JSON object keys is preserved; NFC-equivalent duplicates HOLD.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
import unicodedata

MAX_BYTES = 48_000
MAX_DEPTH = 14
MAX_FIELDS = 150
MAX_DECIMAL_DIGITS = 42
HEX40 = re.compile(r'^[0-9a-f]{40}$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HSN = re.compile(r'^H(0[1-9]|1[0-2])\.S(0[1-9]|1[0-2])\.N(0[1-9]|1[0-2])$')
IDENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:\-]{0,79}$')
REPO_URI = re.compile(r'^https://github\.com/atlaslattice/[A-Za-z0-9_.-]+/blob/[0-9a-f]{40}/[A-Za-z0-9_./-]+$')
DECIMAL_LITERAL = re.compile(r'^[+-]?(?:\d+)(?:\.\d+)?(?:[eE][+-]?\d{1,3})?$')

class WireError(ValueError):
    """Never attach caller payloads to errors; callers receive a generic hold."""


def _object_pairs(pairs):
    obj = {}
    nfc = set()
    for key, value in pairs:
        normalized = unicodedata.normalize('NFC', key)
        if normalized in nfc:
            raise WireError('INVALID_WIRE')
        nfc.add(normalized)
        obj[key] = value
    return obj


def _no_float(_value):
    raise WireError('INVALID_WIRE')


def _no_constant(_value):
    raise WireError('INVALID_WIRE')


def _walk(v, depth=0, count=None):
    if count is None: count = [0]
    if depth > MAX_DEPTH:
        raise WireError('INVALID_WIRE')
    count[0] += 1
    if count[0] > MAX_FIELDS:
        raise WireError('INVALID_WIRE')
    if type(v) is dict:
        seen_normalized = set()
        for k, x in v.items():
            if type(k) is not str or len(k) > 100:
                raise WireError('INVALID_WIRE')
            kn = unicodedata.normalize('NFC', k)
            if kn in seen_normalized:
                raise WireError('INVALID_WIRE')
            seen_normalized.add(kn)
            _walk(x, depth+1, count)
    elif type(v) is list:
        if len(v) > 64: raise WireError('INVALID_WIRE')
        for x in v: _walk(x, depth+1, count)
    elif type(v) is str:
        if len(v) > 16_000: raise WireError('INVALID_WIRE')
        try: v.encode('utf-8')
        except UnicodeEncodeError as exc: raise WireError('INVALID_WIRE') from exc
    elif v is None or type(v) is bool or type(v) is int:
        if type(v) is int and abs(v) > 10**18: raise WireError('INVALID_WIRE')
    else:
        raise WireError('INVALID_WIRE')
    return v


def strict_json(value):
    if type(value) is bytes:
        if len(value) > MAX_BYTES: raise WireError('INVALID_WIRE')
        try: value = value.decode('utf-8')
        except UnicodeDecodeError as exc: raise WireError('INVALID_WIRE') from exc
    if type(value) is str:
        try: raw = value.encode('utf-8')
        except UnicodeEncodeError as exc: raise WireError('INVALID_WIRE') from exc
        if len(raw) > MAX_BYTES: raise WireError('INVALID_WIRE')
        try:
            obj = json.loads(value, object_pairs_hook=_object_pairs, parse_float=_no_float,
                             parse_constant=_no_constant)
        except (ValueError, TypeError, RecursionError) as exc:
            raise WireError('INVALID_WIRE') from exc
    else:
        obj = value
    _walk(obj)
    if type(obj) is not dict: raise WireError('INVALID_WIRE')
    if len(canonical_json(obj)) > MAX_BYTES: raise WireError('INVALID_WIRE')
    return obj


def canonical_json(obj):
    _walk(obj)
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                          allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeEncodeError, RecursionError) as exc:
        raise WireError('INVALID_WIRE') from exc


def digest(obj):
    return sha256(canonical_json(obj)).hexdigest()


def keys_exact(o, keys):
    if type(o) is not dict or set(o) != set(keys):
        raise WireError('INVALID_WIRE')


def clean_text(v, limit=250):
    if type(v) is not str or not v.strip() or len(v) > limit:
        raise WireError('INVALID_WIRE')
    if any(ord(c) < 32 for c in v): raise WireError('INVALID_WIRE')
    return v


def exact_quantity(text, unit):
    """No binary float: decimals are accepted as strings and units mandatory."""
    clean_text(text, 80)
    clean_text(unit, 24)
    if not DECIMAL_LITERAL.fullmatch(text): raise WireError('INVALID_QUANTITY')
    try: d = Decimal(text)
    except InvalidOperation as exc: raise WireError('INVALID_QUANTITY') from exc
    if not d.is_finite() or len(d.as_tuple().digits) > MAX_DECIMAL_DIGITS:
        raise WireError('INVALID_QUANTITY')
    if abs(d.adjusted()) > 250 and d != 0:
        raise WireError('INVALID_QUANTITY')
    if unit not in {'J', 'eV', 'kg', 'g', 'm', 's', 'Hz', 'K', 'Pa', 'W', 'MW', 'L',
                    '1', '%', 'm/s', 'n/s', 'count', 'mol', 'A', 'V'}:
        raise WireError('INVALID_QUANTITY')
    return d
