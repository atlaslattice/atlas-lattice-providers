"""Offline REAL Chromium DOM Range tests for a source-only adapter; no network.
Requires local playwright and browser. Do not mistake for hosted v32 testing.
"""
from pathlib import Path
import json, subprocess, unittest, hashlib
from playwright.sync_api import sync_playwright

SRC=Path(__file__).resolve().parents[1]/'interop'/'swarmchat_v32'/'dom_source_map.mjs'
JS=SRC.read_text().replace('export async function ','async function ')
RUN_JS=r'''async ({ sourceText, sourceSha256, renderedHTML, copies, start, end, mutate, expectedSha, allowRead=true, allowReturn=true}) => {
  // Offline harness runs at about:blank (insecure); stub ONLY cryptographic digest.
  // Exact DOM/Range/Intl.Segmenter operations run in real Chromium.
  Object.defineProperty(window, "crypto",{configurable:true, value:{subtle:{digest: async (_name,bytes)=>{
    const decoded=new TextDecoder("utf-8",{fatal:true}).decode(bytes);
    const sha=decoded===sourceText?sourceSha256:"00".repeat(32);
    return new Uint8Array(sha.match(/../g).map(x=>parseInt(x,16))).buffer;
  }}}});
  document.body.innerHTML="<div id=\"fixture\">"+renderedHTML+"</div>";
  const root=document.getElementById('fixture');
  const nodes=[...root.querySelectorAll('[data-copy]')].map(x=>x.firstChild);
  const sha=sourceSha256;
  const sourceRef={roomId:'v32-work-test-01',seq:14,requestId:'deterministic-req-01'};
  const captured=await captureSourceDomMap({root,sourceRef,sourceText,sourceSha256:sha,copies:copies.map(c=>({...c,node:nodes[c.node]})),readAllowed:async()=>allowRead});
  if (mutate==='text' && nodes[0]) nodes[0].data=nodes[0].data+'!';
  if (mutate==='detach' && nodes[0]) nodes[0].parentNode.remove();
  const verified=await resolveSourceDomRange({capture:captured,startUtf16:start,endUtf16:end,expectedSourceSha256:expectedSha||sha,expectedSourceRef:sourceRef,readAllowed:async()=>allowRead,returnAllowed:async()=>allowReturn});
  return {capture:captured.status,status:verified.status,highlight:verified.range?.toString()||null,
     startContainerText:verified.range?.startContainer.data||null,
     endContainerText:verified.range?.endContainer.data||null,
     mutatedDOM:document.body.innerHTML.includes('<mark>')};
}'''

class DomRangeChromium(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.playwright=sync_playwright().start()
    cls.browser=cls.playwright.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    cls.page=cls.browser.new_page()
    # set_content avoids navigation: no network, no links, no external sources.
    cls.page.set_content('<body><div id="fixture"></div></body>')
    cls.page.add_script_tag(content=JS)
  @classmethod
  def tearDownClass(cls):
    cls.browser.close();cls.playwright.stop()
  def execute(self,source,html,copies,start,end,mutate=None,allowRead=True,allowReturn=True,expectedSha=None):
    return self.page.evaluate(RUN_JS,dict(sourceText=source,sourceSha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),renderedHTML=html,copies=copies,
       start=start,end=end,mutate=mutate,allowRead=allowRead,allowReturn=allowReturn,expectedSha=expectedSha))
  def test_cross_element(self):
    r=self.execute('Hello beautiful world','<span data-copy>Hello </span><strong data-copy>beautiful</strong><span data-copy> world</span>',
       [dict(node=0,fromUtf16=0,toUtf16=6),dict(node=1,fromUtf16=6,toUtf16=15),dict(node=2,fromUtf16=15,toUtf16=21)],3,20)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['highlight'],'lo beautiful worl')
    self.assertEqual(r['startContainerText'],'Hello ');self.assertEqual(r['endContainerText'],' world')
  def test_emoji_before_highlight(self):
    r=self.execute('🌌 headline','<span data-copy>🌌 headline</span>',[dict(node=0,fromUtf16=0,toUtf16=11)],3,11)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['highlight'],'headline')
  def test_partial_grapheme_rejected(self):
    r=self.execute('e\u0301 okay','<span data-copy>e\u0301 okay</span>',[dict(node=0,fromUtf16=0,toUtf16=7)],0,1)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_markdown_source_gap_rejected(self):
    src='Hello **world**!'
    r=self.execute(src,'<span data-copy>Hello </span><strong data-copy>world</strong><span data-copy>!</span>',
      [dict(node=0,fromUtf16=0,toUtf16=6),dict(node=1,fromUtf16=8,toUtf16=13),dict(node=2,fromUtf16=15,toUtf16=16)],0,13)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_markdown_bold_word_inside_copy(self):
    src='Hello **world**!'
    r=self.execute(src,'<span data-copy>Hello </span><strong data-copy>world</strong><span data-copy>!</span>',
      [dict(node=0,fromUtf16=0,toUtf16=6),dict(node=1,fromUtf16=8,toUtf16=13),dict(node=2,fromUtf16=15,toUtf16=16)],8,13)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['highlight'],'world')
  def test_mutation_between_capture_and_range(self):
    r=self.execute('hello','<span data-copy>hello</span>',[dict(node=0,fromUtf16=0,toUtf16=5)],0,5,mutate='text')
    self.assertEqual(r['capture'],'CAPTURED');self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_detached_node(self):
    r=self.execute('hello','<span data-copy>hello</span>',[dict(node=0,fromUtf16=0,toUtf16=5)],0,5,mutate='detach')
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_return_denied(self):
    r=self.execute('hello','<span data-copy>hello</span>',[dict(node=0,fromUtf16=0,toUtf16=5)],0,5,allowReturn=False)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_read_denied(self):
    r=self.execute('hello','<span data-copy>hello</span>',[dict(node=0,fromUtf16=0,toUtf16=5)],0,5,allowRead=False)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_wrong_render_mapping(self):
    r=self.execute('Hello','<span data-copy>Hell0</span>',[dict(node=0,fromUtf16=0,toUtf16=5)],0,5)
    self.assertEqual(r['capture'],'HOLD_UNAVAILABLE')
  def test_cross_node_zero_dom_writes(self):
    r=self.execute('abc','<span data-copy>a</span><span data-copy>b</span><span data-copy>c</span>',
       [dict(node=0,fromUtf16=0,toUtf16=1),dict(node=1,fromUtf16=1,toUtf16=2),dict(node=2,fromUtf16=2,toUtf16=3)],0,3)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertFalse(r['mutatedDOM'])

  def test_stale_sha_refused(self):
    r=self.execute('abc','<span data-copy>abc</span>',[dict(node=0,fromUtf16=0,toUtf16=3)],0,3,expectedSha='a'*64)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_gap_between_copy_segments_refused(self):
    src='abc**def'
    r=self.execute(src,'<span data-copy>abc</span><span data-copy>def</span>',
       [dict(node=0,fromUtf16=0,toUtf16=3),dict(node=1,fromUtf16=5,toUtf16=8)],0,8)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_only_left_side_of_source_gap_accepted(self):
    src='abc**def'
    r=self.execute(src,'<span data-copy>abc</span><span data-copy>def</span>',
       [dict(node=0,fromUtf16=0,toUtf16=3),dict(node=1,fromUtf16=5,toUtf16=8)],0,3)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['highlight'],'abc')
  def test_only_right_side_of_source_gap_accepted(self):
    src='abc**def'
    r=self.execute(src,'<span data-copy>abc</span><span data-copy>def</span>',
       [dict(node=0,fromUtf16=0,toUtf16=3),dict(node=1,fromUtf16=5,toUtf16=8)],5,8)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['highlight'],'def')
  def test_zwj_full_grapheme_across_node_boundary(self):
    src='👩‍🔬 normal'
    r=self.execute(src,'<span data-copy>👩‍🔬</span><span data-copy> normal</span>',
       [dict(node=0,fromUtf16=0,toUtf16=5),dict(node=1,fromUtf16=5,toUtf16=12)],0,12)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['highlight'],src)
  def test_zwj_partial_cluster_refused(self):
    src='👩‍🔬 normal'
    r=self.execute(src,'<span data-copy>👩‍🔬</span><span data-copy> normal</span>',
       [dict(node=0,fromUtf16=0,toUtf16=5),dict(node=1,fromUtf16=5,toUtf16=12)],0,2)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_adjacent_equal_text_distinct_nodes(self):
    src='foofoo'
    r=self.execute(src,'<span data-copy>foo</span><span data-copy>foo</span>',
       [dict(node=0,fromUtf16=0,toUtf16=3),dict(node=1,fromUtf16=3,toUtf16=6)],3,6)
    self.assertEqual(r['status'],'DOM_RANGE_VERIFIED');self.assertEqual(r['startContainerText'],'foo')
  def test_unmapped_suffix_refused(self):
    src='abcxyz'
    r=self.execute(src,'<span data-copy>abc</span>',[dict(node=0,fromUtf16=0,toUtf16=3)],3,6)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')
  def test_reorder_dom_nodes_refused(self):
    src='abcxyz'
    r=self.execute(src,'<span data-copy>xyz</span><span data-copy>abc</span>',
       [dict(node=1,fromUtf16=0,toUtf16=3),dict(node=0,fromUtf16=3,toUtf16=6)],0,6)
    self.assertEqual(r['status'],'HOLD_UNAVAILABLE')

if __name__=='__main__':unittest.main(verbosity=2)
