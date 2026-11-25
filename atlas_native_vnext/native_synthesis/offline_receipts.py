"""Durable offline *preparation* receipts. SQLite, no host delivery/auth grant.

Only HMAC scope IDs and public, source-validated candidate digests are stored.
This is not a receiver inbox, cannot guarantee network exactly-once, and never
sends messages to SwarmChat or writes an Alexandria/Atlas ONE data store.
"""
from __future__ import annotations
from hashlib import sha256
from hmac import new as hmac_new
import sqlite3
from threading import RLock
from .wire import WireError, HEX64, IDENT, clean_text, canonical_json

HOLD = {'status':'HOLD','message_posted':False,'host_verified':False,'authority_effect':'NONE'}
MAX_EPOCH = 2**31 - 1

class OfflinePreparationStore:
    def __init__(self, database=':memory:', scope_key=None):
        if type(database) is not str or not database or scope_key is None or type(scope_key) is not bytes or len(scope_key)<32:
            raise WireError('INVALID_CONFIG')
        self._key=scope_key
        self._conn=sqlite3.connect(database,timeout=10,check_same_thread=False,isolation_level=None)
        self._lock=RLock()
        self._conn.execute('PRAGMA busy_timeout=10000')
        self._conn.execute('PRAGMA foreign_keys=ON')
        # Cross-process restart must not silently accept a different HMAC scope
        # key: otherwise the same request can be staged as a distinct scope.
        # This is a local compatibility pin, NOT proof of host identity.
        identity=hmac_new(scope_key,b'atlas.native.offline-receipts.key/v0.3.account-bound','sha256').hexdigest()
        try:
            # Acquire the initialization lock BEFORE creating or reading any
            # schema markers. A legacy/partially damaged ledger without its
            # scope-key marker must not be silently adopted as v0.3.
            self._conn.execute('BEGIN IMMEDIATE')
            present={row[0] for row in self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if 'meta' not in present and present:
                raise WireError('INVALID_CONFIG')
            self._conn.execute('CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
            prev=self._conn.execute('SELECT value FROM meta WHERE name=?',('scope_key_id',)).fetchone()
            if prev is not None and prev[0]!=identity:
                raise WireError('INVALID_CONFIG')
            if prev is None:
                # Also reject a removed marker in an otherwise populated v0.3
                # file; missing epoch/receipt ownership is never a fresh DB.
                if any(name!='meta' for name in present) or self._conn.execute(
                        'SELECT 1 FROM meta LIMIT 1').fetchone() is not None:
                    raise WireError('INVALID_CONFIG')
                self._conn.execute('INSERT INTO meta(name,value) VALUES (?,?)',('scope_key_id',identity))
            self._conn.execute('COMMIT')
        except Exception:
            if self._conn.in_transaction:self._conn.execute('ROLLBACK')
            self._conn.close()
            raise
        self._conn.execute('CREATE TABLE IF NOT EXISTS scopes (scope_hash TEXT PRIMARY KEY, epoch INTEGER NOT NULL CHECK(epoch >= 0))')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS records (
            scope_hash TEXT NOT NULL, request_id TEXT NOT NULL, payload_digest TEXT NOT NULL,
            epoch INTEGER NOT NULL, state TEXT NOT NULL CHECK(state = 'PREPARED_NOT_POSTED'),
            PRIMARY KEY(scope_hash,request_id), FOREIGN KEY(scope_hash) REFERENCES scopes(scope_hash))''')

    def _scope(self, tenant, principal, room, purpose, source_digest, *, account=None):
        for x in (tenant,account,principal,room,purpose):
            if type(x) is not str or not IDENT.fullmatch(x):
                raise WireError('INVALID_SCOPE')
        if type(source_digest) is not str or not HEX64.fullmatch(source_digest):
            raise WireError('INVALID_SCOPE')
        document=canonical_json({'tenant':tenant,'account':account,'principal':principal,'room':room,
                                 'purpose':purpose,'source_digest':source_digest})
        return hmac_new(self._key,document,'sha256').hexdigest()

    def stage(self, tenant, principal, room, purpose, source_digest, request_id, payload_digest, epoch=0, *, account=None):
        """Local durable candidate receipt; no permission or send side effects."""
        try:
            scope=self._scope(tenant,principal,room,purpose,source_digest,account=account)
            if type(request_id) is not str or not IDENT.fullmatch(request_id) or type(payload_digest) is not str or not HEX64.fullmatch(payload_digest):
                raise WireError('INVALID_INPUT')
            if type(epoch) is not int or not 0<=epoch<MAX_EPOCH:
                raise WireError('INVALID_EPOCH')
            with self._lock:
                try:
                    self._conn.execute('BEGIN IMMEDIATE')
                    self._conn.execute('INSERT OR IGNORE INTO scopes(scope_hash,epoch) VALUES (?,0)',(scope,))
                    row=self._conn.execute('SELECT epoch FROM scopes WHERE scope_hash=?',(scope,)).fetchone()
                    if row is None or row[0]>=MAX_EPOCH or row[0]!=epoch:
                        self._conn.execute('ROLLBACK')
                        return dict(HOLD)
                    prev=self._conn.execute('SELECT payload_digest,epoch FROM records WHERE scope_hash=? AND request_id=?',(scope,request_id)).fetchone()
                    if prev:
                        self._conn.execute('COMMIT')
                        if prev!=(payload_digest,epoch): return dict(HOLD)
                        return {'status':'DEDUPLICATED_PREPARED_LOCAL_ONLY','message_posted':False,'host_verified':False,'authority_effect':'NONE'}
                    self._conn.execute('INSERT INTO records(scope_hash,request_id,payload_digest,epoch,state) VALUES (?,?,?,?,?)',
                                       (scope,request_id,payload_digest,epoch,'PREPARED_NOT_POSTED'))
                    self._conn.execute('COMMIT')
                    return {'status':'NEW_PREPARED_LOCAL_ONLY','message_posted':False,'host_verified':False,'authority_effect':'NONE'}
                except Exception:
                    if self._conn.in_transaction:self._conn.execute('ROLLBACK')
                    raise
        except (WireError,TypeError,ValueError,OverflowError,sqlite3.Error):
            return dict(HOLD)

    def withdraw(self, tenant, principal, room, purpose, source_digest, *, account=None):
        """Advance a *local synthetic* epoch; NOT a real host rights withdrawal."""
        try:
            scope=self._scope(tenant,principal,room,purpose,source_digest,account=account)
            with self._lock:
                try:
                    self._conn.execute('BEGIN IMMEDIATE')
                    self._conn.execute('INSERT OR IGNORE INTO scopes(scope_hash,epoch) VALUES (?,0)',(scope,))
                    # A saturated epoch must never silently claim successful withdrawal.
                    # Future stage() calls also HOLD at MAX_EPOCH.
                    current=self._conn.execute('SELECT epoch FROM scopes WHERE scope_hash=?',(scope,)).fetchone()[0]
                    if current>=MAX_EPOCH:
                        self._conn.execute('ROLLBACK')
                        return dict(HOLD)
                    self._conn.execute('UPDATE scopes SET epoch=epoch+1 WHERE scope_hash=?',(scope,))
                    row=self._conn.execute('SELECT epoch FROM scopes WHERE scope_hash=?',(scope,)).fetchone()
                    self._conn.execute('COMMIT')
                    return {'status':'SIMULATED_WITHDRAWAL_ONLY','new_epoch':row[0],
                            'host_permissions_changed':False,'message_posted':False}
                except Exception:
                    if self._conn.in_transaction:self._conn.execute('ROLLBACK')
                    raise
        except (WireError,TypeError,ValueError,sqlite3.Error):
            return dict(HOLD)

    def report(self):
        with self._lock:
            n=self._conn.execute('SELECT count(*) FROM records').fetchone()[0]
            return {'status':'LOCAL_RECEIPT_COUNT_ONLY','prepared_records':n,
                    'published':0,'host_verification':'NOT_PERFORMED','peer_reads':0}

    def close(self):
        with self._lock:self._conn.close()
