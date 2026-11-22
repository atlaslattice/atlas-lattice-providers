# CONTINUUM OS local cockpit v0.1

**CANDIDATE SOURCE ONLY · NOT CANON · NOT DEPLOYED · NO AUTHORITY**

This is a bounded, local-first implementation slice of [issue #37](https://github.com/atlaslattice/atlas-lattice-providers/issues/37) and [the original cockpit specification](CONTINUUM_OS_GPT_NATIVE.md). Its source is [scripts/continuum_cli.py](../scripts/continuum_cli.py). It does **not** start an agent runtime, contact SwarmChat, connect cloud accounts, authenticate people, act on tasks, or grant permissions.

The default input is the repository's local `swarmhub/DISPATCH_QUEUE.yaml`, read as a **conservative field subset**, not full YAML semantic interpretation. Missing, oversized or symlinked source paths are refused. Status is local-file state, never hosted state.

## Usage

From a cloned repository with Python 3.11+ and no third-party packages:

```bash
python scripts/continuum_cli.py status
python scripts/continuum_cli.py rehydrate
python scripts/continuum_cli.py dispatch list
python scripts/continuum_cli.py dispatch claim A1-OM01-LUCERNA-RECEIPT-SPINE
python scripts/continuum_cli.py return-packet create A1-OM01-LUCERNA-RECEIPT-SPINE
python scripts/continuum_cli.py receipts verify
python scripts/continuum_cli.py fossilize-crash
python scripts/continuum_cli.py --write-manifest local_fossils/candidate-001.json fossilize-crash
python scripts/continuum_cli.py open-cockpit
```

Command outcomes are intentionally limited:

| Command | Actual effect |
| --- | --- |
| `status` | Counts locally parsed candidate dispatch packets and reported pending approvals |
| `rehydrate` | Prints local source-index pointers; no remote sync or agent recovery |
| `dispatch list` | Reads the local queue; no assignments or messages |
| `dispatch claim <packet_id>` | Produces an **UNSENT / UNASSIGNED** proposal for review |
| `return-packet create <packet_id>` | Produces a draft template without invented child results, receipts or identity |
| `receipts verify` | Computes local file SHA-256; does not authenticate source origin |
| `fossilize-crash` | Previews an allowlisted **hash-only manifest**, not raw source preservation |
| `--write-manifest ... fossilize-crash` | Opt-in, non-overwriting local JSON file under `local_fossils/`; never silently exports source bytes |
| `open-cockpit` | Prints an offline documentation entrypoint; does not open a browser or launch a hosted UI |

The manifest path is restricted to `local_fossils/<name>`; existing files cannot be overwritten. File component symlinks and source symlinks are rejected. On platforms lacking `O_NOFOLLOW`, local filesystem trust must be assessed separately. Durable crash backup, atomicity across concurrent processes and retention/erasure are not established by a hash-only manifest.

## Executed source tests

```bash
python -m unittest discover -s tests -p test_continuum_cli.py -v
python -O -m unittest discover -s tests -p test_continuum_cli.py -q
python -m py_compile scripts/continuum_cli.py
```

**2026-11-22:** 16/16 local tests passed normally and 16/16 under optimized Python. Local files were compared byte-for-byte with GitHub branch readback using Git blobs:

- CLI: `8f82ec1038c9fde7806f4f5cf1a7252365915e7b`
- Tests: `8f4710f1849c837176a0732bc46896a34f8b2bb5`

Tests use synthetic queue fixtures and no real resident identity, source credential, private Play content, external network or production host. GitHub-hosted CI remains independently blocked by [issue #54](https://github.com/atlaslattice/atlas-lattice-providers/issues/54). This CLI is **NOT** the final operating cockpit, and issue #37 stays open for authenticated live-state retrieval, durable local crash recovery, permissions-at-effect, independent review and actual UI integration.

**Keeper:** A flight recorder can tell us what was saved; it must not pretend a runway exists.
