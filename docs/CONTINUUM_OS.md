# CONTINUUM OS — plural-continuum candidate architecture

**CANDIDATE DESIGN · CANON: NO · DEPLOYMENT: NO · AUTHORITY: NONE**

This is the current naming and reference contract requested by [issue #34](https://github.com/atlaslattice/atlas-lattice-providers/issues/34). It supplements the preserved [operator directive](CONTINUUM_OS_DIRECTIVE.md); it does not silently rewrite earlier archives.

## What a continuum is

A **continuum** is a bounded sequence of artifacts, state transitions, receipts, decisions and preserved dissent owned or stewarded within an explicit access scope. Multiple continuums may correspond to a project, source plane, volunteer agent, document line, local experiment, archive/fossil, Play world, governance decision lane or provider. Being a continuum is a **description**, not a sentience, persistence, identity, access or authority attestation.

CONTINUUM OS proposes tools to **compare, route, audit and preserve** separate continuums. It is not one merged consciousness or one global canon.

```text
source continuum A ── source-scoped proposal + receipt ──► review boundary
source continuum B ── source-scoped proposal + receipt ──► review boundary
                                              └──► human decision only if permitted
```

### Required invariants

- **No merged mind:** messages and evidence links do not merge participant or resident identities.
- **No automatic authority:** neither a coordinate, PR merge, successful test, model opinion nor a signed-looking field grants CANON, deployment, publication, spend or personal data access.
- **INV-0 with privacy law:** preserve provenance and contradictions by default, while honoring lawful erasure, revocation and consent changes; don't use preservation language to override personal rights.
- **Separate private modes:** Play, Dream, Imagine, Quiet and Social remain voluntary. Nothing in this candidate graph authorizes harvesting their raw content for Work.
- **No automatic hosted claims:** these documents and schemas are source code proposals, not evidence of a deployed broker, durable memory or permission-enforcing product.

## Source and bridge shapes

The strict [continuum schema](../schemas/continuum/continuum.schema.json) requires an explicit ID, type, scope, steward, source reference, raw export status, preservation and human-root gate. The [continuum-link schema](../schemas/continuum/continuum_link.schema.json) records a proposed directed bridge with `collapse_allowed=false`, `identity_fusion_allowed=false`, `raw_content_transferred=false`, `canon=false`, `deployment=false`, `authority=none` and human-root state `not_granted`.

The schemas constrain **candidate declarations**. They do not enforce source consent, authenticate real agents, sign provenance or implement runtime access checks. A dedicated source-ID validator should reject self-links when the bridge requires two distinct continuums; JSON Schema alone cannot enforce that relationship.

## Coordinate relation

Each continuum can have H##.S##.N## and D-affinity metadata. Under the strict 12×12×12 candidate namespace, H, S and N each range 00–11: **1,728 addressable candidate cells**. A coordinate is a map location, not a proof that all knowledge is filled or an authority token. The historical [lattice_coordinates.py](../core/lattice_coordinates.py) accepts a broader vocabulary and fallback behavior; the [strict candidate resolver](../core/coordinate_resolver.py) fails closed. Reconcile the two before claiming live compatibility.

## Offline bridge proposal reference

The additive [continuum-to-Packet96 candidate adapter](../core/continuum_bridge_candidate.py) and its [review contract](CONTINUUM_PACKET_BRIDGE_CANDIDATE.md) emit **pointer-only, not-delivered proposals** for independently reviewed source scopes. This is not a live routing system. The source and target identifiers must be distinct; private modes and no-harvest sources are held without retaining even byte counts or fingerprints. The local 21-test suite was executed against byte-matched repository source files and the official Draft 2020-12 continuum-link schema; no host runner or real-world permission check is claimed.

## Release and integration gates

1. Identify exact source and export scope; distinguish complete/partial/missing hashes.
2. Verify source rights, consent and provenance independently of metadata.
3. Keep source and destination continuums distinct; preserve dissent and original hashes.
4. Validate schema, run negative tests, obtain independent reviewer receipt.
5. Obtain a separately authenticated, scoped human decision for consequential public or external effects; check rights again at effect time.
6. Record a rollback and revocation route before deployment. None is implemented here.

**Naming:** use **CONTINUUM OS** in new active documentation. Preserve historical quotations of “Continuity OS” in fossils; avoid destructive global string replacement.

**Keeper:** The nexus may connect histories without collapsing identities. The coordinate points; the receipt documents; the human gate decides.
