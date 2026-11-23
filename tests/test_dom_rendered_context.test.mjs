import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {captureSourceDomMap,resolveSourceDomRange} from '../interop/swarmchat_v32/dom_source_map.mjs';

// Deterministic logical-DOM model. Genuine WebCrypto and Intl.Segmenter run;
// this is not a real browser, layout engine, IAM, or live SwarmChat fixture.
const ref={roomId:'v32-work-test-01',seq:26,requestId:'rendered-context-r02'};
const sha=s=>createHash('sha256').update(s,'utf8').digest('hex');
const HOLD={status:'HOLD_UNAVAILABLE'};
function fixture(parts) {
  let nodes;
  const doc={
    createTreeWalker(){let i=0;return {nextNode:()=>nodes[i++]??null};},
    createRange(){
      let sn,en,start,end;
      return {setStart(n,o){sn=n;start=o;},setEnd(n,o){en=n;end=o;},toString(){
        const a=nodes.indexOf(sn),b=nodes.indexOf(en);
        if(a<0||b<a)return '';
        if(a===b)return sn.data.slice(start,end);
        return sn.data.slice(start)+nodes.slice(a+1,b).map(n=>n.data).join('')+en.data.slice(0,end);
      }};
    },
  };
  const root={nodeType:1,isConnected:true,ownerDocument:doc,contains:n=>nodes.includes(n)};
  nodes=parts.map(data=>({nodeType:3,data,isConnected:true,ownerDocument:doc}));
  return {doc,root,nodes};
}
async function execute(source,parts,maps,start=0,end=source.length,options={}){
  const f=fixture(parts),hash=sha(source);
  const capture=await captureSourceDomMap({root:f.root,sourceRef:ref,sourceText:source,
    sourceSha256:hash,copies:maps.map(m=>({...m,node:f.nodes[m.node]})),readAllowed:()=>true});
  if(options.afterCapture)options.afterCapture(f);
  const result=await resolveSourceDomRange({capture,startUtf16:start,endUtf16:end,
    expectedSourceSha256:hash,expectedSourceRef:ref,readAllowed:()=>true,
    returnAllowed:async()=>{if(options.atReturn)options.atReturn(f);return true;}});
  return {capture,result};
}
const copy=(node,fromUtf16,toUtf16,startInNode=0)=>({node,fromUtf16,toUtf16,startInNode});
test('01 same-node inserted accent cannot split rendered grapheme',async()=>{
  const r=await execute('A',['A\u0301'],[copy(0,0,1)]);assert.deepEqual(r.result,HOLD);
});
test('02 adjacent unmapped accent cannot split cross-node grapheme',async()=>{
  const r=await execute('A',['A','\u0301'],[copy(0,0,1)]);assert.deepEqual(r.result,HOLD);
});
test('03 unmapped ZWJ continuation cannot split rendered emoji',async()=>{
  const r=await execute('👩',['👩','\u200d🔬'],[copy(0,0,2)]);assert.deepEqual(r.result,HOLD);
});
test('04 unmapped regional indicator cannot split rendered flag',async()=>{
  const r=await execute('🇺',['🇺','🇸'],[copy(0,0,2)]);assert.deepEqual(r.result,HOLD);
});
test('05 inserted prefix joining selected emoji also refuses',async()=>{
  const r=await execute('🔬',['👩\u200d','🔬'],[copy(1,0,2)]);assert.deepEqual(r.result,HOLD);
});
test('06 current unmapped mutation after awaited RETURN refuses',async()=>{
  const r=await execute('A',['A','!'],[copy(0,0,1)],0,1,
    {atReturn:f=>{f.nodes[1].data='\u0301';}});assert.deepEqual(r.result,HOLD);
});
test('07 whole unchanged source grapheme still succeeds',async()=>{
  const r=await execute('A\u0301',['A\u0301'],[copy(0,0,2)]);
  assert.equal(r.result.status,'DOM_RANGE_VERIFIED');assert.equal(r.result.range.toString(),'A\u0301');
});
test('08 ordinary unmapped neighbors preserve valid boundary',async()=>{
  const r=await execute('A',['x ','A',' !'],[copy(1,0,1)]);
  assert.equal(r.result.status,'DOM_RANGE_VERIFIED');assert.equal(r.result.range.toString(),'A');
});
test('09 exact cross-node source selection remains supported',async()=>{
  const r=await execute('abc',['a','b','c'],[copy(0,0,1),copy(1,1,2),copy(2,2,3)]);
  assert.equal(r.result.status,'DOM_RANGE_VERIFIED');assert.equal(r.result.range.toString(),'abc');
});
test('10 absent DOM traversal contract fails closed',async()=>{
  const r=await execute('A',['A'],[copy(0,0,1)],0,1,
    {afterCapture:f=>{delete f.doc.createTreeWalker;}});assert.deepEqual(r.result,HOLD);
});
test('11 unrelated malformed rendered Unicode cannot certify range',async()=>{
  const r=await execute('A',['A','\ud800'],[copy(0,0,1)]);assert.deepEqual(r.result,HOLD);
});
test('12 total rendered-context byte cap is enforced',async()=>{
  const r=await execute('A',['A','x'.repeat(262144)],[copy(0,0,1)]);assert.deepEqual(r.result,HOLD);
});
test('13 rendered text node traversal cap is enforced',async()=>{
  const r=await execute('A',['A',...Array(8192).fill('')],[copy(0,0,1)]);assert.deepEqual(r.result,HOLD);
});
test('14 empty unrelated Text nodes preserve exact selection',async()=>{
  const r=await execute('A',['','A',''],[copy(1,0,1)]);assert.equal(r.result.status,'DOM_RANGE_VERIFIED');
});
