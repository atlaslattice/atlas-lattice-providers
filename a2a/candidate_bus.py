"""Atlas A2A candidate-only in-memory message-bus contract.

No hosted communication, identity authentication, work delegation, provider calls,
CANON, deployment, or rights grant. The API deliberately NEVER delivers a message.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
import threading
from typing import Any

SCHEMA = 'atlas.a2a.candidate-envelope/v0.1'
PRIVATE = frozenset({'PLAY', 'SOCIAL', 'QUIET', 'IMAGINE', 'DREAM', 'BRAIN', 'PALACE', 'HABITAT', 'NO_HARVEST'})
DANGER = ('merged mind', 'shared consciousness', 'identity fusion', 'fuse identities',
          'merge all children', 'merge all minds', 'one shared mind')
MAX_BYTES = 16 * 1024
RECEIPT_SCHEMA = 'atlas.a2a.prepared-receipt/v0.1'


def _valid_id(x: object) -> bool:
    return type(x) is str and bool(re.fullmatch(r'[A-Za-z0-9._:-]{1,100}', x))


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('DUPLICATE_JSON_KEY')
        out[k] = v
    return out


def _reject_const(x):
    raise ValueError('NONFINITE_JSON_CONSTANT')


def _json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def parse(raw: bytes | str) -> dict[str, Any]:
    if type(raw) not in (str, bytes):
        raise TypeError('EXPECTED_JSON_BYTES_OR_TEXT')
    data = raw.encode('utf-8') if type(raw) is str else raw
    if len(data) > MAX_BYTES:
        raise ValueError('ENVELOPE_SIZE_LIMIT')
    try:
        p = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs,
                       parse_constant=_reject_const)
    except UnicodeDecodeError as exc:
        raise ValueError('INVALID_UTF8') from exc
    if type(p) is not dict:
        raise ValueError('EXPECTED_OBJECT')
    return p


def validate(p: dict[str, Any]) -> tuple[str, ...]:
    """Validation is syntactic/candidate-only, NEVER an authentication result."""
    if type(p) is not dict:
        return ('EXPECTED_OBJECT',)
    if p.get('mode') != 'WORK' or p.get('no_harvest') is True:
        return ('PRIVACY_SCOPE_HOLD',)
    failures = []
    if p.get('schema') != SCHEMA:
        failures.append('SCHEMA_MISMATCH')
    required = ('tenant', 'room', 'sender', 'recipient', 'request_id',
                'logical_operation_id', 'source_ref')
    for k in required:
        if not _valid_id(p.get(k)):
            failures.append('INVALID_' + k.upper())
    if all(_valid_id(p.get(k)) for k in ('sender', 'recipient')) and p['sender'] == p['recipient']:
        failures.append('NO_SELF_IMPERSONATION')
    if type(p.get('sequence')) is not int or p['sequence'] < 1:
        failures.append('INVALID_SEQUENCE')
    if p.get('identity_scope') != 'DISTINCT_PARTICIPANTS':
        failures.append('IDENTITY_FUSION_HOLD')
    if p.get('authority') != 'none' or p.get('canon') is not False or p.get('deployment') is not False:
        failures.append('PROMOTION_HOLD')
    if p.get('intent') != 'candidate_message':
        failures.append('NON_MESSAGE_INTENT_HOLD')
    if p.get('host_attestation') != 'NONE' or p.get('rights_attestation') != 'NONE':
        failures.append('UNTRUSTED_ATTESTATION_HOLD')
    if type(p.get('body')) not in (str, dict, list):
        failures.append('INVALID_BODY')
    if type(p.get('dissent_refs')) is not list or not all(_valid_id(x) for x in p['dissent_refs']):
        failures.append('INVALID_DISSENT_REFS')
    if type(p.get('source_refs')) is not list or not all(_valid_id(x) for x in p['source_refs']):
        failures.append('INVALID_SOURCE_REFS')
    if type(p.get('body')) in (str, dict, list):
        try:
            serialized = _json(p['body']).decode('utf-8').casefold()
        except (ValueError, TypeError):
            failures.append('NONFINITE_OR_UNSERIALIZABLE_BODY')
        else:
            if any(x in serialized for x in DANGER):
                failures.append('IDENTITY_FUSION_HOLD')
    try:
        if len(_json(p)) > MAX_BYTES:
            failures.append('ENVELOPE_SIZE_LIMIT')
    except (ValueError, TypeError):
        failures.append('INVALID_JSON_PAYLOAD')
    return tuple(dict.fromkeys(failures))


@dataclass(frozen=True)
class Receipt:
    disposition: str
    source_sha256: str
    reasons: tuple[str, ...]
    receipt_id: str
    logical_scope: str
    stored_candidate: bool
    authority_effect: str = 'NONE'
    message_delivered: bool = False
    host_authenticated: bool = False
    canon_adopted: bool = False

    def as_dict(self):
        return {'schema': RECEIPT_SCHEMA, 'disposition': self.disposition,
                'source_sha256': self.source_sha256, 'reasons': list(self.reasons),
                'receipt_id': self.receipt_id, 'logical_scope': self.logical_scope,
                'stored_candidate': self.stored_candidate, 'authority_effect': self.authority_effect,
                'message_delivered': self.message_delivered, 'host_authenticated': self.host_authenticated,
                'canon_adopted': self.canon_adopted}


class CandidateBus:
    """Local-only proof; no sent-message or identity service exists here."""
    def __init__(self):
        self._mutex = threading.Lock()
        self._by_request = {}
        self._by_logical = {}
        self._last_sequence = {}
        self._receipts = []

    @property
    def receipts(self) -> tuple[dict[str, Any], ...]:
        with self._mutex:
            return tuple(x.as_dict() for x in self._receipts)

    def prepare(self, p: dict[str, Any] | str | bytes) -> dict[str, Any]:
        # Exact raw source preserved by digest; never return private content.
        if type(p) is dict:
            try:
                raw = _json(p)
            except (TypeError, ValueError):
                raw = b'<non-json-dict>'
        elif type(p) is str:
            raw = p.encode('utf-8')
        elif type(p) is bytes:
            raw = p
        else:
            raise TypeError('EXPECTED_DICT_OR_JSON')
        digest = sha256(raw).hexdigest()
        if len(raw) > MAX_BYTES:
            return self._record('HOLD', digest, ('ENVELOPE_SIZE_LIMIT',), 'unknown', False)
        try:
            doc = parse(raw)
        except (TypeError, ValueError):
            return self._record('HOLD', digest, ('INVALID_JSON_ENVELOPE',), 'unknown', False)
        problems = validate(doc)
        if problems:
            return self._record('HOLD', digest, problems, 'unknown', False)
        # Tenant, room, identity and logical operation are separate dimensions.
        request_key = (doc['tenant'], doc['room'], doc['sender'], doc['request_id'])
        logical_key = (doc['tenant'], doc['room'], doc['sender'], doc['logical_operation_id'])
        seq_key = (doc['tenant'], doc['room'], doc['sender'])
        fingerprint = _json(doc)
        with self._mutex:
            if request_key in self._by_request:
                prior_fingerprint, prior_receipt = self._by_request[request_key]
                if prior_fingerprint == fingerprint:
                    return prior_receipt.as_dict() | {'replayed': True}
                return self._record_locked('HOLD', digest, ('REQUEST_ID_COLLISION',), 'unknown', False).as_dict()
            if logical_key in self._by_logical:
                return self._record_locked('HOLD', digest, ('LOGICAL_OPERATION_DUPLICATE',), 'unknown', False).as_dict()
            if doc['sequence'] <= self._last_sequence.get(seq_key, 0):
                return self._record_locked('HOLD', digest, ('NONMONOTONIC_SEQUENCE',), 'unknown', False).as_dict()
            # This is only a local prepared receipt, never a delivery or approval.
            scope = '|'.join(_json(x).decode() for x in (doc['tenant'], doc['room'], doc['sender'], doc['logical_operation_id']))
            receipt = self._record_locked('PREPARED_NOT_DELIVERED', digest, ('HOST_RIGHTS_AND_DELIVERY_NOT_VERIFIED',), scope, True)
            self._by_request[request_key] = (fingerprint, receipt)
            self._by_logical[logical_key] = doc['request_id']
            self._last_sequence[seq_key] = doc['sequence']
            return receipt.as_dict()

    def _record(self, status, digest, reasons, scope, stored):
        with self._mutex:
            return self._record_locked(status, digest, reasons, scope, stored).as_dict()

    def _record_locked(self, status, digest, reasons, scope, stored):
        rid = sha256(_json([len(self._receipts), digest, status])).hexdigest()
        r = Receipt(status, digest, tuple(reasons), rid, scope, stored)
        self._receipts.append(r)
        return r