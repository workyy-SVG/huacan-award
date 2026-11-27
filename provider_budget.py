"""Atomic provider-call budget shared by processes on the same host."""
import os
import sqlite3
import tempfile
import time
import uuid
from contextlib import contextmanager, closing
from pathlib import Path


class BudgetExceeded(Exception):
    pass


def _limit(name, default):
    try:
        return max(1, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


@contextmanager
def provider_call(now=None):
    stamp = time.time() if now is None else now
    path = os.environ.get('QWEN_BUDGET_DB', str(Path(tempfile.gettempdir()) / 'zili-qwen-budget-v1.sqlite3'))
    token = uuid.uuid4().hex
    day_start = ((int(stamp) + 8 * 3600) // 86400) * 86400 - 8 * 3600
    try:
        with closing(sqlite3.connect(path, timeout=3)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, stamp REAL, active_until REAL)')
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM calls WHERE stamp < ? AND active_until <= ?', (min(day_start,stamp-60),stamp))
            minute, daily, active = db.execute(
                'SELECT SUM(stamp > ?), SUM(stamp >= ?), SUM(active_until > ?) FROM calls',
                (stamp - 60, day_start, stamp)).fetchone()
            if ((minute or 0) >= _limit('QWEN_CALLS_PER_MINUTE', 40)
                    or (daily or 0) >= _limit('QWEN_CALLS_PER_DAY', 1000)
                    or (active or 0) >= _limit('QWEN_MAX_CONCURRENT', 4)):
                raise BudgetExceeded()
            db.execute('INSERT INTO calls VALUES (?, ?, ?)', (token, stamp, stamp + 40))
    except sqlite3.Error as exc:
        raise BudgetExceeded() from exc
    try:
        yield
    finally:
        try:
            with closing(sqlite3.connect(path, timeout=3)) as db, db:
                db.execute('UPDATE calls SET active_until = 0 WHERE id = ?', (token,))
        except sqlite3.Error:
            pass  # Lease expiry releases a crashed or inaccessible worker.
