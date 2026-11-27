import base64
import gzip
import json
import os
import re
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import qwen_live
from provider_budget import BudgetExceeded, provider_call
from release_quality import replace_once

ROOT = Path(__file__).parent
CATALOGUE = {'cases':[{'url':'nian.html','character':'年'}], 'regions':{'两岸':[
    {'character':'年','place':'泉州','title':'团圆饭','body':'除夕赶回家与家人围炉吃年饭。','source':'https://example.org'}]}}
REQUEST = {'mode':'story','story':'nian','question':'如何团聚？'}


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db = str(Path(self.directory.name)/'budget.sqlite3')
        self.env = patch.dict(os.environ, {'QWEN_BUDGET_DB':self.db,'QWEN_CALLS_PER_MINUTE':'40','QWEN_CALLS_PER_DAY':'1000','QWEN_MAX_CONCURRENT':'4'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.directory.cleanup()

    def answer(self, text):
        def response(*a,**k):
            return BytesIO(json.dumps({'choices':[{'message':{'content':text}}]}).encode())
        with patch.object(qwen_live,'sleep'), patch.object(qwen_live,'urlopen',side_effect=response) as calls:
            result = qwen_live.answer(REQUEST,CATALOGUE,{'DASHSCOPE_API_KEY':'mock'})
            return result,calls.call_count

    def test_invalid_request_types_never_call_provider(self):
        with patch.object(qwen_live,'urlopen') as calls:
            for request in [None,[],{**REQUEST,'story':['nian']},{**REQUEST,'story':{}},
                            {**REQUEST,'question':17},{**REQUEST,'id':'x'*129},{**REQUEST,'question':'字'*401}]:
                with self.subTest(request=request):
                    self.assertIn('error',qwen_live.answer(request,CATALOGUE,{}))
            calls.assert_not_called()

    def test_fabricated_fact_with_valid_id_rejected(self):
        result,count = self.answer('泉州除夕坐火箭去月球。[1]')
        self.assertIn('error',result)
        self.assertEqual(count,2)

    def test_fake_quote_rejected(self):
        result,_ = self.answer('{"evidence":[{"id":1,"quote":"泉州除夕坐火箭去月球"}]}')
        self.assertIn('error',result)

    def test_verified_quote_and_ignored_untrusted_summary(self):
        result,_ = self.answer('{"summary":"虚构结论","evidence":[{"id":1,"quote":"除夕赶回家与家人围炉吃年饭。"}]}')
        self.assertNotIn('虚构结论',result['text'])
        self.assertIn('围炉',result['text'])
        self.assertEqual(len(result['sources']),1)

    def test_insufficient_material_is_explicit(self):
        result,_ = self.answer('{"evidence":[]}')
        self.assertIn('不足',result['text'])
        self.assertEqual(result['sources'],[])

    def test_retries_share_provider_budget(self):
        with patch.dict(os.environ,{'QWEN_CALLS_PER_MINUTE':'1'}):
            result,count = self.answer('无证据')
        self.assertEqual(count,1)
        self.assertIn('预算',result['error'])

    def test_budget_shared_by_independent_connections(self):
        def attempt(_):
            try:
                with provider_call(): return 1
            except BudgetExceeded: return 0
        with patch.dict(os.environ,{'QWEN_CALLS_PER_MINUTE':'7','QWEN_MAX_CONCURRENT':'100'}):
            with ThreadPoolExecutor(max_workers=12) as pool:
                accepted = sum(pool.map(attempt,range(50)))
        self.assertEqual(accepted,7)

    def test_budget_releases_concurrency_but_keeps_daily_count(self):
        with patch.dict(os.environ,{'QWEN_MAX_CONCURRENT':'1','QWEN_CALLS_PER_DAY':'2'}):
            with provider_call():
                with self.assertRaises(BudgetExceeded):
                    with provider_call(): pass
            with provider_call(): pass
            with self.assertRaises(BudgetExceeded):
                with provider_call(): pass

    def test_build_hook_drift_fails(self):
        with self.assertRaises(ValueError): replace_once('changed','hook','new')

    def test_shipped_dictionary_and_assets(self):
        html=(ROOT/'validation-final.html').read_text(encoding='utf-8')
        payload=json.loads(gzip.decompress(base64.b64decode(re.search(r"const packed = '([^']+)'",html)[1])))
        self.assertNotIn('84de889',html)
        for name in ['index.html','nian.html','men.html','cha.html','chuan.html','deng.html','yuan.html']:
            self.assertNotIn('reading.definitions?.find',payload['pages'][name])
        self.assertIn('navigationSequence',html)
        self.assertIn('导出收藏备份',html)


if __name__ == '__main__': unittest.main()
