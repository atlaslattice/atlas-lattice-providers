# SwarmChat v32 — Revocable DOM highlight lease (review-only)

**CANDIDATE / NOT CANON. AUTHORITY: none. DEPLOYMENT: not activated.**

**Status:** SOURCE-ONLY / LOCAL NODE+CHROMIUM PASS / GITHUB DRAFT / NOT IN LIVE SITE / HOST IAM NOT VERIFIED.

## Why this extension exists

The existing v32 review PR #65 already maps a *selected and source-hash-verified* Work message to a native DOM Range across exactly copied text nodes. A peer raised the next falsifier: what happens when access to that source is revoked **after** the Range was returned? A retained visual highlight can leak previously authorized private evidence after withdrawal. The lower-level function returns a Range but cannot reclaim a Range copied by untrusted callers.

This additive, UI-only `dom_highlight_lease.mjs` helper owns the Range within a closure, presents it via the native CSS Custom Highlight API, and returns only a frozen opaque handle `{status,dispose,isActive}`. A publisher-controlled AbortSignal must fire promptly on account/room/source revocation. That event synchronously removes the highlight and cancels the timer. DOM mutation, page navigation (`pagehide`), explicit disposal, or bounded TTL likewise remove it. A future caller must re-read/re-authorize; an expired handle cannot replay itself.

## Verified scope

- 73 existing+new distinct Node cases PASS normally and 73/73 with Node 22 `--jitless` (28 new lease cases).
- 36 real headless Chromium cases PASS (16 new lease cases, 20 existing Range cases). Includes real CSS paint appearing when active and disappearing after abort/revocation; actual DOM mutation and cross-element range checks.
- 109 distinct tests, 182 passing executions across Node normal, Node jitless and offline Chromium. Exact logs and SHA256 manifest included in the accompanying artifact.
- Chromium uses an **explicit deterministic WebCrypto digest stub only** because `about:blank` lacks a secure context. The existing Node tests exercise the original DOM adapter with genuine WebCrypto. Browser range/layout/mutation/paint operations are real Chromium APIs, not mocks.

## Required host integration

1. The **trusted publisher**, not this helper, chooses a Work-mode source under the correct account, room, current epoch, consent and READ grants. Protect message bodies in cache and transport.
2. The publisher supplies a short-lived `AbortSignal` that fires synchronously on rights withdrawal or source change; the helper also times out at 60 seconds maximum. **It cannot observe IAM changes without a host signal.**
3. Verify requestId, source/renderer/map SHA pins, expected identity and returned Range against the currently authorized source. The lower-level `dom_source_map.mjs` and this presenter are separate stages.
4. Do not hand out the lower-level Range or a serialized document fragment to unrelated code. If a caller retains its own copy of source text, this UI lease **cannot erase that copy**.
5. Provide host-owned CSS: `::highlight(atlas-v32-evidence-lease){background-color: ...}`. Native CSS Highlight is not supported in every client; if unsupported, the helper returns a constant HOLD without fallback insertion or DOM write.
6. Test actual authenticated two-account ACL / READ→RETURN revocation, source and renderer mutation, account switches, CSS Highlight support, pagehide, screen-reader behavior, contrast/color scheme, Android touch, and WebGL overlay composition. **None of these host/security/accessibility tests are satisfied by the offline suites.**

## Public API

```js
import { showRevocableSourceHighlight } from './dom_highlight_lease.mjs';
const abortController = new AbortController();
const lease = await showRevocableSourceHighlight({
  capture, root, startUtf16, endUtf16,
  expectedSourceSha256, expectedSourceRef,
  readAllowed: () => trustedHostCurrentReadCheck(),
  returnAllowed: () => trustedHostCurrentReturnCheck(),
  abortSignal: abortController.signal, ttlMs: 15_000,
});
// On trusted current rights withdrawal: abortController.abort();
// The visual CSS registration disappears immediately.
```

This example is **not runnable without trusted host integration**. It does not grant consent, authorization or resident identity. Omitted/later-acquired rights must HOLD. CSS Highlight name is fixed for **one displayed evidence selection per document**; it does not silently overwrite unrelated registered highlights. No raw source body or Range is returned by the new presenter. Existing source history, objections and alternatives are unchanged.

## Peer and release relationships

- The original revocable-render question is source-linked to SwarmChat evolution Work room messages #13, #19, #24, #26, and #27.
- Existing PR #65 remains the **only** review branch for this component; no duplicate publisher/control plane is introduced.
- Existing Graph Fabric search/index source, Atlas ONE PR #18 full-body/rights snapshots, hosted GitHub Actions admission, v32 visual UI and CANON ratification remain separate gates.
- Commit only as additive draft files. No merge, deployment, permissions change, billing, or private material imports in this work.
