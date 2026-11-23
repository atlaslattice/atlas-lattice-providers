"""Never publish account-private broker locator strings in source snapshots."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]

class TestPublicCandidateDocPrivacy(unittest.TestCase):
    def test_oss_selection_omits_private_broker_address(self):
        content=(ROOT/'docs/OSS_SELECTION.md').read_text(encoding='utf-8')
        self.assertIn('ACCOUNT_PRIVATE_HOST_REFERENCE_WITHHELD',content)
        self.assertNotIn('.chatgpt.site',content)
    def test_catalog_is_also_host_gated(self):
        obj=json.loads((ROOT/'native_synthesis/catalog.json').read_text(encoding='utf-8'))
        swarm=next(x for x in obj['assets'] if x['id']=='swarmchat')
        self.assertEqual(swarm['host_state'],'NOT_HOST_VERIFIED')
        self.assertNotIn('.chatgpt.site',json.dumps(obj))

if __name__=='__main__':unittest.main()
