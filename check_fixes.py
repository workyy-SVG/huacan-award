import ast
import base64
import gzip
import json
import re
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent
sys.path.insert(0,str(ROOT))
import qwen_live
import request_limits
from release_fixes import patch_release

catalogue = {'cases':[{'url':'nian.html','character':'年'}], 'regions':{'大陆':[{'character':'年','place':'泉州','title':'团圆','body':'除夕团圆饭','source':'https://example.org'}]}}
def response(text): return BytesIO(json.dumps({'choices':[{'message':{'content':text}}]}).encode())
request = {'mode':'story','story':'nian','question':'这里有什么习俗？'}
with patch.object(qwen_live,'sleep'), patch.object(qwen_live,'urlopen',side_effect=lambda *a,**k:response('测试回答 [999]')) as calls:
    assert 'error' in qwen_live.answer(request,catalogue,{'DASHSCOPE_API_KEY':'mock'})
    assert calls.call_count == 2
with patch.object(qwen_live,'urlopen',side_effect=lambda *a,**k:response('{"evidence":[{"id":1,"quote":"除夕团圆饭"}]}')):
    assert len(qwen_live.answer(request,catalogue,{'DASHSCOPE_API_KEY':'mock'})['sources']) == 1
with patch.object(qwen_live,'urlopen',side_effect=lambda *a,**k:response('{"ids":[1,1,999]}')):
    assert len(qwen_live.answer({'mode':'search','question':'团圆'},catalogue,{'DASHSCOPE_API_KEY':'mock'})['records']) == 1
state={}
assert request_limits.allow_request(state,now=100)
assert not request_limits.allow_request(state,now=101)
assert request_limits.allow_request(state,now=104)
request_limits._global.clear()
for i in range(40): assert request_limits.allow_request({},now=200)
assert not request_limits.allow_request({},now=200)
assert request_limits.allow_request({},now=261)
html=patch_release((ROOT/'published-theme.html').read_text(encoding='utf-8'),ROOT)
assert "if (key === 'keepsake') return navigate(keepsakePage);" in html
assert "sessionStorage.setItem('zili-navigation-v2'" in html
payload=json.loads(gzip.decompress(base64.b64decode(re.search(r"const packed = '([^']+)'",html)[1])))
assert '待补汤圆' not in json.dumps(payload,ensure_ascii=False)
assert 'lookup-standards' in payload['pages']['nian.html']
assert 'OpenCC.Converter' in html
assert 'zili-ready' in html
assert 'navigate("nian.html")' in patch_release((ROOT/'published-theme.html').read_text(encoding='utf-8'),ROOT,'nian')
ast.parse((ROOT/'streamlit_app.py').read_text(encoding='utf-8'))
print('PASS: citations, retries, search deduplication, session cooldown, process limit, navigation, bundled lookup notes, evidence wording, explicit story URL')
