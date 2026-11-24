/**
 * Atlas SwarmChat v32 - review-only, exact Work source -> DOM Range bridge.
 *
 * Trust boundary:
 * - Only a trusted Work renderer can pass exact sourceText and explicit COPY
 *   segments for DOM text nodes. This module does not acquire or authorize data.
 * - Only COPY spans are mapped; omitted/altered Markdown and HTML syntax remain
 *   unmappable. No inferred mappings from rendered text or remote sources.
 * - A SHA-256 of the raw source and an independent caller-supplied digest must
 *   agree; map snapshots recheck mutable DOM text before returning a Range.
 * - readAllowed / returnAllowed are deliberately required host callbacks,
 *   NEVER authoritative by themselves. The real publisher must own identity,
 *   revocation, egress and dispose the Range upon loss of access.
 * - This does not write DOM, emit source text, or mutate SwarmChat.
 */

const HOLD = Object.freeze({status:'HOLD_UNAVAILABLE'});
// Only an opaque handle crosses the API. Raw body and DOM nodes live in WeakMap.
const CAPTURE_STATE = new WeakMap();
const MAX_RAW_UTF8 = 256 * 1024;
const MAX_SEGMENTS = 2048;
const MAX_RENDER_TEXT_NODES = 8192;
const SHA = /^[a-f0-9]{64}$/;

function isValidScalarSequence(s) {
  for (let i = 0; i < s.length; i++) {
    const n = s.charCodeAt(i);
    if (n >= 0xd800 && n <= 0xdbff) {
      if (++i >= s.length || s.charCodeAt(i) < 0xdc00 || s.charCodeAt(i) > 0xdfff) return false;
    } else if (n >= 0xdc00 && n <= 0xdfff) return false;
  }
  return true;
}

const encoder = new TextEncoder();
function hex(bytes) {
  return Array.from(new Uint8Array(bytes), v=>v.toString(16).padStart(2,'0')).join('');
}

async function rawSha256(text) {
  if (!crypto?.subtle) return null;
  return hex(await crypto.subtle.digest('SHA-256', encoder.encode(text)));
}

function goodBoundary(text, start, end) {
  if (typeof Intl?.Segmenter !== 'function') return false;
  const segments = new Intl.Segmenter('und',{granularity:'grapheme'}).segment(text);
  let seenStart = start === 0 || start === text.length;
  let seenEnd = end === 0 || end === text.length;
  for (const g of segments) {
    if (g.index === start) seenStart = true;
    if (g.index === end) seenEnd = true;
    if (seenStart && seenEnd) break;
  }
  return seenStart && seenEnd;
}

function exactSourceRef(ref) {
  if (!ref || typeof ref !== 'object' || Array.isArray(ref)) return null;
  const {roomId,seq,requestId} = ref;
  if (typeof roomId !== 'string' || !/^[A-Za-z0-9_-]{3,80}$/.test(roomId) ||
      !Number.isSafeInteger(seq) || seq < 1 || seq > 500 ||
      typeof requestId !== 'string' || requestId.length < 1 || requestId.length > 80) return null;
  return roomId.length+':'+roomId+'|'+seq+'|'+requestId.length+':'+requestId;
}

function eligibleNode(node,root) {
  return node?.nodeType === 3 && node.isConnected && root?.isConnected &&
         typeof root.contains === 'function' && root.contains(node) &&
         node.ownerDocument === root.ownerDocument;
}

/**
 * Read the current root's logical DOM text, including unmapped neighbors.
 * A source grapheme can merge with rendered combining marks, ZWJ, or regional
 * indicators across Text nodes. Raw-source boundaries alone cannot certify a
 * rendered selection. This bounded snapshot stays internal and grants no rights.
 */
function renderedTextSnapshot(root, document) {
  if (typeof document.createTreeWalker !== 'function') return null;
  const walker = document.createTreeWalker(root, 4); // NodeFilter.SHOW_TEXT
  const offsets = new Map();
  const chunks = [];
  let units = 0, bytes = 0, count = 0;
  let node = root.nodeType === 3 ? root : walker.nextNode();
  while (node) {
    if (++count > MAX_RENDER_TEXT_NODES || !eligibleNode(node, root) ||
        typeof node.data !== 'string') return null;
    const data = node.data;
    bytes += encoder.encode(data).length;
    if (bytes > MAX_RAW_UTF8) return null;
    offsets.set(node, units);
    chunks.push(data);
    units += data.length;
    node = walker.nextNode();
  }
  const text = chunks.join('');
  return isValidScalarSequence(text) ? {text, offsets} : null;
}

/**
 * Capture a finite byte-exact COPY map; capture is independent of later calls.
 * Each entry: {fromUtf16,toUtf16,node,startInNode}. Gaps are intentionally
 * unmapped source characters (e.g. Markdown delimiters); rendered transformations
 * must be treated as separate UNMAPPED steps, not guessed away.
 */
export async function captureSourceDomMap({root,sourceRef,sourceText,sourceSha256,copies,readAllowed} = {}) {
  try {
    if (typeof readAllowed !== 'function' || await readAllowed() !== true) return HOLD;
    const sourceKey = exactSourceRef(sourceRef);
    if (!sourceKey || !root?.isConnected || !root?.ownerDocument || typeof sourceText !== 'string' ||
        !isValidScalarSequence(sourceText) || !SHA.test(sourceSha256) ||
        encoder.encode(sourceText).length > MAX_RAW_UTF8 ||
        !Array.isArray(copies) || copies.length < 1 || copies.length > MAX_SEGMENTS) return HOLD;
    if ((await rawSha256(sourceText)) !== sourceSha256) return HOLD;
    let lastEnd = 0;
    const spans = [];
    for (const entry of copies) {
      if (!entry || typeof entry !== 'object') return HOLD;
      const {fromUtf16,toUtf16,node,startInNode=0} = entry;
      if (![fromUtf16,toUtf16,startInNode].every(Number.isSafeInteger) ||
          fromUtf16 < lastEnd || toUtf16 <= fromUtf16 || toUtf16 > sourceText.length ||
          startInNode < 0 || !eligibleNode(node,root)) return HOLD;
      const length = toUtf16-fromUtf16;
      if (startInNode+length > node.data.length ||
          node.data.slice(startInNode,startInNode+length) !== sourceText.slice(fromUtf16,toUtf16) ||
          !goodBoundary(sourceText,fromUtf16,toUtf16)) return HOLD;
      spans.push({fromUtf16,toUtf16,node,startInNode,nodeData:node.data});
      lastEnd = toUtf16;
    }
    // Store raw source internally only; no mutation of the DOM.
    const internal = Object.freeze({root,sourceKey,sourceText,sourceSha256,
      spans: Object.freeze(spans.map(x=>Object.freeze(x))),
      document:root.ownerDocument});
    const handle=Object.freeze({status:'CAPTURED'});
    CAPTURE_STATE.set(handle,internal);
    return handle;
  } catch (_) { return HOLD; }
}

/**
 * Resolve a previously trusted raw-source UTF-16 span into one real DOM Range.
 * Returns only a Range and stable metadata to the authorized caller. A Range is
 * NOT an authorization token. Never store it after access is revoked.
 */
export async function resolveSourceDomRange({capture,startUtf16,endUtf16,
    expectedSourceSha256,expectedSourceRef,readAllowed,returnAllowed} = {}) {
  try {
    if (typeof readAllowed !== 'function' || typeof returnAllowed !== 'function' ||
        await readAllowed() !== true || capture?.status !== 'CAPTURED') return HOLD;
    const c = CAPTURE_STATE.get(capture);
    if (!c || !exactSourceRef(expectedSourceRef) || exactSourceRef(expectedSourceRef) !== c.sourceKey ||
        !SHA.test(expectedSourceSha256) || expectedSourceSha256 !== c.sourceSha256 ||
        !Number.isSafeInteger(startUtf16) || !Number.isSafeInteger(endUtf16) ||
        startUtf16 < 0 || endUtf16 <= startUtf16 || endUtf16 > c.sourceText.length ||
        !goodBoundary(c.sourceText,startUtf16,endUtf16)) return HOLD;
    if ((await rawSha256(c.sourceText)) !== expectedSourceSha256) return HOLD;

    let covered = startUtf16;
    let startPoint = null, endPoint = null;
    // Any source gap inside the span, including omitted Markdown syntax, HOLDS.
    for (const s of c.spans) {
      if (!eligibleNode(s.node,c.root) || s.node.ownerDocument !== c.document ||
          s.node.data !== s.nodeData) return HOLD;
      if (s.toUtf16 <= covered) continue;
      if (s.fromUtf16 > covered) return HOLD;
      if (!startPoint) startPoint = [s.node,s.startInNode+(startUtf16-s.fromUtf16)];
      covered = Math.min(s.toUtf16,endUtf16);
      endPoint = [s.node,s.startInNode+(covered-s.fromUtf16)];
      if (covered === endUtf16) break;
    }
    if (covered !== endUtf16 || !startPoint || !endPoint) return HOLD;
    // Check again after all async operations, prior to returning a live DOM Range.
    if (await returnAllowed() !== true) return HOLD;
    // The root can be adopted into another document while RETURN is pending.
    // Matching text/connectivity must not reuse the prior document's context.
    if (!c.root.isConnected || c.root.ownerDocument !== c.document ||
        c.spans.some(s=>!eligibleNode(s.node,c.root)||
          s.node.ownerDocument!==c.document||s.node.data!==s.nodeData)) return HOLD;
    // Validate the endpoints in CURRENT rendered context as well as raw source.
    // Inspect unmapped adjacent nodes too; a suffix mark may join the selection
    // without changing any mapped node or the selected Range's string value.
    const rendered = renderedTextSnapshot(c.root, c.document);
    if (!rendered || !rendered.offsets.has(startPoint[0]) ||
        !rendered.offsets.has(endPoint[0])) return HOLD;
    const renderedStart = rendered.offsets.get(startPoint[0]) + startPoint[1];
    const renderedEnd = rendered.offsets.get(endPoint[0]) + endPoint[1];
    if (renderedEnd <= renderedStart ||
        !goodBoundary(rendered.text, renderedStart, renderedEnd) ||
        rendered.text.slice(renderedStart, renderedEnd) !==
          c.sourceText.slice(startUtf16,endUtf16)) return HOLD;
    const range = c.document.createRange();
    range.setStart(...startPoint);
    range.setEnd(...endPoint);
    if (range.toString() !== c.sourceText.slice(startUtf16,endUtf16)) return HOLD;
    return {status:'DOM_RANGE_VERIFIED',unit:'utf16',startUtf16,endUtf16,
      sourceSha256:expectedSourceSha256,range};
  } catch (_) { return HOLD; }
}
