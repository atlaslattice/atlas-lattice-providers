import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { captureSourceDomMap } from '../interop/swarmchat_v32/dom_source_map.mjs';
import { showRevocableSourceHighlight } from '../interop/swarmchat_v32/dom_highlight_lease.mjs';

const sha=s=>createHash('sha256').update(s,'utf8').digest('hex');
const sourceRef={roomId:'v32-work-lease-test',seq:26,requestId:'lease-test-26'};
const highlightName='atlas-v32-evidence-lease';
function fixture(text='a🪿bc',opts={}) {
  const registry=new Map();
  const windowListeners=new Map();
  const observers=[];
  let cancelled=0;
  const win={
    CSS:{highlights:registry},
    Highlight:class {constructor(range){this.range=range;}},
    MutationObserver:class {
      constructor(fn){this.cb=fn;this.active=false;observers.push(this);}
      observe(_root,options){this.active=true;this.options=options;}
      disconnect(){this.active=false;}
    },
    setTimeout:(fn,ms)=>setTimeout(fn,ms),
    clearTimeout:(id)=>{cancelled++;clearTimeout(id);},
    addEventListener:(name,fn)=>{if(!windowListeners.has(name))windowListeners.set(name,new Set());windowListeners.get(name).add(fn);},
    removeEventListener:(name,fn)=>windowListeners.get(name)?.delete(fn),
    dispatch:(name)=>{for(const fn of windowListeners.get(name)||[])fn();},
  };
  const doc={defaultView:win,createTreeWalker(){let done=false;return {nextNode(){if(done)return null;done=true;return node;}};},createRange(){let a,b,start,end;const range={
    setStart(n,o){a=n;start=o;},setEnd(n,o){b=n;end=o;},
    toString(){return a===b?a.data.slice(start,end):'CROSS_NODE_FAKE';},
    startContainer:null,endContainer:null,
    detach(){this.detached=true;},
  };
  const ss=range.setStart.bind(range),se=range.setEnd.bind(range);
  range.setStart=(n,o)=>{ss(n,o);range.startContainer=n;};
  range.setEnd=(n,o)=>{se(n,o);range.endContainer=n;};
  return range;}};
  const node={nodeType:3,data:text,ownerDocument:doc,isConnected:true};
  const root={isConnected:true,ownerDocument:doc,contains:n=>n===node};
  const controller=new AbortController();
  let read=true,returned=true;
  const grant={readAllowed:async()=>read,returnAllowed:async()=>returned};
  const select={startUtf16:0,endUtf16:text.length};
  const emit=()=>{for(const obs of observers) if(obs.active)obs.cb([{type:'characterData'}]);};
  async function capture() {
    return await captureSourceDomMap({root,sourceRef,sourceText:text,sourceSha256:sha(text),
      copies:[{fromUtf16:0,toUtf16:text.length,node,startInNode:0}],readAllowed:grant.readAllowed});
  }
  async function show(overrides={}){
    const captured=await capture();
    return await showRevocableSourceHighlight({capture:captured,root,sourceRef,
      ...select,expectedSourceSha256:sha(text),expectedSourceRef:sourceRef,
      readAllowed:grant.readAllowed,returnAllowed:grant.returnAllowed,
      abortSignal:controller.signal,ttlMs:200,...overrides});
  }
  return {registry,win,doc,root,node,controller,grant,select,show,capture,emit,observers,
    setRead:v=>{read=v;},setReturn:v=>{returned=v;},
    cancelled:()=>cancelled};
}
const holds=(x)=>assert.deepEqual(x,{status:'HOLD_UNAVAILABLE'});
const active=x=>{assert.equal(x.status,'HIGHLIGHT_LEASE_ACTIVE'); assert.equal(x.isActive(),true);};

test('01 success registers a single CSS Highlight and no raw range escapes',async()=>{
 const f=fixture(),h=await f.show(); active(h);
 assert.equal(f.registry.size,1);assert.equal(typeof h.range,'undefined');assert.deepEqual(Object.keys(h),['status','dispose','isActive']);h.dispose();
});
test('02 abort synchronously clears registration',async()=>{const f=fixture(),h=await f.show();active(h);f.controller.abort();assert.equal(h.isActive(),false);assert.equal(f.registry.size,0);});
test('03 dispose idempotent and frozen public handle',async()=>{const f=fixture(),h=await f.show();h.dispose();h.dispose();assert.equal(Object.isFrozen(h),true);assert.equal(f.registry.size,0);});
test('04 TTL cleans up without further callbacks',async()=>{const f=fixture(),h=await f.show({ttlMs:10});active(h);await new Promise(resolve=>setTimeout(resolve,30));assert.equal(h.isActive(),false);assert.equal(f.registry.size,0);});
test('05 denied READ rejects before registration',async()=>{const f=fixture();f.setRead(false);holds(await f.show());assert.equal(f.registry.size,0);});
test('06 denied RETURN rejects before registration',async()=>{const f=fixture();f.setReturn(false);holds(await f.show());assert.equal(f.registry.size,0);});
test('07 already aborted signal rejects',async()=>{const f=fixture();f.controller.abort();holds(await f.show());});
test('08 missing CSS Highlight API refuses rather than insecure fallback',async()=>{const f=fixture();delete f.win.Highlight;holds(await f.show());});
test('09 bad digest rejects',async()=>{const f=fixture();holds(await f.show({expectedSourceSha256:'0'.repeat(64)}));});
test('10 wrong source reference rejects',async()=>{const f=fixture();holds(await f.show({expectedSourceRef:{...sourceRef,seq:27}}));});
test('11 mutation between capture and Range refuses',async()=>{const f=fixture();const cap=await f.capture();f.node.data='changed';holds(await f.show({capture:cap}));});
test('12 owned second registration replaces prior without stale delete',async()=>{const f=fixture(),h=await f.show(),c2=new AbortController();active(h);const h2=await f.show({abortSignal:c2.signal});active(h2);assert.equal(h.isActive(),false);h.dispose();assert.equal(f.registry.size,1);c2.abort();assert.equal(f.registry.size,0);});
test('13 unrelated CSS highlight must not be overwritten',async()=>{const f=fixture();const foreign={foo:1};f.registry.set(highlightName,foreign);holds(await f.show());assert.equal(f.registry.get(highlightName),foreign);});
test('14 MutationObserver clears highlight',async()=>{const f=fixture(),h=await f.show();active(h);f.emit();assert.equal(h.isActive(),false);assert.equal(f.registry.size,0);});
test('15 pagehide clears highlight',async()=>{const f=fixture(),h=await f.show();f.win.dispatch('pagehide');assert.equal(h.isActive(),false);});
test('16 handle does not serialize source or Range',async()=>{const f=fixture('SECRET_🪿'),h=await f.show();active(h);assert.equal(JSON.stringify(h),'\{"status":"HIGHLIGHT_LEASE_ACTIVE"\}');h.dispose();});
test('17 no signal rejects',async()=>{const f=fixture();holds(await f.show({abortSignal:null}));});
test('18 disconnected root refuses',async()=>{const f=fixture();f.root.isConnected=false;holds(await f.show());});
test('19 invalid span refuses',async()=>{const f=fixture();holds(await f.show({endUtf16:100}));});
test('20 TTL must be finite and bounded',async()=>{const f=fixture();for(const x of [-1,0,9,60001,Infinity,1.1,'20'])holds(await f.show({ttlMs:x}));});
test('21 denied callback exception returns constant HOLD',async()=>{const f=fixture();holds(await f.show({returnAllowed:async()=>{throw Error('secret');}}));});
test('22 abort during pending final RETURN must HOLD',async()=>{const f=fixture();let calls=0;let controller=f.controller;const ret=async()=>{calls++;if(calls>1)controller.abort();return true;};holds(await f.show({returnAllowed:ret}));assert.equal(f.registry.size,0);});
test('23 dispose clears timers',async()=>{const f=fixture(),h=await f.show();h.dispose();assert.ok(f.cancelled()>0);});
test('24 missing MutationObserver refuses',async()=>{const f=fixture();delete f.win.MutationObserver;holds(await f.show());});
test('25 stale root ownerDocument rejected on range check',async()=>{const f=fixture();const root={isConnected:true,ownerDocument:{},contains:()=>true};holds(await f.show({root}));});
test('26 registry set failure is fail-closed',async()=>{const f=fixture();f.registry.set=()=>{throw Error('secret')};holds(await f.show());});
test('27 partial emoji grapheme selection rejects',async()=>{const f=fixture();holds(await f.show({startUtf16:1,endUtf16:2}));});
test('28 already-denied READ does not allocate timer',async()=>{const f=fixture();f.setRead(false);holds(await f.show());assert.equal(f.cancelled(),0);});
test('29 document adoption during final RETURN cannot register in stale window',async()=>{
 const f=fixture();let calls=0;
 const ret=async()=>{
   if(++calls===2){const nextDocument={};f.root.ownerDocument=nextDocument;f.node.ownerDocument=nextDocument;}
   return true;
 };
 const h=await f.show({returnAllowed:ret});
 try{holds(h);assert.equal(f.registry.size,0);assert.ok(f.cancelled()>0);}
 finally{h.dispose?.();}
});
