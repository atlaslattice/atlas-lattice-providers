"""One source identity must never overwrite another through filename aliases."""
from __future__ import annotations

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import json
from pathlib import Path
import pytest

from providers.openai.evals_bullshit_olympics_bridge import EvalsBullshitOlympicsBridge


def call(coro):
    return asyncio.run(coro)


def bridge(tmp_path):
    return EvalsBullshitOlympicsBridge(simulate=True, eval_dir=str(tmp_path))


def create(b, name, value='original'):
    return call(b.create_eval_dataset(name, [{'input': value}]))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_valid_id_is_a_one_to_one_filename_without_rewriting(tmp_path):
    b=bridge(tmp_path)
    out=create(b, 'A_B-91')
    assert Path(out['dataset_path']) == tmp_path/'A_B-91.jsonl'
    assert json.loads(Path(out['dataset_path']).read_text())['input']=='original'


@pytest.mark.parametrize('alias', [
    'a/b', 'a\\b', 'a b', 'a.b', 'a:b', './safe', '../safe',
    '.', '..', 'a%20b', 'a\nb', 'a\x00b', 'a\tb', 'a\u202eb',
    'é', 'Ω', 'Ａ', 'x'*81,
])
def test_names_requiring_lossy_normalization_are_rejected(tmp_path, alias):
    b=bridge(tmp_path)
    with pytest.raises(ValueError, match='eval_name'):
        create(b, alias)
    assert list(tmp_path.iterdir()) == []
    assert b._evals == {}


@pytest.mark.parametrize('bad_name', [0, True, 1.5, [], {}, ['valid']])
def test_nonstring_name_is_not_silently_defaulted(tmp_path, bad_name):
    b=bridge(tmp_path)
    with pytest.raises(ValueError, match='eval_name'):
        create(b, bad_name)
    assert not list(tmp_path.iterdir())


def test_collision_attack_cannot_overwrite_existing_dataset(tmp_path):
    b=bridge(tmp_path)
    original=create(b,'a_b','ORIGINAL SOURCE')
    target=Path(original['dataset_path']); before=digest(target)
    with pytest.raises(ValueError):
        create(b,'a/b','MALICIOUS REPLACEMENT')
    assert digest(target)==before
    assert b._evals['a_b'][0].input=='ORIGINAL SOURCE'


def test_duplicate_name_cannot_overwrite_previous_bytes_or_memory(tmp_path):
    b=bridge(tmp_path)
    original=create(b,'same','FIRST VERSION')
    file=Path(original['dataset_path']); before=file.read_bytes()
    with pytest.raises(FileExistsError):
        create(b,'same','SECOND VERSION')
    assert file.read_bytes()==before
    assert b._evals['same'][0].input=='FIRST VERSION'


def test_restart_cannot_replace_prior_evidence(tmp_path):
    a=bridge(tmp_path); first=create(a,'same','ORIGINAL')
    target=Path(first['dataset_path']); before=target.read_bytes()
    b=bridge(tmp_path)
    with pytest.raises(FileExistsError):
        create(b,'same','REPLACEMENT')
    assert target.read_bytes()==before
    assert 'same' not in b._evals


def test_existing_symlink_refuses_overwrite_or_follow(tmp_path):
    outside=tmp_path.parent / (tmp_path.name+'-private-outside.txt')
    try:
        outside.write_text('OUTSIDE DATA')
        (tmp_path/'protected.jsonl').symlink_to(outside)
        with pytest.raises(FileExistsError):
            create(bridge(tmp_path),'protected','EVIL')
        assert outside.read_text()=='OUTSIDE DATA'
    finally:
        outside.unlink(missing_ok=True)


def test_missing_or_empty_name_defaults_but_second_call_is_not_implicit_overwrite(tmp_path):
    b=bridge(tmp_path)
    a=create(b,None,'FIRST')
    assert Path(a['dataset_path']).name == 'atlas_lattice_eval.jsonl'
    with pytest.raises(FileExistsError):
        create(b,'','SECOND')
    assert json.loads(Path(a['dataset_path']).read_text())['input']=='FIRST'


@pytest.mark.parametrize('bad_items', [None, 'x', [{'input':'good'}, 'not dict'], 12, {}])
def test_malformed_items_leave_no_files(tmp_path, bad_items):
    b=bridge(tmp_path)
    with pytest.raises(ValueError, match='items'):
        call(b.create_eval_dataset('sample', bad_items))
    assert list(tmp_path.iterdir())==[]


@pytest.mark.parametrize('bad_name', ['../sensitive', 'some space', 'x.y', 'á'])
def test_grader_rejects_ambiguous_name_without_writing(tmp_path, bad_name):
    b=bridge(tmp_path)
    result=call(b.run_bullshit_as_grader(bad_name,'item','output'))
    assert result=={'error': 'invalid_eval_name'}
    assert list(tmp_path.iterdir())==[]


def test_fresh_instance_can_grade_saved_valid_name(tmp_path):
    b=bridge(tmp_path); create(b,'source_1','preserved input')
    fresh=bridge(tmp_path)
    result=call(fresh.run_bullshit_as_grader('source_1','source_1-0','output'))
    assert result['eval_result']['status']=='NOT_RUN'
    assert result['eval_result']['score'] is None
    assert (tmp_path/'source_1.jsonl').exists()
    assert (tmp_path/'source_1.results.jsonl').exists()


def test_two_unrelated_valid_names_remain_distinct(tmp_path):
    b=bridge(tmp_path)
    a=create(b,'case-A','a'); c=create(b,'case_A','c')
    assert a['dataset_path']!=c['dataset_path']
    assert len(list(tmp_path.glob('*.jsonl')))==2


def test_duplicate_error_does_not_truncate_result_ledger(tmp_path):
    b=bridge(tmp_path)
    create(b,'case','first')
    call(b.run_bullshit_as_grader('case','case-0','output'))
    path=tmp_path/'case.results.jsonl'
    digest_before=digest(path)
    with pytest.raises(FileExistsError):
        create(b,'case','second')
    assert digest(path)==digest_before


def test_names_differing_only_in_case_never_replace_existing_data(tmp_path):
    b=bridge(tmp_path)
    first=create(b,'data','lower')
    original=Path(first['dataset_path']).read_bytes()
    try:
        second=create(b,'DATA','upper')
    except FileExistsError:
        # On case-insensitive filesystems, preserving data means refusing alias.
        pass
    else:
        # On case-sensitive filesystems, both paths are independent.
        assert Path(second['dataset_path']).read_bytes() != original
    assert Path(first['dataset_path']).read_bytes() == original


def test_eight_concurrent_writers_never_overwrite_same_name(tmp_path):
    barrier=Barrier(8)
    def worker(index):
        instance=bridge(tmp_path)
        barrier.wait()
        try:
            create(instance,'single_source',str(index))
            return True
        except FileExistsError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(worker,range(8)))
    assert results.count(True)==1
    assert results.count(False)==7
    written=json.loads((tmp_path/'single_source.jsonl').read_text())['input']
    assert written in {str(i) for i in range(8)}
