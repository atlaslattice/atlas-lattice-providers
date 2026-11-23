"""Concurrent cold-start SQLite source-contract tests, no host/network effects."""
from __future__ import annotations
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKER=r'''
import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from native_synthesis.offline_receipts import OfflinePreparationStore
from native_synthesis.wire import WireError
from pathlib import Path
while not Path(sys.argv[3]).exists():time.sleep(0.005)
try:
    s=OfflinePreparationStore(sys.argv[2],scope_key=bytes.fromhex(sys.argv[4]));s.close()
    print('OPEN_OK')
except WireError:
    print('HOLD_INVALID_CONFIG')
'''

class ColdStartSourceGateTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.db=Path(self.t.name)/'receipts.db'
        self.gate=Path(self.t.name)/'go'
    def tearDown(self):self.t.cleanup()
    def _race(self,keys):
        children=[]
        try:
            for key in keys:
                child=subprocess.Popen([sys.executable,'-c',WORKER,str(ROOT),str(self.db),str(self.gate),key.hex()],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                children.append(child)
            self.gate.touch()
            outcomes=[]
            for child in children:
                out,err=child.communicate(timeout=10)
                self.assertEqual(child.returncode,0,msg=err)
                outcomes.append(out.strip())
            return outcomes
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill();child.communicate()
    def test_simultaneous_same_key_initializers_reuse_one_marker(self):
        key=b'local-synthetic-key-abc123456789xy'
        results=self._race((key,key))
        self.assertEqual(results.count('OPEN_OK'),2)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT count(*) FROM meta WHERE name='scope_key_id'").fetchone()[0],1)
            self.assertEqual(con.execute('SELECT count(*) FROM records').fetchone()[0],0)
    def test_simultaneous_different_keys_fail_closed_for_one(self):
        results=self._race((b'A'*32,b'B'*32))
        self.assertEqual(sorted(results),['HOLD_INVALID_CONFIG','OPEN_OK'])
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT count(*) FROM meta WHERE name='scope_key_id'").fetchone()[0],1)
            self.assertEqual(con.execute('SELECT count(*) FROM records').fetchone()[0],0)
    def test_two_initializers_refuse_markerless_legacy_file(self):
        with sqlite3.connect(self.db) as con:
            con.execute('CREATE TABLE scopes(scope_hash TEXT PRIMARY KEY,epoch INTEGER NOT NULL)')
            con.execute("INSERT INTO scopes VALUES ('legacy-opaque-scope',1)")
        results=self._race((b'A'*32,b'A'*32))
        self.assertEqual(results,['HOLD_INVALID_CONFIG','HOLD_INVALID_CONFIG'])
        with sqlite3.connect(self.db) as con:
            self.assertIsNone(con.execute("SELECT name FROM sqlite_master WHERE name='meta'").fetchone())
            self.assertEqual(con.execute('SELECT count(*) FROM scopes').fetchone()[0],1)

if __name__=='__main__':unittest.main()
