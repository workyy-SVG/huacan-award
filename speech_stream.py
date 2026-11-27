"""SSE speech worker. Only the Streamlit script thread accesses session state."""
import base64
import hashlib
import json
import queue
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from cloud_tts import VOICES
from provider_budget import provider_call
from qwen_live import config
from speech_cache import read_clip, save_clip


class SpeechStream:
    def __init__(self, request, secrets):
        self.id=request['id'];self.cancelled=threading.Event();self.queue=queue.Queue(maxsize=512)
        self.done=False;self.error='';self.sequence=0
        # Copy configuration on the script thread; no st.secrets access inside the worker.
        self.key=str(config(secrets,'TTS_API_KEY') or config(secrets,'DASHSCOPE_API_KEY')).strip()
        self.base=str(config(secrets,'TTS_BASE_URL') or config(secrets,'QWEN_BASE_URL') or 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.text=request.get('text');self.language=request.get('language')
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()

    def run(self):
        try:
            if not isinstance(self.text,str) or not 1<=len(self.text.strip())<=580 or self.language not in VOICES:
                raise ValueError('语音请求无效。')
            if not self.key:raise ValueError('云端语音尚未配置密钥。')
            parsed=urlsplit(self.base)
            if parsed.scheme!='https' or parsed.hostname not in ('dashscope.aliyuncs.com','dashscope-intl.aliyuncs.com','dashscope-us.aliyuncs.com') or parsed.username or parsed.password or parsed.port not in (None,443):
                raise ValueError('云端语音地址配置无效。')
            voice=VOICES[self.language]
            signature=hashlib.sha256(('stream-pcm-v1'+self.key+parsed.hostname+voice+self.text).encode()).hexdigest()
            cached=read_clip(signature)
            if cached and isinstance(cached.get('pcm'),str):
                pcm=base64.b64decode(cached['pcm'],validate=True)
                if len(pcm)>16*1024*1024:raise ValueError('缓存音频过大。')
                for start in range(0,len(pcm),48000):
                    if self.cancelled.is_set():return
                    self.queue.put(pcm[start:start+48000],timeout=2)
                return
            body={'model':'qwen3-tts-flash','input':{'text':self.text.strip(),'voice':voice,'language_type':'Chinese'}}
            req=Request('https://'+parsed.hostname+'/api/v1/services/aigc/multimodal-generation/generation',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json','X-DashScope-SSE':'enable'})
            pieces=[];size=0;started=time.monotonic()
            with provider_call(),urlopen(req,timeout=20) as response:
                while not self.cancelled.is_set():
                    line=response.readline(1024*1024+1)
                    if not line:break
                    if len(line)>1024*1024:raise ValueError('语音数据异常。')
                    if time.monotonic()-started>100:raise TimeoutError()
                    if not line.startswith(b'data:'):continue
                    payload=line[5:].strip()
                    if payload==b'[DONE]':break
                    event=json.loads(payload)
                    if event.get('code') or event.get('status_code',200)!=200:
                        raise ValueError('云端语音服务返回错误，请检查权限或额度。')
                    value=event.get('output',{}).get('audio',{}).get('data')
                    if value:
                        pcm=base64.b64decode(value,validate=True);size+=len(pcm)
                        if size>16*1024*1024 or len(pcm)%2:raise ValueError('语音数据异常。')
                        pieces.append(pcm);self.queue.put(pcm,timeout=2)
            if not pieces and not self.cancelled.is_set():raise ValueError('云端没有返回音频。')
            if pieces and not self.cancelled.is_set():save_clip(signature,{'pcm':base64.b64encode(b''.join(pieces)).decode()})
        except ValueError as error:self.error=str(error)
        except Exception:self.error='实时语音连接暂时中断，请重新开始。'
        finally:self.done=True

    def drain(self):
        parts=[];size=0
        while size<240000:
            try:part=self.queue.get_nowait()
            except queue.Empty:break
            parts.append(part);size+=len(part)
        if not parts and not (self.done and self.queue.empty()):return None
        self.sequence+=1
        result={'id':self.id,'stream':True,'seq':self.sequence,'done':self.done and self.queue.empty(),'sample_rate':24000}
        if parts:result['pcm']=base64.b64encode(b''.join(parts)).decode()
        if self.error:result['error']=self.error
        return result
