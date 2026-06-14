"""Ledger operations — the heart of Settled.

Epistemic lifecycle:
    proposed  -> settled      (human ✅ ratifies)
    proposed  -> rejected     (human ❌ rejects)
    settled   -> superseded   (a newer settled decision on the same topic supersedes it)
    any       -> contested    (a competing decision on the same topic appears)

The model NEVER sets `settled` on its own. Only a human ✅ does. Wrong > silent.
"""
import hashlib
import json
from datetime import datetime, timezone

from . import db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_topic(text: str) -> str:
    """Cheap topic key so related decisions group together."""
    import re

    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"the", "a", "an", "we", "will", "should", "to", "for", "of", "and",
            "or", "is", "are", "use", "go", "with", "on", "in", "lets", "let",
            "our", "this", "that", "be", "it", "do", "decided", "decision"}
    keep = [w for w in words if w not in stop and len(w) > 2]
    return " ".join(sorted(set(keep))[:6]) or text.lower()[:40]


def same_topic(t1: str, t2: str) -> bool:
    """Fuzzy topic match: overlap coefficient on topic words.

    Exact-string equality is too brittle ("circleci pipelines runner" vs
    "buildkite circleci pipelines runner" must collide so supersede/contest
    edges fire). Overlap = |A∩B| / min(|A|,|B|).
    """
    a, b = set(t1.split()), set(t2.split())
    if not a or not b:
        return t1 == t2
    return len(a & b) / min(len(a), len(b)) >= 0.6


# ---------------------------------------------------------------- audit chain
def _last_hash(c) -> str:
    row = c.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    return row["hash"] if row else "0" * 64


def audit(c, actor, action, decision_id=None, payload=None) -> None:
    ts = _now()
    prev = _last_hash(c)
    body = json.dumps(payload or {}, sort_keys=True)
    digest = hashlib.sha256((prev + actor + action + str(decision_id) + body + ts).encode()).hexdigest()
    c.execute(
        "INSERT INTO audit_log (ts, actor, action, decision_id, payload, prev_hash, hash) "
        "VALUES (?,?,?,?,?,?,?)",
        (ts, actor, action, decision_id, body, prev, digest),
    )


# ------------------------------------------------------------- create / read
def create_candidate(*, statement, quote, permalink, message_ts, channel_id,
                     author_user, confidence) -> int:
    """Record a confidence-gated decision candidate as `proposed` with its anchor."""
    topic = normalize_topic(statement)
    now = _now()
    with db.cursor() as c:
        cur = c.execute(
            "INSERT INTO decisions (topic, statement, status, owner_user, channel_id, "
            "confidence, created_ts, updated_ts) VALUES (?,?,?,?,?,?,?,?)",
            (topic, statement, "proposed", author_user, channel_id, confidence, now, now),
        )
        did = cur.lastrowid
        c.execute(
            "INSERT INTO anchors (decision_id, quote, permalink, message_ts, channel_id, author_user) "
            "VALUES (?,?,?,?,?,?)",
            (did, quote, permalink, message_ts, channel_id, author_user),
        )
        # A competing proposal on the same topic contests existing settled ones.
        cand = c.execute(
            "SELECT id, topic FROM decisions WHERE id<>? AND status IN ('proposed','settled')",
            (did,),
        ).fetchall()
        rivals = [r for r in cand if same_topic(topic, r["topic"])]
        for r in rivals:
            c.execute(
                "INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                (did, r["id"], "contests", now),
            )
        audit(c, actor=author_user or "system", action="propose", decision_id=did,
              payload={"statement": statement, "confidence": confidence, "topic": topic})
        return did


def set_ratify_msg_ts(decision_id: int, msg_ts: str) -> None:
    with db.cursor() as c:
        c.execute("UPDATE decisions SET ratify_msg_ts=? WHERE id=?", (msg_ts, decision_id))


def get_decision(decision_id: int):
    with db.cursor() as c:
        d = c.execute("SELECT * FROM decisions WHERE id=?", (decision_id,)).fetchone()
        if not d:
            return None
        anchors = c.execute("SELECT * FROM anchors WHERE decision_id=?", (decision_id,)).fetchall()
        edges = c.execute(
            "SELECT * FROM edges WHERE from_id=? OR to_id=?", (decision_id, decision_id)
        ).fetchall()
        return {"decision": dict(d), "anchors": [dict(a) for a in anchors],
                "edges": [dict(e) for e in edges]}


def has_quote(quote: str) -> bool:
    """Dedup: has this exact decision already been recorded (and not rejected)?"""
    with db.cursor() as c:
        row = c.execute(
            "SELECT 1 FROM anchors a JOIN decisions d ON d.id=a.decision_id "
            "WHERE a.quote=? AND d.status<>'rejected' LIMIT 1", (quote,)).fetchone()
        return row is not None


def find_by_ratify_msg(msg_ts: str):
    with db.cursor() as c:
        return c.execute("SELECT * FROM decisions WHERE ratify_msg_ts=?", (msg_ts,)).fetchone()


# ------------------------------------------------------------- transitions
def ratify(decision_id: int, user_id: str) -> dict:
    """Human ✅ — promote proposed -> settled, and supersede prior settled rivals."""
    now = _now()
    with db.cursor() as c:
        d = c.execute("SELECT * FROM decisions WHERE id=?", (decision_id,)).fetchone()
        if not d:
            return {"ok": False, "error": "not found"}
        c.execute("INSERT INTO ratifications (decision_id, user_id, action, ts) VALUES (?,?,?,?)",
                  (decision_id, user_id, "ratify", now))
        c.execute("UPDATE decisions SET status='settled', updated_ts=? WHERE id=?", (now, decision_id))
        # Newly settled decision supersedes prior settled decisions on the same topic.
        cand = c.execute(
            "SELECT id, topic FROM decisions WHERE id<>? AND status='settled'",
            (decision_id,),
        ).fetchall()
        prior = [p for p in cand if same_topic(d["topic"], p["topic"])]
        for p in prior:
            c.execute("UPDATE decisions SET status='superseded', updated_ts=? WHERE id=?",
                      (now, p["id"]))
            c.execute("INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                      (decision_id, p["id"], "supersedes", now))
            audit(c, actor=user_id, action="supersede", decision_id=p["id"],
                  payload={"by": decision_id})
        audit(c, actor=user_id, action="ratify", decision_id=decision_id)
        return {"ok": True, "status": "settled", "superseded": [p["id"] for p in prior]}


def reject(decision_id: int, user_id: str) -> dict:
    now = _now()
    with db.cursor() as c:
        if not c.execute("SELECT 1 FROM decisions WHERE id=?", (decision_id,)).fetchone():
            return {"ok": False, "error": "not found"}
        c.execute("INSERT INTO ratifications (decision_id, user_id, action, ts) VALUES (?,?,?,?)",
                  (decision_id, user_id, "reject", now))
        c.execute("UPDATE decisions SET status='rejected', updated_ts=? WHERE id=?", (now, decision_id))
        audit(c, actor=user_id, action="reject", decision_id=decision_id)
        return {"ok": True, "status": "rejected"}


# ------------------------------------------------------------- queries
def query(text: str) -> list[dict]:
    """Find decisions relevant to a free-text query, newest first.

    Returns enriched rows with the binding anchor and supersede history so callers
    (the /settled command and the MCP server) can render the full lifecycle.
    """
    topic = normalize_topic(text)
    terms = [t for t in topic.split() if t]
    with db.cursor() as c:
        rows = c.execute("SELECT * FROM decisions ORDER BY updated_ts DESC").fetchall()
        scored = []
        for r in rows:
            hay = (r["topic"] + " " + r["statement"]).lower()
            score = sum(1 for t in terms if t in hay)
            if score:
                scored.append((score, r))
        scored.sort(key=lambda x: (-x[0], x[1]["updated_ts"]), reverse=False)
        out = []
        for _, r in sorted(scored, key=lambda x: -x[0])[:10]:
            anchor = c.execute(
                "SELECT * FROM anchors WHERE decision_id=? LIMIT 1", (r["id"],)
            ).fetchone()
            out.append({**dict(r), "anchor": dict(anchor) if anchor else None})
        return out


def counts() -> dict:
    with db.cursor() as c:
        rows = c.execute("SELECT status, COUNT(*) n FROM decisions GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}


def awaiting_ratification() -> list[dict]:
    with db.cursor() as c:
        rows = c.execute(
            "SELECT * FROM decisions WHERE status='proposed' ORDER BY created_ts ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def all_decisions(limit: int = 200) -> list[dict]:
    with db.cursor() as c:
        rows = c.execute(
            "SELECT * FROM decisions ORDER BY updated_ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def decisions_with_anchors(limit: int = 100) -> list[dict]:
    """Full ledger snapshot (decision + first anchor) for agent grounding."""
    with db.cursor() as c:
        rows = c.execute(
            "SELECT * FROM decisions ORDER BY updated_ts DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            a = c.execute("SELECT * FROM anchors WHERE decision_id=? LIMIT 1",
                          (r["id"],)).fetchone()
            out.append({**dict(r), "anchor": dict(a) if a else None})
        return out
