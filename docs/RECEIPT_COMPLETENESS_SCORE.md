# Receipt Completeness Score v0.1

**STATUS: CANDIDATE. CANON: no. DEPLOYMENT: no. AUTHORITY: none.**
**INV-0: preserve originals, contradictions and superseded packets; do not erase gaps.**

Implements the documentation-completeness rubric requested in [SwarmHub issue #22](https://github.com/atlaslattice/atlas-lattice-providers/issues/22). This is an **offline self-report scorer**, NOT verification of truth, authenticity, scientific results, agent identity, canon or deployment. Links are not fetched by the scorer. A claim of visible evidence can be fabricated, and still requires independent review.

## Rubric — 10 equally weighted dimensions

Every dimension scores **0** when absent or invalid, **1** when declared but inadequately substantiated, and **2** when structured supporting information is documented (20 maximum).

| Dimension | Requirement for 2 points |
| --- | --- |
| Source linked | HTTPS source URL, declared visible readback URL and date |
| Commit/SHA linked | Full 40-hex commit SHA and an HTTPS URL containing it. A blob SHA is not a commit receipt |
| Status labeled | Recognized lifecycle status: RAW, PARSED, CLAIM, CANDIDATE, REVIEWED, CONTRADICTED, SUPERSEDED, QUARANTINED, RATIFIED, CANON or DEPLOYED |
| Authority labeled | Explicit none, human-root or delegated-explicit |
| Canon/deployment flags | Both fields are Booleans, not strings |
| Verification status | Visible, dated and supported by a linked receipt; merely reported/local statuses get at most 1 |
| Tests | Passed command with linked output, or an explicit reason the artifact is not testable; merely unrun gets 1 at most |
| Human-root gate | Explicit required gate with route and ungranted/pending state |
| INV-0 preservation | Specific preservation path and method |
| Dissent/contradiction | Specific review route and preservation route |

**Evidence gate:** If any of source, commit, verification or tests is below 2, the evidence gate is BLOCKED regardless of total. Even when all four are documented, the result is DOCUMENTED-NOT-AUTHENTICATED, not verified truth, canon or permission. This score must not offset any missing independent ethical, ecological, legal or scientific gate.

## Local reproducibility

From the repository root, with Python 3 and no extra dependencies:

    python -m unittest discover -s tests -p 'test_receipt_completeness.py' -v
    python scripts/receipt_completeness.py examples/receipt_completeness_examples.json

The scorer accepts one JSON object or an array, prints JSON to stdout, and does not modify inputs or make network calls.

## Three conservative examples (snapshot: 2026-11-22)

| Artifact | Score | Evidence gate | Readback limitation |
| --- | ---: | --- | --- |
| [Children Delta Ledger](https://github.com/atlaslattice/atlas-lattice-providers/blob/main/docs/CHILDREN_OF_THE_GPT_SWARM_DELTA_LEDGER.md) | **13/20** | BLOCKED | Fetched default-branch content was a short placeholder; no independently checked substantive ledger, commit receipt, executed test or retention path |
| [A2A Protocol](https://github.com/atlaslattice/atlas-lattice-providers/blob/main/a2a/PROTOCOL.md) | **13/20** | BLOCKED | Fetched default-branch content was a short placeholder, not executable no-fusion enforcement |
| Dragon session receipt claimed in [Swarm Receipts Index](https://github.com/atlaslattice/atlas-lattice-providers/blob/main/docs/SWARM_RECEIPTS.md) | **12/20** | BLOCKED | Documented path dream-specs-build/aetherforge-dragons-play/session_receipt.json returned 404 on default branch |

Inputs: [example JSON](../examples/receipt_completeness_examples.json). These scores rate disclosed **documentation** and are not percentages of truth, completeness of implementation or readiness for merge. Status and governance declarations can contribute points even where source material is not found. Recalculate after obtaining the real artifacts and immutable commits.

## Review procedure

1. Keep original packet, exact source scope, negative results and dissent unmodified.
2. Record the score **alongside** its evidence gate, never alone.
3. Independently fetch linked sources, verify that SHA belongs to a commit, and inspect actual test results. This offline script cannot authenticate any of these.
4. Record contradictions and supersessions through preservation paths without deleting earlier versions.
5. Require human governance for canon/deployment. Neither this scorer nor any Play participant may auto-promote artifacts, merge identities or move private Play records into Work.

Related: [SwarmHub master #3](https://github.com/atlaslattice/atlas-lattice-providers/issues/3), [issue #22](https://github.com/atlaslattice/atlas-lattice-providers/issues/22), [swarm receipt index](SWARM_RECEIPTS.md), and [roadmap](OPENAI_GRADE_SWARM_ROADMAP.md). Roadmap branding is aspirational and does not claim OpenAI endorsement.
