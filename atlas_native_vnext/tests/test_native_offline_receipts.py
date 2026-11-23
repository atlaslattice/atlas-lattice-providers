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

class ReceiptStoreTest(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory()
        self.path=str(Path(self.d.name)/'prepared.sqlite')
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
    def tearDown(self):self.s.close();self.d.cleanup()
    def stage(self,rid='review.001',digest='b'*64,epoch=0):
        return self.s.stage(*SCOPE,rid,digest,epoch)
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
        self.assertEqual(self.s.withdraw(*SCOPE)['new_epoch'],1)
        self.assertEqual(self.stage('fresh.002',epoch=0)['status'],'HOLD')
    def test_regrant_doesnt_resurrect_old_request(self):
        self.stage()
        self.s.withdraw(*SCOPE)
        self.assertEqual(self.stage(epoch=1)['status'],'HOLD')
        self.assertEqual(self.stage('fresh.002',epoch=1)['status'],'NEW_PREPARED_LOCAL_ONLY')
    def test_replayed_epoch_after_restart(self):
        self.s.withdraw(*SCOPE);self.s.close()
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage(epoch=0)['status'],'HOLD')
    def test_scope_collision_safe(self):
        self.stage()
        other=self.s.stage('tenant-A','principal-A','work-room-x','review','a'*64,'review.001','b'*64,0)
        self.assertEqual(other['status'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.s.report()['prepared_records'],2)
    def test_account_switch_different_scope(self):
        self.stage()
        other=self.s.stage('tenant-B','principal-A','work-room','review','a'*64,'review.001','b'*64,0)
        self.assertEqual(other['status'],'NEW_PREPARED_LOCAL_ONLY')
    def test_wrong_key_after_restart_holds_before_replay(self):
        self.stage();self.s.close()
        with self.assertRaises(WireError):
            OfflinePreparationStore(self.path,scope_key=b'x'*32)
        self.s=OfflinePreparationStore(self.path,scope_key=KEY)
        self.assertEqual(self.stage()['status'],'DEDUPLICATED_PREPARED_LOCAL_ONLY')
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
        self.stage();self.s.withdraw(*SCOPE)
        self.assertEqual(self.s.report()['published'],0)
        self.assertEqual(self.s.report()['peer_reads'],0)
    def test_different_source_no_membership_oracle(self):
        self.stage()
        v=self.s.stage(*SCOPE[:-1],'b'*64,'review.001','b'*64,0)
        self.assertEqual(v['status'],'NEW_PREPARED_LOCAL_ONLY')
        self.assertEqual(self.s.report()['prepared_records'],2)

if __name__ == '__main__':unittest.main()
