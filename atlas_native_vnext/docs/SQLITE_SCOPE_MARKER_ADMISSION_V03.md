# Atlas Native Synthesis — SQLite scope-marker admission gate (v0.3)

**SOURCE-ONLY REVIEW / NOT DEPLOYED / NOT HOST AUTHORIZATION / NO CANON EFFECT.**

## Reproduced negative on previous PR #63 source
Prior `offline_receipts.py` blob `09be709ea863c737e2b9b7f1de9720d739a0397f` created `meta` first, then treated the missing `scope_key_id` as a new database. A preexisting SQLite database with `scopes` and one `PREPARED_NOT_POSTED` receipt, but no `meta` table, was therefore **ADMITTED** and reported `prepared_records=1`. This was reproduced locally using the unmodified exact source. It is an offline schema-identity bug, **not an observed live tenant leak**.

## Implemented fail-closed repair
- Open the initialization transaction with `BEGIN IMMEDIATE` **before** creating metadata, so the first-open check and marker insertion share a database writer lock.
- If `scope_key_id` is absent, refuse any preexisting non-`meta` SQLite tables, or nonempty unknown `meta` entries. The old file is not imported, automatically rewritten, relabeled, or given authority.
- Refuse changed/mismatched scope key pins as before. A genuine new, empty database and an empty `meta`-only stub can initialize normally.
- Continue to treat HMAC tenant/account/principal strings as **local synthetic scope labels**, never a host issuer proof.

Exact independently read-back changed GitHub blobs:
- `native_synthesis/offline_receipts.py`: `e98e0c71c2fa612695b2484d633469d8f5857cf7`
- `tests/test_native_offline_receipts.py`: `2aeac1b9fbfd0459d3b22806ef3307a02fbdca28`

## Local test evidence
The original 21 receipt-store tests were preserved and **four** new tests were added: missing-marker with legacy rows, deleted marker with current rows, harmless empty metadata stub, and unknown metadata without scope marker. `25/25` focused receipt tests PASS.

Running the standalone native source tree:
```sh
python -m unittest discover -s tests -p 'test_*.py'
python -O -m unittest discover -s tests -p 'test_*.py'
python scripts/adversarial_preflight.py
```
Both Python modes ran **148 methods: 122 PASS, 26 SKIPPED** (the skips require a separately pinned Atlas Labs PR #61 source checkout). All **1,024 synthetic adversarial checks PASS** with zero real posts, graph writes, model calls or host rights checks. These are **not** 148 passing integration checks, full repository CI, or real peer exchanges.

## Acceptance / outstanding checks
- Verify the exact changed source and regression file SHA at current PR head; run a complete exact-PR61-checkout suite without skipped cases, guarding the separate revision pin rather than treating an older fixture as current.
- Verify two-process first-opening behavior under SQLite locking, key mismatch, malformed/corrupt marker and restart. Preserve legacy database bytes for forensic review; never silently migrate them.
- **GitHub Actions zero-step blocker remains external.** Current PR head `98830cbc40876a959d9a61d5342e109d5a41f78c` triggered run `45239891143`, completed failure with no recorded job steps. Do not infer a Python failure.
- Actual hosted tenant/account identity, Work READ + RETURN permission gates, receiver COMMIT fencing, same-account/different-tenant isolation, protected cache noninterference and publisher rollback remain **UNVERIFIED**.
- Preserve draft PR, original broker, access and CANON. This change is a local adapter safety gate only.
