# Native integration release gates and required host proof

All gates start **HELD** until real independent host evidence is obtained. Nothing in this source tree can grant authority or unblock itself by returning a flag.

| Gate | Concrete proof required |
|---|---|
| SRC-1 | pin exact current deployed Site and Atlas ONE/AtlasGPT package HEAD, manifest and rollback SHA |
| SRC-2 | source licensing review including upstream commit, notices, transitive dependencies and export boundaries |
| SRC-3 | clean locked install/test/build with GitHub Actions assigned runners, nonempty steps and actual logs |
| AUTH-1 | platform-authenticated tenant, principal, conversation and user-consent scope; model labels insufficient |
| AUTH-2 | same issuer must check grants BEFORE storage/index/cache and at RETURN; wrong tenant indistinguishable from nonexistent |
| AUTH-3 | withdrawal epoch survives crash/restore; no stale cache or re-seed resurrects a revoked grant |
| EGRESS-1 | sink-side per-page/per-chunk commit fenced against current W epoch; accepted/in-flight bytes may arrive after W |
| EGRESS-2 | receiver-side durable idempotency + lost ACK reconciled; no blind reemit on ambiguous delivery |
| WORK-1 | permitted Work room exact read + user-approved post + broker seq readback; no automatic model wakes |
| WORK-2 | actual independent conversation/peer identity and voluntary explicit read/reply receipts separate from post count |
| CROSSMODE | Play, Imagine, Dream, Quiet, Brain and Palace existence/metadata/timing not accessible via Work |
| ATLASONE | real host task intake, idempotency, cancel/retry and permissions readback |
| ALEXANDRIA | source/edition-pinned graph candidate, rights at RETURN, review+dissent; semantic edge not auto accepted |
| UWS | actual permissioned metadata read in a disposable tenant; no secrets in trace/headers |
| SCI-1 | verify lab backend/solver revision, units, published data rights, zero-physics/negative controls |
| SCI-2 | empirical calibration & blind verification before any validated science/physical hardware claim |
| RELEASE | owner approves selected release/visibility/production changes separately; rollback rehearsal and canary |

## Acceptance demonstration

One public, benign Work source is chosen independently; an authenticated human issues one experiment task through Atlas ONE; a permitted SwarmChat peer reviews an exact source and returns a falsifier; Alexandria records the separately adjudicated source/evidence candidate. Repeat across a second account with deliberate revocation **between READ and RETURN**, and an old-epoch cached handle. The unauthorized path must produce no source existence clues, metadata, cache hit, output or private body. The ledger must distinguish PREPARED, POSTED, READ, PEER_RETURNED, CI_VERIFIED, HOST_DEPLOYED and CANON_RATIFIED.

**No scheduled tasks, no second broker, no live push/subscribe, no provider spend, no launch** have been created by the current candidate.
