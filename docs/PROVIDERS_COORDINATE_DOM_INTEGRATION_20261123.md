# Coordinate and source-highlight integration — 23 November 2026

**CANDIDATE / NOT CANON. AUTHORITY: none. DEPLOYMENT: not activated.**

## Integrated source

This review branch preserves both existing component histories and the current
main branch's scoped Unified HyperMatrix adoption. It adds no live publisher,
source import, room message, source rights or project adoption changes.

| Source | Exact commit |
| --- | --- |
| Current main / HyperMatrix PR #66 | `4f1b29fae408a84df1c44d41276e6eac599c1f94` |
| Coordinate PR #59 | `3401dfa740c36f8a216198b6f95f25232d348c53` |
| Source-highlight PR #65 | `5c19c3ccd00c860ecde9b85a6adbded7e70bc267` |

Git's actual three-way merge accepted both heads without a conflict. The GitHub
metadata read had reported `mergeable=false`; that stale response was not used
as evidence of a source conflict. The coordinate and DOM component paths do not
overlap, and the new main adoption files remain byte-identical.

## Document context repair

Two deterministic logical-DOM regressions reproduced the same missing recheck at
different async boundaries. Moving a connected renderer root and its Text nodes
into another document during `returnAllowed()` left matching source text and
connectivity intact. The old resolver still returned `DOM_RANGE_VERIFIED`; the
old presenter could report an active lease against the prior window registry.

The resolver now rechecks the captured document identity after awaited RETURN.
The presenter likewise rechecks root and range endpoint documents immediately
before registration, and cleans its observer/timer if that context changed.
These checks preserve the original typed source, digest, grapheme, revocation and
constant-HOLD contracts. The regression fixture is a logical DOM model, with
genuine Node WebCrypto and Intl.Segmenter; real browser document adoption is still
awaiting independent execution.

## Reproduced verification

| Suite | Normal | Optimized runtime |
| --- | --- | --- |
| Coordinate source + all existing peer regressions | 49 / 49 | 49 / 49 Python `-O` |
| Current main project-adoption boundaries | 18 / 18 | 18 / 18 Python `-O` |
| Unicode offsets, DOM map, lease, rendered context | 89 / 89 | 89 / 89 Node `--jitless` |
| New document adoption regressions against original | 0 / 2 | Not repeated |

The integrated passing suites cover 156 distinct test cases. Replay under the
second runtime yields 312 passing executions, not 312 distinct cases. Existing
peer test counts and historical browser receipts remain historical evidence in
their original documents. Four documents gain the repository's required status
metadata and equivalent plain deployment wording; the Eight Gates implementation
and source-pinned project approval context are unchanged.

## Reproduction

```sh
python -m unittest discover -s tests -p 'test_coordinate*.py'
python -m unittest discover -s tests -p 'test_eight_gates_project_adoption.py'
node --test tests/source_highlight_offset.test.mjs tests/test_dom_source_map.test.mjs tests/test_dom_highlight_lease.test.mjs tests/test_dom_rendered_context.test.mjs
```

Repeat Python commands with `python -O`; repeat Node with `node --jitless`.

## Remaining external verification

The attempted Chromium run failed before any case because the executor denied
`socket()` with EPERM. Zero browser cases executed in this integration visit;
the existing six rendered-grapheme browser regressions remain pending here.
Hosted Actions still needs admission of an actual runner and execution of the
current commit. Local test passes do not satisfy that requirement. Hosted
SwarmChat, D1 two-account revocation, real current READ/RETURN, accessibility and
client layout remain separate integration checks.

Rollback is exclusion of this source-only integration branch or reversion of its
small final repair commit; all original component commits remain preserved.
