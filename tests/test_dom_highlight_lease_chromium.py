"""Isolated real Chromium CSS Highlight registry + DOM revocation tests.
No network; about:blank digest provider intentionally stubbed (Node crypto tested
separately). Not a signed-in Site, real IAM, Android, or hosted deployment.
"""
from pathlib import Path
import hashlib
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/'interop/swarmchat_v32/dom_source_map.mjs').read_text(encoding='utf8')
lease=(ROOT/'interop/swarmchat_v32/dom_highlight_lease.mjs').read_text(encoding='utf8')
JS=base.replace('export async function ','async function ')+ '\n'+ lease.replace("import { resolveSourceDomRange } from './dom_source_map.mjs';",'').replace('export async function ','async function ')
# The constant HOLD appears in both source files. Rename the second one here
# only for injecting both scripts in the same browser global test fixture.
JS=JS.replace("const HOLD = Object.freeze({status:'HOLD_UNAVAILABLE'});", "const HOLD = Object.freeze({status:'HOLD_UNAVAILABLE'});", 1)
first=JS.index('const HOLD =')
second=JS.find('const HOLD =',first+1)
JS=JS[:second]+JS[second:].replace("const HOLD = Object.freeze({status:'HOLD_UNAVAILABLE'});",'',1)
SETUP=r'''async ({text,html,copies,start=0,end=null,ttl=200,deniedRead=false,deniedReturn=false,foreign=false,badMap=false}) => {
  // Test is about:blank; only digest generation is stubbed. CSS Highlights,
  // DOM Range, MutationObserver, AbortController and Segmentation are native.
  const sha = globalThis.__testSHA;
  Object.defineProperty(window,'crypto',{configurable:true,value:{subtle:{digest:async(_algorithm,encoded)=>{
    const decoded=new TextDecoder('utf-8',{fatal:true}).decode(encoded);
    const selected=decoded===text?sha:'0'.repeat(64);
    return Uint8Array.from(selected.match(/../g),s=>parseInt(s,16)).buffer;
  }}}});
  document.body.innerHTML='<div id="fixture">'+html+'</div>';
  const root=document.getElementById('fixture');
  const nodes=[...root.querySelectorAll('[data-copy]')].map(e=>e.firstChild);
  const sourceRef={roomId:'v32-work-lease-test',seq:26,requestId:'lease-test-26'};
  const controller=new AbortController();
  if(foreign)CSS.highlights.set('atlas-v32-evidence-lease',new Highlight(document.createRange()));
  const captured=await captureSourceDomMap({root,sourceRef,sourceText:text,sourceSha256:sha,
     copies:copies.map(c=>({...c,node:nodes[c.node]})),readAllowed:()=>true});
  const result=await showRevocableSourceHighlight({root,capture:captured,startUtf16:start,
     endUtf16:end===null?text.length:end,expectedSourceSha256:badMap?'f'.repeat(64):sha,
     expectedSourceRef:sourceRef,readAllowed:()=>!deniedRead,returnAllowed:()=>!deniedReturn,
     abortSignal:controller.signal,ttlMs:ttl});
  globalThis.__leaseState={controller,result,root,nodes};
  return {status:result.status,active:result.isActive?.()??false,
    registered:CSS.highlights.has('atlas-v32-evidence-lease'),
    captured:captured.status,copyCount:copies.length,serialized:JSON.stringify(result)};
}'''

class LeaseBrowserTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.p=sync_playwright().start()
    cls.browser=cls.p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  @classmethod
  def tearDownClass(cls):
    cls.browser.close();cls.p.stop()
  def setUp(self):
    self.page=self.browser.new_page(viewport={'width':800,'height':300},device_scale_factor=1)
    self.page.set_content('<html><style>::highlight(atlas-v32-evidence-lease) { background-color: rgb(255,255,0); }</style><body><p>ready</p></body></html>')
    self.page.add_script_tag(content=JS)
    self.page.evaluate('window.__testSHA=null')
  def tearDown(self):
    self.page.close()
  def setup(self,text='Hello 🪿 world',html='<span data-copy>Hello 🪿 world</span>',copies=None,**kwargs):
    if copies is None: copies=[{'node':0,'fromUtf16':0,'toUtf16':len(text.encode('utf-16-le'))//2}]
    self.page.evaluate('(s)=>window.__testSHA=s',hashlib.sha256(text.encode('utf8')).hexdigest())
    return self.page.evaluate(SETUP,{'text':text,'html':html,'copies':copies,**kwargs})
  def state(self):
    return self.page.evaluate('({registered:CSS.highlights.has("atlas-v32-evidence-lease"),active:__leaseState.result.isActive?.()??false})')
  def test_01_live_css_registry_positive(self):
    r=self.setup();self.assertEqual(r['status'],'HIGHLIGHT_LEASE_ACTIVE');self.assertTrue(r['registered'])
  def test_02_revocation_abort_removes_active_highlight(self):
    self.setup();s=self.page.evaluate('''()=>{__leaseState.controller.abort();return {registered:CSS.highlights.has('atlas-v32-evidence-lease'),active:__leaseState.result.isActive()}}''')
    self.assertEqual(s,{'registered':False,'active':False})
  def test_03_live_dom_mutation_triggers_removal(self):
    self.setup();self.page.evaluate("()=>{__leaseState.nodes[0].data+='x'}")
    self.page.wait_for_timeout(10);self.assertFalse(self.state()['registered'])
  def test_04_dom_child_removal_triggers_removal(self):
    self.setup();self.page.evaluate('()=>__leaseState.nodes[0].parentNode.remove()')
    self.page.wait_for_timeout(10);self.assertFalse(self.state()['registered'])
  def test_05_pagehide_removes_highlight(self):
    self.setup();self.page.evaluate("()=>window.dispatchEvent(new Event('pagehide'))")
    self.assertFalse(self.state()['registered'])
  def test_06_ttl_expires_in_actual_browser(self):
    self.setup(ttl=10);self.page.wait_for_timeout(35);self.assertFalse(self.state()['registered'])
  def test_07_cross_node_span(self):
    text='hello world';r=self.setup(text=text,html='<span data-copy>hello </span><strong data-copy>world</strong>',
       copies=[{'node':0,'fromUtf16':0,'toUtf16':6},{'node':1,'fromUtf16':6,'toUtf16':11}],start=3,end=10)
    self.assertEqual(r['status'],'HIGHLIGHT_LEASE_ACTIVE')
    self.assertEqual(self.page.evaluate('CSS.highlights.get("atlas-v32-evidence-lease").values().next().value.toString()'),'lo worl')
  def test_08_markdown_source_gap_refuses(self):
    text='Hi **moon**';r=self.setup(text=text,html='<span data-copy>Hi </span><strong data-copy>moon</strong>',
      copies=[{'node':0,'fromUtf16':0,'toUtf16':3},{'node':1,'fromUtf16':5,'toUtf16':9}],start=0,end=9)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE');self.assertFalse(r['registered'])
  def test_09_bad_sha_refuses(self):
    r=self.setup(badMap=True);self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_10_no_source_payload_in_serialized_handle(self):
    r=self.setup(text='SECRET_CODE',html='<span data-copy>SECRET_CODE</span>')
    self.assertEqual(r['serialized'],'{"status":"HIGHLIGHT_LEASE_ACTIVE"}')
  def test_11_read_denial_refuses(self):
    r=self.setup(deniedRead=True);self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_12_return_denial_refuses(self):
    r=self.setup(deniedReturn=True);self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_13_foreign_registry_member_not_overwritten(self):
    r=self.setup(foreign=True);self.assertEqual(r['status'],'HOLD_UNAVAILABLE');self.assertTrue(r['registered'])
  def test_14_zwj_cluster_partial_span_refuses(self):
    r=self.setup(text='👩‍🔬a',html='<span data-copy>👩‍🔬a</span>',start=0,end=2)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_15_zwj_cluster_full_span_accepts(self):
    r=self.setup(text='👩‍🔬a',html='<span data-copy>👩‍🔬a</span>',start=0,end=5)
    self.assertEqual(r['status'],'HIGHLIGHT_LEASE_ACTIVE')
  def test_16_visual_repaint_changes_and_revocation_restores(self):
    from PIL import Image,ImageChops
    from io import BytesIO
    # Only one line of visible black text, fixed font/canvas; screenshot
    # difference is real browser paint, not source-only CSS registry state.
    text='ABCDEF'
    self.page.evaluate("document.body.style.cssText='font:48px Arial;margin:40px'")
    self.page.evaluate("document.body.innerHTML='<div id=baseline>ABCDEF</div>'")
    before=Image.open(BytesIO(self.page.screenshot())).convert('RGB')
    r=self.setup(text=text,html='<span data-copy>ABCDEF</span>')
    self.assertEqual(r['status'],'HIGHLIGHT_LEASE_ACTIVE')
    after=Image.open(BytesIO(self.page.screenshot())).convert('RGB')
    # Remove CSS highlight, but same rendered document remains; ensure paint
    # changed due to actual CSS highlights, then returned to no-highlight paint.
    self.assertIsNotNone(ImageChops.difference(before,after).getbbox())
    self.page.evaluate('()=>__leaseState.controller.abort()')
    self.assertFalse(self.state()['registered'])
    after_revoke=Image.open(BytesIO(self.page.screenshot())).convert('RGB')
    # Base HTML differs by container even when styling is removed; test pixel
    # yellow count instead of full screenshot equivalence.
    yellow=lambda im:sum(1 for r,g,b in im.getdata() if r>200 and g>190 and b<70)
    self.assertGreater(yellow(after),0)
    self.assertEqual(yellow(after_revoke),0)

if __name__=='__main__':unittest.main(verbosity=2)
