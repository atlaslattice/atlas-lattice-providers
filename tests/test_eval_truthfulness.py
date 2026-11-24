"""Evidence gate: no pseudo-evaluation can masquerade as a real grade."""
import asyncio
import json
import math
from pathlib import Path
import pytest
from providers.openai.evals_bullshit_olympics_bridge import EvalsBullshitOlympicsBridge


def run(coro):
    return asyncio.run(coro)


def create(bridge):
    run(bridge.create_eval_dataset('case', [{'input':'factual assertion', 'expected':'yes'}]))


def grade(bridge):
    return run(bridge.run_bullshit_as_grader('case', 'case-0', 'yes'))['eval_result']


def test_no_engine_in_simulation_yields_no_score_or_false_grader(tmp_path):
    b=EvalsBullshitOlympicsBridge(simulate=True,eval_dir=str(tmp_path))
    create(b)
    r=grade(b)
    assert r['score'] is None
    assert r['status']=='NOT_RUN'
    assert r['grader']=='none'
    assert r['score_basis']=='NONE'
    saved=json.loads((tmp_path/'case.results.jsonl').read_text().splitlines()[0])
    assert saved['score'] is None and saved['status']=='NOT_RUN'


def test_simulation_never_invokes_explicit_backend(tmp_path):
    class FailIfCalled:
        async def review(self,*args,**kwargs):
            raise AssertionError('Simulation unexpectedly invoked backend')
    b=EvalsBullshitOlympicsBridge(bullshit_engine=FailIfCalled(), simulate=True,eval_dir=str(tmp_path))
    create(b)
    assert grade(b)['status']=='NOT_RUN'


def test_missing_backend_in_live_mode_is_not_a_grade(tmp_path):
    b=EvalsBullshitOlympicsBridge(simulate=False,eval_dir=str(tmp_path))
    b.bullshit=None  # deterministic offline fixture; no provider calls
    create(b)
    assert grade(b)['status']=='NOT_RUN'
    assert grade(b)['score'] is None


def test_missing_grade_field_is_not_replaced_by_fake_default(tmp_path):
    class MissingScore:
        async def review(self,*args,**kwargs):
            return {'verdict':'reported; no number'}
    b=EvalsBullshitOlympicsBridge(bullshit_engine=MissingScore(),simulate=False,eval_dir=str(tmp_path))
    create(b)
    r=grade(b)
    assert r['status']=='INVALID_GRADE' and r['score'] is None


@pytest.mark.parametrize('invalid',[float('nan'), float('inf'), float('-inf'),-0.1,1.1,'0.88',True,None,{}])
def test_invalid_or_unbounded_score_never_credited(tmp_path,invalid):
    class Invalid:
        async def review(self,*args,**kwargs):
            return {'inv_l28_coherence':invalid, 'verdict':'reported'}
    b=EvalsBullshitOlympicsBridge(bullshit_engine=Invalid(),simulate=False,eval_dir=str(tmp_path))
    create(b)
    r=grade(b)
    assert r['score'] is None and r['status']=='INVALID_GRADE'


def test_grader_exception_fails_closed_without_synthetic_grade(tmp_path):
    class Fails:
        async def review(self,*args,**kwargs):
            raise RuntimeError('internal system sensitive information')
    b=EvalsBullshitOlympicsBridge(bullshit_engine=Fails(),simulate=False,eval_dir=str(tmp_path))
    create(b)
    r=grade(b)
    assert r['score'] is None and r['status']=='GRADER_FAILED'
    assert 'sensitive information' not in r['explanation']


def test_valid_fixture_grade_is_labeled_unverified_backend_response(tmp_path):
    class Working:
        calls=0
        async def review(self,*args,**kwargs):
            self.calls += 1
            return {'inv_l28_coherence':0.64,'verdict':'candidate','critical_flaws':[]}
    fixture=Working()
    b=EvalsBullshitOlympicsBridge(bullshit_engine=fixture,simulate=False,eval_dir=str(tmp_path))
    create(b)
    r=grade(b)
    assert fixture.calls==1
    assert r['score']==0.64 and r['status']=='SCORED'
    assert r['score_basis']=='BACKEND_RESPONSE_UNVERIFIED'
    assert r['grader']=='advanced_bullshit_olympics'


def test_persisted_dataset_can_be_reopened_without_grader(tmp_path):
    b=EvalsBullshitOlympicsBridge(simulate=True,eval_dir=str(tmp_path))
    create(b)
    restarted=EvalsBullshitOlympicsBridge(simulate=True,eval_dir=str(tmp_path))
    r=grade(restarted)
    assert r['score'] is None and r['status']=='NOT_RUN'
