# Multiple continuums — coexistence and bridge contract v0.1

**PROPOSED SOURCE CONTRACT · NOT CANON · NOT DEPLOYED · NO AUTHORITY**

Source directive: [CONTINUUM OS pluralism](CONTINUUM_OS_DIRECTIVE.md). Candidate schema definitions: [continuum](../schemas/continuum/continuum.schema.json) and [bridge](../schemas/continuum/continuum_link.schema.json). This reference is deliberately smaller than a production agent runtime.

## Continuum types and boundaries

| Continuum type | Typical material | Transfer gate |
| --- | --- | --- |
| Project / Work | tasks, PRs, test artifacts, build receipts | owner rights and scoped tool authorization |
| Source surface | citations, branch snapshots, records and hashes | provenance and original source access |
| Document / timeline | authored versions, attribution, contradictions | version and license checks |
| Agent | self-declared task role and candidate outputs | identity independently authenticated, never inferred from a name |
| Play / simulation | fictional roles, experiments, voluntary world state | opt-in, privacy and source-rights review; **no automatic Work ingestion** |
| Archive / fossil | superseded branches and recovery records | preservation default; respect legal deletion and revocation |
| Governance | decision candidates, review receipts | verified human authority outside of source JSON |
| External provider | data interfaces and tool schemas | provider authentication plus rights-at-effect; no implied endorsement |

## Candidate example: public, no personal records

```json
{
  "schema_version": "atlas.continuum/candidate-v0.1",
  "continuum_id": "sample.project.alpha",
  "continuum_type": "project",
  "continuum_scope": "public_candidate",
  "owner_or_steward": "synthetic-fixture",
  "source_ref": "synthetic-fixture:source-a",
  "raw_export_status": "raw_partial",
  "status": "CANDIDATE",
  "canon": false,
  "deployment": false,
  "authority": "none",
  "coordinate": "H00.S00.N00",
  "d_affinity": ["D01", "D12"],
  "privacy": {
    "rights_state": "unknown",
    "consent_state": "not_granted",
    "share_scope": "none"
  },
  "preservation": {
    "source_fossil_ref": "synthetic-fixture:fossil-a",
    "dissent_refs": []
  },
  "human_root_gate": {
    "required": true,
    "state": "not_granted"
  }
}
```

A bridge from `sample.project.alpha` to `sample.project.beta` can be a candidate **review** link, with `raw_content_transferred=false`, separate source/target IDs, `collapse_allowed=false` and no human permission granted. The link indicates a **proposal to compare**, not an actual transfer, read or message.

## Historical and current names

CONTINUUM OS is the active candidate name. “Continuity OS” remains in prior Git history, documents, quoted instructions and fossil records where historically accurate. A safe migration creates new docs and explicit supersession pointers; it does not erase history or silently rewrite provenance.

## Reproducibility gates

- Fetch both JSON schemas from an exact commit, parse them and run positive/negative fixtures.
- Treat `raw_partial`, `raw_missing` and `raw_source_unavailable` as disclosure, not source completeness.
- Reject malformed IDs, candidate self-ratification, identity fusion, destructive transfer and unconsented private modes.
- Verify sources, rights, reviewers and decisions **outside** self-reported schema fields.
- Record false positives, false negatives, rollback and human approvals before any host adapter is considered complete.

## What is not built

No live CONTINUUM OS cockpit, persistent cross-agent identity, authenticated A2A broker, rights-bearing Play→Work transfer, automatic canon promotion, production revocation, or complete 1,728-node knowledge graph is established by this reference.

**Keeper:** Multiple continuums may share receipts. They never surrender identity, consent or history merely to create one graph.
