"""Server-side Qwen3 speech; credentials never reach the website."""
import base64
import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener

from provider_budget import BudgetExceeded, provider_call
from qwen_live import config

VOICES = {'mandarin': 'Cherry', 'cantonese': 'Kiki', 'taiwan': 'Roy'}
_cache = OrderedDict()
_lock = threading.Lock()
MAX_AUDIO = 4 * 1024 * 1024


def audio_url(url):
    parsed = urlsplit(url)
    host = parsed.hostname or ''
    if (parsed.scheme not in ('http', 'https') or parsed.username or parsed.password
            or parsed.port not in (None, 443)
            or not (host.startswith('dashscope-') and '.oss-' in host and host.endswith('.aliyuncs.com'))):
        raise ValueError('Unexpected audio host')
    return urlunsplit(parsed._replace(scheme='https'))


class AudioRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, audio_url(newurl))


def synthesize(request, secrets):
    if (not isinstance(request, dict) or not isinstance(request.get('language'), str) or request.get('language') not in VOICES
            or not isinstance(request.get('text'), str) or not 1 <= len(request['text'].strip()) <= 300):
        return {'error': '语音请求无效，请重新选择段落。'}
    key = str(config(secrets, 'TTS_API_KEY') or config(secrets, 'DASHSCOPE_API_KEY')).strip()
    if not key:
        return {'error': '云端语音缺少服务密钥，请管理员配置 DASHSCOPE_API_KEY 或 TTS_API_KEY。'}
    base = str(config(secrets, 'TTS_BASE_URL') or config(secrets, 'QWEN_BASE_URL')
               or 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    parsed = urlsplit(base)
    if (parsed.scheme != 'https' or parsed.hostname not in ('dashscope.aliyuncs.com', 'dashscope-intl.aliyuncs.com', 'dashscope-us.aliyuncs.com')
            or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port not in (None, 443)):
        return {'error': '云端语音服务地址无效，请管理员配置百炼 TTS_BASE_URL。'}
    model = 'qwen3-tts-flash'
    text = request['text'].strip()
    voice = VOICES[request['language']]
    signature = hashlib.sha256((key + parsed.hostname + model + voice + text).encode()).hexdigest()
    with _lock:
        cached = _cache.get(signature)
        if cached and time.monotonic() - cached[0] < 3600:
            _cache.move_to_end(signature)
            return cached[1]
    body = {'model': model, 'input': {'text': text, 'voice': voice, 'language_type': 'Chinese'}}
    endpoint = 'https://' + parsed.hostname + '/api/v1/services/aigc/multimodal-generation/generation'
    try:
        with provider_call():
            req = Request(endpoint, data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            with urlopen(req, timeout=20) as response:
                raw = response.read(128 * 1024 + 1)
            if len(raw) > 128 * 1024:
                raise ValueError('Response too large')
            result = json.loads(raw)
            audio = result.get('output', {}).get('audio', {})
            url = audio_url(audio.get('url', ''))
            with build_opener(AudioRedirect()).open(url, timeout=10) as response:
                content = response.read(MAX_AUDIO + 1)
            if not 44 <= len(content) <= MAX_AUDIO or content[:4] != b'RIFF' or content[8:12] != b'WAVE':
                raise ValueError('Invalid WAV audio')
        answer = {'audio': 'data:audio/wav;base64,' + base64.b64encode(content).decode(),
                  'voice': voice, 'language': request['language']}
        with _lock:
            _cache[signature] = (time.monotonic(), answer)
            _cache.move_to_end(signature)
            while len(_cache) > 24 or sum(len(v[1]['audio']) for v in _cache.values()) > 16 * 1024 * 1024:
                _cache.popitem(last=False)
        return answer
    except HTTPError as error:
        logging.warning('Cloud speech HTTP status %s', error.code)
        if error.code in (401, 403):
            return {'error': '百炼未授权语音合成。请管理员检查密钥权限、地域及 qwen3-tts-flash 服务开通状态。'}
        if error.code in (402, 429):
            return {'error': '云端语音额度不足或请求繁忙，请稍后重试或检查百炼账户额度。'}
        return {'error': '云端语音暂时无法合成，请稍后重试。'}
    except BudgetExceeded:
        return {'error': '云端语音请求较多，请稍后重试。'}
    except Exception as error:
        logging.warning('Cloud speech failed: %s', type(error).__name__)
        return {'error': '云端语音连接失败，请稍后重试。不会改用电脑系统声音。'}
