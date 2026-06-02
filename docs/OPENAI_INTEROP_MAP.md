# OpenAI Interop Map — Atlas Lattice Providers

Status: candidate implementation map for adversarial review.

## Primary mapping

| Atlas / Lattice component | OpenAI-facing primitive | Repo implementation |
|---|---|---|
| ClaimPacket | Structured output schema | `providers/openai/structured_output_schema_spine.py` |
| ToolPassport | Function/tool schema | `providers/openai/tool_passport_function_calling.py` |
| Grok/Lattice routed response | Responses API call | `providers/openai/responses_api_spine.py` |
| GoldenTrace | Trace/thread/run receipt | `providers/openai/openai_tracing_to_golden_trace.py` |
| Bullshit Olympics | Eval grader / dataset generator | `providers/openai/evals_bullshit_olympics_bridge.py` |
| MCP / provider surface | OpenAI provider wrapper | `providers/provider_openai.py` |
| Agent roles | Agents SDK-style manifest | `providers/openai/agents_sdk_adapter.py` |
| Deployment hygiene | Environment and credential readiness | `providers/openai/workload_identity_secrets_hygiene.py` |

## Operating mode

The repo must boot in simulation mode for CI and public review. Live mode is local/deploy only and requires `OPENAI_API_KEY` plus explicit `simulate=False`.

## Acceptance tests

- OpenAI modules compile.
- `tests/test_openai_interop.py` passes without credentials.
- `scripts/openai_interop_check.py` prints readiness status.
- ToolPassport admin/destructive calls require approval.
- GoldenTrace and eval bridges persist JSONL artifacts.

## Next patches

1. Wire `OpenAIProvider` into `multi_provider_mcp_server.py` provider registry.
2. Convert selected MCP tools into ToolPassports automatically.
3. Add live local smoke command for `ResponsesAPISpine(simulate=False)`.
4. Add file-search bridge for Notion/GitHub/GDrive corpora.
5. Add guardrail result schema for human review gates.
