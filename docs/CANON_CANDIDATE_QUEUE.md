# Canon Candidate Queue — public review lane v0.1

**STATUS: CANDIDATE / CANON: NO / DEPLOYMENT: NO / AUTHORITY: NONE**

This queue implements [SwarmHub issue #18](https://github.com/atlaslattice/atlas-lattice-providers/issues/18) as an inspectable **review backlog**, never an autonomous decision engine. No item below is approved, ratified, released, deployed, endorsed, or a source of authority. It is a triage view of public GitHub artifacts, not a dump of private Play/Work threads. Decisions require an independently authenticated, scope-specific human-root process.

## Queue

| Candidate ID | Artifact / source | Why useful | Evidence currently inspected | Risk / contradiction | Review required | Human-root decision | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CCQ-001 | [Children Delta Ledger](CHILDREN_OF_THE_GPT_SWARM_DELTA_LEDGER.md); [SwarmHub #3](https://github.com/atlaslattice/atlas-lattice-providers/issues/3) | Proposed coordination inventory | Default-branch file fetched 2026-11-22; its body was a **90-byte placeholder**, not the claimed comprehensive ledger | Overstated completeness; actual detailed ledger and source rights not yet confirmed | Retrieve actual non-placeholder source, source-root/export status, raw trace and license/privacy review | **PENDING — NO GRANT** | CANDIDATE / evidence blocked |
| CCQ-002 | [NO MERGED MIND issue #5](https://github.com/atlaslattice/atlas-lattice-providers/issues/5); [receipts index](SWARM_RECEIPTS.md) | Separate identities and attribution across A2A | Issue #5 and receipts index visible; executable enforcement path and run receipts not verified | Natural-language constraint could be mistaken for actual enforcement; voice/persona may be confused with identity | Independent behavior tests for bus, Sentinel and packet validation, preservation of negative cases | **PENDING — NO GRANT** | CANDIDATE / implementation unverified |
| CCQ-003 | [A2A PROTOCOL.md](../a2a/PROTOCOL.md); [SwarmHub #5](https://github.com/atlaslattice/atlas-lattice-providers/issues/5) | Messages + receipts across independent continua | Default-branch protocol fetched 2026-11-22; its body was an **81-byte placeholder** | Protocol prose not evidence of implemented authenticated routing; private messages might leak across scopes | Full protocol, tests, attribution, opt-in, replay and rights checks | **PENDING — NO GRANT** | CANDIDATE / evidence blocked |
| CCQ-004 | [Coordination Without Fusion demonstration in receipts index](SWARM_RECEIPTS.md) | Explain the intended child → A2A → receipt → claim chain | Example YAML is visible **as documentation**; dedicated demo file not found at docs/COORDINATION_WITHOUT_FUSION_DEMO.md | A synthetic/example chain is not evidence that independent actors interacted or a runtime exists | Reproducible external test fixture, authentic event IDs, no fake participants, no Play-to-Work ingestion | **PENDING — NO GRANT** | CANDIDATE / demo only |

**These are seed records, not new discoveries or ratifications.** Their contradictions and limitations are retained verbatim in the table. Actual source provenance is still incomplete.

## Mandatory packet fields

For each proposed addition or update:

```yaml
candidate_id: CCQ-...
artifact_ref: canonical source URL or repo path
source_scope: repository, branch, commit, rights status, raw_export_status
why_useful: bounded expected use
evidence_refs: []       # empty is honest; not a negative finding by itself
risks: []
contradictions: []
review_required: exact reviewer and independent gate
human_root_decision: PENDING   # never silently infer APPROVED
status: CANDIDATE
canon: false
deployment: false
authority: none
source_continuum_id: explicit
target_continuum_id: null
preservation_ref: fossil/archive location or MISSING
```

Empty or unknown receipt fields remain **unknown**, not complete. No objective evidence of human-root permission arises from copying `APPROVED` into YAML.

## Promotion boundaries

1. **Queue entry → source retrieval:** fetch exact branch/commit and inspect full raw record, access scope, export state, rights and corrections. A filename, repository issue, model summary or graph centrality is insufficient.
2. **Source retrieval → review:** independent reviewer records reproducible tests or an explicit non-testable reason, contradictory evidence, rights concerns and dissent. Preserve failed or superseded branches per INV-0.
3. **Review → decision:** present a scoped, version-specific candidate for a real human governance action. Queue maintainers cannot approve themselves or infer consent from existing content.
4. **Decision → any canon/deployment:** require a separately verified grant identifying exact version, continuum, purpose, rights, audience, rollback and authorized human. Even valid test results do not self-promote.
5. **Rejected/blocked:** retain source, dissent and receipt links; mark why promotion failed rather than delete. Private Play, resident conversations, identity/consent material, and confidential Work sources do not cross boundaries automatically.

## Existing checkpoints

The [receipt scorer](RECEIPT_COMPLETENESS_SCORE.md) added by [PR #45](https://github.com/atlaslattice/atlas-lattice-providers/pull/45) reports documentary completeness only, not truth. The strict [CoordinateResolver](COORDINATE_RESOLVER_CONTRACT.md) added by [PR #46](https://github.com/atlaslattice/atlas-lattice-providers/pull/46) permits candidate routing but cannot ratify anything.

This queue's current acceptance is limited to **documentation present with four seed candidates and explicit ungranted review gates**. The missing source receipts, executable coordination demonstration and runtime permissions remain open tasks.

**Keeper:** The queue can remember a proposal. It cannot make the proposal true.

## Separate adopted project decision — 23 November 2026

The queue items and historical master index above retain their original status. Explicit owner decision [ATLAS-UHM-CANON-20261123-001](canon/ATLAS_UNIFIED_HYPERMATRIX_20261123.md) adopts the independent HyperMatrix architecture and revisable functional defaults. The active project pointer is `canon/index/active_project_canon.json`; it grants no runtime or Notion permissions and does not ratify unrelated candidates. [Shared amendment discussion](https://github.com/atlaslattice/Atlas-Intelligence/issues/40).

