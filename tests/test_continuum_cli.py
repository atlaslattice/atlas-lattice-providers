"""Synthetic local-only cockpit regressions; no external systems or residents."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1] / "scripts" / "continuum_cli.py"
SPEC=importlib.util.spec_from_file_location("continuum_cli",SOURCE)
cli=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)

QUEUE='''version: 0.1
dispatch_packets:
  - packet_id: A1-TEST
    task_title: First synthetic task
    assigned_child: None
    status: ready_after_human_root_approval
    priority: P0
  - packet_id: A2-TEST
    task_title: Second synthetic task
    assigned_child: None
    status: not_ready
    priority: P1
'''

class CockpitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/'swarmhub').mkdir()
        (self.root/'docs').mkdir()
        (self.root/'swarmhub'/'DISPATCH_QUEUE.yaml').write_text(QUEUE)
    def tearDown(self): self.tmp.cleanup()

    def test_queue_is_not_claim(self):
        report=cli.run('dispatch list',self.root)
        self.assertEqual(len(report['tasks']),2)
        self.assertFalse(report['claims_created'])

    def test_status_is_local_not_host(self):
        r=cli.run('status',self.root)
        self.assertEqual(r['packet_count'],2)
        self.assertEqual(r['pending_approvals_reported'],1)
        self.assertFalse(r['live_host_state_known'])

    def test_rehydrate_does_not_wake(self):
        r=cli.run('rehydrate',self.root)
        self.assertFalse(r['remote_sync'])
        self.assertFalse(r['agents_woken'])

    def test_claim_remains_unsent(self):
        r=cli.run('dispatch claim',self.root,'A1-TEST')
        self.assertFalse(r['assigned']);self.assertFalse(r['sent'])

    def test_return_packet_is_not_result(self):
        r=cli.run('return-packet create',self.root,'A1-TEST')
        self.assertEqual(r['status'],'DRAFT_NOT_SENT')
        self.assertEqual(r['receipts'],[])
        self.assertIs(r['canon'],False)

    def test_unknown_dispatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN_PACKET_ID'):
            cli.run('dispatch claim',self.root,'MISSING')

    def test_bad_packet_id_rejected(self):
        with self.assertRaisesRegex(ValueError,'BAD_PACKET_ID'):
            cli.run('return-packet create',self.root,'../secret')

    def test_duplicate_packet_id_rejected(self):
        path=self.root/'swarmhub'/'DISPATCH_QUEUE.yaml'
        path.write_text(QUEUE+'  - packet_id: A1-TEST\n')
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            cli.queue(self.root)

    def test_no_source_copy_or_raw_history(self):
        r=cli.run('fossilize-crash',self.root)
        self.assertEqual(r['kind'],'CRASH_FOSSIL_MANIFEST_CANDIDATE')
        self.assertFalse(r['source_content_copied'])
        self.assertNotIn('First synthetic task',json.dumps(r))

    def test_missing_files_marked(self):
        r=cli.run('receipts verify',self.root)
        self.assertTrue(any(x['status']=='MISSING_OR_UNREADABLE' for x in r['files']))

    def test_manifest_no_overwrite(self):
        report=cli.run('fossilize-crash',self.root)
        p=cli._write_manifest(self.root,'local_fossils/candidate.json',report)
        self.assertTrue(p.is_file())
        with self.assertRaises(FileExistsError):
            cli._write_manifest(self.root,'local_fossils/candidate.json',report)

    def test_manifest_rejects_external_write(self):
        with self.assertRaises(ValueError):
            cli._write_manifest(self.root,'../escape.json',{})

    def test_reject_local_file_symlink(self):
        source=self.root/'swarmhub'/'DISPATCH_QUEUE.yaml'
        source.unlink()
        source.symlink_to(self.root/'outside')
        with self.assertRaises(ValueError):cli.queue(self.root)

    def test_reject_symlinked_queue_parent(self):
        source=self.root/'swarmhub'/'DISPATCH_QUEUE.yaml'
        external=self.root/'outside'
        external.mkdir()
        (external/'DISPATCH_QUEUE.yaml').write_text(QUEUE)
        source.unlink()
        (self.root/'swarmhub').rmdir()
        (self.root/'swarmhub').symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError): cli.queue(self.root)

    def test_reject_symlinked_manifest_directory(self):
        outside=self.root/'outside'
        outside.mkdir()
        (self.root/'local_fossils').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            cli._write_manifest(self.root, 'local_fossils/synthetic.json', {})

    def test_open_cockpit_does_not_open_browser(self):
        r=cli.run('open-cockpit',self.root)
        self.assertFalse(r['browser_opened'])

if __name__=='__main__':unittest.main()
