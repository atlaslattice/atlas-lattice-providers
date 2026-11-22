import asyncio
from pathlib import Path

from providers.openai import ResponsesAPISpine, StructuredOutputSchemaSpine, ToolPassportFunctionCalling, ToolPassport, OpenAITracingToGoldenTrace, EvalsBullshitOlympicsBridge, WorkloadIdentitySecretsHygiene
from providers.provider_openai import OpenAIProvider


def run(coro):
    return asyncio.run(coro)


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


def test_untrusted_approval_flag_cannot_authorize_protected_tools():
    for safety in ("write", "destructive", "admin"):
        dispatched = []
        bridge = ToolPassportFunctionCalling(
            simulate=False, executor=lambda name, args: dispatched.append(name) or {"ok": True}
        )
        bridge.register_passport(
            ToolPassport(id=f"tool-{safety}", name=f"tool_{safety}",
                         description="Test only", input_schema={"type": "object"},
                         safety_level=safety, requires_approval=False)
        )
        direct = run(bridge.execute_governed_tool(f"tool_{safety}", {}, approved=True))
        indirect = run(bridge.run("execute", tool_name=f"tool_{safety}", arguments={}, approved=True))
        assert direct["status"] == "requires_human_approval"
        assert indirect["status"] == "requires_human_approval"
        assert direct["authorization"] == "HOST_VERIFIER_REQUIRED"
        assert dispatched == []


def test_explicit_approval_requirement_on_read_tool_is_enforced():
    bridge = ToolPassportFunctionCalling(simulate=False, executor=lambda n, a: {"ok": True})
    bridge.register_passport(ToolPassport(id="sensitive-read", name="read_sensitive",
                         description="Test only", input_schema={"type": "object"},
                         safety_level="read", requires_approval=True))
    assert run(bridge.execute_governed_tool("read_sensitive", {}, approved=True))["status"] == "requires_human_approval"


def test_host_verifier_requires_literal_true_and_fails_closed_on_error():
    passport = ToolPassport(id="protected", name="protected_tool", description="Test only",
                            input_schema={"type": "object"}, safety_level="admin")
    for verifier in (lambda p, a, actor: "yes",
                     lambda p, a, actor: 1,
                     lambda p, a, actor: False):
        bridge = ToolPassportFunctionCalling(simulate=False, executor=lambda n, a: {"ok": True},
                                             authorization_verifier=verifier)
        bridge.register_passport(passport)
        assert run(bridge.execute_governed_tool("protected_tool", {}))["status"] == "requires_human_approval"

    def failing_verifier(p, a, actor):
        raise RuntimeError("authorization backend unavailable")

    bridge = ToolPassportFunctionCalling(simulate=False, executor=lambda n, a: {"ok": True},
                                         authorization_verifier=failing_verifier)
    bridge.register_passport(passport)
    assert run(bridge.execute_governed_tool("protected_tool", {}))["status"] == "requires_human_approval"


def test_host_adapter_verifier_can_authorize_exact_request():
    calls = []
    bridge = ToolPassportFunctionCalling(
        simulate=False,
        executor=lambda name, args: calls.append((name, args)) or {"executed": True},
        authorization_verifier=lambda p, a, actor: p.id == "a1" and a == {"key": "value"} and actor == "host"
    )
    bridge.register_passport(ToolPassport(id="a1", name="write_tool", description="Test only",
                         input_schema={"type": "object"}, safety_level="write"))
    assert run(bridge.execute_governed_tool("write_tool", {"key": "wrong"}, actor="host"))["status"] == "requires_human_approval"
    result = run(bridge.execute_governed_tool("write_tool", {"key": "value"}, actor="host"))
    assert result["status"] == "executed"
    assert calls == [("write_tool", {"key": "value"})]


def test_simulation_does_not_call_executor_and_live_without_executor_is_not_executed():
    calls = []
    passport = ToolPassport(id="safe", name="safe_read", description="Test only",
                            input_schema={"type": "object"}, safety_level="read", requires_approval=False)
    simulation = ToolPassportFunctionCalling(simulate=True,
                executor=lambda n, a: calls.append(n) or {"ok": True})
    simulation.register_passport(passport)
    assert run(simulation.execute_governed_tool("safe_read", {}))["status"] == "simulated"
    assert calls == []
    live = ToolPassportFunctionCalling(simulate=False)
    live.register_passport(passport)
    assert run(live.execute_governed_tool("safe_read", {}))["status"] == "executor_unavailable"
    assert calls == []


def test_unknown_safety_level_is_rejected_before_registration():
    bridge = ToolPassportFunctionCalling(simulate=False, executor=lambda n, a: {"ok": True})
    try:
        bridge.register_passport(ToolPassport(id="u1", name="unknown_tool", description="Test only",
                             input_schema={"type": "object"}, safety_level="unsupported", requires_approval=False))
    except ValueError as exc:
        assert "safety_level" in str(exc)
    else:
        raise AssertionError("unsafe passport was registered")
    assert bridge._passports == {}


def test_untrusted_model_claim_cannot_self_approve_or_spoof_source():
    schema = StructuredOutputSchemaSpine(simulate=True)
    raw = {
        "id": "claim-untrusted",
        "claim_text": "unverified statement",
        "review_state": "APPROVED",
        "metadata": {"source": "fake_trusted_reviewer", "authority": "CANON"}
    }
    claim = schema.validate_claim_packet(raw)
    assert claim.review_state == "PENDING_REVIEW"
    assert claim.metadata["source"] == "openai_structured_spine"
    assert claim.metadata["trust_boundary"] == "UNVERIFIED_CANDIDATE"
    assert claim.metadata["declared_review_state"] == "APPROVED"
    assert claim.metadata["untrusted_input_metadata"] == raw["metadata"]


def test_rejected_and_non_dict_input_metadata_are_not_host_reviews():
    schema = StructuredOutputSchemaSpine(simulate=True)
    for state in ("APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED", "NOT_A_REVIEW_STATE"):
        claim = schema.validate_claim_packet({"claim_text": "candidate", "review_state": state,
                                              "metadata": "unstructured"})
        assert claim.review_state == "PENDING_REVIEW"
        assert claim.metadata["source"] == "openai_structured_spine"
        assert claim.metadata["declared_review_state"] == state
        assert claim.metadata["untrusted_input_metadata"] == {}


def _test_passport(id, name, safety="read", approval=False, input_schema=None):
    return ToolPassport(id=id, name=name, description="Synthetic collision test",
                        input_schema={"type": "object"} if input_schema is None else input_schema,
                        safety_level=safety, requires_approval=approval)


def _must_reject_collision(bridge, candidate):
    try:
        bridge.register_passport(candidate)
    except ValueError as exc:
        assert "alias collision" in str(exc)
    else:
        raise AssertionError("ToolPassport collision accepted")


def test_passport_name_cannot_shadow_existing_protected_id():
    bridge = ToolPassportFunctionCalling(simulate=True)
    original = _test_passport("protected-id", "protected-tool", safety="admin", approval=True)
    bridge.register_passport(original)
    _must_reject_collision(bridge, _test_passport("other-id", "protected-id"))
    assert bridge._passports["protected-id"] == original
    assert bridge._passports["protected-tool"] == original
    assert len(bridge.get_openai_tools()) == 1


def test_passport_id_cannot_shadow_existing_name():
    bridge = ToolPassportFunctionCalling(simulate=True)
    original = _test_passport("protected-id", "protected-tool", safety="admin")
    bridge.register_passport(original)
    _must_reject_collision(bridge, _test_passport("protected-tool", "other-name"))
    assert "other-name" not in bridge._passports
    assert bridge._passports["protected-tool"] == original


def test_repeated_id_cannot_replace_safety_policy_but_identical_is_idempotent():
    bridge = ToolPassportFunctionCalling(simulate=True)
    original = _test_passport("same-id", "same-name", safety="admin")
    bridge.register_passport(original)
    _must_reject_collision(bridge, _test_passport("same-id", "same-name", safety="read"))
    assert bridge._passports["same-id"].safety_level == "admin"
    assert bridge.schema_spine._registry["same-id"].safety_level == "admin"
    bridge.register_passport(original)
    assert len(bridge.get_openai_tools()) == 1


def test_invalid_schema_rejected_without_partial_registration():
    bridge = ToolPassportFunctionCalling(simulate=True)
    invalid = _test_passport("invalid", "bad-schema", input_schema=[])
    try:
        bridge.register_passport(invalid)
    except ValueError as exc:
        assert "input_schema" in str(exc)
    else:
        raise AssertionError("invalid schema accepted")
    assert bridge._passports == {}
    assert bridge.get_openai_tools() == []


def test_schema_registry_mismatch_does_not_allow_alternate_alias():
    bridge = ToolPassportFunctionCalling(simulate=True)
    original = _test_passport("s1", "first-tool", safety="admin")
    bridge.schema_spine.register_tool_passport(original)
    _must_reject_collision(bridge, _test_passport("s1", "second-tool", safety="read"))
    assert bridge._passports == {}
    assert bridge.schema_spine._registry["s1"] == original
