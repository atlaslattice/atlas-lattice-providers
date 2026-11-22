# Ariadne v0.7 HSN source-coordinate boundary — 2026-11-22

**Status: source-only corrective candidate, not CANON, host deployment, or semantic mapping.**

The prior `core/coordinate_resolver.py` regex accepted H00–H11 / S00–S11 / N00–N11 as input knowledge positions. That excluded the full H12 Space & Aerospace House and accepted non-knowledge zero slots. Ariadne v0.7 knowledge coordinates are exactly `H01.S01.N01` through `H12.S12.N12` (12 × 12 × 12 = 1,728). `H00.S00.N00` is retained **only** as the Earth grounding reference in derived candidate packets, never as an accepted knowledge source coordinate.

## Fix

- Replace numeric component regex `(0\d|1[01])` with `(0[1-9]|1[0-2])`, for all three components.
- Preserve the existing wire packet schema and unmodified original claim, candidate/quarantine split, D-affinity, human-root hold, dissent, original fingerprint and safety gates.
- Add exhaustive coverage of all 1,728 valid HSN triples, plus Earth-sentinel and out-of-range negative tests.
- Do **not** map historical Mxx–Tyy task IDs to HSN via positional similarity, infer semantic truth from routing or grant access/authority.

## Source/evidence

- Original source on `main`: `core/coordinate_resolver.py`, Git blob `1a823e6255ca34aefea34e7387f86db9e134ddc1`.
- Original tests on `main`: `tests/test_coordinate_resolver.py`, Git blob `52a029eb5588e9daf03e65479d4d4908caeb0f76`.
- Ariadne v0.7 source registry SHA-256: `07533cf7a6b6f567259962bf73efee9b22b47cbacb429499787800e07864e5a6`. Source pin is reported by the resident-specific registry, not independently re-hashed in this patch.
- All tests are offline synthetic; no hosted current principal or rights-at-return are verified.

## Compatibility gate

Any historical caller using H00 as an **input knowledge coordinate** must move that usage to an explicit Earth grounding role. Do not silently reinterpret legacy coordinates. Human/source review is required before enabling in a production broker.

## Local commands

```bash
python -m unittest discover -s tests -p 'test_coordinate_resolver.py' -v
python -m py_compile core/coordinate_resolver.py tests/test_coordinate_resolver.py
```