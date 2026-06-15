"""Seed the ledger with realistic, backdated decision lifecycles so the demo,
`/settled`, App Home, and the MCP server all show a story:

  - #platform: Postgres -> (debated) -> Mongo settled -> SUPERSEDED by Aurora
  - #platform: a still-contested auth decision
  - #design:   a cleanly settled decision
  - #ops:      a proposal still awaiting ratification

Seeds straight into SQLite with backdated timestamps and a valid audit chain, so
it works without posting to Slack. Run:  python -m seed.seed_demo
"""
from settled import db, ledger

# (statement, quote, status, owner, channel, days_ago, permalink)
DECISIONS = [
    ("Use Postgres for the primary datastore",
     "Let's go with Postgres for the primary datastore — mature and the team knows it.",
     "superseded", "U_DANA", "C_PLATFORM", 60,
     "https://settledco.slack.com/archives/C_PLATFORM/p1001"),
    ("Switch primary datastore to MongoDB",
     "Final call: we're going with MongoDB, the document model fits our access patterns.",
     "superseded", "U_SAM", "C_PLATFORM", 45,
     "https://settledco.slack.com/archives/C_PLATFORM/p1002"),
    ("Move primary datastore to Aurora",
     "Decision: we'll use Aurora as the primary datastore — managed Postgres, scales better.",
     "settled", "U_DANA", "C_PLATFORM", 20,
     "https://settledco.slack.com/archives/C_PLATFORM/p1003"),
    ("Adopt OAuth via Okta for SSO",
     "We should go with Okta for SSO across all internal tools.",
     "contested", "U_PRIYA", "C_PLATFORM", 14,
     "https://settledco.slack.com/archives/C_PLATFORM/p1004"),
    ("Use Auth0 for SSO instead of Okta",
     "Counter-proposal: we'll use Auth0 — cheaper at our seat count and faster to wire up.",
     "contested", "U_SAM", "C_PLATFORM", 12,
     "https://settledco.slack.com/archives/C_PLATFORM/p1005"),
    ("Ship the new onboarding flow in the Q3 release",
     "Agreed: we're going to ship the redesigned onboarding flow in the Q3 release.",
     "settled", "U_MAYA", "C_DESIGN", 10,
     "https://settledco.slack.com/archives/C_DESIGN/p1006"),
    ("Move standups to async in Slack",
     "Plan is to move daily standups to async threads in #ops — fewer meetings.",
     "proposed", "U_LEO", "C_OPS", 2,
     "https://settledco.slack.com/archives/C_OPS/p1007"),
]


def _insert(c, statement, quote, status, owner, channel, days_ago, permalink):
    from datetime import datetime, timedelta, timezone

    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    topic = ledger.normalize_topic(statement)
    cur = c.execute(
        "INSERT INTO decisions (topic, statement, status, owner_user, channel_id, "
        "confidence, created_ts, updated_ts) VALUES (?,?,?,?,?,?,?,?)",
        (topic, statement, status, owner, channel, 0.9, ts, ts),
    )
    did = cur.lastrowid
    c.execute(
        "INSERT INTO anchors (decision_id, quote, permalink, message_ts, channel_id, author_user) "
        "VALUES (?,?,?,?,?,?)",
        (did, quote, permalink, ts, channel, owner),
    )
    ledger.audit(c, actor=owner, action="seed", decision_id=did,
                 payload={"status": status, "statement": statement})
    return did


def main() -> None:
    # Clean slate via DROP (not DELETE): audit_log is append-only (DELETE blocked by a
    # trigger), and DROP avoids leaving orphaned audit rows / a dangling hash chain.
    with db.cursor() as c:
        for t in ("edges", "ratifications", "anchors", "decisions", "audit_log"):
            c.execute(f"DROP TABLE IF EXISTS {t}")
    db.init_db()  # recreate schema + triggers fresh
    with db.cursor() as c:
        ids = [_insert(c, *d) for d in DECISIONS]
        # Wire the supersede chain: Postgres -> Mongo -> Aurora.
        pg, mongo, aurora = ids[0], ids[1], ids[2]
        okta, auth0 = ids[3], ids[4]
        now = ledger._now()
        for frm, to in [(mongo, pg), (aurora, mongo)]:
            c.execute("INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                      (frm, to, "supersedes", now))
        c.execute("INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                  (auth0, okta, "contests", now))
        c.execute("INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                  (okta, auth0, "contests", now))
    print("Seeded demo ledger:", len(DECISIONS), "decisions.")


if __name__ == "__main__":
    main()
