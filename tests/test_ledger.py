"""Ledger correctness — the heart of Settled. Covers the audit-found bugs."""
import sqlite3

from conftest import mk

from settled import config, ledger


# ---- topic matching (the high-severity false-merge bug) --------------------
def test_same_topic_single_token_no_false_merge():
    # "Use Postgres" normalizes to one token; must NOT collide with unrelated supersets.
    assert ledger.same_topic("postgres", "backups nightly postgres") is False
    assert ledger.same_topic("friday", "friday standup time") is False


def test_same_topic_real_supersede_still_merges():
    a = ledger.normalize_topic("Let's go with Postgres for the primary datastore")
    b = ledger.normalize_topic("Use Aurora as the primary datastore, managed Postgres")
    assert ledger.same_topic(a, b) is True


# ---- lifecycle + transition guards -----------------------------------------
def test_propose_then_ratify():
    d = mk("We'll use Redis for the cache layer")
    assert ledger.get_decision(d)["decision"]["status"] == "proposed"
    assert ledger.ratify(d, "U_H")["ok"] is True
    assert ledger.get_decision(d)["decision"]["status"] == "settled"


def test_supersede_on_ratify():
    d1 = mk("Use Postgres for the primary datastore")
    ledger.ratify(d1, "U_H")
    d2 = mk("Move the primary datastore to Aurora, managed Postgres")
    res = ledger.ratify(d2, "U_H")
    assert d1 in res["superseded"]
    assert ledger.get_decision(d1)["decision"]["status"] == "superseded"


def test_cannot_resurrect_superseded():
    d1 = mk("Use Postgres for the primary datastore"); ledger.ratify(d1, "U_H")
    d2 = mk("Move the primary datastore to Aurora, managed Postgres"); ledger.ratify(d2, "U_H")
    # d1 is superseded; ratifying it again must be refused, not resurrect it
    assert ledger.ratify(d1, "U_H")["ok"] is False
    assert ledger.get_decision(d1)["decision"]["status"] == "superseded"


def test_reject_guard():
    d = mk("We'll use Redis for the cache layer"); ledger.ratify(d, "U_H")
    assert ledger.reject(d, "U_H")["ok"] is False  # can't reject a settled decision


# ---- dedup ------------------------------------------------------------------
def test_has_quote_normalized():
    mk("Final call: we ship Tuesday", quote="Final call: we ship Tuesday")
    assert ledger.has_quote("final call:   we ship tuesday") is True  # case/space-insensitive
    assert ledger.has_quote("something else entirely") is False


# ---- audit chain ------------------------------------------------------------
def test_audit_chain_valid():
    d = mk("We'll use Redis for the cache layer"); ledger.ratify(d, "U_H")
    assert ledger.verify_chain()["ok"] is True


def test_audit_chain_detects_tampering():
    d = mk("We'll use Redis for the cache layer"); ledger.ratify(d, "U_H")
    # Tamper by raw SQL bypassing the app. The append-only triggers block UPDATE on
    # audit_log, so tampering requires removing them first — verify_chain still catches it.
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("DROP TRIGGER IF EXISTS audit_no_update")
    conn.execute("UPDATE audit_log SET payload='{\"x\":1}' WHERE id=(SELECT MIN(id) FROM audit_log)")
    conn.commit(); conn.close()
    res = ledger.verify_chain()
    assert res["ok"] is False and "row" in res


def test_audit_log_append_only_trigger():
    mk("We'll use Redis for the cache layer")
    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.execute("DELETE FROM audit_log")
        assert False, "DELETE on audit_log should be blocked"
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


# ---- unratify (reversibility) ----------------------------------------------
def test_unratify_restores_superseded():
    d1 = mk("Use Postgres for the primary datastore"); ledger.ratify(d1, "U_H")
    d2 = mk("Move the primary datastore to Aurora, managed Postgres"); ledger.ratify(d2, "U_H")
    res = ledger.unratify(d2, "U_H")
    assert res["ok"] and d1 in res["restored"]
    assert ledger.get_decision(d1)["decision"]["status"] == "settled"
    assert ledger.get_decision(d2)["decision"]["status"] == "proposed"


# ---- query ------------------------------------------------------------------
def test_query_two_char_topic():
    d = mk("Standardize CI on GitHub Actions"); ledger.ratify(d, "U_H")
    hits = [r for r in ledger.query("CI") if r["status"] == "settled"]
    assert hits and hits[0]["statement"] == "Standardize CI on GitHub Actions"


def test_query_newest_first_on_tie():
    import time
    # different topics (no supersede) that both contain "builds" -> equal score
    a = mk("Run nightly builds on Jenkins"); ledger.ratify(a, "U_H")
    time.sleep(0.01)  # guarantee distinct updated_ts
    b = mk("Cache builds with Bazel remote"); ledger.ratify(b, "U_H")
    res = ledger.query("builds")
    assert {r["id"] for r in res} == {a, b}
    assert res[0]["id"] == b  # newest first on equal score
