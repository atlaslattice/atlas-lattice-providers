# Atlas Native Synthesis v0.2 — PR61↔PR63 local integration and release holds

**Scope: additive, reversible, public-source-only. No CANON, science acceptance, private source access, host identity, SwarmChat posting, provider spend or production execution.**

## What is integrated now

The isolated Native Synthesis source from [PR63](https://github.com/atlaslattice/atlas-lattice-providers/pull/63) can call the separately source-pinned Atlas Labs `prepare()` and `catalog()` functions from [PR61](https://github.com/atlaslattice/atlas-lattice-providers/pull/61) *locally* and reconcile their independent schema representations before preparing a source-only receipt. The fusion fixture maps a `fusion-plasma` Atlas Labs candidate with its exact ORCS source URL, commit, blob, and Ariadne v0.7 registry pin to the Native `fusion` domain **without asserting semantically verified HSN equivalence**. No coordinate is invented: missing or historical ontology editions HOLD.

`native_synthesis/interop.py` requires both packages to return explicitly inert, coherent candidate states and the same canonical source/digest. It rejects mismatched source IDs, revision/blob, a forged `host_attested` flag, unexpected fields, Play/Palace/Brain/Work origin, observed measurements, unknown units, changed source/payload or mixed scientific types. It **does not silently convert** `bit→count`, `ratio→1` or other scientific unit semantics. All outputs say NOT_POSTED, NOT_DISPATCHED or NOT_WRITTEN and do not echo hypothesis/falsifier text.

`native_synthesis/offline_receipts.py` uses *actual SQLite transactions* for local preparatory deduplication, keyed by an HMAC of tenant/principal/room/purpose/source digest. It persists source-only request fingerprints and local epoch across restart, denies changed payloads under the same scoped request ID and retains old IDs as tombstones across synthetic withdrawal. The operator-provided HMAC key is pinned in a separate SQLite metadata record; opening an existing ledger with a different key fails closed rather than creating a new scope namespace and admitting old request IDs again. Key rotation requires a deliberate reviewed migration, not a silent reset. It **does not** implement true host authorization, network exactly-once, D1 rights fencing, model wake or receiver read acknowledgments. The input scope is self-declared; neither code nor test converts that into platform identity.

`native_synthesis/pipeline.py` combines both source preparers and that local SQLite recorder. Result: `LOCAL_REVIEW_PREPARED_NOT_SENT`, never a hosted delivery. Only public synthetic fixture data is used.

## Exact tested source and commands

- Source pin for Atlas Labs PR61 `labs/atlas_labs_v32.py`: Git blob SHA-1 `eb667d20e8e80c463dbc84e1559d808dd803047c`. The smoke-runner checks source *bytes before importing*, rejects anything else and only then imports locally. The package never vendors PR61 or external upstream code.
- Native PR63 source parent at integration start: `59a994b36ed404f80c3507eccec7ee1eaea7eb11`; current head must be independently refreshed before review/merge.
- Separate public ORCS source is `GPTWORK_START_HERE_STARS_2_0.md` at commit `ea2ba0133338b316b01c62f83c97bd845c61a9f0`, blob `ef51e2a526e27119b9504ba8a13eabf80b975f01`. The scientific document itself explicitly holds implementation pending scientific approval and is not simulation validation.

```sh
cd atlas_native_vnext
PYTHONPATH=.:/path/to/exact/PR61/source \
  python -m unittest discover -s tests -v
PYTHONPATH=.:/path/to/exact/PR61/source \
  python -O -m unittest discover -s tests -q
python scripts/run_local_pipeline.py \
  --labs-source /path/to/exact/PR61/source/labs/atlas_labs_v32.py \
  --input examples/pr61-native-fusion.json
python scripts/adversarial_preflight.py
```

On an installation that does **not** provide the exact PR61 source, source-dependent integration tests are **SKIPPED**, not counted as passing independently. This is intentional to avoid treating an unreviewed package import as trusted.

## Release-critical gaps (all HELD)

1. **GitHub Actions:** original 0-step runner failures must be diagnosed by GitHub account/organization owner; source-only local tests do not imply CI success. Require assigned runner, executed steps, real logs, correct exact HEAD.
2. **OpenAI-native host integration:** approved Responses/Agents SDK runtime, real principal+tenant+conversation identity, server-owned tool registry, cost controls, and a genuine trusted grant issuer. Never infer permission from text/metadata or synthetic HMAC.
3. **SwarmChat broker:** exact live Site SHA, authorized Work only, real room seq readback, separate actual peer read/reply; host handles revocation at storage READ and receiver-side RETURN/commit, per-chunk and account switch; never join/subscribe/wake automatically.
4. **Atlas ONE/Alexandria:** actual task receipt with idempotency, graph edge candidate and reviewer dissent, no cross-edition `SAME_AS` without independent adjudication. The existing PRs remain draft.
5. **Scientific validation:** real solver input/output revision, measurement calibration, Monte Carlo stochastic error, controlled units, uncertainty covariance and blind holdouts; physical QPU/fusion production not asserted.
6. **Licensing and privacy:** per-file upstream license and dependency notices, separate non-public assets, no private broker locator in public release, credential sweep and history-risk assessment. No bulk-vendor of source-available code without terms review.
7. **Deployment/rollback:** separately authorized publishing decision, two-account negative host tests, exact served build, rollback/canary and rights restoration verification. No automatic CANON promotion.
8. **Competitive comparison:** preregister same tasks and model/cost/latency/accessibility fixtures; collect data from real peer baselines before any superiority claim.

Source receipt ≠ hosted proof. Real user rights and legal licensing are independent of structural type validation.
