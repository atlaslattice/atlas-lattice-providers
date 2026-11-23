"""Missing source account is HOLD, never an uncaught input exception.

These fixtures use only an offline ephemeral SQLite database. They do not
model or authenticate a real host principal or broker.
"""
import unittest
from native_synthesis.pipeline import OfflineAtlasPipeline
from native_synthesis.offline_receipts import OfflinePreparationStore

class AccountBoundaryTests(unittest.TestCase):
    def test_no_account_withdrawal_returns_generic_hold(self):
        db=OfflinePreparationStore(':memory:',scope_key=b'local-32-byte-test-key-abcdefghijklm')
        try:
            p=OfflineAtlasPipeline(lambda x: {'status':'HOLD'},lambda: {},db)
            r=p.withdraw_local(tenant='tenant-001',principal='principal-001',room='room-001',source_sha256='a'*64)
            self.assertEqual(r['status'],'HOLD')
            self.assertEqual(db.report()['prepared_records'],0)
        finally:db.close()
    def test_no_account_local_prepare_is_inert(self):
        db=OfflinePreparationStore(':memory:',scope_key=b'local-32-byte-test-key-abcdefghijklm')
        try:
            p=OfflineAtlasPipeline(lambda x: {'status':'HOLD'},lambda: {},db)
            r=p.prepare({'private':'canary'},tenant='tenant-001',principal='principal-001',room='room-001')
            self.assertEqual(r['status'],'HOLD')
            self.assertEqual(db.report()['prepared_records'],0)
        finally:db.close()

if __name__=='__main__':unittest.main()
