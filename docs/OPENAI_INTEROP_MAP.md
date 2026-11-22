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


## ToolPassport registration integrity

The local ToolPassport registry accepts a passport under both `id` and `name`. Registration must reject a new passport if **either** key already denotes a different passport, including a changed safety policy under the same identifier. This prevents a lower-safety alias from silently replacing an administrative tool. Identical registrations are idempotent.

Registration validates identifier/name, input-schema type, safety label and boolean approval flag **before** writing either the dispatch registry or the structured-output registry. Invalid or colliding entries must leave both registries unchanged. This does not authenticate the host, authorize tool execution, or grant CANON; those remain separate gates. Regression tests in `tests/test_openai_interop.py` cover aliases, conflicting IDs, idempotence and partial-registration failures.

## Evals evidence truthfulness (no fake scores)

`EvalsBullshitOlympicsBridge` no longer invents a numerical grade or a backend grader identity when it has not run an evaluator. Every persisted result includes an explicit `status` and `score_basis`:

- `NOT_RUN`: simulated run or no available grader. `score=null`, `grader="none"`, `score_basis="NONE"`.
- `GRADER_FAILED`: the selected backend raised an exception. `score=null`; no private exception text appears in the exported evaluation record.
- `INVALID_GRADE`: backend response lacks a real, finite numeric score in [0,1]. No silently supplied default or clamping.
- `SCORED`: backend was invoked and returned a valid score. `score_basis="BACKEND_RESPONSE_UNVERIFIED"` means neither source truth, evaluator independence, scientific validation nor CANON were established.

`simulate=True` never calls an explicitly supplied evaluator. Changes to downstream readers should distinguish `score=null` from zero performance and reject unreviewed `SCORED` as a sufficient release gate. Tests in `tests/test_eval_truthfulness.py` cover the original false-positive case, malformed/nonfinite grades, backend failures and persistence. This is a **local contract correction**, not verification of an external grader or a hosted rollout.


## Evaluation dataset filename integrity (v0.4, offline source-only)

Previously, dataset labels were normalized by replacing punctuation with underscores, so labels such as `a/b` and `a_b` mapped to the same JSONL path and the second dataset silently truncated the first. This was reproduced against the v0.3 module.

- Dataset names are **identifiers, not paths**: only ASCII letters, digits, hyphen and underscore; length 1–80. Ambiguous, internationalized or path-like labels fail explicitly instead of being silently normalized. `None` and the empty string retain the historical default `atlas_lattice_eval`.
- `create_eval_dataset` prepares serialization before opening and uses exclusive `x` creation. A duplicate name raises `FileExistsError`; existing files and symlinks are not followed or overwritten. In-memory mappings change only after successful file write.
- The same checked name applies to result lookup. Existing safe-name datasets remain readable across process restarts.
- Case-only names may be distinct on case-sensitive hosts; on a case-insensitive filesystem the second create must fail, **never replace** the first.
- The local test file `tests/test_eval_dataset_integrity.py` includes malformed labels, alias-collision reproduction, restart persistence, symlinks, failed writes and eight concurrent writers. The test alone does not prove deployed host behavior.

**Compatibility / migration:** Legacy datasets created under lossy-normalized names remain untouched. They must be individually mapped to a new safe label under independent source review, not silently renamed, imported or overwritten. New results are still local append-only JSONL by convention, **not** a tamper-evident ledger or current-rights enforcement. No CANON, verified scientific claim, authenticated principal, or runtime deployment follows from this patch.
