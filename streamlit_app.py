"""Render the six-character website with its assets bundled into Streamlit."""
import base64
import json
import mimetypes
from pathlib import Path
import re

import streamlit as st

ROOT = Path(__file__).resolve().parent
PAGES = ("index.html", "featured.html", "regions.html", "nian.html",
         "men.html", "cha.html", "chuan.html", "deng.html", "yuan.html")


def site_version():
    names = {*PAGES, "cases.json", "style.css", "app.js", "demo.js"}
    # Include the regional gallery page in the cache fingerprint.
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
iframe{display:block;width:100%;height:100%;border:0}
</style><iframe title="字里寻踪" id="site"></iframe>
<script>
const pages = """ + pages_json + """;
const images = """ + assets_json + """;
window.ziliImage = name => images[name] || name;
const frame = document.getElementById('site');
function navigate(page, hash = '') {
  if (!Object.hasOwn(pages, page)) return;
  document.body.style.background = page === 'index.html' ? '#e6e5e1' : '#e9decd';
  frame.onload = () => {
    const doc = frame.contentDocument;
    const scrollToSection = (node) => {
      if (!node) return;
      const view = frame.contentWindow;
      const offset = Number.parseFloat(view.getComputedStyle(node).scrollMarginTop) || 0;
      view.scrollTo(0, view.scrollY + node.getBoundingClientRect().top - offset);
    };
    if (hash) {
      const node = doc.getElementById(hash);
      if (node?.tagName === 'DETAILS') node.open = true;
      scrollToSection(node);
    }
    doc.addEventListener('click', event => {
      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.hasAttribute('download')) return;
      const href = anchor.getAttribute('href');
      if (!href || /^(?:[a-z]+:|\/\/)/i.test(href)) return;
      if (href.startsWith('#')) {
        event.preventDefault();
        const node = doc.getElementById(href.slice(1));
        if (node?.tagName === 'DETAILS') node.open = true;
        scrollToSection(node);
        return;
      }
      const [path, fragment] = href.split('#');
      const nextPage = path === './' ? 'index.html' : path.replace(/^\.\//, '');
      if (!Object.hasOwn(pages, nextPage)) return;
      event.preventDefault();
      navigate(nextPage, fragment);
    });
  };
  frame.srcdoc = pages[page];
}
navigate('index.html');
</script>""", height=860)
