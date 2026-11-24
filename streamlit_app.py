"""Render the six-character website with its assets bundled into Streamlit."""
import base64
import gzip
import json
import mimetypes
from pathlib import Path
import re

from io import BytesIO

from PIL import Image
import streamlit as st
from streamlit.components.v1 import html as render_html

ROOT = Path(__file__).resolve().parent
# Region navigation is provided by the fixed Streamlit sidebar.
PAGES = ("index.html", "featured.html", "regions.html", "nian.html",
         "men.html", "cha.html", "chuan.html", "deng.html", "yuan.html")


def site_version():
    names = {*PAGES, "cases.json", "style.css", "app.js", "demo.js", "unihan-variants.gz.b64", "featured-strokes.json",
             "hanzi-writer.min.js", "zili-strokes.js", "zili-lookup-results.js"}
    # Include the regional gallery page in the cache fingerprint.
    # Story pages include their inline lookup panels in the cached site bundle.
    return tuple(
        (path.name, info.st_mtime_ns, info.st_size)
        for path in sorted(ROOT.iterdir())
        if path.is_file() and (path.name in names or path.suffix.lower() in (".webp", ".png", ".jpg"))
        for info in (path.stat(),)
    )


def enrich_lookup(page):
    """Add local Unihan candidates to the existing dictionary query."""
    page = page.replace(
        "const [form, storyUrl] = entries[word] ?? [word];",
        """const [preferred, storyUrl] = entries[word] ?? [word];
  const variants = parent.ziliVariants?.[word] ?? [];
  const candidates = [...new Set([word, preferred, ...variants])].slice(0, 4);
  let form = word;
  document.dispatchEvent(new CustomEvent('zili:lookup', {detail:word}));""",
    )
    page = page.replace("const word = input.value.trim();", """const word = input.value.trim();
  document.dispatchEvent(new CustomEvent('zili:lookup', {detail:null}));""")
    old_request = "const response = await fetch('https://www.moedict.tw/uni/' + encodeURIComponent(form), {signal:controller.signal});"
    page = page.replace(old_request, """let response;
    for (const candidate of candidates) {
      form = candidate;
      response = await fetch('https://www.moedict.tw/uni/' + encodeURIComponent(form), {signal:controller.signal});
      if (response.status !== 404) break;
    }""")
    return page.replace(
        "if (!response.ok) throw new Error('Dictionary request failed');",
        """if (!response.ok) throw new Error('Dictionary request failed');
    source.href = 'https://www.moedict.tw/' + encodeURIComponent(form);""",
    ).replace(
        """entry.stroke_count].filter(Boolean)""",
        """entry.stroke_count, variants.length && '关联字形（Unihan） ' + variants.join('、')].filter(Boolean)""",
    )


@st.cache_data(show_spinner=False)
def bundle_site(version):
    def image_url(name):
        path = ROOT / name
        if path.parent != ROOT or not path.is_file():
            return name
        mime = mimetypes.guess_type(name)[0]
        if not mime or not mime.startswith("image/"):
            return name
        data = path.read_bytes()
        if name == "globe-cover-reference.png":
            with Image.open(path) as cover:
                buffer = BytesIO()
                cover.convert("RGB").save(buffer, format="JPEG", quality=92, optimize=True)
                data = buffer.getvalue()
                mime = "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

    def json_script(value):
        return json.dumps(value, ensure_ascii=False).replace("<", r"\u003c")

    catalogue = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    variants = json.loads(gzip.decompress(base64.b64decode((ROOT / "unihan-variants.gz.b64").read_bytes())))
    strokes = json.loads((ROOT / "featured-strokes.json").read_text(encoding="utf-8"))
    stroke_library = (ROOT / "hanzi-writer.min.js").read_text(encoding="utf-8")
    stroke_ui = (ROOT / "zili-strokes.js").read_text(encoding="utf-8")
    keepsake_style = """<style>
#keepsake-status:not(:empty), #keepsake-collection-link:not([hidden]) { margin-top: 8px; }
#keepsake-collection-link:not([hidden]) { display: block; font-weight: 700; }
#keepsake .keepsake { min-height: clamp(290px, 26vw, 360px); }
@media (max-width: 540px) {
  #keepsake .keepsake { min-height: 240px; }
}
</style>"""
    observation_style = """<style>
#form .observation .glyph {
  width: clamp(118px, 20vw, 224px);
  font-size: clamp(4.6rem, 11.2vw, 9.4rem);
}
#form .observation p {
  color: #2d2119;
  font-size: clamp(1rem, 1.6vw, 1.25rem);
  font-weight: 500;
  line-height: 1.65;
  margin: 0 0 .65em;
}
#form .observation #open-glyph {
  color: #702117;
  font-size: clamp(1rem, 1.45vw, 1.125rem);
  font-weight: 700;
  min-height: 44px;
}
@media (min-width: 720px) {
  #form .observation .glyph { position: relative; left: -22px; }
}
@media (max-width: 540px) {
  #form .observation { grid-template-columns: 118px minmax(0, 1fr); }
}
</style>"""
    stroke_style = '<style>.stroke-preview{border-top:1px solid #decdb4;margin-top:14px;padding:12px 0}.stroke-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.stroke-controls select{font:inherit;padding:4px}.stroke-board{width:184px;height:184px;margin:10px auto;background:#fffaf2;border:1px solid #d8c1a5;border-radius:8px}.stroke-status{margin:5px 0!important}.stroke-preview small{color:#695849}</style>'
    lookup_ui = (ROOT / "zili-lookup-results.js").read_text(encoding="utf-8")
    lookup_style = """<style>
.lookup-result:has(.lookup-three){width:100%;max-width:none;box-sizing:border-box;font-size:1.0625rem;line-height:1.65}
.lookup-result:has(.lookup-three) #word{font-size:clamp(1.75rem,3vw,2.25rem);margin:0 0 14px}
.story-lookup .lookup-credit{font-size:1rem;line-height:1.55}
.lookup-three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(12px,1.5vw,22px)}
.lookup-tile{min-width:0;padding:clamp(14px,1.5vw,24px);background:#fffaf0;border:1px solid #d7c2a4;border-radius:10px;overflow-wrap:anywhere}
.lookup-tile h3{margin:0 0 12px;color:#8c291e;font-size:clamp(1.2rem,1.65vw,1.5rem);line-height:1.35}
.lookup-tile p{font-size:inherit;line-height:inherit}
.lookup-tile button{font:inherit}
.lookup-definition{font-size:1.1875rem;line-height:1.7}
.lookup-definition a:any-link{color:#702117;font-weight:700;line-height:1.5;text-underline-offset:.19em}
.lookup-definition a:hover,.lookup-definition a:focus-visible{color:#49140d}
.lookup-link-arrow{display:inline-block;margin-inline-start:.3em;text-decoration:none}
.lookup-forms{display:flex;gap:8px;flex-wrap:wrap}
.lookup-forms button,.lookup-play{border:1px solid #d7c2a4;border-radius:8px;background:#fff8ed;color:#8c291e;padding:7px 13px}
.lookup-forms button{font:28px/1.2 KaiTi,serif}
.lookup-forms button small{display:block;font:600 .8rem/1.4 system-ui,sans-serif}
.lookup-forms button[aria-pressed=true],.lookup-play:not(:disabled){background:#8c291e;color:#fff}
.lookup-glyph{font:clamp(76px,8vw,110px)/1.25 KaiTi,serif;text-align:center;color:#8c291e}
.lookup-stroke-board{margin:12px auto;width:min(100%,260px);aspect-ratio:1;border:1px solid #d7c2a4;border-radius:8px}
.lookup-stroke-board svg{display:block;width:100%;height:auto}
.lookup-stroke-controls{display:grid;justify-items:start;gap:10px;margin-top:14px}
.lookup-stroke-controls .lookup-stroke-status{margin:0}
.lookup-variant-note,.lookup-stroke-status{color:#695849}
@media(max-width:900px){.lookup-three{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.lookup-three{grid-template-columns:minmax(0,1fr)}}
</style>"""
    writer_script = "<script>" + stroke_library + "</script>"
    pages = {}
    for name in PAGES:
        page = (ROOT / name).read_text(encoding="utf-8")
        page = re.sub(r'<link rel="stylesheet" href="style.css"\s*/?>',
                      lambda _: "<style>" + (ROOT / "style.css").read_text(encoding="utf-8") + "</style>", page)
        page = re.sub(r'<script( defer)? src="(app|demo)\.js"></script>',
                      lambda m: "<script>" + ("document.addEventListener('DOMContentLoaded', () => {\n" if m[1] else "")
                      + (ROOT / (m[2]+".js")).read_text(encoding="utf-8")
                      + ("\n});" if m[1] else "") + "</script>", page)
        page = page.replace("fetch('cases.json')", "Promise.resolve(new Response(JSON.stringify(" + json_script(catalogue) + ")))") if "fetch('cases.json')" in page else page
        page = page.replace("return config.images?.[record.id] || record.image;", "return parent.ziliImage(config.images?.[record.id] || record.image);")
        page = page.replace("return config.images?.[record.id] || record.id + '.webp';", "return parent.ziliImage(config.images?.[record.id] || record.id + '.webp');")
        page = re.sub(r'(picture\.src\s*=\s*)image\s*;', r'\1parent.ziliImage(image);', page)
        has_lookup = 'www.moedict.tw/uni/' in page
        if has_lookup:
            page = enrich_lookup(page)
            page = re.sub(r'(<section id="lookup-result"[\s\S]*?</section>)',
                          lambda m: m[1] + lookup_style + writer_script +
                          "<script>" + lookup_ui + "</script>", page, count=1)
        if 'id="glyph-dialog"' in page:
            page = re.sub(r'(<details(?: id="sources")?)(>\s*<summary>资料核验与素材说明</summary>)',
                          r'\1 open\2', page, count=1)
            page = page.replace("</head>", observation_style + keepsake_style + "</head>", 1)
            page = page.replace('保存寻踪记录</button>',
                                '保存寻踪记录</button><p id="keepsake-status" role="status"></p>'
                                '<a id="keepsake-collection-link" href="keepsakes.html" hidden>'
                                '查看已保存的寻踪卡 →</a>', 1)
            page = page.replace("</body>", stroke_style + ("" if has_lookup else writer_script) +
                                "<script>" + stroke_ui + "</script></body>")
        pages[name] = page
    references = "\n".join([*pages.values(), json_script(catalogue)])
    assets = {path.name: image_url(path.name) for path in ROOT.iterdir()
              if path.suffix.lower() in (".webp", ".png", ".jpg")
              and (path.name in references or path.name.startswith("nian-"))}
    payload = json_script({"pages": pages, "images": assets, "variants": variants, "strokes": strokes})
    return base64.b64encode(gzip.compress(payload.encode("utf-8"), compresslevel=6)).decode("ascii")


st.set_page_config(page_title="字里寻踪", page_icon="年", layout="wide")
st.html("""<style>
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #e9decd;
    height: 100dvh;
    overflow: hidden;
}
[data-testid="stMainBlockContainer"] { max-width: none; padding: 0; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 0; }
[data-testid="stHeader"] { display: none; }
iframe[data-testid="stIFrame"] {
    display: block;
    width: 100%;
    height: 100dvh !important;
    border: 0;
}
</style>""")
site_payload = bundle_site(site_version())
render_html("""<!doctype html><meta charset="utf-8"><style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#e9decd}
*{box-sizing:border-box}
#layout{display:grid;grid-template-columns:clamp(244px,24vw,320px) minmax(0,1fr);height:100dvh}
#layout.home{grid-template-columns:minmax(0,1fr)}
#directory{overflow:auto;background:#f9f0de;border-right:1px solid #d7c2a4;padding:28px 20px;color:#473326;font:16px/1.65 system-ui,sans-serif}
#directory[hidden]{display:none}
.brand{font:700 32px KaiTi,serif;color:#84281e}.subtitle{font-size:14px;color:#705946;margin:4px 0 23px}
#directory nav{display:grid;gap:8px}
#directory button{width:100%;border:0;border-radius:9px;background:transparent;text-align:left;padding:11px 14px;color:inherit;font:inherit;cursor:pointer}
#directory button:hover:not([aria-current]){background:#f0e0c5}
#directory button[aria-current]{background:#8c291e;color:white}
#directory button:focus-visible{outline:2px solid #a35a23;outline-offset:2px}
#directory small{display:block;font-size:13px;opacity:.86}
iframe{display:block;width:100%;height:100%;min-height:0;border:0}
@media(max-width:660px){#layout{grid-template-columns:1fr;grid-template-rows:auto minmax(0,1fr)}#layout.home{grid-template-rows:minmax(0,1fr)}#directory{border-right:0;border-bottom:1px solid #d7c2a4;padding:10px 13px}.brand{font-size:24px}.subtitle,#directory small{display:none}#directory nav{grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;margin-top:7px}#directory button{padding:7px 4px;min-height:40px;text-align:center;font-size:14px}}
</style>
<div id="layout" class="home">
<aside id="directory" hidden><div class="brand">字里寻踪</div><p class="subtitle">两岸四海的生活印记</p><nav aria-label="功能目录">
<button type="button" data-tab="home">首页<small>回到封面入口</small></button>
<button type="button" data-tab="featured">精选寻踪<small>沿一个字读完整故事</small></button>
<button type="button" data-tab="regions">四海故事<small>按地区浏览生活记录</small></button>
<button type="button" data-tab="lookup">自由查字<small>输入或选择感兴趣的字</small></button>
<button type="button" data-tab="keepsake">我的寻踪卡<small>带走想记住的生活细节</small></button>
<button type="button" data-tab="sources">资料与来源<small>查看原文与素材说明</small></button>
</nav></aside><iframe title="字里寻踪" id="site"></iframe></div>
<script>
(async () => {
const packed = '""" + site_payload + """';
const bytes = Uint8Array.from(atob(packed), character => character.charCodeAt(0));
const decompressed = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
const {pages, images, variants, strokes} = await new Response(decompressed).json();
window.ziliVariantPairs = variants.pairs;
window.ziliSameForms = new Set(variants.same);
window.ziliVariants = Object.fromEntries(Object.entries(variants.pairs).map(([char, [simple, traditional]]) =>
  [char, [...new Set([...simple, ...traditional])].filter(form => form !== char)]));
window.ziliStrokeData = strokes;
window.ziliImage = name => images[name] || name;
const frame = document.getElementById('site');
const directory = document.getElementById('directory');
const layout = document.getElementById('layout');
let current = 'index.html', lastStory = '';
let lookupScroll = 0;
const keepsakePage = 'keepsakes.html';
const keepsakeKey = 'zili-keepsakes-v1';
let savedKeepsakes = [];
try {
  const stored = JSON.parse(localStorage.getItem(keepsakeKey) || '[]');
  if (Array.isArray(stored)) savedKeepsakes = stored.filter(item =>
    item && typeof item.id === 'string' && Object.hasOwn(pages, item.page));
} catch {}
window.ziliSaveKeepsake = (record, image) => {
  const item = {
    id: record.id, page: current, character: frame.contentDocument.body.dataset.character || '年',
    place: record.place, title: record.title, detail: record.recorded_action || record.body, image
  };
  savedKeepsakes = [item, ...savedKeepsakes.filter(entry => entry.id !== item.id)];
  try {
    localStorage.setItem(keepsakeKey, JSON.stringify(savedKeepsakes));
    return true;
  } catch {
    return false;
  }
};
pages[keepsakePage] = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>已保存的寻踪卡</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3ebdd;color:#34271e;font:16px/1.65 system-ui,sans-serif}
main{margin:auto;padding:26px 0;max-width:1208px}h1{margin:0 0 8px;font:700 clamp(1.8rem,4vw,2.8rem) KaiTi,serif}
a{color:#79271a;font-weight:700}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:16px}
article{border:1px solid #d6b995;background:#fff9ee;border-radius:12px;overflow:hidden}
article div{padding:15px}article h2{margin:4px 0 8px;font-size:1.2rem}
article img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}small{color:#79271a;font-weight:700}
</style></head><body><main><h1>已保存的寻踪卡</h1><p id="saved-count"></p><div class="cards" id="saved-cards"></div></main></body></html>`;
function renderKeepsakes(doc) {
  const add = (parent, tag, value = '') => {
    const node = doc.createElement(tag);
    node.textContent = value;
    parent.append(node);
    return node;
  };
  const count = doc.getElementById('saved-count');
  count.textContent = savedKeepsakes.length ? savedKeepsakes.length + ' 条已保存' : '还没有收藏。';
  if (!savedKeepsakes.length) add(count, 'a', ' 去看看故事 →').href = lastStory || 'featured.html';
  const cards = doc.getElementById('saved-cards');
  for (const item of savedKeepsakes) {
    const card = add(cards, 'article');
    if (images[item.image]) {
      const image = add(card, 'img');
      image.src = images[item.image];
      image.alt = '';
    }
    const body = add(card, 'div');
    add(body, 'small', item.character + ' · ' + item.place);
    add(body, 'h2', item.title);
    add(body, 'p', item.detail);
    add(body, 'a', '回到故事 →').href = item.page + '#' + item.id;
  }
}
const isStory = page => /^(nian|men|cha|chuan|deng|yuan)\\.html$/.test(page);
function selectTab(key) {
  for (const button of directory.querySelectorAll('[data-tab]')) {
    if (button.dataset.tab === key) button.setAttribute('aria-current','page');
    else button.removeAttribute('aria-current');
  }
}
function goToSection(doc, hash) {
  const node = doc.getElementById(hash === 'sources' && !doc.getElementById('sources') ? 'journey-sources' : hash);
  if (!node) return;
  if (node.tagName === 'DETAILS') node.open = true;
  const view = frame.contentWindow;
  const offset = Number.parseFloat(view.getComputedStyle(node).scrollMarginTop) || 0;
  view.scrollTo(0, view.scrollY + node.getBoundingClientRect().top - offset);
}
function activateLocal(doc, key) {
  if (key === 'lookup') {
    const trigger = doc.querySelector('[data-open-story-lookup]');
    if (trigger) {
      if (doc.body.classList.contains('lookup-only')) return;
      lookupScroll = frame.contentWindow.scrollY;
      const input = doc.getElementById('hanzi');
      input.value = '';
      input.dispatchEvent(new frame.contentWindow.Event('input', {bubbles:true}));
      trigger.click();
      doc.body.classList.add('lookup-only');
      frame.contentWindow.scrollTo(0, 0);
      return;
    }
    goToSection(doc, 'lookup');
    doc.getElementById('hanzi')?.focus({preventScroll:true});
    return;
  }
  goToSection(doc, key);
}
function navigate(page, hash = '', tab = '') {
  if (!Object.hasOwn(pages, page)) return;
  current = page;
  if (isStory(page)) lastStory = page;
  const cover = page === 'index.html' && tab !== 'lookup';
  const selected = tab || (page === keepsakePage ? 'keepsake' : page === 'regions.html' ? 'regions' : cover ? 'home' : 'featured');
  directory.hidden = cover;
  layout.classList.toggle('home', cover);
  selectTab(selected);
  frame.onload = () => {
    const doc = frame.contentDocument;
    if (page === keepsakePage) renderKeepsakes(doc);
    if (savedKeepsakes.length) {
      const collectionLink = doc.getElementById('keepsake-collection-link');
      if (collectionLink) collectionLink.hidden = false;
    }
    doc.getElementById('cover-character')?.addEventListener('change', event => {
      const destination = event.target.value;
      if (isStory(destination)) navigate(destination);
    });
    if (hash) activateLocal(doc, hash);
    const close = doc.getElementById('close-story-lookup');
    const restoreStory = () => {
      if (!doc.body.classList.contains('lookup-only')) return;
      doc.body.classList.remove('lookup-only');
      frame.contentWindow.scrollTo(0, lookupScroll);
      selectTab('featured');
    };
    close?.addEventListener('click', restoreStory);
    doc.getElementById('story-lookup')?.addEventListener('keydown', event => {
      if (event.key === 'Escape') restoreStory();
    });
    doc.addEventListener('click', event => {
      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.hasAttribute('download')) return;
      const href = anchor.getAttribute('href');
      if (!href || /^(?:[a-z]+:|\\/\\/)/i.test(href)) return;
      if (href.startsWith('#')) {
        event.preventDefault();
        const id = href.slice(1);
        if (id === 'keepsake' || id === 'sources' || id === 'journey-sources') selectTab(id === 'journey-sources' ? 'sources' : id);
        goToSection(doc, id);
        return;
      }
      const [path, fragment] = href.split('#');
      const next = path === './' ? 'index.html' : path.replace(/^\\.\\//, '');
      if (!Object.hasOwn(pages, next)) return;
      event.preventDefault();
      if (next === 'index.html' && fragment === 'lookup') {
        openFunction('lookup');
        return;
      }
      navigate(next, fragment);
    });
  };
  const innerStyles = cover ? '' : '<style>.demo-shell,.journey-layout{display:block!important;width:100%;max-width:none;margin:0}.demo-shell>.page,.journey-layout>.page{width:100%;max-width:none;margin:0;min-height:100dvh;box-shadow:none}.demo-shell>.directory,.journey-layout>.journey-sidebar{display:none!important}body>main,.sheet>main{width:calc(100% - 2 * clamp(14px,3vw,44px));max-width:none}.lookup-only .page>header,.lookup-only main>:not(#story-lookup){display:none!important}.lookup-only .page{min-height:100dvh}</style>';
  const lookupLanding = page === 'index.html' && tab === 'lookup'
    ? '<style>.globe-cover{width:min(92%,620px);aspect-ratio:auto;padding:28px 12px;background:none;overflow:visible}.globe-cover .globe-art,.globe-cover .globe-start{display:none}.globe-cover .globe-search{position:static;width:100%;height:46px}</style>'
    : '';
  const lookupSizing = cover ? '' : '<style>.story-lookup .story-lookup-form,.globe-cover .globe-search{min-height:52px;grid-template-columns:minmax(0,1fr) 84px 64px}.story-lookup .story-lookup-form{max-width:700px}.story-lookup .story-lookup-form>*,.globe-cover .globe-search>*{font-size:16px}.story-lookup-form select,.globe-search select{padding-inline:10px}@media(max-width:420px){.story-lookup .story-lookup-form,.globe-cover .globe-search{grid-template-columns:minmax(0,1fr) 74px 56px}}</style>';
  const creditStyle = '<style>.lookup-credit{margin:7px 0 0;color:#695849;font:clamp(11px,2.4vw,14px)/1.3 system-ui,sans-serif}.cover-credit{max-width:650px;margin:0 auto;padding:0 16px 10px;text-align:center}.globe-cover .lookup-credit{position:absolute;top:146cqw;left:7.7%;width:84.8%;margin:0;text-align:center;font-size:clamp(10px,1.8cqw,12px)}.globe-cover:has(.globe-search) .lookup-credit a{color:inherit}.globe-cover.lookup-credit-flow .lookup-credit{position:static;width:auto;margin-top:7px}</style>';
  const credit = '<p class="lookup-credit">萌典提供读音、部首、笔画和释义；Unicode Unihan 识别简繁关联；Hanzi Writer 在精选字的字形弹窗里演示笔顺。</p>';
  const pageHtml = pages[page].replace(
    /(<form class="(?:globe-search|story-lookup-form)"[^>]*>[\\s\\S]*?<\\/form>)/,
    '$1' + (cover ? '' : credit)
  );
  const attributedPage = cover
    ? (pageHtml.split('</main>', 1)[0] + '</main></body></html>').replace(
        /<form class="globe-search"[^>]*>[\\s\\S]*?<\\/form>/,
        '<div class="globe-search cover-picker"><select id="cover-character" aria-describedby="cover-case-note" aria-label="选一个字，进入故事"><option value="">选一个字，进入故事</option><option value="nian.html">年</option><option value="men.html">门</option><option value="cha.html">茶</option><option value="chuan.html">船</option><option value="deng.html">灯</option><option value="yuan.html">圆</option></select></div><p id="cover-case-note" class="cover-case-note">六个代表字，展示各地生活与习俗</p>'
      )
    : pageHtml;
  const lookupHtml = lookupLanding ? attributedPage.replace('class="globe-cover"', 'class="globe-cover lookup-credit-flow"') : attributedPage;
  const inlineImages = lookupHtml
    .replace(/(src=")([\\w.-]+\\.(?:webp|png|jpg))(")/g, (match, start, name, end) =>
      images[name] ? start + images[name] + end : match)
    .replace(/url\\((["']?)([\\w.-]+\\.(?:webp|png|jpg))\\1\\)/g, (match, quote, name) =>
      images[name] ? 'url("' + images[name] + '")' : match);
  const pickerStyle = cover ? '<style>.globe-cover:has(.cover-picker){aspect-ratio:1600/2500}.globe-cover .cover-case-note{position:absolute;top:calc(145.54cqw + 5px);left:50%;transform:translateX(-50%);max-width:88%;width:max-content;margin:0;padding:3px 8px;border-radius:6px;background:#fff7e9;color:#79291e;text-align:center;font:600 clamp(11px,2.6cqw,16px)/1.35 system-ui,sans-serif}.globe-cover .cover-picker{display:block}.cover-picker select{width:100%;height:100%;padding:0 14px;border-radius:999px;font:clamp(15px,3.5cqw,20px) system-ui,sans-serif}</style>' : '';
  const coverPaperStyle = cover ? `<style>
    body{background:linear-gradient(180deg,#f6f3ed,#f5f2eb 64%,#f7f4ee)}
    .globe-cover{background:transparent}
    @media (min-width:601px){
      .globe-cover .globe-art{
        -webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);
        mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);
      }
    }
  </style>` : '';
  frame.srcdoc = inlineImages.replace('</head>', innerStyles + lookupLanding + lookupSizing + creditStyle + pickerStyle + coverPaperStyle + '</head>');
}
function openFunction(key) {
  if (key === 'home') return navigate('index.html');
  if (key === 'featured') return navigate('featured.html');
  if (key === 'regions') return navigate('regions.html');
  if (isStory(current)) {
    const doc = frame.contentDocument;
    if (key !== 'lookup' && doc.body.classList.contains('lookup-only')) {
      doc.getElementById('close-story-lookup').click();
    }
    selectTab(key);
    activateLocal(frame.contentDocument, key);
    return;
  }
  if (lastStory) return navigate(lastStory, key, key);
  if (key === 'lookup') return navigate('index.html', 'lookup', key);
  navigate('featured.html', '', key);
}
for (const button of directory.querySelectorAll('[data-tab]')) {
  button.addEventListener('click', () => openFunction(button.dataset.tab));
}
navigate('index.html');
})().catch(error => {
  console.error('Unable to load site', error);
  const notice = document.createElement('p');
  notice.setAttribute('role', 'alert');
  notice.style.cssText = 'margin:24px;font:16px system-ui';
  notice.textContent = '暂时无法载入《字里寻踪》，请刷新页面重试。';
  document.getElementById('layout').replaceWith(notice);
});
</script>""", height=860, scrolling=False)
