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


## Host authorization boundary (fail closed, candidate)

`ToolPassportFunctionCalling` treats its caller-supplied `approved` flag as untrusted data; passing `approved=True` never authorizes an operation. The constructor may accept an `authorization_verifier(passport, arguments, actor)` **from the trusted host integration only**. It must return the literal boolean `True` for the exact operation, otherwise approval fails closed. A verifier exception also denies authorization. Do not expose the verifier as a model-call parameter or construct it from an unauthenticated caller's declaration.

- All `write`, `destructive`, and `admin` passports require host verification; explicit `requires_approval=True` additionally protects `read` passports. Unknown safety labels are denied.
- Without the trusted verifier, protected execution returns `requires_human_approval` with `authorization: HOST_VERIFIER_REQUIRED`.
- Non-simulated execution with no real executor returns `executor_unavailable`, not a forged execution receipt.
- CI may exercise a *test-only verifier* with synthetic arguments; this is not deployed identity, authorization at return, OAuth, verified user intent, or production tool dispatch.
- This bridge does **not** yet implement the trusted host integration. Until one is independently reviewed and tested, do not enable protected live operations.

## Explicit remaining merge gates

- Verify the host-controlled authorization callback and its binding to authenticated principal, operation, arguments, scope, expiry, revocation and consent at the moment of dispatch.
- Audit tool-passport schema validation, source rights, receipt storage and secret handling.
- Verify current head CI, dependent application integration, and branch freshness.
- Retain CANDIDATE / NOT CANON and no deployment or endorsement claims.

## Candidate-only ClaimPacket review boundary

`StructuredOutputSchemaSpine.validate_claim_packet()` accepts **untrusted** model/caller output. The caller may declare `review_state` and `metadata.source`, but neither is treated as host-reviewed status. The actual resulting `review_state` is always `PENDING_REVIEW`, and reserved metadata identifies `UNVERIFIED_CANDIDATE`. Original assertions are preserved under `declared_review_state` and `untrusted_input_metadata` for dissent and provenance. The verifier does not assign CANON, grant rights, or validate science.

A future host-mediated review action needs its own authenticated reviewer, source-cut and rights-at-return checks. Do not implement approval by passing `review_state=APPROVED` through a model-produced ClaimPacket.
