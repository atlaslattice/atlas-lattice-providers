# Dual coordinate editions: CONTINUUM OS × Ariadne v0.7 — 2026-11-22

**Source-only additive compatibility candidate; not CANON, deployment, identity, semantic mapping or rights.**

The existing CONTINUUM OS [contract](../CONTINUUM_OS.md) intentionally uses a zero-based 12×12×12 candidate namespace (`H00..H11`, `S00..S11`, `N00..N11`). Ariadne v0.7 source uses the one-based 12×12×12 knowledge namespace (`H01..H12`, `S01..S12`, `N01..N12`). Both have **1,728 positions** but represent **different coordinate editions**; conversion by positional coincidence is **not** a semantic map. The prior default regex is correct *for the historical CONTINUUM namespace* but rejects Ariadne H12; this patch adds an explicit alternative without changing the default.

## Wire contract

- **Default / old caller:** missing `coordinate_edition` continues to mean `LEGACY_ZERO_BASED_12` (H00..H11 etc). Existing Earth-anchored H00 input behavior remains structurally accepted in that historical scheme.
- **Explicit Ariadne v0.7 caller:** add `coordinate_edition: ARIADNE_V07`, `coordinate_registry_digest: 07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6`, and `coordinate: Hxx.Syy.Nzz` where every component is 01..12. H00 is **not** an Ariadne knowledge source address.
- Both keep `earth_reference: H00.S00.N00` as an **output grounding reference**, and all existing candidate, provenance, dissent, D-affinity, NO MERGED MIND, human-root and authority gates.
- The derived candidate packet adds `coordinate_edition` and `coordinate_registry_digest` for audit. These fields are independently re-derived by `validate_grounding`; caller-side claims do not authenticate the Ariadne original source or grant any rights.
- Unrecognized editions, missing/wrong digest, out-of-range or malformed coordinate triples are quarantined without data loss.

## Evidence

- Original provider core: Git blob `1a823e6255ca34aefea34e7387f86db9e134ddc1`.
- Original provider tests: Git blob `52a029eb5588e9daf03e65479d4d4908caeb0f76`.
- Ariadne source SHA-256 above is a **registry-reported pin**, not an independent rehash of its original JSON in this patch.
- Exhaustive two-edition tests exercise **1,728 Ariadne** and **1,728 legacy** coordinates separately, plus negative cases and immutability/authority checks. Only synthetic local tests are claimed.

## Integration HOLD

Source-reported task sharding, visual coordinates and `H00` grounding cannot silently substitute for semantic identity or access rights. Any live host calling this resolver must explicitly select and verify its edition, perform real account authorization at read and return, and separately resolve cross-version source semantics. No CANON changes or deployment are made.

## Reproduce

```bash
python -m unittest discover -s tests -p 'test_coordinate_resolver.py' -v
python -m py_compile core/coordinate_resolver.py tests/test_coordinate_resolver.py
```
