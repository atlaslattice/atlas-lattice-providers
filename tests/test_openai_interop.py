import asyncio
import json
from pathlib import Path

from providers.openai import ResponsesAPISpine, StructuredOutputSchemaSpine, ToolPassportFunctionCalling, ToolPassport, OpenAITracingToGoldenTrace, EvalsBullshitOlympicsBridge, WorkloadIdentitySecretsHygiene
from providers.provider_openai import OpenAIProvider


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_responses_spine_simulation():
    spine = ResponsesAPISpine(simulate=True)
    out = run(spine.create_response(input="hello lattice"))
    assert out["claim_packet"]["openai_live_api"] is False
    assert "hello lattice" in out["response"]["output"]


def test_structured_claim_validation_and_tool_schema():
    schema = StructuredOutputSchemaSpine(simulate=True)
    claim = schema.validate_claim_packet({"claim_text": "receipt", "epistemic_certainty": 1.5})
    assert claim.epistemic_certainty == 1.0
    passport = ToolPassport(id="p1", name="lattice_echo", description="Echo safely", input_schema={"type": "object", "properties": {"text": {"type": "string"}}})
    registered = schema.register_tool_passport(passport)
    assert registered["openai_tool"]["type"] == "function"


def test_tool_passport_safety_gate():
    t = ToolPassportFunctionCalling(simulate=True)
    t.register_passport(ToolPassport(id="admin1", name="admin_tool", description="Admin", input_schema={"type": "object"}, safety_level="admin"))
    out = run(t.execute_governed_tool("admin_tool", {}, approved=False))
    assert out["status"] == "requires_human_approval"


def test_trace_persistence(tmp_path):
    tracer = OpenAITracingToGoldenTrace(simulate=True, trace_dir=str(tmp_path))
    out = run(tracer.record_openai_trace("trace-1", payload={"ok": True}))
    assert out["golden_trace_hash"].startswith("0x")
    assert Path(out["persisted_to"]).exists()


def test_eval_dataset_export_and_grade(tmp_path):
    bridge = EvalsBullshitOlympicsBridge(simulate=True, eval_dir=str(tmp_path))
    ds = run(bridge.create_eval_dataset("demo", [{"input": "x", "expected": "y"}]))
    assert Path(ds["dataset_path"]).exists()
    grade = run(bridge.run_bullshit_as_grader("demo", "demo-0", "y"))
    assert grade["eval_result"]["score"] >= 0


def test_hygiene_and_provider_boot():
    h = WorkloadIdentitySecretsHygiene(simulate=True)
    report = h.check_environment()
    assert "OPENAI_API_KEY" in report["report"]["present"]
    provider = OpenAIProvider(simulate=True)
    assert provider.name == "openai"
