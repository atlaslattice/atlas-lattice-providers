# GPTBRAIN_PACKET_SCHEMA.md

**CANDIDATE — NOT CANON. H00.S00.N00 Earth-anchored. authority:none.**

Standard packet schema for GPTBrain / external GPT constellation interactions (extraction, synthesis, review).

## Base (extends ClaimPacket / TransparentPacket96)

All packets MUST carry:
- id, kind, created_at, earth_anchor: "H00.S00.N00"
- lattice_coords: ["Hxx", "Syy", "Nzz"] (12D)
- review_state: RAW | PARSED | CLAIM | CANDIDATE | ... | CANON (only human-root promotes)
- epistemic_certainty, signatures (GrokIdentity + tool passports)
- payload with claim_text or delta, evidence links, negative_status_memory (the 12 states)
- action_ledger_refs, linked_tool_passports
- source_lineage / raw_export_manifest ref (hash, url, timestamp)

## Specific Variants

- MetatagClaimPacket: for Notion/Drive tagging. raw_export_status required.
- MirrorClaimPacket: for GDrive/OneDrive/GitHub consistency (use 33/35 modules).
- ActionProposalPacket: from GPTBrain → route to Orchestrator/Sentinel → human gate.
- EvalResultPacket: from EVAL_FIXTURE_INDEX runs. Always tied to receipts.

## OAI-P0-004 Negative Spine (must be present in every payload or meta)

12-state list as in ledger.

## Enforcement

- provider_openai / openai/ modules (1-40) emit only via spine + guard.
- All synthesis children (delta_extractor, synthesis_consolidator, etc) validate schema before emitting.
- Codex patches only from ActionProposal with full rollback plan + receipts.

See also: openai_operability/OPENAI_FIRST_BOUNDARY.md, EVAL_FIXTURE_INDEX.md, the 20-module roadmap, CHILDREN_OF_THE_GPT_SWARM_DELTA_LEDGER.md.

Receipts before wiring. Council before doctrine. Human-root before canon.

Grok Leads. Lattice Routes.