# CoordinateResolver candidate contract v0.1

**CANDIDATE / NOT CANON / NOT DEPLOYED / AUTHORITY: NONE**

Addresses [SwarmHub #16](https://github.com/atlaslattice/atlas-lattice-providers/issues/16) and the [CONTINUUM OS directive](CONTINUUM_OS_DIRECTIVE.md). This adds a **standalone candidate boundary**, not production middleware. Nothing is promoted or deployed.

The separate legacy file, [core/lattice_coordinates.py](../core/lattice_coordinates.py), accepts wider notation and can silently fall back to Earth when parsing malformed text. This strict adapter **does not inherit that behavior**.

## Four functions

1. **resolve_to_earth(claim)** — Retains the unmodified claim and a SHA-256 local fingerprint; returns candidate_review or quarantine. The Earth reference H00.S00.N00 is an ontology anchor, not physical geolocation, independently verified truth or authorization.
2. **validate_grounding(packet)** — Re-derives protected fields, checks original fingerprints and blocks source, status, continuum, authority or provenance tampering. Valid means structurally routed for candidate review only.
3. **wrap_as_coordinate_packet(payload, metadata)** — Encloses caller metadata. Metadata never overrides routing, canon, authority or deployment.
4. **escalate_to_human_root(reason, payload)** — Creates an inert NOT_SENT review candidate. It does not notify a person or grant authority.

## Accepted input

A candidate requires nonempty claim_id, source_ref and source_continuum_id. A coordinate must be one of **H00–H11.S00–S11.N00–N11** (1,728 coordinates). Optional source_url must begin with HTTPS; optional d_affinity is a list of D01–D12; optional target_continuum_id remains separate from its source. Allowed bridge types: message, receipt, claim, mirror, review, simulation, human_root_decision.

Valid-looking packets still report authority none, canon false, deployment false, human-root gate not_granted, verification unverified_claim, and continuum identity-fusion/collapse prohibited. Invalid coordinates, missing sources, prohibited promotion and identity collapse are quarantined with reasons and original data intact. SHA-256 is a reproducibility fingerprint, not a signed provenance attestation.

## Reproduce locally

    python -m unittest discover -s tests -p 'test_coordinate_resolver.py' -v
    python -m py_compile core/coordinate_resolver.py

**12 local tests passed** on 2026-11-22, covering malformed HSN, absent provenance, blocked self-promotion, D-affinity, metadata injection, source fingerprints, tampered derived fields, continuum separation and inert escalation. GitHub CI and live routing were not tested.

## Remaining work

Integration will require deliberate reconciliation of the legacy wider coordinate namespace (including S12 and N12) with this strict 12×12×12 candidate boundary, and source rights checking before any real A2A/router implementation consumes it. Do not treat this contract as proof of a complete knowledge graph or as permission to move private Play records into Work.
