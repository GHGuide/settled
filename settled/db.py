"""SQLite ledger schema + connection. Postgres-compatible SQL kept simple.

Tables
------
decisions      one row per decision-shaped moment, carries epistemic status
anchors        verbatim quote + permalink that grounds a decision (source of truth)
edges          signed relationships between decisions (supersedes / contests / relates)
ratifications  human votes from the ✅/❌ loop
audit_log      append-only, hash-chained (SHA-256(prev_hash + content + ts))
"""
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    topic         TEXT NOT NULL,              -- normalized topic key for grouping
    statement     TEXT NOT NULL,              -- short human-readable summary (display only)
    status        TEXT NOT NULL DEFAULT 'proposed',  -- proposed|contested|settled|superseded|rejected
    owner_user    TEXT,                       -- slack user id credited with the decision
    channel_id    TEXT NOT NULL,
    confidence    REAL NOT NULL DEFAULT 0,
    created_ts    TEXT NOT NULL,
    updated_ts    TEXT NOT NULL,
    ratify_msg_ts TEXT                         -- ts of the ratification prompt message
);

CREATE TABLE IF NOT EXISTS anchors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id),
    quote       TEXT NOT NULL,                 -- VERBATIM substring of the source message
    permalink   TEXT NOT NULL,
    message_ts  TEXT NOT NULL,
    channel_id  TEXT NOT NULL,
    author_user TEXT
);

CREATE TABLE IF NOT EXISTS edges (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id   INTEGER NOT NULL REFERENCES decisions(id),
    to_id     INTEGER NOT NULL REFERENCES decisions(id),
    type      TEXT NOT NULL,                   -- supersedes|contests|relates
    created_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ratifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL REFERENCES decisions(id),
    user_id     TEXT NOT NULL,
    action      TEXT NOT NULL,                 -- ratify|reject
    ts          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    actor       TEXT,
    action      TEXT NOT NULL,
    decision_id INTEGER,
    payload     TEXT,                          -- json
    prev_hash   TEXT NOT NULL,
    hash        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decisions_topic  ON decisions(topic);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_anchors_decision ON anchors(decision_id);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def cursor():
    conn = connect()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with cursor() as c:
        c.executescript(SCHEMA)
