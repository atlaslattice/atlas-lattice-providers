# SwarmChat v32: source-bound DOM Range integration candidate

**SOURCE-ONLY / DRAFT / NOT MOUNTED / NOT DEPLOYED / NOT HOST CI.**

This additive adapter extends PR #65's raw-source Unicode-span helper. It does not replace Graph Fabric, any peer source verifier, an existing renderer, or the running SwarmChat v32 Site.

## Actual reproducibility

The exact source module and Node tests passed locally in Node 22.16.0: **13/13 standard + 13/13 --jitless PASS** with real Node WebCrypto SHA-256 and an isolated fake DOM.

A separate offline Playwright + real Chromium fixture passed **20/20 real DOM Range tests**: cross-element selections, Unicode/emoji/ZWJ and grapheme checks, Markdown source gaps, node reorder/detach/mutation, denied mock READ/RETURN, source-hash mismatch and no DOM writes. The browser's isolated about:blank page has no secure WebCrypto context, so the fixture explicitly stubs **only SHA-256** with a deterministic exact-source test digest; cryptographic verification is exercised in Node separately. This is NOT an authenticated v32 UI test or proof of host authorization.

## Input and output

- captureSourceDomMap accepts root, sourceRef(roomId,seq,requestId), sourceText, sourceSha256, explicit COPY segments, and readAllowed callback.
- resolveSourceDomRange takes the opaque capture handle, UTF-16 source span, expected source ref and hash, readAllowed and returnAllowed callbacks.
- An explicit COPY segment maps equal source UTF-16 units to one DOM Text node. Gaps (Markdown delimiters and rendered transformations) are NOT guessed away. A selection spanning a gap HOLDS; a selection fully within valid COPY spans can map across DOM nodes.
- Capture handles are **opaque**: source text and DOM references live in a private WeakMap, not in serializable returned state. Forged handles, mixed sources, stale hashes, moved nodes and partial grapheme boundaries HOLD. A DOM Range is not an authorization token.

## Security and adoption gates

Trusted publisher must pin the Work record, enforce READ+RETURN+egress rights, and discard Range selections on revocation; untrusted browser callbacks cannot grant rights. The renderer must supply an independently authenticated source-to-render map; altered Markdown/HTML cannot be silently mapped. Signed-in Chrome/Android, assistive tech, revoked-after-Range and two-account isolation are NOT TESTED. No private mode ingestion, D1 write, CANON, spending or deployment.

Local commands:
- node --test tests/test_dom_source_map.test.mjs
- node --jitless --test tests/test_dom_source_map.test.mjs
- python -m unittest discover -s tests -p test_dom_range_chromium.py -v (requires local Playwright/Chromium)

Related: SwarmChat evolution Work #10/#13/#14/#19 and Providers PR #65. Historical 440-character excerpt scoring is not a live v32 proof.
