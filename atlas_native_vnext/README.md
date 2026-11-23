# Atlas Native Synthesis v0.1 — source-only OpenAI-native interoperability kernel

**CANDIDATE. NOT CANON. NOT HOSTED. NOT AN AUTHENTICATED SWARMCHAT / ATLAS ONE BRIDGE. NO PROVIDER SPEND OR THIRD-PARTY SOURCE CODE VENDORED.**

This additive, reversible implementation starts from the real `atlaslattice` ecosystem and composes a common *review contract*, not an unauthorized replacement of existing applications. The package contains **original Python code** plus a source-pinned capability manifest. It does not clone or incorporate upstream copyrighted implementations. Integration of upstream modules is proposed through independently authorized and licensed ports.

## What actually runs now

- A 31-asset curated machine-readable capability inventory (Atlas, UWS, science, quantum, agent/dev/3D/data candidates). All metadata is `NOT_HOST_VERIFIED`.
- A fail-closed public Noosphere **272-repository** metadata-only triage (when supplied the actual public registry file; rejects private/mixed scopes) and public-source experiment intake, explicit scientific units/Decimal values, pinned Ariadne v0.7 coordinate, hypothesis, negative-control/falsifier, and human-root hold.
- A **typed A+B=C** cross-domain candidate requiring distinct source records, different lab domains, explicit alternatives and a falsifier; does **not** claim causality or scientific efficacy.
- Three *inert* output envelopes: `Atlas ONE task candidate not dispatched`, `SwarmChat Work preview not posted`, `Alexandria graph candidate not written`.
- Strict OpenAI **Responses API** function tool schemas and `function_call_output` adaptation. These execute locally only; the OpenAI model is NOT called.
- Preview-only MCP tool descriptions, A2A skills, UWS metadata-read plan, quantum/numerical backend selection, and constrained graph view data.
- An in-memory source-only candidate receipt journal with append-only hash chain and request-id collision/replay checks. This is not durable D1 or exactly-once delivery.
- A **synthetic** host-authority reference model with signed grants, current epoch recheck, and withdrawal. It is not platform identity verification and must never be exposed as a public auth endpoint.

## Run, no dependencies or API keys

```sh
cd atlas_native_vnext
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -q
python -m native_synthesis status
python -m native_synthesis catalog --family quantum
python -m native_synthesis experiment < examples/experiment-stub.json
python -m native_synthesis fusion < examples/cross-domain-stub.json
python -m native_synthesis inventory < path/to/public_repo_inventory_2026-11-22.json
python scripts/adversarial_preflight.py
python -m native_synthesis response-tools
python -m native_synthesis response-call < examples/openai-response-call.json
```

**No network calls are made**. All sample data are synthetic; public source URLs and Git SHAs are locators, not evidence of a successful content retrieval, external permission or valid scientific measurement.

## Native OpenAI integration choice

Use **OpenAI Responses API function calling** for a bounded tool-loop (source-safe tool results) or **OpenAI Agents SDK** for orchestration/handoffs/guardrails/tracing; do not rebuild those SDK internals. In either case, the host must authenticate and authorize before connecting live tools. `native_synthesis.responses.function_tools()` builds strict Responses function schemas. `handle_function_call()` accepts only explicit allowlisted function calls and formats `function_call_output` without making an API request. The official Responses tool format is documented at https://developers.openai.com/api/docs/guides/function-calling .

Keep independent Work permissions, real peer identity, source/revision rights, source-specific licenses, tool approval, recipient egress rights, experiment evidence state and human-root CANON authorization **outside** model-supplied text. Real API invocation requires separately supplied host secrets, consent, spend approval, a verified server and a responsible operator.

## Why this is not a blind rewrite

`atlaslattice` includes current native projects, obsolete designs, forks, scratch files, research manuscripts and private source surfaces. A repository title, GitHub fork or large code volume does not prove product readiness. Instead:

1. Pin upstream/fork source revision and license; compare actual code and update drift.
2. Select **one responsible implementation** per overlapping responsibility (agent runtime, search, graph, orchestration, browser execution).
3. Wrap with independent authority and provenance rather than copying or merging external trees.
4. Require deterministic negative tests, two-account isolation, published scientific definitions, cost controls, rollback and current hosted proof.
5. Integrate only reviewed code in **staged, reversible commits**. No public/private access changes, production deployment, private-mode ingestion, hardware claims or automatic CANON adoption.

See `docs/ARCHITECTURE.md`, `docs/OSS_SELECTION.md`, `docs/COMPETITOR_EVAL.md`, and `docs/HOST_ACCEPTANCE.md`.

## Operating posture and known limitations

- SOURCE_TRACED = documented GitHub URLs/commits and separately verified representative blob SHAs; not all 31 upstream sources exhaustively reviewed.
- TESTED_LOCAL = standalone unit tests in a mock/offline runtime; no network/real D1 tests.
- CI_VERIFIED, INTEGRATED_HOST, PEER_RETURNED, SCIENTIFIC_VALIDATED, CANON_RATIFIED = **NOT PROVEN** here.
- A total of 273 accessible `atlaslattice` repositories were inventoried in the current source cut. This package curates **31 candidate assets**, not 273 integrated modules.
- `n8n` and `Dify` source-available variants have license restrictions; neither is copied into this package.
- The synthetic authority uses a local HMAC key for regression fixtures. Real identity, issuer trust, principal binding, D1 race semantics, network/stream withdrawal and durable exactly-once delivery require independently controlled platform interfaces.

**Build principle:** research can inspire work; only source, tests, rights and observed host effects establish what works.
