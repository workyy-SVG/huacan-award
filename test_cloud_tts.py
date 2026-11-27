import io
import json
import unittest
import tempfile
import os
from unittest.mock import patch
from urllib.error import HTTPError
import cloud_tts


class CloudSpeechTests(unittest.TestCase):
    def setUp(self):
        cloud_tts._cache.clear()
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        patcher=patch.dict(os.environ,{'TTS_CACHE_DB':directory.name+'/audio.sqlite3'})
        patcher.start();self.addCleanup(patcher.stop)

    def test_voices_payload_audio_and_cache(self):
        wav=b'RIFF'+b'\0'*4+b'WAVE'+b'\0'*60
        calls=[]
        def api(req,timeout):
            calls.append(json.loads(req.data))
            return io.BytesIO(json.dumps({'output':{'audio':{'url':'http://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/test.wav'}}}).encode())
        class Opener:
            def open(self,url,timeout):
                self.url=url
                assert url.startswith('https://')
                return io.BytesIO(wav)
        with patch('cloud_tts.urlopen',api),patch('cloud_tts.build_opener',return_value=Opener()),patch('cloud_tts.provider_call'):
            for language,voice in cloud_tts.VOICES.items():
                request={'language':language,'text':'团圆故事。'}
                first=cloud_tts.synthesize(request,{'DASHSCOPE_API_KEY':'test-key'})
                self.assertTrue(first['audio'].startswith('data:audio/wav;base64,'))
                self.assertEqual(calls[-1]['input']['voice'],voice)
                cloud_tts._cache.clear()  # Simulate a worker/module restart: disk reuse must work.
                self.assertEqual(cloud_tts.synthesize(request,{'DASHSCOPE_API_KEY':'test-key'}),first)
        self.assertEqual(len(calls),3)

    def test_invalid_requests_never_call_provider(self):
        with patch('cloud_tts.urlopen') as api:
            for request in [None,{}, {'language':{},'text':'x'}, {'language':'macau','text':'x'}, {'language':'taiwan','text':'x'*301}]:
                self.assertIn('error',cloud_tts.synthesize(request,{}))
            api.assert_not_called()

    def test_safe_audio_host(self):
        for url in ['http://127.0.0.1/x','https://evil.example/a.wav','https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com.evil.example/a.wav']:
            with self.assertRaises(ValueError):cloud_tts.audio_url(url)

    def test_unauthorized_is_explicit(self):
        with patch('cloud_tts.urlopen',side_effect=HTTPError('https://x',403,'forbidden',{},None)),patch('cloud_tts.provider_call'):
            result=cloud_tts.synthesize({'language':'cantonese','text':'你好'}, {'DASHSCOPE_API_KEY':'test-secret'})
        self.assertIn('未授权',result['error'])
        self.assertNotIn('test-secret',str(result))


if __name__=='__main__':unittest.main()
