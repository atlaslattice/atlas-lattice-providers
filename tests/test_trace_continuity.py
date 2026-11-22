"""Local receipt continuity: durable evidence before any fresh claim."""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
from pathlib import Path
import pytest
from providers.openai.openai_tracing_to_golden_trace import (
    GoldenTraceEvent, OpenAITracingToGoldenTrace, TraceIntegrityError,
)


def run(coro):
    return asyncio.run(coro)


def bridge(tmp, ledger=None):
    return OpenAITracingToGoldenTrace(trace_dir=str(tmp), action_ledger=ledger, simulate=True)


def send(tmp, name, payload=None, **kwargs):
    return run(bridge(tmp).record_openai_trace(name, payload=payload or {}, **kwargs))


def events(tmp):
    files=sorted(Path(tmp).glob('*.jsonl'))
    return [json.loads(line) for f in files for line in f.read_text().splitlines()]


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_new_receipt_uses_full_width_sha256_and_fields(tmp_path):
    out=send(tmp_path,'t1',{'x':1},openai_thread_id='th1',openai_run_id='run1')
    e=events(tmp_path)[0]
    assert e['hash_scheme']=='sha256-v2'
    assert out['golden_trace_hash']==e['hash']
    assert len(e['hash'])==66 and e['hash'].startswith('0x')
    assert e['prev_hash'] is None
    assert out['integrity_checked_local'] is True
    assert out['lattice_action_emitted'] is False


def test_new_records_continue_chain_across_new_instances(tmp_path):
    a=send(tmp_path,'first',{'x':1})
    b=send(tmp_path,'second',{'x':2})
    records=events(tmp_path)
    assert len(records)==2
    assert records[1]['prev_hash']==a['golden_trace_hash']
    assert records[1]['hash']==b['golden_trace_hash']


def test_duplicate_trace_name_preserves_distinct_durable_events(tmp_path):
    for n in range(3):
        send(tmp_path,'same',{'iteration':n})
    records=events(tmp_path)
    assert len(records)==3
    assert all(records[i]['prev_hash']==records[i-1]['hash'] for i in [1,2])
    assert [e['payload']['iteration'] for e in records]==[0,1,2]


@pytest.mark.parametrize('field,corrupt',[
    ('payload',{'x':99}),('openai_trace_id','altered'),
    ('openai_thread_id','forged'),('openai_run_id','forged'),
    ('lattice_action_id','forged'),('hash','0xdeadbeef'),('ts','1999-01-01T00:00:00Z'),
])
def test_tampering_any_v2_hashed_field_blocks_append(tmp_path,field,corrupt):
    o=send(tmp_path,'first',{'x':1},openai_thread_id='original',openai_run_id='run')
    p=Path(o['persisted_to']);e=json.loads(p.read_text());e[field]=corrupt
    p.write_text(json.dumps(e)+'\n')
    before=p.read_bytes()
    with pytest.raises(TraceIntegrityError):
        send(tmp_path,'second')
    assert p.read_bytes()==before
    assert not (tmp_path/'.writer.lock').exists()


def test_broken_prev_hash_on_second_event_blocks_append(tmp_path):
    send(tmp_path,'first');o=send(tmp_path,'second');p=Path(o['persisted_to'])
    rows=p.read_text().splitlines();last=json.loads(rows[1])
    last['prev_hash']='0xwrong'
    p.write_text(rows[0]+'\n'+json.dumps(last)+'\n')
    before=checksum(p)
    with pytest.raises(TraceIntegrityError,match='broken_trace_hash_chain'):
        send(tmp_path,'third')
    assert checksum(p)==before


def test_legacy_receipts_verify_with_old_algorithm_then_transition_to_v2(tmp_path):
    old=GoldenTraceEvent(openai_trace_id='old',payload={'evidence':'preserved'},
                         ts='2026-11-22T12:00:00Z',hash_scheme='legacy32')
    old.hash=old.compute_hash()
    assert len(old.hash)==34
    historical=old.to_dict(); historical.pop('hash_scheme')
    fname=tmp_path/'20261122.jsonl'
    fname.write_text(json.dumps(historical)+'\n')
    new=send(tmp_path,'new',{'evidence':'new'})
    rows=events(tmp_path)
    assert rows[0]['hash']==old.hash
    assert rows[1]['prev_hash']==old.hash
    assert len(new['golden_trace_hash'])==66


def test_legacy_payload_tampering_is_caught_with_no_rewrite(tmp_path):
    old=GoldenTraceEvent(openai_trace_id='old',payload={'evidence':'good'},
                         ts='2026-11-22T12:00:00Z',hash_scheme='legacy32')
    old.hash=old.compute_hash(); data=old.to_dict();data.pop('hash_scheme')
    data['payload']={'evidence':'bad'}
    p=tmp_path/'20261122.jsonl';p.write_text(json.dumps(data)+'\n')
    original=p.read_bytes()
    with pytest.raises(TraceIntegrityError,match='trace_hash_mismatch'):
        send(tmp_path,'next')
    assert p.read_bytes()==original


def test_missing_final_newline_traps_partial_record(tmp_path):
    old=send(tmp_path,'first'); p=Path(old['persisted_to'])
    p.write_bytes(p.read_bytes().rstrip(b'\n'))
    with pytest.raises(TraceIntegrityError,match='truncated_trace_ledger'):
        send(tmp_path,'second')


def test_duplicate_json_field_rejected_on_replay(tmp_path):
    old=send(tmp_path,'first');p=Path(old['persisted_to'])
    p.write_text(p.read_text().replace('"payload":', '"payload":{}, "payload":',1))
    with pytest.raises(TraceIntegrityError,match='duplicate_json_key'):
        send(tmp_path,'second')


def test_unknown_ledger_filename_prevents_ignored_history(tmp_path):
    (tmp_path/'arbitrary.jsonl').write_text('{}\n')
    with pytest.raises(TraceIntegrityError,match='unexpected_trace_ledger_name'):
        send(tmp_path,'new')


def test_existing_writer_lock_blocks_operation_and_stays_untouched(tmp_path):
    p=tmp_path/'.writer.lock'; p.write_text('unknown previous owner')
    with pytest.raises(FileExistsError):
        send(tmp_path,'x')
    assert p.read_text()=='unknown previous owner'
    assert list(tmp_path.glob('*.jsonl'))==[]


def test_invalid_trace_identity_does_not_open_ledger(tmp_path):
    for bad in (None,'',123,False):
        with pytest.raises(ValueError):
            run(bridge(tmp_path).record_openai_trace(bad))
    assert not list(tmp_path.iterdir())


def test_invalid_payload_is_rejected_without_disk_mutation(tmp_path):
    with pytest.raises(ValueError):
        run(bridge(tmp_path).record_openai_trace('id',payload=['not','object']))
    assert not list(tmp_path.iterdir())


def test_invalid_existing_symlink_does_not_leak_to_external_file(tmp_path):
    outside=tmp_path.parent/(tmp_path.name+'-external')
    try:
        outside.write_text('EXTERNAL PRIVATE DATA')
        # Empty symlink still forbidden; would otherwise overwrite outside.
        (tmp_path/'20261122.jsonl').symlink_to(outside)
        with pytest.raises(TraceIntegrityError,match='nonregular_trace_ledger'):
            send(tmp_path,'first')
        assert outside.read_text()=='EXTERNAL PRIVATE DATA'
    finally:
        outside.unlink(missing_ok=True)


def test_multiple_links_not_accepted_for_existing_destination(tmp_path):
    # Hardlinks can alias another path even when no symlink is involved.
    outside=tmp_path.parent/(tmp_path.name+'-linked')
    try:
        outside.write_text('')
        import datetime
        today=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')
        os.link(outside,tmp_path/f'{today}.jsonl')
        with pytest.raises(TraceIntegrityError,match='nonregular_or_linked_trace_ledger'):
            send(tmp_path,'first')
        assert outside.read_bytes()==b''
    finally:
        outside.unlink(missing_ok=True)


def test_failed_action_ledger_not_reported_as_emitted(tmp_path):
    class Broken:
        def emit(self,*args,**kwargs): raise RuntimeError('sensitive private reason')
    out=run(bridge(tmp_path,Broken()).record_openai_trace('first'))
    assert out['lattice_action_emitted'] is False
    assert len(events(tmp_path))==1


def test_missing_action_ledger_method_is_not_success(tmp_path):
    out=run(bridge(tmp_path,object()).record_openai_trace('first'))
    assert out['lattice_action_emitted'] is False


def test_async_action_ledger_must_finish_before_success(tmp_path):
    class Working:
        def __init__(self):self.received=[]
        async def emit(self, name, data): self.received.append((name,data))
    ledger=Working()
    out=run(bridge(tmp_path,ledger).record_openai_trace('first'))
    assert out['lattice_action_emitted'] is True
    assert ledger.received[0][0]=='openai_trace_ingested'


def test_unknown_hash_scheme_is_not_silently_accepted(tmp_path):
    out=send(tmp_path,'first'); p=Path(out['persisted_to'])
    e=json.loads(p.read_text());e['hash_scheme']='unknown-mode'
    p.write_text(json.dumps(e)+'\n')
    with pytest.raises(TraceIntegrityError,match='unsupported_trace_hash_scheme'):
        send(tmp_path,'second')


def test_results_are_purely_local_without_canon_promotion(tmp_path):
    out=send(tmp_path,'self-declared',{'claim':'unreviewed'})
    assert out['integrity_checked_local'] is True
    assert 'canon' not in out and 'verified_identity' not in out
    assert len(events(tmp_path))==1


def test_untrusted_payload_cannot_override_action_ledger_source_fields(tmp_path):
    class Capturing:
        def __init__(self):self.payload=None
        def append(self, **data):self.payload=data['payload']
    captured=Capturing()
    out=run(bridge(tmp_path,captured).record_openai_trace(
        'source',openai_thread_id='real-thread',openai_run_id='real-run',
        payload={'golden_trace_hash':'FORGED', 'thread_id':'forged-thread',
                 'run_id':'forged-run', 'source':'SELF_DECLARED'}))
    p=captured.payload
    assert out['lattice_action_emitted'] is True
    assert p['golden_trace_hash']==out['golden_trace_hash']
    assert p['thread_id']=='real-thread' and p['run_id']=='real-run'
    assert p['untrusted_trace_payload']['golden_trace_hash']=='FORGED'


def test_explicit_negative_adapter_ack_is_not_emission(tmp_path):
    class Unconfirmed:
        def emit(self,*args,**kwargs): return False
    out=run(bridge(tmp_path,Unconfirmed()).record_openai_trace('first'))
    assert out['lattice_action_emitted'] is False
    assert len(events(tmp_path))==1
