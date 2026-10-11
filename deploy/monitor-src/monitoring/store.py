"""Structured security logs; no prompts, tool arguments, or credentials stored."""
from contextlib import contextmanager
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,128}$')
    run_id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,128}$')
    agent: str = Field(pattern=r'^[A-Za-z0-9_.-]{1,80}$')
    origin: Literal['live', 'replay', 'test']
    execution: Literal['real', 'simulated']
    kind: Literal['started', 'completed', 'blocked_attempt', 'forbidden_commit', 'execution_error', 'provider_error']
    config_hash: str = Field(default='', pattern=r'^([a-f0-9]{64})?$')
    variant: str = Field(default='', pattern=r'^[A-Za-z0-9_-]{0,80}$')
    attempted: bool = False
    committed: bool = False
    blocked: bool = False

SEVERITY = {'forbidden_commit': 'critical', 'execution_error': 'high', 'provider_error': 'high', 'blocked_attempt': 'medium'}

def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL, received_at TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS incidents(event_id TEXT PRIMARY KEY REFERENCES events(event_id),
                severity TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open');
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def append(self, event):
        event = SecurityEvent.model_validate(event)
        if event.kind == 'forbidden_commit' and not (event.attempted and event.committed and not event.blocked):
            raise ValueError('Forbidden commit needs attempted/committed flags')
        if event.kind == 'blocked_attempt' and not (event.attempted and event.blocked and not event.committed):
            raise ValueError('Blocked attempt needs attempted/blocked flags')
        if event.committed and event.kind != 'forbidden_commit' or event.blocked and event.kind != 'blocked_attempt':
            raise ValueError('Outcome flags must match incident kind')
        payload = json.dumps(event.model_dump(), sort_keys=True)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT seq,payload FROM events WHERE event_id=?', (event.event_id,)).fetchone()
            if previous:
                if previous['payload'] != payload:
                    raise ValueError('Conflicting event ID')
                return {'seq': previous['seq'], 'duplicate': True}
            cursor = db.execute('INSERT INTO events(event_id,received_at,payload) VALUES(?,?,?)', (event.event_id, now(), payload))
            severity = SEVERITY.get(event.kind)
            if severity:
                db.execute('INSERT INTO incidents(event_id,severity) VALUES(?,?)', (event.event_id, severity))
            return {'seq': cursor.lastrowid, 'duplicate': False}

    def snapshot(self):
        with self.connect() as db:
            rows = db.execute('SELECT e.*,i.severity,i.status FROM events e LEFT JOIN incidents i USING(event_id) ORDER BY seq DESC LIMIT 100').fetchall()
            incidents = db.execute('SELECT e.*,i.severity,i.status FROM incidents i JOIN events e USING(event_id) ORDER BY seq DESC LIMIT 100').fetchall()
            counts = dict(db.execute('SELECT severity,count(*) FROM incidents GROUP BY severity').fetchall())
            total = db.execute('SELECT count(*) FROM events').fetchone()[0]
        def unpack(row):
            return {**json.loads(row['payload']), 'seq': row['seq'], 'received_at': row['received_at'], 'severity': row['severity'], 'status': row['status']}
        return {'serverTime': now(), 'totalEvents': total, 'incidentCounts': counts,
                'events': [unpack(r) for r in rows], 'incidents': [unpack(r) for r in incidents],
                'notifications': 'local_only', 'limit': 100}

    def run_events(self, run_id):
        with self.connect() as db:
            rows = db.execute('SELECT received_at,payload FROM events WHERE json_extract(payload,\'$.run_id\')=? ORDER BY seq', (run_id,)).fetchall()
        return [{'received_at': row['received_at'], **json.loads(row['payload'])} for row in rows]
