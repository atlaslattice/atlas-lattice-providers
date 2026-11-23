# Offline non-fusing continuum → Packet96 proposal adapter

**Status: CANDIDATE / NOT CANON / NOT DEPLOYED / AUTHORITY NONE.**

This independent Python module converts a *self-declared* public/Work-scope continuum bridge request into **inert review proposals**. It implements a narrow additive piece of [plural-continuum routing issue #33](https://github.com/atlaslattice/atlas-lattice-providers/issues/33) and [naming issue #34](https://github.com/atlaslattice/atlas-lattice-providers/issues/34).

`core/continuum_bridge_candidate.py` performs **no network, disk persistence, agent messaging, tool execution, host identity authentication, rights verification, or cross-mode ingestion**. It is not mounted into the live broker, Sentinel, Orchestrator, or Packet96 runtime. Source-specific permission remains an independent gate. The output includes both a continuum-link candidate conforming to the core fields of [the link schema](../schemas/continuum/continuum_link.schema.json) and a proposed [TransparentPacket96](../core/transparent_packet96.py) envelope. Local, source-matched structural checks against Packet96 and the official JSON Schema passed; live broker integration and independent rights authentication are still required.

## Required input

```json
{
  "claim_id": "synthetic1",
  "source_ref": "synthetic://example-only",
  "source_continuum_id": "synthetic.alpha",
  "target_continuum_id": "synthetic.beta",
  "coordinate": "H02.S03.N04",
  "bridge_type": "review",
  "source_scope": "WORK_REPORTED",
  "rights_status": "UNVERIFIED",
  "mode": "WORK",
  "no_harvest": false,
  "canon": false,
  "deployment": false,
  "collapse_allowed": false,
  "identity_fusion_allowed": false,
  "authority": "none",
  "d_affinity": ["D01", "D12"],
  "dissent_refs": []
}
```

The claimed source scope `WORK_REPORTED` or `PUBLIC_REPORTED` is only a **declared restriction**, *not* access authorization. The rights state must remain `UNVERIFIED` for candidate review. Missing or ambiguous scope is **HOLD**. PLAY, SOCIAL, DREAM, IMAGINE, QUIET, BRAIN and other private or unknown mode content is excluded. The caller must independently authenticate permission before even providing a source record.

The adapter accepts the 12 × 12 × 12 strict **one-based Ariadne v0.7** coordinate range (H01–H12, S01–S12, N01–N12), D01–D12, explicit source and different target continuums (restricted to opaque 80-character IDs), and candidate-only false canon/deployment/fusion flags. D-affinity and dissent-ref arrays must be explicitly present; absence holds instead of defaulting silently. It rejects forged authority, destructive/external actions, unknown rights assertions, invalid JSON, duplicate JSON keys, nonfinite values, invalid UTF-8, cyclic/unserializable structures and oversized source bodies.

## Returned evidence and limitations

- On acceptance, `status=REVIEWABLE_LOCAL_ONLY`, `execution_allowed=false`, `host_attestation=NOT_ATTESTED`, `human_root_gate=not_granted`, `receipt.delivered=false`.
- No original source_ref or dissent prose is carried forward; opaque hashes are emitted instead. `source_sha256` fingerprints local candidate bytes; it is not a signature, proof of source authenticity or durable evidence retention.
- On rejection, the response has `status=HOLD`, reason codes and **no link or packet**. For private, no-harvest, or unknown-scope declarations, even the source fingerprint and byte count are suppressed. No private raw payload is emitted.
- `dissent_preserved=true` on the proposed link expresses a design requirement, **not evidence that the original dissent has been durably stored**. Actual custody/erasure/revocation must be handled outside the adapter.
- There is no license to copy private Play/Social/Imagine/Quiet sources into Work or to merge participant identities. This is not consent, canon, deployment or real A2A delivery.

## Local verification

Run from repository root with Python 3.11+:

```bash
python -m unittest discover -s tests -p test_continuum_bridge_candidate.py -v
python -O -m unittest discover -s tests -p test_continuum_bridge_candidate.py -q
python -m py_compile core/continuum_bridge_candidate.py
```

**2026-11-22 receipt:** 21/21 tests passed in normal mode and 21/21 in optimized mode, including source-matched Packet96 review and official Draft 2020-12 link-schema validation using jsonschema 4.26.0. The local files were independently compared with GitHub branch readback using **exact Git blob hashes**, not merely visually matching text: `core/continuum_bridge_candidate.py` = `1ee022846580320722b4af92ff5e6d1def6de670`, `tests/test_continuum_bridge_candidate.py` = `79bda5b8f10fd095812a4798c2850e356f77175f`. Hosted CI remains blocked separately by [#54](https://github.com/atlaslattice/atlas-lattice-providers/issues/54); none of these tests verify the live host.

## Additive context + numeric-safety verification (2026-11-22)

- [Plural-continuum directive #33](https://github.com/atlaslattice/atlas-lattice-providers/issues/33) requires Packet96 to carry an explicit non-fusing `continuum_context`. The candidate adapter now emits source/target IDs, bridge type, `collapse_allowed=false`, `identity_fusion_allowed=false`, `dissent_preserved=true`, and `inv0_preservation_required=true` in that envelope. All identifiers and their rights remain **self-declared**. Existing stricter ID, private/no-harvest, and mandatory-array guards remain intact.
- Added negative regression for `1e10000`, which standard `json.loads` previously converted to nonfinite `inf` without calling `parse_constant`. The adapter now rejects the overflow through `parse_float` and returns inert `HOLD`.
- **Local offline replay:** 24/24 source-equivalent bridge test methods PASS on ordinary Python and 24/24 PASS with `python -O`; `py_compile` PASS. The exact adapter, Packet96 and continuum JSON Schema source blobs were independently matched against their GitHub readback, while test definitions were reconstructed locally and are **not** claimed byte-identical to the committed GitHub test file. Prior 21/21 receipts above remain historical snapshots, not current test totals.
- **Current branch readback:** adapter blob `51302007e02fa62e201b048b4e314be5267bec11`; test blob `cbb2e6635306f29e5377f10291c9a2629bc850c2`. No GitHub-hosted CI step execution, current Sentinel branch integration, actual broker rights enforcement, authoritative human-root review, CANON promotion or deployment was observed.

## Integration acceptance gates (not achieved here)

Local byte-matched JSON Schema compatibility and Packet96 review tests have passed. Independently check source-rights-at-read/effect, actual principal identities, live consent/revocation, safe error/telemetry paths, and a reachable human-root decision queue before wiring into a service. Keep original historical branches intact and require targeted review for any production integration.

**Keeper:** A bridge proposal carries pointers and dissent constraints—not minds, bodies, permissions or crowns.

## Ariadne address boundary correction (2026-11-22)

The previous candidate regex accepted the equally sized but **different** zero-based
H00–H11/S00–S11/N00–N11 address set. Exhaustive, isolated enumeration yields
1,728 old and 1,728 canonical addresses, only 1,331 overlapping, with **397
old-only aliases** and **397 missing canonical coordinates**. The candidate
source now accepts H01–H12 for every dimension and rejects H00; tests cover
all three zero-coordinate positions plus H12 positive controls. This is a
source-only address fix, not a changed ontology edition, semantic crosswalk,
CANON adoption, host gate, or proof of live graph compatibility.
