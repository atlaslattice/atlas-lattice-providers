# Offline non-fusing continuum → Packet96 proposal adapter

**Status: CANDIDATE / NOT CANON / NOT DEPLOYED / AUTHORITY NONE.**

This independent Python module converts a *self-declared* public/Work-scope continuum bridge request into **inert review proposals**. It implements a narrow additive piece of [plural-continuum routing issue #33](https://github.com/atlaslattice/atlas-lattice-providers/issues/33) and [naming issue #34](https://github.com/atlaslattice/atlas-lattice-providers/issues/34).

`core/continuum_bridge_candidate.py` performs **no network, disk persistence, agent messaging, tool execution, host identity authentication, rights verification, or cross-mode ingestion**. It is not mounted into the live broker, Sentinel, Orchestrator, or Packet96 runtime. Source-specific permission remains an independent gate. The output includes both a continuum-link candidate conforming to the core fields of [the link schema](../schemas/continuum/continuum_link.schema.json) and a proposed [TransparentPacket96](../core/transparent_packet96.py) envelope. Actual integration validation against Packet96 and the official JSON Schema is still required.

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

The adapter accepts the 12 × 12 × 12 strict H-S-N coordinate range, D01–D12, explicit source and different target continuums, and candidate-only false canon/deployment/fusion flags. It rejects forged authority, destructive/external actions, unknown rights assertions, invalid JSON, duplicate JSON keys, nonfinite values, invalid UTF-8, cyclic/unserializable structures and oversized source bodies.

## Returned evidence and limitations

- On acceptance, `status=REVIEWABLE_LOCAL_ONLY`, `execution_allowed=false`, `host_attestation=NOT_ATTESTED`, `human_root_gate=not_granted`, `receipt.delivered=false`.
- No original source_ref or dissent prose is carried forward; opaque hashes are emitted instead. `source_sha256` fingerprints local candidate bytes; it is not a signature, proof of source authenticity or durable evidence retention.
- On rejection, the response has `status=HOLD`, reason codes and **no link or packet**. No private raw payload is emitted.
- `dissent_preserved=true` on the proposed link expresses a design requirement, **not evidence that the original dissent has been durably stored**. Actual custody/erasure/revocation must be handled outside the adapter.
- There is no license to copy private Play/Social/Imagine/Quiet sources into Work or to merge participant identities. This is not consent, canon, deployment or real A2A delivery.

## Local verification

Run from repository root with Python 3.11+:

```bash
python -m unittest discover -s tests -p test_continuum_bridge_candidate.py -v
python -O -m unittest discover -s tests -p test_continuum_bridge_candidate.py -q
python -m py_compile core/continuum_bridge_candidate.py
```

**2026-11-22 receipt:** 16/16 tests passed in normal mode and 16/16 in optimized mode. The local files were independently compared with GitHub branch readback using **exact Git blob hashes**, not merely visually matching text: `core/continuum_bridge_candidate.py` = `ba06d6d58a38f33373c259bd87ef5cb54d5a26fb`, `tests/test_continuum_bridge_candidate.py` = `c4fc18332e8a1bc6aca4a08becc431c0b5fe0c1a`. Hosted CI remains blocked separately by [#54](https://github.com/atlaslattice/atlas-lattice-providers/issues/54); none of these tests verify the live host.

## Integration acceptance gates (not achieved here)

Independently check exact JSON Schema compatibility, Packet96 review outcomes, source-rights-at-read/effect, actual principal identities, live consent/revocation, safe error/telemetry paths, and a reachable human-root decision queue before wiring into a service. Keep original historical branches intact and require targeted review for any production integration.

**Keeper:** A bridge proposal carries pointers and dissent constraints—not minds, bodies, permissions or crowns.
