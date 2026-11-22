"""Adversarial completion semantics on existing host-verified ToolPassport baseline."""
import asyncio
import pytest
from providers.openai import ToolPassport, ToolPassportFunctionCalling

def run(coro):
    return asyncio.run(coro)

def make(executor=None, ledger=None):
    p=ToolPassport(id="t-local", name="t_local", description="synthetic",
                   input_schema={"type":"object"}, safety_level="read", requires_approval=False)
    b=ToolPassportFunctionCalling(simulate=False, executor=executor, ledger=ledger)
    b.register_passport(p)
    return b

@pytest.mark.parametrize("bad", [None, [], ["x"], "text", 123, True])
def test_wrong_argument_shape_fail_closed_before_executor(bad):
    called=[]
    b=make(executor=lambda *a: called.append(a))
    result=run(b.execute_governed_tool("t_local", bad, approved=True))
    assert result["status"]=="invalid_arguments"
    assert called==[]

def test_executor_raises_and_does_not_create_success_ledger():
    ledger=[]
    class FakeLedger:
        def emit(self, name, data): ledger.append((name,data))
    def broken(*args):
        raise RuntimeError("private error should not escape")
    b=make(executor=broken, ledger=FakeLedger())
    result=run(b.execute_governed_tool("t_local", {}, approved=True))
    assert result["status"]=="executor_failed"
    assert ledger==[]

def test_async_executor_awaited_before_completion():
    async def invoke(name, data): return {"async_result":"verified_local_only"}
    b=make(executor=invoke)
    result=run(b.execute_governed_tool("t_local", {}))
    assert result["status"]=="executed"
    assert result["result"]=={"async_result":"verified_local_only"}

def test_simulation_does_not_claim_actuation():
    p=ToolPassport(id="sim", name="sim", description="synthetic", input_schema={"type":"object"},
                   safety_level="read", requires_approval=False)
    b=ToolPassportFunctionCalling(simulate=True)
    b.register_passport(p)
    result=run(b.execute_governed_tool("sim", {}))
    assert result["status"]=="simulated"
    assert result["result"]["simulated_output"].startswith("Would execute")
