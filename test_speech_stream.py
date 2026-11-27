import base64
import io
import json
import unittest
from unittest.mock import patch
from speech_stream import SpeechStream


class StreamTests(unittest.TestCase):
    def test_sse_frames_are_delivered_before_download_and_cached(self):
        pcm=b'\0\0'*240
        payload=b'data: '+json.dumps({'output':{'audio':{'data':base64.b64encode(pcm).decode()}}}).encode()+b'\n\n'
        payload+=b'data: {"output":{"audio":{"url":"ignored.wav"}}}\n\ndata: [DONE]\n\n'
        with patch('speech_stream.urlopen',return_value=io.BytesIO(payload)) as api,patch('speech_stream.read_clip',return_value=None),patch('speech_stream.save_clip') as save,patch('speech_stream.provider_call'):
            job=SpeechStream({'id':'test','text':'连续朗读','language':'cantonese'},{'DASHSCOPE_API_KEY':'test-secret'})
            job.thread.join(2)
            packet=job.drain()
            self.assertTrue(packet['done']);self.assertEqual(base64.b64decode(packet['pcm']),pcm)
            self.assertNotIn('error',packet);self.assertEqual(packet['sample_rate'],24000)
            self.assertEqual(api.call_args.args[0].get_header('X-dashscope-sse'),'enable')
            self.assertEqual(json.loads(api.call_args.args[0].data)['input']['voice'],'Kiki');save.assert_called_once()

    def test_cached_stream_never_calls_provider(self):
        with patch('speech_stream.read_clip',return_value={'pcm':base64.b64encode(b'\0\0'*48000).decode()}),patch('speech_stream.urlopen') as api:
            job=SpeechStream({'id':'cached','text':'缓存','language':'taiwan'},{'DASHSCOPE_API_KEY':'test-secret'});job.thread.join(2)
            packet=job.drain();self.assertTrue(packet['done']);self.assertTrue(packet['pcm']);api.assert_not_called()

    def test_invalid_input_does_not_call_service(self):
        with patch('speech_stream.urlopen') as api:
            job=SpeechStream({'id':'bad','text':'字'*581,'language':'mandarin'},{});job.thread.join(2)
            self.assertIn('error',job.drain());api.assert_not_called()


if __name__=='__main__':unittest.main()
