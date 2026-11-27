"""In-process budget plus a per-session cooldown; no provider call on rejection."""
from collections import deque
from threading import Lock
from time import monotonic

_lock = Lock()
_global = deque()

def allow_request(session, now=None):
    now = monotonic() if now is None else now
    recent = [stamp for stamp in session.get('qwen_request_times', []) if 0 <= now - stamp < 60]
    with _lock:
        while _global and now - _global[0] >= 60:
            _global.popleft()
        if (recent and now - recent[-1] < 3) or len(recent) >= 8 or len(_global) >= 40:
            return False
        recent.append(now)
        _global.append(now)
    session['qwen_request_times'] = recent
    return True
