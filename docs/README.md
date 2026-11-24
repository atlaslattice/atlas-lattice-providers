# Documentation guide

**CANDIDATE · NOT CANON · AUTHORITY: NONE · DEPLOYMENT: NONE**

Use this page to choose a starting point. The linked contracts retain their own
edition, scope and evidence. The directory also contains historical plans and
placeholders; a document's presence does not establish a finished integration.

## Local components

| Component | Contract or walkthrough | Source | Starting test |
| --- | --- | --- | --- |
| Candidate message bus | [A2A contract](A2A_CANDIDATE_BUS_CONTRACT.md) | [`a2a/candidate_bus.py`](../a2a/candidate_bus.py) | [`test_candidate_bus.py`](../tests/test_candidate_bus.py) |
| Coordinate routing | [Coordinate contract](COORDINATE_RESOLVER_CONTRACT.md) | [`core/coordinate_resolver.py`](../core/coordinate_resolver.py) | [`test_coordinate_resolver.py`](../tests/test_coordinate_resolver.py) |
| Packet review | [Packet source and interface](../core/transparent_packet96.py) | [`core/transparent_packet96.py`](../core/transparent_packet96.py) | [`test_transparent_packet96.py`](../tests/test_transparent_packet96.py) |
| Schema definitions | [Schema guide](../schemas/README.md) | [`schemas/`](../schemas/) | Select the relevant schema's test |

The [root quick start](../README.md#local-quick-start) runs three small offline
suites. The [contributor guide](../CONTRIBUTING.md) explains how to report evidence
and preserve source boundaries.

## Architecture and operations

- [CONTINUUM OS overview](CONTINUUM_OS.md) — architecture and terminology.
- [Eight Gates architecture](EIGHT_GATES_ENFORCEMENT_ARCHITECTURE_V1.0.md) — the
  existing source/status/review checks.
- [Operator status document](OPERATOR_STATUS.md) — a stored report, not a live
  system-health endpoint. `scripts/operator_status.py` rewrites that document
  and creates a local report when invoked.
- [Provider adapters](../providers/) — inspect each adapter's dependencies,
  simulated behavior and external effects before use.

## Finding current work

[Open pull requests](https://github.com/atlaslattice/atlas-lattice-providers/pulls)
show proposed changes; [issues](https://github.com/atlaslattice/atlas-lattice-providers/issues)
hold acceptance criteria and blockers. Read both before starting an overlapping
change. A draft PR and a local test report are separate from the default branch
and hosted CI.

For coordinate work, preserve the exact edition recorded by the source. The
default-branch resolver's zero-based contract and Ariadne v0.7 coordinates require
an explicit versioned conversion; this guide does not redefine either edition.

Keep historical source files and their original status. Add explicit links when
one implementation follows another, rather than renaming old documents to imply
that they were always the current implementation.
