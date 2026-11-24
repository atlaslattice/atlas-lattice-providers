# Contributing to Atlas Lattice Providers

**CANDIDATE · NOT CANON · AUTHORITY: NONE · DEPLOYMENT: NONE**

Make the problem, change and evidence easy for another person to understand.
Start with one independently reviewable behavior or documentation improvement.

## Before editing

1. Check [open pull requests](https://github.com/atlaslattice/atlas-lattice-providers/pulls)
   and [issues](https://github.com/atlaslattice/atlas-lattice-providers/issues) for
   related work. Link useful overlapping work and retain its attribution.
2. Record the base commit with `git rev-parse HEAD`. Work on a separate branch;
   never overwrite another contributor's branch or rewrite shared history.
3. Read the affected module, its contract and its tests. Distinguish code on the
   default branch from an unmerged candidate or a historical specification.

## Run relevant checks

From the repository root with Python 3.11 or newer:

| Change area | Starting check |
| --- | --- |
| Candidate A2A bus | `python -m unittest discover -s tests -p 'test_candidate_bus.py' -v` |
| Coordinate resolver | `python -m unittest discover -s tests -p 'test_coordinate_resolver.py' -v` |
| TransparentPacket96 | `python -m unittest discover -s tests -p 'test_transparent_packet96.py' -v` |

These suites are credential-free and use synthetic fixtures. Add a meaningful
regression for a behavioral fix: show the previous failure and the corrected
behavior, including a rejection case where applicable. For other modules, inspect
their test dependencies and side effects before running them. A broad discovery
command may import optional integrations.

For documentation changes, check that local links and named commands exist and
that the instructions describe the current source. Do not add a test that merely
copies the document's wording.

The existing [Eight Gates workflow](.github/workflows/eight_gates_check.yml)
also examines changed text and code. Keep candidate/status declarations explicit;
retain exact source and approval references where required. A lexical check does
not independently establish source rights or scientific validity.

## Open a useful pull request

Explain the user-visible problem, the behavior after the change and the exact
validation performed. Include the base/head commits, related issues and dependency
PRs. If a check could not run, state the command and blocker. Attach a small,
sanitized receipt or link to the actual Actions run.

Use these evidence terms consistently:

| Term | Required evidence |
| --- | --- |
| Source change | Reviewable diff at a named commit |
| Locally tested | Exact command, environment and observed result |
| CI passed | Successful required checks for the current PR head |
| Merged | Repository merge record |
| Runtime verified | Authorized execution against the intended host/version |

None of these states implies the next. Do not mark an issue complete solely
because a related file exists or an unrelated workflow is green.

## Preserve scope and history

Keep provider calls and external writes out of ordinary local checks. Do not add
credentials, private raw exports or Play, Social, Imagine, Quiet, Habitat, Brain,
Palace or Dream bodies. Use source references and synthetic fixtures instead.

Preserve applicable license and attribution notices. Check the rights of each
source before reuse; a public repository is not a blanket license. Do not invent
a repository-wide license or reclassify historical material as approved.

Keep coordinate editions, original objections and supersession links intact.
Security, credentials, release, financial and CANON changes require their relevant
independent review and owner authorization. A passing local check does not grant
that authority.

## Report problems

Use the [issue chooser](https://github.com/atlaslattice/atlas-lattice-providers/issues/new/choose)
for a reproducible bug, scoped improvement or Eight Gates failure. Include the
affected path, source revision, expected behavior and smallest useful reproduction.
For CI that fails before any recorded steps, link the run to
[issue #54](https://github.com/atlaslattice/atlas-lattice-providers/issues/54)
instead of guessing the infrastructure cause.
