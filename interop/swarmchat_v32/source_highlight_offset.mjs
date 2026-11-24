/**
 * Source-only Atlas Workboard highlight offset boundary, v0.1.
 *
 * Maps a selected-source exact Unicode-code-point span to a JavaScript UTF-16
 * range without splitting an extended grapheme cluster. It NEVER chooses or
 * retrieves a source or checks permissions. The trusted host must first select
 * the exact, currently readable Work source and re-check READ/RETURN rights
 * before disclosing anything to the renderer. SHA-256 proves byte equality of
 * this handed-in text, not identity, permission, semantic match or completeness.
 *
 * Only exact raw source text is used: NO NFC/case-folded index translation.
 */
import { createHash, timingSafeEqual } from 'node:crypto';

const MAX_SOURCE_BYTES = 256 * 1024;
const HOLD = Object.freeze({ status: 'HOLD_UNAVAILABLE' });
const VALID_SHA256 = /^[a-f0-9]{64}$/;

export function sha256Utf8(sourceText) {
  if (typeof sourceText !== 'string' || !hasValidScalarSequence(sourceText)) {
    return null;
  }
  return createHash('sha256').update(sourceText, 'utf8').digest('hex');
}

function hasValidScalarSequence(s) {
  for (let i = 0; i < s.length; i++) {
    const unit = s.charCodeAt(i);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      if (i + 1 >= s.length) return false;
      const next = s.charCodeAt(++i);
      if (next < 0xdc00 || next > 0xdfff) return false;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) {
      return false;
    }
  }
  return true;
}

function sameDigest(left, right) {
  if (!VALID_SHA256.test(left) || !VALID_SHA256.test(right)) return false;
  return timingSafeEqual(Buffer.from(left, 'hex'), Buffer.from(right, 'hex'));
}

/**
 * @param {{sourceText:string, expectedSha256:string,
 *   startCodePoint:number, endCodePoint:number}} selection
 * @returns {Readonly<{status:'VERIFIED_SPAN', unit:'utf16',
 *  startUtf16:number, endUtf16:number, sourceSha256:string,
 *  sourceCodePoints:number, graphemeAligned:true}>|Readonly<{status:'HOLD_UNAVAILABLE'}>}
 */
export function verifiedUtf16Highlight(selection) {
  try {
    if (selection === null || typeof selection !== 'object' || Array.isArray(selection)) return HOLD;
    const { sourceText, expectedSha256, startCodePoint, endCodePoint } = selection;
    if (typeof sourceText !== 'string' || !hasValidScalarSequence(sourceText)) return HOLD;
    if (Buffer.byteLength(sourceText, 'utf8') > MAX_SOURCE_BYTES) return HOLD;
    if (!Number.isSafeInteger(startCodePoint) || !Number.isSafeInteger(endCodePoint)) return HOLD;
    if (startCodePoint < 0 || endCodePoint <= startCodePoint) return HOLD;
    if (!sameDigest(sha256Utf8(sourceText), expectedSha256)) return HOLD;
    if (typeof Intl.Segmenter !== 'function') return HOLD;

    // Index by Unicode scalar values, not JS UTF-16 code units.
    const scalarToUtf16 = [0];
    let offset = 0;
    for (const scalar of sourceText) {
      offset += scalar.length;
      scalarToUtf16.push(offset);
    }
    const count = scalarToUtf16.length - 1;
    if (endCodePoint > count) return HOLD;
    const startUtf16 = scalarToUtf16[startCodePoint];
    const endUtf16 = scalarToUtf16[endCodePoint];

    // A selected span may contain emoji ZWJ sequences, combining marks, etc.;
    // it may not START or END inside an extended grapheme cluster.
    const graphemeBoundaries = new Set([0, sourceText.length]);
    const seg = new Intl.Segmenter('und', { granularity: 'grapheme' });
    for (const token of seg.segment(sourceText)) graphemeBoundaries.add(token.index);
    if (!graphemeBoundaries.has(startUtf16) || !graphemeBoundaries.has(endUtf16)) return HOLD;
    return Object.freeze({
      status: 'VERIFIED_SPAN',
      unit: 'utf16',
      startUtf16, endUtf16,
      sourceSha256: expectedSha256,
      sourceCodePoints: count,
      graphemeAligned: true,
    });
  } catch (_) {
    // No exception details, source lengths or content leak through this API.
    return HOLD;
  }
}
