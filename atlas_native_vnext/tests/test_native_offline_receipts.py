"""Real SQLite commits, but NOT a real broker or hosted delivery."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from native_synthesis.offline_receipts import OfflinePreparationStore
from native_synthesis.wire import WireError

SCOPE=('tenant-A','principal-A','work-room','review','a'*64)
KEY=b'local-operator-secret-'*2
ACCOUNT='account-A'

class ReceiptStoreTest(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory()
        self.path=str(Path(self.d.name)/'prepared.sqlite')
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
    def tearDown(self):self.s.close();self.d.cleanup()
    def stage(self,rid='review.001',digest='b'*64,epoch=0):
        return self.s.stage(*SCOPE,rid,digest,epoch,account=ACCOUNT)
    def test_new_is_not_sent(self):
        x=self.stage()
        self.assertEqual(x['status'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertFalse(x['message_posted'])
    def test_duplicate_returns_one_receipt(self):
        self.stage()
        self.assertEqual(self.stage()['status'],'DEDUPLICATED_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.s.report()['prepared_records'],1)
    def test_changed_digest_denied(self):
        self.stage()
        self.assertEqual(self.stage(digest='c'*64)['status'],'HOLD')
    def test_restart_is_idempotent(self):
        self.stage();self.s.close()
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage()['status'],'DEDUPLICATED_PREPARED_LOCAL_ONLY')
    def test_withdraw_blocks_old_epoch(self):
        self.stage()
        self.assertEqual(self.s.withdraw(*SCOPE,account=ACCOUNT)['new_epoch'],1)
        self.assertEqual(self.stage('fresh.002',epoch=0)['status'],'HOLD')
    def test_regrant_doesnt_resurrect_old_request(self):
        self.stage()
        self.s.withdraw(*SCOPE,account=ACCOUNT)
        self.assertEqual(self.stage(epoch=1)['status'],'HOLD')
        self.assertEqual(self.stage('fresh.002',epoch=1)['status'],'NEW_PREPARED_LOCAL_ONLY')
    def test_replayed_epoch_after_restart(self):
        self.s.withdraw(*SCOPE,account=ACCOUNT);self.s.close()
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage(epoch=0)['status'],'HOLD')
    def test_scope_collision_safe(self):
        self.stage()
        other=self.s.stage('tenant-A','principal-A','work-room-x','review','a'*64,'review.001','b'*64,0,account=ACCOUNT)
        self.assertEqual(other['status'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.s.report()['prepared_records'],2)
    def test_account_switch_different_scope(self):
        self.stage()
        other=self.s.stage('tenant-B','principal-A','work-room','review','a'*64,'review.001','b'*64,0,account=ACCOUNT)
        self.assertEqual(other['status'],'NEW_PREPARED_LOCAL_ONLY')
    def test_wrong_key_after_restart_holds_before_replay(self):
        self.stage();self.s.close()
        with self.assertRaises(WireError):
            OfflinePreparationStore(self.path,scope_key=b'x'*32)
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage()['status'],'DEDUPLICATED_PREPARED_LOCAL_ONLY')
    def test_epoch_saturation_never_resurrects_staging(self):
        # Synthetic local upper-bound probe; NOT a host rights withdrawal.
        scope=self.s._scope(*SCOPE,account=ACCOUNT)
        self.s._conn.execute('INSERT OR REPLACE INTO scopes(scope_hash,epoch) VALUES (?,?)',
                             (scope,2147483646))
        self.assertEqual(self.stage('before-saturation',epoch=2147483646)['status'],
                         'NEW_PREPARED_LOCAL_ONLY')
        r=self.s.withdraw(*SCOPE,account=ACCOUNT)
        self.assertEqual(r['status'],'SIMULATED_WITHDRAWAL_ONLY')
        self.assertEqual(r['new_epoch'],2147483647)
        # Staged operations remain held even if caller guesses the final epoch.
        self.assertEqual(self.stage('after-saturation',epoch=2147483647)['status'],'HOLD')
        self.assertEqual(self.s.withdraw(*SCOPE,account=ACCOUNT)['status'],'HOLD')
        self.assertEqual(self.s.report()['prepared_records'],1)

    def test_saturated_epoch_survives_restart_and_fails_closed(self):
        scope=self.s._scope(*SCOPE,account=ACCOUNT)
        self.s._conn.execute('INSERT OR REPLACE INTO scopes(scope_hash,epoch) VALUES (?,?)',
                             (scope,2147483647))
        self.s.close()
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage('replay',epoch=2147483647)['status'],'HOLD')
        self.assertEqual(self.s.withdraw(*SCOPE,account=ACCOUNT)['status'],'HOLD')

    def test_same_tenant_principal_different_account_no_dedup(self):
        self.stage()
        second=self.s.stage(*SCOPE,'review.001','b'*64,0,account='account-B')
        self.assertEqual(second['status'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.s.report()['prepared_records'],2)
        self.assertEqual(self.s.withdraw(*SCOPE,account='account-B')['new_epoch'],1)
        self.assertEqual(self.stage('fresh.002')['status'],'NEW_PREPARED_LOCAL_ONLY')

    def test_missing_or_invalid_account_holds_without_writes(self):
        self.assertEqual(self.s.stage(*SCOPE,'review.001','b'*64,0)['status'],'HOLD')
        self.assertEqual(self.s.withdraw(*SCOPE)['status'],'HOLD')
        for account in (None,[],{},'private account',True):
            with self.subTest(account=repr(account)):
                self.assertEqual(self.s.stage(*SCOPE,'review.001','b'*64,0,account=account)['status'],'HOLD')
        self.assertEqual(self.s.report()['prepared_records'],0)

    def test_v02_database_not_silently_reused_with_new_account_scope(self):
        import hmac,hashlib
        self.s.close()
        legacy=hmac.new(KEY,b'atlas.native.offline-receipts.key/v0.2','sha256').hexdigest()
        db=sqlite3.connect(self.path)
        db.execute("UPDATE meta SET value=? WHERE name='scope_key_id'",(legacy,))
        db.commit();db.close()
        with self.assertRaises(WireError): OfflinePreparationStore(self.path,scope_key=KEY)
        # Old database remains present; use a different new filename in production.
        self.assertTrue(Path(self.path).exists())
        # TearDown needs an owned valid connection, not the refused legacy one.
        self.s=OfflinePreparationStore(':memory:',scope_key=KEY)

    def test_missing_marker_legacy_tables_not_adopted_or_mutated(self):
        self.s.close()
        Path(self.path).unlink()
        con=sqlite3.connect(self.path)
        con.execute('CREATE TABLE scopes(scope_hash TEXT PRIMARY KEY,epoch INTEGER NOT NULL)')
        con.execute("INSERT INTO scopes VALUES ('untrusted-legacy-scope',0)")
        con.execute('CREATE TABLE records(scope_hash TEXT,request_id TEXT,payload_digest TEXT,epoch INTEGER,state TEXT)')
        con.execute("INSERT INTO records VALUES ('untrusted-legacy-scope','req','abc',0,'PREPARED_NOT_POSTED')")
        con.commit();con.close()
        with self.assertRaises(WireError):OfflinePreparationStore(self.path,scope_key=KEY)
        con=sqlite3.connect(self.path)
        self.assertEqual(con.execute("SELECT name FROM sqlite_master WHERE name='meta'").fetchone(),None)
        self.assertEqual(con.execute('SELECT count(*) FROM records').fetchone()[0],1)
        con.close()
        self.s=OfflinePreparationStore(':memory:',scope_key=KEY)

    def test_deleted_marker_with_existing_records_not_reinitialized(self):
        self.stage()
        self.s.close()
        con=sqlite3.connect(self.path)
        con.execute("DELETE FROM meta WHERE name='scope_key_id'")
        con.commit();con.close()
        with self.assertRaises(WireError):OfflinePreparationStore(self.path,scope_key=KEY)
        con=sqlite3.connect(self.path)
        self.assertEqual(con.execute('SELECT count(*) FROM records').fetchone()[0],1)
        self.assertEqual(con.execute("SELECT count(*) FROM meta WHERE name='scope_key_id'").fetchone()[0],0)
        con.close()
        self.s=OfflinePreparationStore(':memory:',scope_key=KEY)

    def test_blank_meta_only_snapshot_can_initialize(self):
        self.s.close()
        Path(self.path).unlink()
        con=sqlite3.connect(self.path)
        con.execute('CREATE TABLE meta(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
        con.commit();con.close()
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage()['status'],'NEW_PREPARED_LOCAL_ONLY')

    def test_unrecognized_meta_row_without_marker_is_hold(self):
        self.s.close()
        Path(self.path).unlink()
        con=sqlite3.connect(self.path)
        con.execute('CREATE TABLE meta(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
        con.execute("INSERT INTO meta VALUES ('legacy-nonce','untrusted')")
        con.commit();con.close()
        with self.assertRaises(WireError):OfflinePreparationStore(self.path,scope_key=KEY)
        self.s=OfflinePreparationStore(':memory:',scope_key=KEY)

    def test_multiple_threads_single_record(self):
        with ThreadPoolExecutor(max_workers=12) as ex:
            r=list(ex.map(lambda _:self.stage(),range(24)))
        self.assertEqual(sum(x['status']=='NEW_PREPARED_LOCAL_ONLY' for x in r),1)
        self.assertEqual(sum(x['status']=='DEDUPLICATED_PREPARED_LOCAL_ONLY' for x in r),23)
        self.assertEqual(self.s.report()['prepared_records'],1)
    def test_database_does_not_store_plain_scope(self):
        self.stage()
        raw=Path(self.path).read_bytes()
        for value in (b'tenant-A',b'principal-A',b'work-room'):
            self.assertNotIn(value,raw)
    def test_bad_payload_and_epoch_hold(self):
        self.assertEqual(self.stage(digest='INVALID')['status'],'HOLD')
        self.assertEqual(self.stage(epoch=True)['status'],'HOLD')
    def test_bad_config_denied(self):
        with self.assertRaises(WireError):OfflinePreparationStore(':memory:',scope_key=b'short')
    def test_no_published_events(self):
        self.stage();self.s.withdraw(*SCOPE,account=ACCOUNT)
        self.assertEqual(self.s.report()['published'],0)
        self.assertEqual(self.s.report()['peer_reads'],0)
    def test_different_source_no_membership_oracle(self):
        self.stage()
        v=self.s.stage(*SCOPE[:-1],'b'*64,'review.001','b'*64,0,account=ACCOUNT)
        self.assertEqual(v['status'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.s.report()['prepared_records'],2)

if __name__ == '__main__':unittest.main()
