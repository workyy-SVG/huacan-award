"""Apply narrowly scoped fixes to the generated release without replacing its design."""
import base64
import gzip
import json
import re


def repair_text(text):
    return (text.replace('老街长桌宴的年节饮食（待补汤圆细节） · 待补证据', '老街长桌宴里的团聚')
            .replace('老街长桌宴的年节饮食（待补汤圆细节）', '老街长桌宴里的团聚')
            .replace('待补直接证据', '此例记录长桌宴与团聚，不作为当地汤圆习俗的证据')
            .replace('待补证据', '此例聚焦长桌宴与团聚'))


def patch_release(html, root, story=''):
    def unpack(match):
        payload = json.loads(gzip.decompress(base64.b64decode(match[2])))
        for key, page in payload['pages'].items():
            page = repair_text(page)
            payload['pages'][key] = page
        # The generated bundle embeds the lookup implementation; replace its IIFE too.
        old_lookup = (root / 'zili-lookup-results-original.js').read_text(encoding='utf-8')
        new_lookup = (root / 'zili-lookup-results.js').read_text(encoding='utf-8')
        for key in payload['pages']:
            payload['pages'][key] = payload['pages'][key].replace(old_lookup.strip(), new_lookup.strip())
        raw = repair_text(json.dumps(payload, ensure_ascii=False)).encode()
        return match[1] + base64.b64encode(gzip.compress(raw, mtime=0)).decode() + match[3]

    html = re.sub(r"(const packed = ')([^']+)(';)", unpack, html, count=1)
    library = gzip.decompress(base64.b64decode((root / 'opencc-full.gz.b64').read_bytes())).decode('utf-8')
    html = html.replace('const traditionalRegions = ', library + '\nconst convertTraditional = OpenCC.Converter({from:"cn",to:"tw"});\nconst traditionalRegions = ', 1)
    html = re.sub(r'function traditionalText\(text\) \{[\s\S]*?\n\}',
                  'function traditionalText(text) { return convertTraditional(text); }', html, count=1)
    html = html.replace("'切换为繁體'", "'切换为繁体'")
    # Keep quotations and dictionary glyphs unchanged; localize dynamic interface attributes.
    html = html.replace("  walk(doc.body);", """  walk(doc.body);
  function localizeAttributes() {
    for (const element of doc.querySelectorAll('[placeholder],[aria-label],[title]')) {
      if (element.closest(skip)) continue;
      for (const name of ['placeholder','aria-label','title']) {
        const value = element.getAttribute(name);
        if (value) element.setAttribute(name, traditionalText(value));
      }
    }
  }
  localizeAttributes();""", 1)
    html = html.replace("else for (const node of change.addedNodes) walk(node);", "else for (const node of change.addedNodes) walk(node);\n      localizeAttributes();", 1)
    html = html.replace("function openFunction(key) {", "function openFunction(key) {\n  if (key === 'keepsake') return navigate(keepsakePage);", 1)
    html = html.replace("  current = page;", """  current = page;
  try { sessionStorage.setItem('zili-navigation-v2', JSON.stringify({page, hash, tab, traditionalUI})); } catch {}""", 1)
    html = html.replace("    const doc = frame.contentDocument;", "    const doc = frame.contentDocument;", 1)
    # Notify the component only after page listeners have been mounted.
    html = html.replace("    if (hash) activateLocal(doc, hash);", "    parent.postMessage({type:'zili-ready'}, '*');\n    if (hash) activateLocal(doc, hash);", 1)
    html = html.replace("\nnavigate('index.html');", """
let restored;
try { restored = JSON.parse(sessionStorage.getItem('zili-navigation-v2') || 'null'); } catch {}
if (restored && Object.hasOwn(pages, restored.page)) {
  traditionalUI = !!restored.traditionalUI;
  navigate(restored.page, restored.hash || '', restored.tab || '');
} else navigate('index.html');""", 1)
    # Mobile navigation: one compact menu above the current page, desktop untouched.
    controls = '''<style>@media(max-width:680px){#directory{position:relative!important;padding:8px 12px!important}#directory .subtitle{display:none}#directory .brand{font-size:24px}#directory nav{display:none!important}#directory.mobile-open nav{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))}#mobile-menu{display:block!important;position:absolute;right:12px;top:8px;width:auto!important;padding:6px 12px!important}#layout:not(.home){grid-template-rows:auto minmax(0,1fr)!important}#directory button{min-height:44px}#site{min-height:0}}</style>'''
    html = html.replace('</style>', '</style>' + controls, 1)
    html = html.replace("const layout = document.getElementById('layout');", """const layout = document.getElementById('layout');
const menu = document.createElement('button');
menu.id = 'mobile-menu'; menu.type = 'button'; menu.textContent = '功能菜单';
menu.style.display = 'none'; menu.setAttribute('aria-expanded','false');
menu.onclick = () => { const open = directory.classList.toggle('mobile-open'); menu.setAttribute('aria-expanded',String(open)); };
directory.prepend(menu);
directory.querySelector('nav').addEventListener('click', () => { directory.classList.remove('mobile-open'); menu.setAttribute('aria-expanded','false'); });""", 1)
    if story and story + '.html' in ('nian.html','men.html','cha.html','chuan.html','deng.html','yuan.html'):
        html = html.replace('if (restored && Object.hasOwn(pages, restored.page)) {',
                            'if (true) { navigate(' + json.dumps(story + '.html') + '); } else if (restored && Object.hasOwn(pages, restored.page)) {')
    return html
