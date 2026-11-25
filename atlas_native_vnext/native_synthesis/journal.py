"""In-memory, append-only candidate receipt ledger and replay/idempotency test.

A local mutex is NOT a cross-process/remote receiver exactly-once guarantee.
No private text or raw protected source bodies are stored.
"""
from __future__ import annotations
from copy import deepcopy
from threading import RLock
from .wire import WireError, canonical_json, digest, clean_text

GENESIS = '0'*64

class CandidateJournal:
    def __init__(self):
        self._entries=[]
        self._by_key={}
        self._lock=RLock()

    def append(self, request_id, operation, envelope):
        clean_text(request_id,80)
        clean_text(operation,80)
        if type(envelope) is not dict: raise WireError('INVALID_WIRE')
        forbidden={'body','raw','palace','secret','token','source_text','api_key'}
        if set(envelope) & forbidden: raise WireError('INVALID_WIRE')
        fp=digest({'operation':operation,'envelope':envelope})
        with self._lock:
            prior=self._by_key.get(request_id)
            if prior is not None:
                if prior['payload_sha256'] != fp:
                    raise WireError('REQUEST_ID_CONFLICT')
                return {'status':'DEDUPLICATED_LOCAL_ONLY','seq':prior['seq'],
                        'receipt_sha256':prior['receipt_sha256']}
            seq=len(self._entries)+1
            prev=self._entries[-1]['receipt_sha256'] if self._entries else GENESIS
            doc={'seq':seq,'previous_sha256':prev,'request_id':request_id,
                 'operation':operation,'payload_sha256':fp,'status':'SOURCE_PREPARED_ONLY'}
            doc['receipt_sha256']=digest(doc)
            self._entries.append(deepcopy(doc));self._by_key[request_id]=deepcopy(doc)
            return {'status':'NEW_LOCAL_ONLY','seq':seq,'receipt_sha256':doc['receipt_sha256']}

    def verify(self):
        with self._lock:
            prev=GENESIS
            for i, doc in enumerate(self._entries,1):
                if doc['seq']!=i or doc['previous_sha256']!=prev:
                    return False
                expected=digest({k:v for k,v in doc.items() if k!='receipt_sha256'})
                if expected != doc['receipt_sha256']: return False
                prev=expected
            return True

    @property
    def count(self):
        with self._lock: return len(self._entries)

    def report(self):
        with self._lock:
            return {'receipts':len(self._entries),'verified_local_chain':self.verify(),
                    'host_delivery_proven':False,'human_review_proven':False,
                    'head_sha256':self._entries[-1]['receipt_sha256'] if self._entries else GENESIS}
