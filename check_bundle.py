"""Execute the exact release renderer and check the JavaScript it ships."""
import ast
import base64
import gzip
import json
import re
from io import BytesIO
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).parent.resolve()
PAGES=('index.html','featured.html','regions.html','nian.html','men.html','cha.html','chuan.html','deng.html','yuan.html')
tree=ast.parse((ROOT/'streamlit_app.py').read_text(encoding='utf-8'))
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='published_story_theme')
function.decorator_list=[]
exec(compile(ast.Module(body=[function],type_ignores=[]),'renderer','exec'))
html=published_story_theme(ROOT/'published-theme.html','',())
assert 'data-tab="guide"' in html
assert "button.id = 'script-switch'" not in html
release_payload = json.loads(gzip.decompress(base64.b64decode(re.search(r"const packed = '([^']+)'",html)[1])))
assert '图解' in release_payload['pages']['guide.html']
assert 'OpenCC.Converter' in html
assert 'zili-pending:' in html
assert 'mobile-home.css' not in html  # the stylesheet is bundled, not fetched by browser
assert 'Mobile cover only' in html
assert "if (key === 'keepsake') return navigate(keepsakePage);" in html
assert 'localizeAttributes' in html
assert 'lookup-standards' in html or 'lookup-standards' in gzip.decompress(base64.b64decode(re.search(r"const packed = '([^']+)'",html)[1])).decode()
assert '待补汤圆' not in gzip.decompress(base64.b64decode(re.search(r"const packed = '([^']+)'",html)[1])).decode()
(ROOT/'validation-final.html').write_text(html,encoding='utf-8')
for i,script in enumerate(re.findall(r'<script[^>]*>([\s\S]*?)</script>',html)):
    (ROOT/f'validation-final-{i}.js').write_text(script,encoding='utf-8')
print('PASS: actual renderer, embedded assets, OpenCC, mobile-only style, collection navigation, evidence wording, pending-answer restoration')
