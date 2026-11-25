"""Local rights-fence reference. NOT an identity issuer or hosted IAM.

Only a trusted *host* may call issue() in an implementation. This in-memory
class is an executable test fake, not a production substitute for D1 or platform
session binding. It does not authorize an agent to act and exposes no HTTP API.
"""
from __future__ import annotations
from hashlib import sha256
import hmac
import json
import secrets
from threading import RLock
from .wire import WireError, canonical_json, clean_text, strict_json

class SyntheticHostAuthority:
    """Local model for exact-scope, revocable capability + monotonic epoch."""
    def __init__(self, key=None):
        self._key = key or secrets.token_bytes(32)
        if type(self._key) is not bytes or len(self._key) < 32:
            raise ValueError('LOCAL_KEY_INVALID')
        self._lock = RLock()
        self._epochs = {}
        self._issued = set()
        self._last = {}

    @staticmethod
    def _scope(tenant, principal, room, purpose, source):
        for v in (tenant, principal, room, purpose, source): clean_text(v, 120)
        return json.dumps([tenant, principal, room, purpose, source], separators=(',',':'))

    def issue(self, tenant, principal, room, purpose, source, deadline):
        if type(deadline) is not int or deadline <= 0: raise WireError('INVALID_GRANT')
        with self._lock:
            scope = self._scope(tenant, principal, room, purpose, source)
            epoch = self._epochs.get(scope, 0)
            doc = {'tenant':tenant,'principal':principal,'room':room,'purpose':purpose,
                   'source':source,'epoch':epoch,'deadline':deadline}
            raw = canonical_json(doc)
            mac = hmac.new(self._key, raw, 'sha256').hexdigest()
            token = raw.hex()+'.'+mac
            self._issued.add(mac)
            return token

    def check(self, token, tenant, principal, room, purpose, source, now):
        if type(now) is not int or now < 0: return False
        if type(token) is not str or len(token)>4000: return False
        try:
            head, sig = token.split('.', 1)
            raw=bytes.fromhex(head)
            doc=strict_json(raw)
            expected=hmac.new(self._key,raw,'sha256').hexdigest()
            if not hmac.compare_digest(expected,sig): return False
            scope=self._scope(tenant,principal,room,purpose,source)
            with self._lock:
                if sig not in self._issued: return False
                if doc != {'tenant':tenant,'principal':principal,'room':room,
                           'purpose':purpose,'source':source,'epoch':self._epochs.get(scope,0),
                           'deadline':doc.get('deadline')}:
                    return False
                if type(doc.get('deadline')) is not int or now>=doc['deadline']: return False
                if type(doc.get('epoch')) is not int: return False
                return True
        except (ValueError, TypeError, UnicodeError, WireError):
            return False

    def withdraw(self, tenant, principal, room, purpose, source):
        scope=self._scope(tenant,principal,room,purpose,source)
        with self._lock:
            self._epochs[scope]=self._epochs.get(scope,0)+1
            return self._epochs[scope]

    def return_fence(self, token, context, now):
        """Same authority and lock as admission; fails closed when rights stale."""
        try:
            return self.check(token,context['tenant'],context['principal'],context['room'],
                              context['purpose'],context['source'],now)
        except (TypeError, KeyError): return False

class UnavailableAuthority:
    def check(self,*_a,**_kw): return False
    def return_fence(self,*_a,**_kw): return False
