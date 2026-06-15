"""Test config: isolated temp DB, keyless (no network), fresh schema per test."""
import os
import pathlib
import tempfile

# Must be set BEFORE importing settled.config (it reads DB_PATH / provider at import).
_DB = pathlib.Path(tempfile.gettempdir()) / "settled_pytest.db"
os.environ["SETTLED_DB_PATH"] = str(_DB)
os.environ["SETTLED_LLM_PROVIDER"] = "stub"          # never hit a network in tests
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("SLACK_APP_TOKEN", "xapp-test")

import pytest  # noqa: E402

from settled import db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Clean slate before every test (DROP works around the append-only audit trigger)."""
    for suffix in ("", "-wal", "-shm"):
        p = pathlib.Path(str(_DB) + suffix)
        if p.exists():
            p.unlink()
    with db.cursor() as c:
        for t in ("edges", "ratifications", "anchors", "decisions", "audit_log"):
            c.execute(f"DROP TABLE IF EXISTS {t}")
    db.init_db()
    yield


def mk(statement, quote=None, owner="U_A", channel="C", conf=0.9):
    from settled import ledger
    return ledger.create_candidate(
        statement=statement, quote=quote or statement, permalink="https://x/p1",
        message_ts="1.0", channel_id=channel, author_user=owner, confidence=conf)
