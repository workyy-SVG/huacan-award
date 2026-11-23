"""Render the six-character website with its assets bundled into Streamlit."""
import base64
import gzip
import json
import mimetypes
from pathlib import Path
import re

import streamlit as st

ROOT = Path(__file__).resolve().parent
# Region navigation is provided by the fixed Streamlit sidebar.
PAGES = ("index.html", "featured.html", "regions.html", "nian.html",
         "men.html", "cha.html", "chuan.html", "deng.html", "yuan.html")


def site_version():
    names = {*PAGES, "cases.json", "style.css", "app.js", "demo.js", "unihan-variants.gz.b64", "featured-strokes.json",
             "hanzi-writer.min.js", "zili-strokes.js"}
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
  let form = word;""",
    )
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
        return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")

    def json_script(value):
        return json.dumps(value, ensure_ascii=False).replace("<", r"\u003c")

    catalogue = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    assets = {p.name: image_url(p.name) for p in ROOT.iterdir()
              if p.suffix.lower() in (".webp", ".png", ".jpg")}
    variants = json.loads(gzip.decompress(base64.b64decode((ROOT / "unihan-variants.gz.b64").read_bytes())))
    strokes = json.loads((ROOT / "featured-strokes.json").read_text(encoding="utf-8"))
    stroke_library = (ROOT / "hanzi-writer.min.js").read_text(encoding="utf-8")
    stroke_ui = (ROOT / "zili-strokes.js").read_text(encoding="utf-8")
    stroke_style = '<style>.stroke-preview{border-top:1px solid #decdb4;margin-top:14px;padding:12px 0}.stroke-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.stroke-controls select{font:inherit;padding:4px}.stroke-board{width:184px;height:184px;margin:10px auto;background:#fffaf2;border:1px solid #d8c1a5;border-radius:8px}.stroke-status{margin:5px 0!important}.stroke-preview small{color:#695849}</style>'
    pages = {}
    for name in PAGES:
        page = (ROOT / name).read_text(encoding="utf-8")
        page = re.sub(r'<link rel="stylesheet" href="style.css"\s*/?>',
                      lambda _: "<style>" + (ROOT / "style.css").read_text(encoding="utf-8") + "</style>", page)
        page = re.sub(r'<script( defer)? src="(app|demo)\.js"></script>',
                      lambda m: "<script>" + ("document.addEventListener('DOMContentLoaded', () => {\n" if m[1] else "")
                      + (ROOT / (m[2]+".js")).read_text(encoding="utf-8")
                      + ("\n});" if m[1] else "") + "</script>", page)
        page = re.sub(r'(src=")([\w.-]+\.(?:webp|png|jpg))(")',
                      lambda m: m[1] + assets.get(m[2], m[2]) + m[3], page)
        page = re.sub(r'url\((["\']?)([\w.-]+\.(?:webp|png|jpg))\1\)',
                      lambda m: 'url("' + assets.get(m[2], m[2]) + '")', page)
        page = page.replace("fetch('cases.json')", "Promise.resolve(new Response(JSON.stringify(" + json_script(catalogue) + ")))") if "fetch('cases.json')" in page else page
        page = page.replace("return config.images?.[record.id] || record.image;", "return parent.ziliImage(config.images?.[record.id] || record.image);")
        page = page.replace("return config.images?.[record.id] || record.id + '.webp';", "return parent.ziliImage(config.images?.[record.id] || record.id + '.webp');")
        page = re.sub(r'(picture\.src\s*=\s*)image\s*;', r'\1parent.ziliImage(image);', page)
        if 'www.moedict.tw/uni/' in page:
            page = enrich_lookup(page)
        if 'id="glyph-dialog"' in page:
            page = page.replace("</body>", stroke_style + "<script>" + stroke_library +
                                "</script><script>" + stroke_ui + "</script></body>")
        pages[name] = page
    return json_script(pages), json_script(assets), json_script(variants), json_script(strokes)


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
pages_json, assets_json, variants_json, strokes_json = bundle_site(site_version())
st.iframe("""<!doctype html><meta charset="utf-8"><style>
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
const pages = """ + pages_json + """;
const images = """ + assets_json + """;
window.ziliVariants = """ + variants_json + """;
window.ziliStrokeData = """ + strokes_json + """;
window.ziliImage = name => images[name] || name;
const frame = document.getElementById('site');
const directory = document.getElementById('directory');
const layout = document.getElementById('layout');
let current = 'index.html', lastStory = '';
let lookupScroll = 0;
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
  const selected = tab || (page === 'regions.html' ? 'regions' : cover ? 'home' : 'featured');
  directory.hidden = cover;
  layout.classList.toggle('home', cover);
  selectTab(selected);
  frame.onload = () => {
    const doc = frame.contentDocument;
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
  const creditStyle = '<style>.lookup-credit{margin:7px 0 0;color:#695849;font:clamp(11px,2.4vw,14px)/1.3 system-ui,sans-serif}.globe-cover .lookup-credit{position:absolute;top:146cqw;left:7.7%;width:84.8%;margin:0;text-align:center;font-size:clamp(10px,2.25cqw,14px)}.globe-cover:has(.globe-search) .lookup-credit a{color:inherit}.globe-cover.lookup-credit-flow .lookup-credit{position:static;width:auto;margin-top:7px}</style>';
  const pageHtml = pages[page].replace(
    /(<form class="(?:globe-search|story-lookup-form)"[^>]*>[\\s\\S]*?<\\/form>)/,
    '$1<p class="lookup-credit">字典数据来源：萌典（Moedict）公开接口 · 简繁关联：Unicode Unihan</p>'
  );
  const lookupHtml = lookupLanding ? pageHtml.replace('class="globe-cover"', 'class="globe-cover lookup-credit-flow"') : pageHtml;
  frame.srcdoc = lookupHtml.replace('</head>', innerStyles + lookupLanding + lookupSizing + creditStyle + '</head>');
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
</script>""", height=860)
