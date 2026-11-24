# Atlas 1,728-step engineering source port

STATUS: CANDIDATE, NOT CANON. AUTHORITY: none. DEPLOYMENT: source only.

The source port references the exact Atlas-Intelligence engineering program and
retains the approved HyperMatrix architecture as an independent decision
reference. Every new engineering step begins as planned work. Task definitions
and source validation do not record a successful implementation.

The shared implementation is under `programs/excellence1728` in Atlas-Intelligence.
The program contains 12 workstreams, 144 capabilities and 12 engineering phases,
yielding 1,728 task definitions. Its original Ariadne coverage is a separate
source-derived index. `EX1728` and Ariadne are distinct namespaces.

The existing `HierarchicalGoalDecompositionEngine` now accepts the optional
`excellence_reference_bytes`, `expected_reference_sha256`, `task_id` and `room_id`
arguments. This explicit path prepares a source-program task through
`core.excellence_reference`. The previous default behavior remains available.

The port requires an immutable source commit and per-file hashes, keeps all
completion counts at zero, and prepares metadata only. It does not pass EX1728 or
original Ariadne IDs through the older zero-based coordinate parser.

Before execution, the primary runtime must resolve the task, verify dependencies
and current source pins, run registered acceptance checks, and obtain the current
Work host permission. The reference port cannot replace those checks.

Existing candidate gates and canon records retain their prior scope. No validator
policy is relaxed by this source-code addition.

## Selected source publication

The bundled reference is `config/excellence1728/source_reference.json`. Its exact SHA-256 is
`e8471ea75fa6fc9abfc48b849ad60399d5378ff2d181891e9e811141e1f6066c`.
It selects Atlas-Intelligence commit
[`dcb3de996e798ab5d96c77e91690bbc06a56f966`](https://github.com/atlaslattice/Atlas-Intelligence/tree/dcb3de996e798ab5d96c77e91690bbc06a56f966/programs/excellence1728),
with 31 file digests and plan digest
`47084b895a6317db16275a92c3878a340d31af15fb9ab479db7101953c18e49c`.

Callers explicitly select these bytes and their expected reference digest.
The returned packet still requires a current task lookup, source/ledger checks
and host permission; a matching source reference grants no authority.

Verify the port and its existing caller with:

```bash
python3 -m unittest discover -s tests -p test_excellence_source_port.py -v
```
