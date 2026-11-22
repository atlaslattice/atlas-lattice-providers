# SwarmHub public receipt proof index v1 — point-in-time audit

**Status: CANDIDATE. Canon: no. Deployment: no. Authority: none.**

**Date:** 2026-11-22. **Scope:** selected publicly inspectable files at `atlaslattice/atlas-lattice-providers` default branch `main`, with historical claims preserved as *reported*. This register is **not** a full repository census, CI attestation, proof of source truth, personal identity, rights clearance, agency, or scientific validation.

Read first: [original receipts ledger](SWARM_RECEIPTS.md), [candidate queue](CANON_CANDIDATE_QUEUE.md), [receipt completeness rubric](RECEIPT_COMPLETENESS_SCORE.md). All links must be read under their original permissions. No private Play exports were copied into Work.

## Readback status legend

- **visible-content**: file was fetched and substantive contents inspected; factual claims *within* the file not necessarily verified.
- **visible-stub**: file fetched but is only a placeholder or summary; full-source completeness **blocked**.
- **reported**: an index, issue or agent says an artifact exists, but the full artifact has not been independently fetched from the claimed location.
- **404-at-claimed-path**: default-branch fetch returned 404; does **not** prove a file never existed on other branches or private systems.
- **branch-only**: a verifiable PR or alternate ref exists, not the same as default-branch integration.
- **test-local**: tests were reportedly run in an isolated local copy; not a hosted CI run.
- **CI-unknown**: connector status-check array empty; cannot claim success or failure of GitHub Actions.

A Git blob SHA identifies **file content**. A Git commit SHA identifies a **revision**. Do not substitute one for the other.

## Readback registry

| Artifact / report | Exact GitHub path | Status | Blob SHA / bytes | Commit or build receipt |
| --- | --- | --- | --- | --- |
| Original Swarm Receipts Index | [docs/SWARM_RECEIPTS.md](SWARM_RECEIPTS.md) | visible-content | `712ecda54aadbd4eb2222f2a9096bdac244f5e3b` / 7,476 (pre-this-index) | Historical document; independent per-row commits missing |
| Children Delta Ledger | [docs/CHILDREN_OF_THE_GPT_SWARM_DELTA_LEDGER.md](CHILDREN_OF_THE_GPT_SWARM_DELTA_LEDGER.md) | **visible-stub** | `c82016fb4426016ac59482a813b54a6106ca5c61` / 90 | Full ledger and raw export unknown |
| A2A Protocol | [a2a/PROTOCOL.md](../a2a/PROTOCOL.md) | **visible-stub** | `d42e40400dc611150a283726c8b0beffcc2b9724` / 81 | Executable message bus not proven |
| TransparentPacket96 candidate code | [core/transparent_packet96.py](../core/transparent_packet96.py) | visible-content | `452ec1e95fb2b0a789f9455624bd64e6e57865aa` / 6,088 | Current file exists; standalone test and router coupling not established here |
| Orchestrator enforcement at alleged path | `core/orchestrator_prime.py` | **404-at-claimed-path** | unavailable | Alternative path/branch search required |
| Sentinel enforcement at alleged path | `core/sentinel_agent.py` | **404-at-claimed-path** | unavailable | Alternative path/branch search required |
| Dragon Play receipt at alleged path | `dream-specs-build/aetherforge-dragons-play/session_receipt.json` | **404-at-claimed-path** | unavailable | May exist in private room/local storage; not ingested |
| Archive mirror at alleged path | `archive/reports/SWARMHUB_MIRROR_FROM_PROVIDERS_20260603.json` | **404-at-claimed-path** | unavailable | Cross-hub mirror not verified |
| Receipt completeness scorer | [scripts/receipt_completeness.py](../scripts/receipt_completeness.py) | visible-content / test-local | `92859287b6ade2530059f8f52c3cc597988dec73` / 7,789 | [PR #45](https://github.com/atlaslattice/atlas-lattice-providers/pull/45), merged `d630b545a7c42f2b2e2627eec6fb75296e5d9e38`; hosted CI unknown |
| Receipt scorer documentation | [docs/RECEIPT_COMPLETENESS_SCORE.md](RECEIPT_COMPLETENESS_SCORE.md) | visible-content | `c8aa4868ecd01ecc89c5935393819cdef2b025a0` / 4,874 | Same merged PR #45 |
| Strict CoordinateResolver contract code | [core/coordinate_resolver.py](../core/coordinate_resolver.py) | visible-content / test-local | `1a823e6255ca34aefea34e7387f86db9e134ddc1` / 6,280 | [PR #46](https://github.com/atlaslattice/atlas-lattice-providers/pull/46), merged `078ab0ffad9aaa7ee04f86a3258fb67c98b32a98`; NOT wired to live router |
| CoordinateResolver documentation | [docs/COORDINATE_RESOLVER_CONTRACT.md](COORDINATE_RESOLVER_CONTRACT.md) | visible-content | `81a37f771bf4415f9898123823479a2ad9e33fa0` / 3,036 | Same merged PR #46 |
| Canon Candidate Queue | [docs/CANON_CANDIDATE_QUEUE.md](CANON_CANDIDATE_QUEUE.md) | visible-content | `4fa364b23f27c7c71487458a4a9ca12bea90549a` / 5,822 | [PR #48](https://github.com/atlaslattice/atlas-lattice-providers/pull/48), merged `d0dc7d3bbaa20447c09db49f11fdb07014ddb708`; NO GRANTS |

**SHA scope:** Blob hashes above are GitHub file-fetch responses from this date. Commit identifiers for the three new PRs were independently confirmed through merge results and readbacks. No commit IDs are invented for older documents. Branch contents can change later; re-fetch before use.

## Reproducible reviewer check

1. Fetch the exact path and SHA, then compare content to expected bytes. A file named "full" whose content is only a placeholder must remain **visible-stub**.
2. Check source-root identity, source rights, `raw_export_status`, author, claim scope and whether a SHA is a blob or commit.
3. Run the relevant tests from a pinned revision and capture GitHub Actions run URL/output; no green CI is inferred from an empty status list.
4. Preserve missing/failed/contradicted packets and dissent under INV-0; do not replace them with invented successful receipts.
5. Confirm human-root decision independently before any canon or deployment promotion. GitHub merge, centrality, score, or an AI-generated review is not such a decision.

## Broken links / needs-fetch queue

| Priority | Blocker | Safe next action |
| --- | --- | --- |
| P0 | Full Delta Ledger is missing from the cited default branch (90-byte stub) | Locate original version/commit/source export, preserve and audit rights |
| P0 | A2A Protocol is an 81-byte placeholder | Find actual protocol and runnable bus implementation; test identity boundaries |
| P0 | Orchestrator and Sentinel at cited paths returned 404 | Search all authorized branches and related repositories; **do not invent** replacement authority |
| P0 | Dragon Play receipt and archive mirror returned 404 | Request exact file/ref and scope; do not pull private Play into Work |
| P0 | No GitHub-hosted CI success established for new candidate modules | Run or fetch actual workflow run receipts and record results |
| P1 | Legacy coordinate parser allows wider vocabulary, while new resolver is strict 12³ | Define compatibility and migration before production integration |
| P1 | Real A2A identity, signed attribution, consent and replay safeguards unknown in these readbacks | Independent negative testing and external authorization review |

## Overclaim gate

This index is **a receipt register, not a proof of truth or complete deployment**. A test-local assertion is not hosted CI. A blob hash is not a commit. A document is not executable enforcement. A source-linked packet is not independent source validation. No Play participant or model can self-ratify canon, deploy software, erase dissent, impersonate a persistent agent, or transfer private-room content into Work.

Related [issue #12](https://github.com/atlaslattice/atlas-lattice-providers/issues/12), [SwarmHub #3](https://github.com/atlaslattice/atlas-lattice-providers/issues/3), [NO MERGED MIND tests #8](https://github.com/atlaslattice/atlas-lattice-providers/issues/8), [TransparentPacket96 #14](https://github.com/atlaslattice/atlas-lattice-providers/issues/14), [Sentinel #15](https://github.com/atlaslattice/atlas-lattice-providers/issues/15).

**Keeper:** A link tells you where to look. A receipt tells you what happened. Neither grants authority.
