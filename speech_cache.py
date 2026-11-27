"""Bounded disk cache for cloud-generated audio, reusable after app reruns."""
import gzip
import json
import os
import sqlite3
import tempfile
import time
from contextlib import closing
from pathlib import Path


def database():
    path=os.environ.get('TTS_CACHE_DB',str(Path(tempfile.gettempdir())/'zili-speech-cache-v1.sqlite3'))
    db=sqlite3.connect(path,timeout=2)
    db.execute('CREATE TABLE IF NOT EXISTS clips (key TEXT PRIMARY KEY, stamp REAL, payload BLOB)')
    return db


def read_clip(key):
    try:
        with closing(database()) as db:
            row=db.execute('SELECT stamp,payload FROM clips WHERE key=?',(key,)).fetchone()
        if row and time.time()-row[0]<7*86400:
            return json.loads(gzip.decompress(row[1]))
    except (sqlite3.Error,OSError,ValueError):
        pass


def save_clip(key,answer):
    try:
        payload=gzip.compress(json.dumps(answer).encode(),compresslevel=1)
        with closing(database()) as db,db:
            db.execute('INSERT OR REPLACE INTO clips VALUES (?,?,?)',(key,time.time(),payload))
            db.execute('DELETE FROM clips WHERE stamp<?',(time.time()-7*86400,))
            count,size=db.execute('SELECT COUNT(*),COALESCE(SUM(length(payload)),0) FROM clips').fetchone()
            if count>512 or size>128*1024*1024:
                for old,amount in db.execute('SELECT key,length(payload) FROM clips ORDER BY stamp').fetchall():
                    if count<=512 and size<=128*1024*1024:break
                    db.execute('DELETE FROM clips WHERE key=?',(old,));count-=1;size-=amount
    except (sqlite3.Error,OSError):
        pass  # Read-only/full storage must never prevent speech.
