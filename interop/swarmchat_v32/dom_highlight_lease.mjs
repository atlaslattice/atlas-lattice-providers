/**
 * SwarmChat v32 source-only, OPTIONAL, revocable UI highlighting boundary.
 * A trusted renderer chooses the source and supplies live authorization hooks.
 * This module neither authenticates a user nor obtains private source bytes.
 * It retains a DOM Range internally, never returns one or source text, and
 * unregisters a CSS Highlight on host revocation, pagehide, DOM mutation or TTL.
 *
 * A DOM/renderer integration is NOT proof of atomic READ/RETURN rights.
 * CSS Highlight API renders with publisher-owned ::highlight styling only.
 */
import { resolveSourceDomRange } from './dom_source_map.mjs';

const HOLD = Object.freeze({status:'HOLD_UNAVAILABLE'});
const HIGHLIGHT_NAME = 'atlas-v32-evidence-lease';
const MAX_TTL_MS = 60_000;
const MIN_TTL_MS = 10;
const owners = new WeakMap(); // document -> active internal lease, never exported

function eligibleSignal(signal) {
  return signal && typeof signal.aborted === 'boolean' &&
    typeof signal.addEventListener === 'function' &&
    typeof signal.removeEventListener === 'function';
}

function eligibleRegistry(win) {
  const registry=win?.CSS?.highlights;
  return registry && typeof registry.get==='function' &&
    typeof registry.has==='function' && typeof registry.set==='function' &&
    typeof registry.delete==='function' && typeof win.Highlight==='function' &&
    typeof win.MutationObserver==='function' &&
    typeof win.setTimeout==='function' && typeof win.clearTimeout==='function' &&
    typeof win.addEventListener==='function' && typeof win.removeEventListener==='function';
}

function cleanLease(state) {
  if (!state || !state.active) return;
  state.active=false;
  try { state.observer?.disconnect(); } catch (_) {}
  try { state.signal?.removeEventListener('abort',state.dispose); } catch (_) {}
  try { state.win?.removeEventListener('pagehide',state.dispose); } catch (_) {}
  try { if (state.timeoutId!==null) state.win?.clearTimeout(state.timeoutId); } catch (_) {}
  try {
    if (owners.get(state.doc)===state) {
      if (state.registry.get(HIGHLIGHT_NAME)===state.highlight) {
        state.registry.delete(HIGHLIGHT_NAME);
      }
      owners.delete(state.doc);
    }
  } catch (_) {}
  try { state.range?.detach?.(); } catch (_) {}
  state.range=null;
  state.highlight=null;
  state.observer=null;
  state.timeoutId=null;
  state.root=null;
  state.signal=null;
}

/**
 * UI-only, fail-closed presentation of one already-authorized source match.
 * REQUIRED host-side: account/room identity, current READ/RETURN rights,
 * source/select semantics, and prompt AbortController.abort() on revocation.
 * One evidence highlight is allowed per document. No callbacks run in the
 * background to retrieve source. TTL is bounded; no persistent work state.
 *
 * Success returns only an opaque, frozen {status,dispose,isActive}. The Range
 * is deliberately private; callers must not independently render/store a
 * Range obtained from the lower-level bridge after permission withdrawal.
 */
export async function showRevocableSourceHighlight({
  capture, root, startUtf16, endUtf16, expectedSourceSha256,
  expectedSourceRef, readAllowed, returnAllowed, abortSignal, ttlMs=30_000,
}={}) {
  let state=null;
  try {
    if (!root?.isConnected || !root?.ownerDocument ||
        typeof root.contains!=='function' ||
        typeof readAllowed!=='function' || typeof returnAllowed!=='function' ||
        !eligibleSignal(abortSignal) || abortSignal.aborted ||
        !Number.isSafeInteger(ttlMs) || ttlMs<MIN_TTL_MS || ttlMs>MAX_TTL_MS) return HOLD;
    const doc=root.ownerDocument;
    const win=doc.defaultView;
    if (!eligibleRegistry(win)) return HOLD;
    const registry=win.CSS.highlights;
    // Do not overwrite a highlight owned by some unrelated Site component.
    if (registry.has(HIGHLIGHT_NAME) && !owners.has(doc)) return HOLD;
    if (await readAllowed()!==true || abortSignal.aborted || !root.isConnected) return HOLD;
    const result=await resolveSourceDomRange({capture,startUtf16,endUtf16,
      expectedSourceSha256,expectedSourceRef,readAllowed,returnAllowed});
    if (result?.status!=='DOM_RANGE_VERIFIED' || !result.range || abortSignal.aborted) return HOLD;
    const range=result.range;
    if (range.startContainer?.ownerDocument!==doc ||
        range.endContainer?.ownerDocument!==doc ||
        !root.contains(range.startContainer) || !root.contains(range.endContainer)) return HOLD;
    const expectedVisibleText=range.toString();
    if (!expectedVisibleText || !root.isConnected) return HOLD;
    // Prepare revocation/mutation fencing BEFORE final async permission check.
    state={active:true,doc,win,registry,root,range,signal:abortSignal,
      highlight:null,observer:null,timeoutId:null,dispose:null};
    state.dispose=()=>cleanLease(state);
    state.observer=new win.MutationObserver(()=>state.dispose());
    state.observer.observe(root,{subtree:true,childList:true,characterData:true,attributes:true});
    abortSignal.addEventListener('abort',state.dispose,{once:true});
    win.addEventListener('pagehide',state.dispose,{once:true});
    state.timeoutId=win.setTimeout(state.dispose,ttlMs);
    if (await returnAllowed()!==true || abortSignal.aborted || !root.isConnected ||
        !root.contains(range.startContainer) || !root.contains(range.endContainer) ||
        range.toString()!==expectedVisibleText || !state.active) {
      state.dispose();return HOLD;
    }
    // One authoritative selection per document. Existing owned lease is
    // removed; stale prior handle cannot delete the new lease.
    const old=owners.get(doc);
    if (old) old.dispose();
    if (registry.has(HIGHLIGHT_NAME)) {state.dispose();return HOLD;}
    state.highlight=new win.Highlight(range);
    owners.set(doc,state);
    registry.set(HIGHLIGHT_NAME,state.highlight);
    if (abortSignal.aborted || !root.isConnected) {state.dispose();return HOLD;}
    return Object.freeze({
      status:'HIGHLIGHT_LEASE_ACTIVE',
      dispose:()=>state.dispose(),
      isActive:()=>state.active,
    });
  } catch (_) {
    if (state) state.dispose();
    return HOLD;
  }
}
