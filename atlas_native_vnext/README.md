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

## v0.2 — PR61 ↔ PR63 offline source integration

- Added `native_synthesis/interop.py` to reconcile **separately version-pinned** Atlas Labs v32 PR #61 and Native Synthesis PR #63 review packets. Source and ontology editions, unit semantics, source Git blob, experiment digest and three inert destinations must agree; missing/legacy HSN and unsupported unit conversions HOLD.
- Added `native_synthesis/offline_receipts.py` and `native_synthesis/pipeline.py`: **real local SQLite staging transactions**, HMAC-obscured scope, replay/digest rejection across local restarts, monotone synthetic withdrawal epoch, and fail-closed HMAC-key rotation. No host rights or external delivery can result.
- Added an optional exact-source smoke script that verifies PR61's `labs/atlas_labs_v32.py` Git blob SHA-1 `eb667d20e8e80c463dbc84e1559d808dd803047c` **before import**. PR61 code is not vendored in this branch; source-dependent tests skip when absent.
- Independent local run with exact pinned PR61 source: **135/135 Python unittest methods passed** normally and with `python -O`; 1,024 synthetic adversarial checks passed; disposable PR61→PR63→SQLite smoke returned `LOCAL_REVIEW_PREPARED_NOT_SENT`.
- The current public documentation omits the account-private broker locator; earlier PR commits may still contain historical references and require separate repository-owner review before public release. No Git history was force-rewritten.

Runbook: [docs/ATLAS_NATIVE_PR61_PIPELINE_v02.md](docs/ATLAS_NATIVE_PR61_PIPELINE_v02.md). **The system is still SOURCE_ONLY and local-test verified, not CI or host verified, nor integrated into a live OpenAI/Atlas ONE/SwarmChat service.**

## Operating posture and known limitations

- SOURCE_TRACED = documented GitHub URLs/commits and separately verified representative blob SHAs; not all 31 upstream sources exhaustively reviewed.
- TESTED_LOCAL = standalone unit tests in a mock/offline runtime; no network/real D1 tests.
- CI_VERIFIED, INTEGRATED_HOST, PEER_RETURNED, SCIENTIFIC_VALIDATED, CANON_RATIFIED = **NOT PROVEN** here.
- A total of 273 accessible `atlaslattice` repositories were inventoried in the current source cut. This package curates **31 candidate assets**, not 273 integrated modules.
- `n8n` and `Dify` source-available variants have license restrictions; neither is copied into this package.
- The synthetic authority uses a local HMAC key for regression fixtures. Real identity, issuer trust, principal binding, D1 race semantics, network/stream withdrawal and durable exactly-once delivery require independently controlled platform interfaces.

**Build principle:** research can inspire work; only source, tests, rights and observed host effects establish what works.

## November 22, 2026 HST — integration and fail-closed source checkpoint

This is a **source-only** checkpoint. The native kernel does not create an Atlas ONE,
SwarmChat or Alexandria host session, grant source rights, run UWS/quantum hardware,
post peer messages, ratify CANON or deploy a Site.

Independent Atlas Labs PR #61 source is **not vendored** into this package.
Install the exact reviewed `labs/atlas_labs_v32.py` blob
`eb667d20e8e80c463dbc84e1559d808dd803047c` in a separate local checkout.
From this package's root, activate its optional cross-repository tests with:

```sh
PYTHONPATH="/path/to/atlas-labs-pr61-checkout:$PWD" python -m unittest discover -s tests -p 'test_*.py' -q
PYTHONPATH="/path/to/atlas-labs-pr61-checkout:$PWD" python -O -m unittest discover -s tests -p 'test_*.py' -q
python scripts/adversarial_preflight.py
```

Using that exact standalone PR #61 source, **138/138 tests passed with zero skips**
in ordinary and optimized Python. The 1,024-case deterministic synthetic
adversarial preflight passed separately; synthetic cases do not count as peer
exchanges or host acceptance. Without the separate checkout, 25 optional
cross-repository checks deliberately skip: do not quote `OK (skipped=25)` as
full integration coverage.

New source/negative controls added on this candidate branch:

- `OfflinePreparationStore`: near epoch `2**31-1`, complete a final local
  withdrawal and then hold every new stage; a saturated `withdraw()` returns
  HOLD, never a misleading simulated success. The saturated HOLD survives
  reopening the same SQLite file. **This is NOT a real host authorization
  revocation** or distributed exactly-once guarantee.
- GitHub source locators now reject `../`, `./` and repeated empty path segments.
  They remain self-reported candidate pointers: the code does not fetch or
  independently validate the referenced blob bytes or source licenses.
- Atlas ONE v2 **separate rewrite PR #8** remains an independent candidate.
  Its initial Work host-port omitted explicit tenant/account fields; this was
  repaired in draft PR #8 source. The installed host, D1 identity, and atomic
  sink commit remain independently UNVERIFIED; no live leak is alleged.

**Release HOLD:** GitHub Actions jobs are still reporting failure without
recorded steps; host principal/tenant binding, two-account D1 READ/RETURN,
actual model activation, durable receiver receipts, source privacy, publisher
license/rollback, real UWS/QPU/science execution and matched competitor benchmarks
must be separately observed. All research outputs are candidates until reviewed.

## November 23, 2026 — offline account-bound receipt contract (v0.3)

**Breaking, fail-closed local-only API amendment**, not a host-account grant:
`OfflinePreparationStore.stage(...,account='...')`,
`withdraw(...,account='...')`, and
`OfflineAtlasPipeline.prepare(...,account='...')` now bind the account ID
independently of tenant/principal/room/source. Absent or invalid account
returns a generic `HOLD`, including the pipeline entrypoint.

The HMAC scope namespace changed to
`atlas.native.offline-receipts.key/v0.3.account-bound`. Opening an old
v0.2 source-only SQLite ledger with the new code fails closed as
`INVALID_CONFIG`; preserve original files for offline audit and use a NEW
disposable v0.3 database. No automatic migration, deletion, or replay of old
receipts. Only the issuer-owned host can authenticate an actual account;
model-declared strings and the synthetic fixture do not.

**Executable source evidence:** PR #63 head
`7513eb74630d4661228da521aac8ba98eed7e2f8`;
the account scope store, pipeline, tests and runner were fetched back from
GitHub and matched their local Git blob hashes. Current local test run:
**144 test methods, 118 passed + 26 skipped** in normal and optimized Python.
The 26 skipped require a currently pinned separate Atlas Labs source checkout
and are **not passed tests**. A byte-pinned historical PR61 fixture was
different from newer PR61 HEAD, so current-host cross-repo parity is HOLD.

**Differential falsifier:** historical v0.2 cannot represent account B as
distinct: A and B under the same tenant/principal/room/request produce
NEW/DEDUP and one stored receipt. Repaired v0.3 scopes them separately:
NEW/NEW; B withdrawal leaves A's scope unchanged. This proves ONLY a
synthetic SQLite contract, not a real SwarmChat two-account/D1/network
boundary. CI issue #54 remains open: latest Eight Gates run
[45236508176](https://github.com/atlaslattice/atlas-lattice-providers/actions/runs/45236508176)
reported zero executed steps and missing logs. No merge/CANON/deployment.
