"""Optional no-network Atlas Labs PR61 <-> Native PR63 offline smoke runner.

Never use this script as authority to connect to a real SwarmChat room or
publish science: it only stages a disposable local SQLite preparation receipt.
"""
from __future__ import annotations
import argparse
from hashlib import sha1
from types import ModuleType
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from native_synthesis.offline_receipts import OfflinePreparationStore
from native_synthesis.pipeline import OfflineAtlasPipeline

LABS_PR61_SOURCE_GIT_BLOB='eb667d20e8e80c463dbc84e1559d808dd803047c'


def import_pinned_labs_source(path: Path):
    """Hash exact bytes BEFORE executing source; owner chooses trusted path."""
    raw=path.read_bytes()
    if len(raw)>250_000 or sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=LABS_PR61_SOURCE_GIT_BLOB:
        raise ValueError('Labs source Git blob is not the reviewed PR61 revision')
    # Execute the bytes that passed the Git blob check. Re-opening the path
    # with a source loader could execute replacement bytes after the hash check.
    # This does not pin imports made *by* the reviewed module or prove host IAM.
    module=ModuleType('atlas_labs_pinned_source_only')
    module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def main():
    a=argparse.ArgumentParser(description='LOCAL ONLY: no authenticated host, science lab or broker calls')
    a.add_argument('--labs-source',required=True,help='exact PR61 labs/atlas_labs_v32.py file')
    a.add_argument('--input',required=True,help='PUBLIC-only Atlas Labs experiment JSON')
    args=a.parse_args()
    labs=import_pinned_labs_source(Path(args.labs_source))
    raw=Path(args.input).read_bytes()
    if len(raw)>32_768:raise SystemExit('Input too large')
    with TemporaryDirectory() as tmp:
        s=OfflinePreparationStore(str(Path(tmp)/'source_only.sqlite'),scope_key=b'synthetic-fixture-operator-key-32-bytes')
        try:
            pipe=OfflineAtlasPipeline(labs.prepare,labs.catalog,s)
            result=pipe.prepare(raw,tenant='synthetic-tenant',principal='synthetic-principal',
                                room='offline-review')
            result['offline_store_report']=s.report()
            result['pr61_source_git_blob_sha1']=LABS_PR61_SOURCE_GIT_BLOB
        finally:s.close()
    print(json.dumps(result,indent=2,sort_keys=True))
    if result['status']!='LOCAL_REVIEW_PREPARED_NOT_SENT':raise SystemExit(1)

if __name__=='__main__':main()
