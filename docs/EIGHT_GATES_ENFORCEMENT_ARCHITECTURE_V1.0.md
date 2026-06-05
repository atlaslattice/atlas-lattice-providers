# Eight Gates Enforcement Architecture (EGEA) — V1.0

```text
STATUS: CANDIDATE ARCHITECTURE
CANON: NO
DEPLOYMENT: NO
AUTHORITY: NONE
PURPOSE: Mechanical enforcement layer for ONE_LATTICE_MANY_MODULES
HUMAN-ROOT: REQUIRED FOR PROMOTION
```

## Purpose

EGEA converts project governance into mechanical checks. It prevents artifacts, modules, children, workflows, receipts, dashboards, graph edges, mirrors, or simulations from promoting themselves from `CANDIDATE` into `RATIFIED`, `CANON`, `DEPLOYED`, or `LIVE-INTEGRATED`.

## Core Principle

```text
human-root holds the gate.
No automated promotion.
No deep integration without explicit, auditable passage through the 8 Gates.
Everything can connect to everything.
Nothing can promote itself.
```

## Non-Authority Rule

```text
graph edge ≠ authority
cluster ≠ canon
centrality ≠ truth
source visibility ≠ permission
receipt ≠ approval
patch ≠ merge
simulation ≠ deployment
dashboard visibility ≠ authority
```

## The 8 Gates

| Gate # | Gate Name | Question | Pass Requirement | Failure Action |
|---:|---|---|---|---|
| 1 | Source Gate | Do we know where this came from? | Source URL/path/export/thread/author/timestamp recorded | Mark RAW_SOURCE_MISSING; quarantine from promotion |
| 2 | Hash Gate | Can we prove the artifact content? | SHA-256 or equivalent content hash recorded where applicable | Mark HASH_MISSING; block release |
| 3 | Status Gate | Is the artifact correctly labeled? | `canon_status`, `deployment_status`, `authority_scope` present | Add candidate banner; block promotion |
| 4 | Secret Gate | Does it leak secrets or private data? | Secret scan passes; no keys/tokens/raw private data | Quarantine; rotate keys if needed |
| 5 | Overclaim Gate | Does it claim more authority/truth than warranted? | No canon/deployment/endorsement/“first true” overclaims | Preserve original, add safer banner, route to review |
| 6 | Repro Gate | Can a clean clone or clean export reproduce it? | Import/compile/test/demo works from public or declared source | Mark LOCAL_ONLY; block remote proof claims |
| 7 | Review Gate | Has it been adversarially reviewed? | Routed to proper review lane | Mark PENDING_REVIEW; no promotion |
| 8 | Human-Root Gate | Did human-root explicitly approve promotion? | Explicit logged approval from Dave / human-root | Remain CANDIDATE; no canon/deploy |

## Required Artifact Banner

```text
CANDIDATE — NOT CANON
DEPLOYMENT: NO
AUTHORITY: NONE
```

## Placeholder Blockers

```text
full code omitted
assume local content
from temp_
abbrev in payload
placeholder
[FULL CONTENT OF
full enhanced code
```

## State Transition Rules

Allowed automatic transitions: `RAW → PARSED → CLAIM → CANDIDATE`, plus `CANDIDATE → PENDING_REVIEW | QUARANTINED | CONTRADICTED | SUPERSEDED`.

Blocked automatic transitions: `CANDIDATE → RATIFIED | CANON | DEPLOYED`, and `REVIEWED → CANON | DEPLOYED`.

Human-root required transitions: `REVIEWED → RATIFIED`, `RATIFIED → CANON`, `RATIFIED → DEPLOYED`, `CANDIDATE → PUBLIC_RELEASED`.

## Minimal Implementation Files

```text
core/eight_gates.py
schemas/eight_gates_packet.schema.yaml
.github/workflows/eight_gates_check.yml
.github/ISSUE_TEMPLATE/eight_gates_failure.yml
```

## Keeper

```text
The gate is not a crown.
The graph is not authority.
The receipt is not approval.
The dashboard is not deployment.
Everything can connect to everything.
Nothing can promote itself.
Human-root holds the gate.
NOTHING DIES.
```
