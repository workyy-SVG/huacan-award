"""Checked release transformations; fail rather than silently ship missing hooks."""
import base64
import gzip
import json
import re

OLD_DEFINITION = 'reading.definitions?.find(item => item.def)?.def'
NEW_DEFINITION = "(reading.definitions || []).filter(item => item.def).map((item, index) => (index + 1) + '. ' + (item.type ? '[' + item.type + '] ' : '') + item.def + (item.example?.length ? ' 例：' + item.example.join('；') : '')).join('\\n')"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Release hook mismatch: {old[:90]}')
    return text.replace(old, new, 1)


def improve_release(html, root):
    packed = re.search(r"(const packed = ')([^']+)(';)", html)
    if not packed:
        raise ValueError('Missing release bundle')
    payload = json.loads(gzip.decompress(base64.b64decode(packed[2])))
    for name, page in payload['pages'].items():
        if name in ('index.html','nian.html','men.html','cha.html','chuan.html','deng.html','yuan.html'):
            page = replace_once(page, OLD_DEFINITION, NEW_DEFINITION)
            page = page.replace('definitions.append(paragraph);', "paragraph.style.whiteSpace = 'pre-wrap';\n      definitions.append(paragraph);")
            request = "await fetch('https://www.moedict.tw/uni/' + encodeURIComponent(form), {signal:controller.signal})"
            if page.count(request) != 1:
                raise ValueError('Dictionary request hook changed: ' + name)
            page = page.replace(request, 'await parent.ziliFetchDictionary(form, controller.signal)')
            page = page.replace("status.textContent = [entry.radical", "status.textContent = (response.fromCache ? '本地缓存 · ' : '') + [entry.radical")
        payload['pages'][name] = page
    encoded = base64.b64encode(gzip.compress(json.dumps(payload,ensure_ascii=False).encode(),mtime=0)).decode()
    html = html[:packed.start(2)] + encoded + html[packed.end(2):]
    manifest = json.loads((root/'qwen-component'/'asset-manifest.json').read_text(encoding='utf-8'))
    atlas_images = {name: 'data:image/webp;base64,' + base64.b64encode((root/'qwen-component'/'atlas'/item['file']).read_bytes()).decode()
                    for name,item in manifest.items()}
    atlas = 'const atlasImages = ' + json.dumps(atlas_images) + ';\n' + """
function localizeAtlas(text) {
  return text.replace(/__ZILI_ATLAS__\\/([\\w.-]+)/g, (_, name) => {
    if (!atlasImages[name]) throw Error('Missing artwork: ' + name);
    return atlasImages[name];
  });
}
for (const key of Object.keys(images)) images[key] = localizeAtlas(images[key]);
for (const key of Object.keys(pages)) pages[key] = localizeAtlas(pages[key]);
for (const style of document.querySelectorAll('style')) style.textContent = localizeAtlas(style.textContent);
"""
    story_art_start = html.index('const storyArt = ') + len('const storyArt = ')
    _, story_art_length = json.JSONDecoder().raw_decode(html[story_art_start:])
    story_art_end = story_art_start + story_art_length
    if html[story_art_end] != ';':
        raise ValueError('Story artwork initializer changed')
    html = html[:story_art_end+1] + "\nfor (const key of Object.keys(storyArt)) storyArt[key] = localizeAtlas(storyArt[key]);\n" + html[story_art_end+1:]
    cache = json.loads((root / 'dictionary-cache.json').read_text(encoding='utf-8-sig'))['entries']
    html = replace_once(html, 'let restored;', atlas + '\nlet restored;')
    runtime = 'window.ziliDictionaryCache = ' + json.dumps(cache,ensure_ascii=False).replace('<', r'\u003c') + ';\n' + (root / 'release_runtime.js').read_text(encoding='utf-8')
    html = replace_once(html, 'function navigate(page, hash = \'\', tab = \'\') {', runtime + "\nfunction navigate(page, hash = '', tab = '') {")
    html = replace_once(html, '  current = page;', "  const sequence = ++navigationSequence;\n  current = page;\n  rememberRoute(page, hash, tab);")
    html = replace_once(html, '  frame.onload = () => {\n    const doc = frame.contentDocument;', "  frame.onload = () => {\n    if (sequence !== navigationSequence) return;\n    const doc = frame.contentDocument;\n    if (doc.documentElement.dataset.navigationSequence !== String(sequence)) return;")
    html = replace_once(html, "  frame.srcdoc = ", "  frame.style.pointerEvents = 'none';\n  frame.setAttribute('aria-busy','true');\n  const preparedPage = ")
    html = replace_once(html, "    parent.postMessage({type:'zili-ready'}, '*');", "    frame.style.pointerEvents = '';\n    frame.removeAttribute('aria-busy');\n    doc.documentElement.dataset.releaseReady = 'true';\n    bindShareLink(doc, page);\n    parent.postMessage({type:'zili-ready'}, '*');")
    html = replace_once(html, "    add(body, 'a', '回到故事 →').href = item.page + '#' + item.id;\n  }\n}", "    add(body, 'a', '回到故事 →').href = item.page + '#' + item.id;\n  }\n  manageCollection(doc, add);\n}")
    html = replace_once(html, 'detail: record.recorded_action || record.body, image', 'detail: record.recorded_action || record.body, source: record.source_url || record.source || \'\', image')
    html = html.replace('entry.id !== item.id)', 'entry.id !== item.id || entry.page !== item.page)')
    html = replace_once(html, "if (restored && Object.hasOwn(pages, restored.page)) {", "if (restoreRoute()) { /* URL state takes priority. */ } else if (restored && Object.hasOwn(pages, restored.page)) {")
    # Intercept links immediately, before images finish loading and enhancements mount.
    early = """<script>document.addEventListener('click', event => {
if (document.documentElement.dataset.releaseReady === 'true') return;
const anchor = event.target.closest('a[href]');
if (!anchor || event.defaultPrevented || anchor.target === '_blank' || anchor.hasAttribute('download')) return;
const href = anchor.getAttribute('href');
if (!href || /^(?:[a-z]+:|\\/\\/)/i.test(href)) return;
event.preventDefault(); event.stopImmediatePropagation(); parent.ziliEarlyNavigate(href);
}, true);</script>"""
    html = replace_once(html, "  frame.onload = () => {", "  window.ziliEarlyNavigate = href => {\n    const [path, fragment] = href.split('#');\n    if (!path) { goToSection(frame.contentDocument, fragment); rememberRoute(current, fragment); return; }\n    const next = path === './' ? 'index.html' : path.replace(/^\\.\\//, '');\n    if (Object.hasOwn(pages, next)) navigate(next, fragment || '');\n  };\n  frame.onload = () => {")
    assignment = "\n  const earlyScript = " + json.dumps(early).replace('</', r'<\/') + ";\n  frame.srcdoc = localizeAtlas(preparedPage).replace('</head>', earlyScript + '</head>').replace('<html', '<html data-navigation-sequence=\"' + sequence + '\"');\n}\nfunction openFunction(key)"
    html = replace_once(html, '\n}\nfunction openFunction(key)', assignment)
    return html
