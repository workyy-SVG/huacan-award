"""Refresh six demonstration entries from the dictionary's public JSON endpoint."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

def refresh():
    entries = {}
    for word in '年門茶船燈圓':
        with urlopen('https://www.moedict.tw/uni/' + quote(word), timeout=20) as response:
            entry = json.load(response)
        if entry.get('title') != word or not isinstance(entry.get('heteronyms'),list):
            raise ValueError('Invalid dictionary entry')
        entries[word] = entry
    payload = {'source':'https://www.moedict.tw/',
               'cached_at':datetime.now(timezone.utc).isoformat(), 'entries':entries}
    (Path(__file__).parent/'dictionary-cache.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Cached', len(entries), 'dictionary entries')

if __name__ == '__main__': refresh()
