"""Regression coverage for preserving the live site during speech commands."""
import ast
import json
from pathlib import Path
import queue
import sys
import types
import unittest
from unittest.mock import patch


class State(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class FakeSpeech:
    def __init__(self, request, secrets):
        import threading
        self.id = request['id']
        self.cancelled = threading.Event()
        self.done = False
        self.queue = queue.Queue()
        self.packet = None

    def drain(self):
        packet, self.packet = self.packet, None
        return packet


class SiteRefreshTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(Path(__file__).with_name('streamlit_app.py').read_text(encoding='utf-8'))
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'render_connected_site')
        self.interval = None
        def fragment(**options):
            self.interval = options['run_every']
            return lambda f: f
        self.state = State()
        self.request = None
        self.renders = []
        def site(**args):
            self.renders.append(args)
            return self.request
        def forbidden(*args, **kwargs):
            self.fail('Speech must not stop or rerun the entire app')
        env = dict(st=types.SimpleNamespace(session_state=self.state, secrets={},
                   fragment=fragment, rerun=forbidden, stop=forbidden),
                   site=site, story='nian', version=('v1',), json=json,
                   release_html='unused', published_story_theme=lambda *args:'<html>site</html>')
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<site-fragment>', 'exec'), env)
        self.render = env['render_connected_site']
        self.stub = patch.dict(sys.modules, {'speech_stream':types.SimpleNamespace(SpeechStream=FakeSpeech)})
        self.stub.start()
        self.addCleanup(self.stub.stop)

    def test_switch_cancel_complete_without_full_rerun(self):
        self.render()
        self.assertEqual(self.interval, .25)
        self.assertTrue(self.renders[-1]['html'])
        self.request = dict(id='ready', mode='site_ready', site_key=self.renders[-1]['site_key'])
        self.render()
        for i, language in enumerate(['mandarin', 'cantonese', 'cantonese', 'taiwan']):
            old = self.state.get('speech_stream_job')
            self.request = dict(id=str(i), mode='tts_stream', text='团圆', language=language)
            self.render()
            job = self.state.speech_stream_job
            if old:
                self.assertTrue(old.cancelled.is_set())
            self.render()
            self.assertIs(self.state.speech_stream_job, job, 'Repeated ticks must not restart synthesis')
            job.packet = dict(id=str(i), stream=True, seq=1, done=False, pcm='AAAA')
            self.render()
            self.render()
            self.assertEqual(self.renders[-1]['response']['pcm'], 'AAAA')
            self.assertEqual(self.renders[-1]['html'], '')
        self.request = dict(id='cancel', mode='tts_cancel')
        self.render()
        self.assertTrue(job.cancelled.is_set())
        self.assertIsNone(self.state.speech_stream_job)
        self.request = dict(id='final', mode='tts_stream', text='团圆', language='cantonese')
        self.render()
        job = self.state.speech_stream_job
        job.done = True
        job.packet = dict(id='final', stream=True, seq=1, done=True)
        self.render()
        self.assertIsNone(self.state.speech_stream_job)
        self.render()
        self.assertTrue(self.renders[-1]['response']['done'])
        self.assertEqual(len({r['site_key'] for r in self.renders}), 1)

    def test_bootstrap_recovers_html_on_next_tick(self):
        self.render()
        self.request = dict(id='bootstrap', mode='bootstrap')
        self.render()
        self.render()
        self.assertTrue(self.renders[-1]['html'])
        self.request = dict(id='ready', mode='site_ready', site_key=self.renders[-1]['site_key'])
        self.render()
        self.render()
        self.assertEqual(self.renders[-1]['html'], '')


if __name__ == '__main__':
    unittest.main()
