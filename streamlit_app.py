"""Render the six-character website with its assets bundled into Streamlit."""
import base64
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
    names = {*PAGES, "cases.json", "style.css", "app.js", "demo.js"}
    # Include the regional gallery page in the cache fingerprint.
    # Story pages include their inline lookup panels in the cached site bundle.
    return tuple(
        (path.name, info.st_mtime_ns, info.st_size)
        for path in sorted(ROOT.iterdir())
        if path.is_file() and (path.name in names or path.suffix.lower() in (".webp", ".png", ".jpg"))
        for info in (path.stat(),)
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
        pages[name] = page
    return json_script(pages), json_script(assets)


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
pages_json, assets_json = bundle_site(site_version())
st.iframe("""<!doctype html><meta charset="utf-8"><style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#e9decd}
*{box-sizing:border-box}
#layout{display:grid;grid-template-columns:clamp(233px,23vw,300px) minmax(0,1fr);height:100dvh}
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
window.ziliImage = name => images[name] || name;
const frame = document.getElementById('site');
const directory = document.getElementById('directory');
const layout = document.getElementById('layout');
let current = 'index.html', lastStory = '';
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
    if (trigger) {trigger.click(); return;}
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
    doc.getElementById('close-story-lookup')?.addEventListener('click', () => selectTab('featured'));
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
  const innerStyles = cover ? '' : '<style>.demo-shell,.journey-layout{display:block!important;max-width:1080px;margin:auto}.demo-shell>.directory,.journey-layout>.journey-sidebar{display:none!important}</style>';
  frame.srcdoc = pages[page].replace('</head>', innerStyles + '</head>');
}
function openFunction(key) {
  if (key === 'home') return navigate('index.html');
  if (key === 'featured') return navigate('featured.html');
  if (key === 'regions') return navigate('regions.html');
  if (isStory(current)) {
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
