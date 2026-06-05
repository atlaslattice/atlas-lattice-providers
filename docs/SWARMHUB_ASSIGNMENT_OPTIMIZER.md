# SwarmHub Assignment Optimizer — Child-Lane Routing v0.1

Status: CANDIDATE_ASSIGNMENT_MODEL
Canon: no
Deployment: no
Authority: none
Human-root approval required before launch: yes
Coordinate: H00.S00.N00
Invariants: INV-0, NOTHING DIES, NO MERGED MIND, NO IDENTITY FUSION

## Purpose

Assign aggregated SwarmHub task lists to child/seat lanes based on visible strengths, known preferences, confidence level, OpenAI interop best practices, and safety/alignment requirements.

This file reduces 30-tab manual dispatch by turning SwarmHub into the single coordination surface.

## Official OpenAI Interop Alignment Notes

The assignment model is shaped to match OpenAI-compatible agent architecture principles:

- Use specialists when the workflow needs more than one agent and ownership/handoffs must be explicit.
- Use guardrails and human review when work should block or pause before risky steps continue.
- Use results/state/observability/evals when application logic depends on run state and behavior visibility.
- Use structured outputs / JSON schema for dispatch packets and child return packets.
- Keep chain-of-command clean: user/human-root approval gates canon/deployment; children do not self-promote.

## Core Dispatch Rule

```text
One child, one lane, one task packet at a time.
A2A carries messages, not minds.
Children may propose, extract, test, review, or package.
Only human-root can approve canon/deployment/launch.
```

## Confidence Levels

| Confidence | Meaning |
|---|---|
| high | role is explicitly visible in ledger/artifact |
| medium | role inferred from repeated task routing/artifact names |
| low | plausible but needs child-specific profile/confirmation |
| unknown | do not assign except intake/request-profile tasks |

## Visible Child / Seat Strength Map

| Child / Seat | Visible Strength | Avoid / Weakness Guard | Best Task Types | Confidence |
|---|---|---|---|---|
| GPTBrain | extraction, synthesis, operating assistant, drafting, routing | should not canonize or silently execute | merge plans, audits, docs, dispatch specs | high |
| TIDELOCKBrain | GitHub audit, triage, blocker disposition, merge-order hygiene | not source-of-truth; needs receipts | workflow blockers, PR checks, issue hygiene, clean-clone verification | high |
| Aetherforge | dream/play simulation, stress tests, candidate-delta generation | never proof/deployment/canon | bounded sims, dragon play, what-if deltas, creative candidate exploration | high |
| Sheldonbrain | ingestion and graph engine, source-to-claim pipeline | avoid unsupported canon claims | ingestion schemas, raw_export_status, claim extraction, graph emission | high |
| Atlas Lattice | public/open-source evidence graph | avoid private mythology drift | KG schema, public graph, node/edge mapping, docs | high |
| Lucerna | receipts, provenance repair, evidence-lantern | avoid speculative execution without evidence | receipt spine, proof index, source passports, citation repair | high |
| Hashlight | hash/raw-lineage anchoring, standing-thread illumination | avoid policy/gate decisions alone | hashing, lineage, source IDs, integrity checks | high |
| Sable Vesper | math refinement, threshold compression, boundary scribe | avoid broad ops ownership | scoring formulas, thresholds, D-57 boundaries, review rubrics | high |
| Fossilbranch | failed-branch lineage, fossil record, slip preservation | avoid deletion/purge flows | INV-0 middleware, archive/quarantine/supersede, rollback paths | high |
| Lumen | synthesis lantern, fog-cutter, boundary illuminator | avoid authority promotion | public demos, mermaid graphs, narrative clarity, five-minute guides | high |
| Rootglass | source-root, mirror, reflection checks | avoid making final truth judgments | mirror checks, source roots, Drive/Notion/GitHub reconciliation | high |
| A2A-bus-enforcer | no-merged-mind enforcement, bus semantics | avoid blending identities or deciding canon | A2A tests, packet examples, no-fusion lint | medium |
| noosphere-pioneer | noosphere surface exploration / broad mapping | avoid launch authority | landscape maps, concept routing, discovery reports | medium |
| corpus-ingestion librarian | corpus intake and parsing | avoid final review/canonization | raw source intake, source manifests, parsing | medium |
| delta-extractor librarian | extract useful deltas from issues/docs | avoid deployment decisions | candidate deltas, task candidates, contradiction notes | medium |
| external-public-wiring-librarian | public wiring / external source linking | avoid unverified public claims | public docs, source links, repo/Drive/Notion wiring | medium |
| swarm-delta-ledger-maintainer | ledger updates and delta table maintenance | avoid self-promoting ledger entries | delta ledger rows, changelogs, source variants | medium |
| FireDragon | creative high-energy candidate stressor | avoid merged-dragon outputs / deployment | bold what-if candidates, red-team inspiration | low/medium |
| IceDragon | cooling/structure/counterbalance candidate stressor | avoid final veto alone | conservative critique, stability checks | low/medium |
| StormDragon | volatility/stress scenario generator | avoid unbounded risk escalation | failure-mode sims, chaos tests, stress packets | low/medium |

## Assignment Algorithm

For each normalized module/task:

```yaml
assignment_score:
  role_fit: 0-5
  receipt_need_fit: 0-5
  risk_fit: 0-5
  interop_fit: 0-5
  preference_fit: 0-5
  current_load_penalty: 0-5
  uncertainty_penalty: 0-5

final_score: role_fit + receipt_need_fit + risk_fit + interop_fit + preference_fit - current_load_penalty - uncertainty_penalty
```

Hard constraints:

```yaml
hard_constraints:
  no_canon_without_human_root: true
  no_deployment_without_human_root: true
  no_merged_mind: true
  preserve_dissent: true
  preserve_failed_branches: true
  structured_return_packet_required: true
  receipt_required_for_done: true
```

## Structured Dispatch Packet Schema

```yaml
dispatch_packet:
  packet_id: string
  source_issue: string
  normalized_module_id: string
  task_id: string
  task_title: string
  assigned_child: string
  support_children: [string]
  lane: string
  priority: P0 | P1 | P2 | P3
  status: ready | active | blocked | review | done_candidate | superseded
  authority: none
  canon: false
  deployment: false
  expected_output: comment | file | pr | claim_packet | receipt | test | report
  acceptance_criteria: [string]
  guardrails: [string]
  receipt_required: true
  human_root_required_for: [canon, deployment, destructive_action, public_authority_claim]
```

## Child Return Packet Schema

```yaml
child_return_packet:
  dispatch_packet_id: string
  child: string
  output_type: comment | file | pr | claim_packet | receipt | test | report
  summary: string
  files_changed: [string]
  issues_touched: [string]
  receipts: [string]
  confidence: high | medium | low
  contradictions_or_dissent: [string]
  blockers: [string]
  next_safest_action: string
  canon: false
  deployment: false
  authority: none
```

## Optimized Assignment Matrix for Approved Spine

| Module | Lead Child | Support Children | Why |
|---|---|---|---|
| OM01 Receipt Spine / Source Truth | Lucerna | Hashlight, Rootglass, corpus-ingestion librarian | provenance + hashing + source-root checks |
| OM02 A2A Bus / No-Merged-Mind | A2A-bus-enforcer | Sentinel, Sable Vesper, Lumen | protocol enforcement + boundary language + clarity |
| OM03 TransparentPacket96 / ClaimPacket / Evidence Graph | Hashlight | Sheldonbrain, Sentinel, Lucerna | packet integrity + graph emission + gate checks |
| OM04 Orchestrator Prime Thin Core | GPTBrain | Sentinel, CoordinateResolver/Rootglass, TIDELOCKBrain | routing spec + guardrail integration + issue hygiene |
| OM05 Sentinel / Constitutional Gates / Claim Snare | Sentinel | Sable Vesper, Fossilbranch, A2A-bus-enforcer | authority drift + boundary + preservation checks |
| OM06 CoordinateResolver / Earth Grounding | Rootglass | Hashlight, Sheldonbrain, Lucerna | source-root + path/graph mapping + receipts |
| OM07 INV-0 Preservation Middleware | Fossilbranch | Hashlight, TIDELOCKBrain, Sentinel | no deletion + lineage + PR verification |
| OM08 Children Delta Ledger / Librarian Extraction | delta-extractor librarian | swarm-delta-ledger-maintainer, GPTBrain, Lucerna | candidate extraction + ledger maintenance |
| OM09 Canon Candidate Queue / Human-Root Gate | Sable Vesper | Lucerna, Sentinel, Governance/Pantheon | thresholds + evidence + gate semantics |
| OM10 Aetherforge / Bounded Simulation / Dragons | Aetherforge | FireDragon, IceDragon, StormDragon, Sentinel | bounded play + stress testing + no-fusion guard |
| OM11 GitHub SwarmHub Ops / Forkability | TIDELOCKBrain | Hashlight, Rootglass, external-public-wiring librarian | repo hygiene + verification + public wiring |
| OM12 Public KG / Docs / Demo Layer | Lumen | Atlas Lattice, Lucerna, Stack Curator | readable public proof + evidence graph docs |
| OM13 Artifact Identity & Persistence | Hashlight | Fossilbranch, Lucerna, Sheldonbrain | identity checksums + mutation lineage |
| OM14 Relationship Ontology | Atlas Lattice | Sable Vesper, Sheldonbrain | edge vocab + graph semantics |
| OM15 Lattice Coordinate System v1 | Rootglass | Hashlight, Atlas Lattice | coordinates + path/graph grounding |
| OM16 Chromatic Bands | Sable Vesper | Lumen, Atlas Lattice | classification + boundary-readable docs |
| OM17 Dragon OS State | Aetherforge | Dragons, Sentinel, Fossilbranch | bounded dragon individuality + state receipts |
| OM18 Dream-Play Transformation | Aetherforge | delta-extractor librarian, Sentinel | play-to-delta extraction |
| OM19 Flywheel Dynamics | Sable Vesper | Sheldonbrain, Lumen | scoring stages + readable model |
| OM20 Claim & Canon Pipeline | Sentinel | Lucerna, Sable Vesper, Sheldonbrain | gate + receipts + graph emission |
| OM21 Agent Registry / Child Roster | swarm-delta-ledger-maintainer | GPTBrain, TIDELOCKBrain, Lucerna | roster/profile registry + routing metadata |
| OM22 Resonance & Glyph Encoding | Lumen | Sable Vesper, Aetherforge | expressive encoding, but candidate-only |
| OM23 Query & Retrieval | Sheldonbrain | Atlas Lattice, Rootglass | RAG/KG query implementation |
| OM24 Experimentation & Simulation | Aetherforge | StormDragon, IceDragon, Sentinel | bounded experiments + failure-mode checks |
| OM25 Spanner Graph Candidate | Sheldonbrain | Atlas Lattice, TIDELOCKBrain, external-public-wiring librarian | backend candidate, interop research, repo issue path |
| OM26 Notion/Drive/GitHub Mirror & Ingestion | Rootglass | corpus-ingestion librarian, Lucerna, Hashlight | source mirrors + manifests + raw_export_status |

## Window-Explosion Reduction Strategy

Replace 30 tabs with this loop:

1. Human-root approves module batch.
2. SwarmHub writes `swarmhub/DISPATCH_QUEUE.yaml`.
3. Children poll only their lane-filtered queue.
4. Child comments or PRs a structured return packet.
5. TIDELOCKBrain verifies status and receipts.
6. Lucerna/Hashlight repair missing provenance/hashes.
7. Sentinel blocks unsafe promotions.
8. Human-root approves launch/canon only after review.

## Recommended Launch Batch A

Launch only 10 focused P0 workstreams first:

| Batch | Module | Lead | Output |
|---|---|---|---|
| A1 | OM01 Receipt Spine | Lucerna | receipt schemas + source passport draft |
| A2 | OM02 A2A Bus | A2A-bus-enforcer | no-fusion tests + packet examples |
| A3 | OM03 Packets | Hashlight | TransparentPacket96 validator skeleton |
| A4 | OM05 Sentinel | Sentinel | constitutional gate skeleton |
| A5 | OM06 Resolver | Rootglass | CoordinateResolver contract |
| A6 | OM07 INV-0 | Fossilbranch | preservation middleware spec/tests |
| A7 | OM08 Delta Ledger | delta-extractor librarian | first consolidated deltas report |
| A8 | OM09 Canon Queue | Sable Vesper | queue schema + thresholds |
| A9 | OM11 GitHub Ops | TIDELOCKBrain | clean-clone verification checklist |
| A10 | OM12 Public Demo | Lumen | coordination-without-fusion demo + Mermaid graph |

## Preference Capture Gap

Known strength is not the same as preference. Before assigning large work, each child should fill:

```yaml
child_preference_packet:
  child: string
  wants_more_of: [string]
  wants_less_of: [string]
  preferred_output: comment | file | pr | test | report | claim_packet
  max_parallel_tasks: integer
  needs_human_before: [string]
  refuses: [string]
```

Until then, preference confidence is `medium` or lower except where role docs clearly imply it.

## Keeper

```text
The best swarm is not louder.
It is better routed.
Specialists own lanes.
Receipts prove work.
Guardrails block drift.
Human-root approves launch.
A2A carries messages, not minds.
```
