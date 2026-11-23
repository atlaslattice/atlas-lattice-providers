import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { captureSourceDomMap, resolveSourceDomRange } from '../src/dom_source_map.mjs';
const sourceRef = {roomId:'v32-work-test-01',seq:14,requestId:'deterministic-req-01'};
const sha = text=>createHash('sha256').update(text,'utf8').digest('hex');

function fixture(sourceText, cut=sourceText.length, changedText=sourceText) {
 const doc = {createRange(){
  let startNode, endNode, start, end;
  return {setStart(n,o){startNode=n;start=o},setEnd(n,o){endNode=n;end=o},toString(){
    if(startNode!==endNode) return 'UNSUPPORTED_FAKE_CROSS_NODE';
    return startNode.data.slice(start,end);
  }};
 }};
 const node={nodeType:3,data:changedText,isConnected:true,ownerDocument:doc};
 const root={isConnected:true,ownerDocument:doc,contains:n=>n===node};
 return {sourceText,root,node,copies:[{fromUtf16:0,toUtf16:cut,node,startInNode:0}]};
}
async function run(text,start,end,options={}){
 const f=fixture(text);
 const cap=await captureSourceDomMap({root:f.root,sourceRef,sourceText:text,sourceSha256:sha(text),copies:f.copies,readAllowed:()=>options.read!==false});
 const result=await resolveSourceDomRange({capture:cap,startUtf16:start,endUtf16:end,expectedSourceSha256:options.sha||sha(text),expectedSourceRef:options.expectedSourceRef||sourceRef,readAllowed:()=>options.read!==false,returnAllowed:()=>options.return!==false});
 return {cap,result,f};
}
test('01 actual SHA-256 from Node WebCrypto is accepted',async()=>{
 const {cap,result}=await run('alpha',0,5);assert.equal(cap.status,'CAPTURED');assert.equal(result.status,'DOM_RANGE_VERIFIED');
});
test('02 wrong digest fails constant shape',async()=>{const {result}=await run('alpha',0,5,{sha:'f'.repeat(64)});assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});});
test('03 combining mark split denied',async()=>{const {result}=await run('e\u0301',0,1);assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});});
test('04 emoji word offset accepted',async()=>{const {result}=await run('🌌a',2,3);assert.equal(result.status,'DOM_RANGE_VERIFIED');});
test('05 replay after mutation denies',async()=>{const {cap,result,f}=await run('alpha',0,5);assert.equal(result.status,'DOM_RANGE_VERIFIED');f.node.data='gamma';const again=await resolveSourceDomRange({capture:cap,startUtf16:0,endUtf16:5,expectedSourceSha256:sha('alpha'),expectedSourceRef:sourceRef,readAllowed:()=>true,returnAllowed:()=>true});assert.deepEqual(again,{status:'HOLD_UNAVAILABLE'});});
test('06 revoked read denies',async()=>{const {result}=await run('alpha',0,5,{read:false});assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});});
test('07 revoked return denies',async()=>{const {result}=await run('alpha',0,5,{return:false});assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});});
test('08 source surrogate invalid',async()=>{const f=fixture('\ud800');const cap=await captureSourceDomMap({root:f.root,sourceRef,sourceText:'\ud800',sourceSha256:sha('\ud800'),copies:f.copies,readAllowed:()=>true});assert.deepEqual(cap,{status:'HOLD_UNAVAILABLE'});});
test('09 no source exposed in success metadata',async()=>{const {result}=await run('VERY_PRIVATE',0,4);assert.equal(result.status,'DOM_RANGE_VERIFIED');assert.equal('sourceText' in result,false);});

test('11 same text wrong room identity refuses',async()=>{
 const {result}=await run('abc',0,3,{expectedSourceRef:{...sourceRef,roomId:'another-work-room'}});
 assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});
});
test('12 forged capture handle refuses',async()=>{
 const result=await resolveSourceDomRange({capture:{status:'CAPTURED'},startUtf16:0,endUtf16:1,
   expectedSourceSha256:sha('abc'),expectedSourceRef:sourceRef,readAllowed:()=>true,returnAllowed:()=>true});
 assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});
});
test('13 capture handle does not serialize private source',async()=>{
 const {cap}=await run('secret-source',0,6);
 assert.equal(JSON.stringify(cap),'{"status":"CAPTURED"}');
});

test('10 out of bounds refuses',async()=>{const {result}=await run('abc',1,9);assert.deepEqual(result,{status:'HOLD_UNAVAILABLE'});});
