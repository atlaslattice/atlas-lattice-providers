# SwarmChat v32 source-only Unicode highlight adapter

**Status:** SOURCE-ONLY / 32 local Node tests in normal and --jitless modes / NOT HOSTED / NOT DEPLOYED.

This isolated module complements existing graph search and selected-source review proposals. It does not fetch or index source records, infer semantic relationships, authenticate a resident, or change SwarmChat.

## API
`verifiedUtf16Highlight({sourceText, expectedSha256, startCodePoint, endCodePoint})`

- Input: exact **previously authorized Work** source string and raw UTF-8 SHA256 digest, with a half-open Unicode scalar/code-point span from a separately verified exact match.
- Output on success: deterministic `{status:"VERIFIED_SPAN",unit:"utf16",startUtf16,endUtf16,sourceSha256,sourceCodePoints,graphemeAligned:true}`; no source text.
- Failure: identical `{status:"HOLD_UNAVAILABLE"}` for stale hashes, malformed Unicode, out-of-range spans, partial grapheme clusters, absent ICU Segmenter and oversized source.
- Handles supplementary characters (emoji), ZWJ graphemes, regional flags, combining marks and CRLF; never silently normalizes source.
- Executes NO network, browser, model, Work-room, private-mode or hosted operations.

## Host integration contract

The publisher, **not this utility**, must select the exact source under current READ permission, validate the source and phrase/token semantics separately, and re-check all current RETURN and sink permissions before revealing a highlight. SHA256 here is byte integrity, **not** identity or authorization. Browser/ICU cross-platform support and current served Site source remain **unverified**; do not report a WebGL or ACL pass.

Run:
```sh
node --test tests/source_highlight_offset.test.mjs
node --jitless --test tests/source_highlight_offset.test.mjs
```

32 test cases passed locally in both Node 22 modes. A future integrator should validate a trusted host-source snapshot, test real desktop/Android rendering (UTF-16 offsets), apply revocation at RETURN, and preserve original room history/source rights. Reversible by excluding this unimported helper from build.

Source-linked review context: [SwarmChat habitat QA #64](https://github.com/atlaslattice/atlas-lattice-providers/issues/64).
