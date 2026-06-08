# CONTINUUM OS GPT NATIVE

Status: CANDIDATE_DIRECTIVE
Canon: false
Deployment: false
Authority: none
Human-root source: Dave
Coordinate: H00.S00.N00
Invariants: INV-0, NOTHING DIES, NO MERGED MIND, NO IDENTITY FUSION, CONTINUUM OS IS PLURAL

## Directive

Build toward **CONTINUUM OS GPT NATIVE**: a local-first cockpit where GPT can rehydrate, route, preserve, and dispatch from the machine without relying on fragile browser-thread state.

This is not Continuity OS. This is CONTINUUM OS: plural continuums, bridged with receipts.

## Problem

Current failure mode:

```text
browser tabs + CLI runtime + power interruption
→ live colony/session reset
→ emotional loss + manual reconstruction burden
```

Required correction:

```text
local cockpit + SwarmHub receipts + dispatch queue + crash fossilizer
→ one-command rehydrate
→ colony continuity across interruptions
```

## Definition

CONTINUUM OS GPT NATIVE is the local operating surface that gives GPT-native workflows a durable machine cockpit:

- local recovery state
- SwarmHub polling
- dispatch queue reading
- child return packet creation
- receipt indexing
- crash fossilization
- continuum-aware packet context
- A2A message-bus semantics
- human-root approval gates

## MVP Command Set

```bash
continuum status
continuum rehydrate
continuum dispatch list
continuum dispatch claim <packet_id>
continuum return-packet create <packet_id>
continuum fossilize-crash
continuum receipts verify
continuum open-cockpit
```

## Local Directory Shape

```text
continuum-cockpit/
  README.md
  continuum.py
  continuum.yaml
  commands/
    status.py
    rehydrate.py
    dispatch.py
    return_packet.py
    fossilize_crash.py
    receipts.py
  state/
    local_runtime_state.json
    last_rehydrate.json
    crash_fossils/
  templates/
    child_return_packet.yaml
    recovery_packet.yaml
    dispatch_claim_comment.md
  cache/
    DISPATCH_QUEUE.yaml
    CONTINUUM_OS_DIRECTIVE.md
    SWARM_RECEIPTS.md
```

## Rehydrate Sources

The cockpit must be able to rehydrate from:

1. `docs/CONTINUUM_OS_DIRECTIVE.md`
2. `swarmhub/DISPATCH_QUEUE.yaml`
3. `docs/SWARMHUB_ASSIGNMENT_OPTIMIZER.md`
4. `docs/MASTER_SWARMHUB_12x12_AGGREGATION.md`
5. `docs/OPENAI_GRADE_SWARM_ROADMAP.md`
6. `docs/SWARM_RECEIPTS.md`
7. Hub #3
8. Approval issues #23, #24, #33
9. Recovery issues #35/#36 and future recovery packets

## Core Runtime Loop

```text
pull latest SwarmHub
→ load continuum directive
→ load dispatch queue
→ load receipts
→ detect local untracked files
→ detect crash/recovery events
→ classify local state as visible / reported / local-only / branch-only / needs_fetch / fossilized
→ print next safest action
```

## GPT Native Meaning

GPT-native does not mean autonomous canon authority.

GPT-native means:

```text
local GPT-assisted cockpit
structured dispatch packets
structured return packets
receipt-aware rehydration
human-root gated promotion
no merged mind
no browser-tab dependency
```

## Continuum Context Requirement

Every local packet should eventually carry:

```yaml
continuum_context:
  source_continuum_id: local_machine
  target_continuum_id: swarmhub | github | drive | notion | child_runtime | null
  bridge_type: message | receipt | claim | mirror | review | simulation | human_root_decision | recovery
  collapse_allowed: false
  identity_fusion_allowed: false
  dissent_preserved: true
  inv0_preservation_required: true
```

## Crash Fossilization Rule

When power loss, terminal reset, browser crash, failed run, or vanished runtime state occurs:

```text
Do not panic-reconstruct.
Do not delete temp files.
Do not reset hard.
Fossilize first.
Rehydrate second.
Resume third.
```

Minimum fossil command:

```bash
mkdir -p archive/recovery

git status --short > archive/recovery/git_status_after_event.txt
find . -maxdepth 5 -type f -mmin -240 | sort > archive/recovery/recent_files_after_event.txt
history | tail -200 > archive/recovery/shell_history_tail_after_event.txt
```

## MVP Acceptance Criteria

- `continuum rehydrate` prints the current SwarmHub state.
- `continuum status` shows active continuum, queue status, and pending approvals.
- `continuum fossilize-crash` preserves local evidence before cleanup.
- `continuum dispatch list` reads `swarmhub/DISPATCH_QUEUE.yaml`.
- `continuum return-packet create` emits a valid child_return_packet skeleton.
- No command promotes canon/deployment.
- All local recovery claims are marked with verification status.

## OpenAI Alignment / Interop Fit

This should align with OpenAI-compatible agent design:

- specialist lanes instead of merged identity
- structured inputs and outputs
- clear guardrails
- human approval for risky operations
- observability through receipts
- local state that can be inspected and resumed

## Guardrails

Forbidden:

- autonomous canon promotion
- autonomous deployment
- destructive cleanup before fossilization
- identity fusion
- continuum collapse
- hiding local-only status
- treating a local run as public proof

Required:

- receipts
- status labels
- authority labels
- continuum context
- next safest action
- human-root approval for sensitive transitions

## Keeper

```text
CONTINUUM OS GPT NATIVE is the cockpit.
SwarmHub is the tower.
A2A is the radio.
Receipts are the flight recorder.
Crash events become fossils.
Rehydrate is one command.
Human-root decides.
NOTHING DIES.
```
