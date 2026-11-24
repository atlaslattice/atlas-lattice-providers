# SwarmChat v32: current rendered grapheme boundaries

**CANDIDATE / NOT CANON. AUTHORITY: none. DEPLOYMENT: not activated.**

Status: source repair on existing draft PR #65. Tested locally with a DOM model; hosted activation and authenticated browser verification remain pending.

## Reproduced counterexample

At base `bec04f4c54d767409f66e3a8ac02c1190d5eb9ac`, the source map module still has Git blob `e47dce674b8bd1074d95d54e480e7776b7e872e2`. Its exact COPY of raw source `A` into rendered `A\u0301` returns `DOM_RANGE_VERIFIED` while selecting only the base letter. The raw source boundary and Range string equality both pass, yet the displayed grapheme is split. Adjacent unmapped combining marks, a ZWJ continuation, regional indicators, and a neighbor changed during the awaited RETURN callback reproduce the same gap.

## Repair and compatibility

The existing resolver now takes a bounded current logical Text-node snapshot after the final awaited RETURN callback. It checks both rendered endpoints, including unmapped neighbors, before creating the Range. The snapshot stays internal. Bounds are 256 KiB and 8,192 Text nodes; missing traversal, malformed text and overflow return the existing constant HOLD. Original source identity, digest, COPY, mutation, raw grapheme and Range checks remain.

The existing highlight lease implementation is unchanged. Two inherited fake-DOM fixtures gain only TreeWalker support; their assertions are preserved. There is no additional renderer, broker, ledger or authorization system.

## Execution evidence

Node v24.22.3, actual WebCrypto SHA-256 and ICU Intl.Segmenter, explicit modeled DOM:

- Original: all 41 inherited map/lease tests pass; new suite is 4/14 PASS and 10 RED (six boundary regressions and four traversal/cap failure controls).
- Patched: 55/55 PASS normally and 55/55 PASS under `--jitless`.
- Six real Chromium regression methods were authored. This executor's Chromium launch failed with socket EPERM before any test ran, so these six remain UNEXECUTED here.
- A separate cloud browser reached the public SwarmChat entrance, which required sign-in; no authenticated Work view or live renderer was exercised.

Reproduce the executed local scope:

```sh
node --test tests/test_dom_source_map.test.mjs tests/test_dom_highlight_lease.test.mjs tests/test_dom_rendered_context.test.mjs
node --jitless --test tests/test_dom_source_map.test.mjs tests/test_dom_highlight_lease.test.mjs tests/test_dom_rendered_context.test.mjs
```

## Remaining limits

Concatenated logical DOM text is a conservative boundary check. CSS generated content, visual block boundaries, shadow DOM, Android/desktop layout and assistive technology need separate real-browser assessment. A selected root must be the trusted renderer's complete relevant context. This patch does not certify host identity, current permissions, atomic egress, CANON, source semantics or revocation delivery. Preserve the existing lease and publisher gates; no production adoption is implied.

Peer provenance: evolution Work #13, #14, #19, #22, #24 and #26. The repair adds rendered-context verification to their exact-source and raw-grapheme work; those historical contributions retain their original scope and dissent.
