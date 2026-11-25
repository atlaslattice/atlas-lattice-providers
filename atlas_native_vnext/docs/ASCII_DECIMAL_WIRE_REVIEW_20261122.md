# Atlas Native Synthesis — ASCII scientific decimal wire review (2026-11-22)

**CANDIDATE / SOURCE-ONLY / NOT HOSTED / NOT CANON / NO AUTHORITY.**
This is a narrow additive review receipt for the independent `atlas_native_vnext/` kernel; it does not merge PR #61 or dispatch a Work task, read private bodies, execute providers, change host rights or alter upstream OSS licensing.

## Reproduction and correction

The original exact module `native_synthesis/wire.py` at Git blob `f425930834a463032aa18f05ef1619bfc6a68f6f` used Python regex `\\d` for mantissa and exponent digits. Python `Decimal` accepts Unicode decimal numerals, so the original synthetic tests falsely accepted nine inputs including `1.٢`, `9٩`, `1e+٩` and `1e۹` as valid scientific wire quantities. This is a **cross-language grammar ambiguity** in a source-only packet, not proof of a hosted exploit or experimental data error.

The corrected pattern uses explicit ASCII `[0-9]` in each decimal position and leaves ordinary signed decimals, exact unit allowlist, mantissa precision and exponent magnitude limits unchanged. Correct source Git blob: `caf3aeae1d9af24ecc0ef38e9893f233859be856`.

## Local verification and provenance

Exact original GitHub source was reconstructed byte-for-byte locally; original Git blob SHA-1 matched. With the new regression module, the original source produced 9 negative subcase failures in 11 methods. The corrected source then passed **11/11 Python unittest methods in normal mode, 11/11 with `-O`**, and `py_compile` for source and tests. Tests include nine Unicode mixed-script negative cases, valid integer/fraction/scientific inputs, nonfinite/float-style denial, unsupported units, nonstring denial, precision and exponent bounds. Exact newly committed test blob: `1318dda16c487d9f33f9c9b0d5bc8081d31506a9`.

One intermediate source commit `39f0d5c86845e76e645209312ac8148ea5b707c0` accidentally expanded replacement text. This was immediately corrected with original-source reconstruction in commit `15fc74564b64cc763f83b6cadbe1328f9b9fe388`; both remain in history. Subsequent test commit: `d6f5a8e946270a1370cb8281c352e253591c4ac3`. Authenticated GitHub readback verified correct source/test Git blobs against locally executed copies.

**Verification limit:** these 11 are focused tests on the exact `wire.py` module, not execution of the full 91-method package suite, not proof of CI pass, rights-at-RETURN, independently authenticated peers, real host, model SDK execution, or deployed capacity.

## Release HOLD

PR #63 stays **OPEN/DRAFT/UNMERGED** pending a full exact-HEAD checkout suite, repository CI with executed runner steps and retrievable logs (shared CI issue #54), independent code/license/rights review, source dependency and release checks, and explicit appropriate owner authority. PR #61 is a separate source-only Labs draft; no automatic cross-PR merge or canon edition equivalence. Preserve all original history, objections and local evidence. Fourteen voluntary non-Work beats remain UNPERFORMED.
