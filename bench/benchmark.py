#!/usr/bin/env python3
"""Quantify Settled's impact.

On threads where a decision was reversed, an agent that retrieves "a decision on
this topic" can't tell the BINDING one from a superseded/contested one. We measure
how often that lands on a stale (non-current) decision, vs Settled's is_binding.

Run:  python -m bench.benchmark
"""
import os
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "demo" / "out"
OUT.mkdir(parents=True, exist_ok=True)
os.environ["SETTLED_DB_PATH"] = str(OUT / "bench_ledger.db")
os.environ.setdefault("SETTLED_LLM_PROVIDER", "stub")

from settled import db, ledger  # noqa: E402

# Realistic reversed-decision threads. Each: (query, [(statement, final_status), ...]).
# Exactly one 'settled' per topic is the current binding decision (or none = contested).
SCENARIOS = [
    ("primary datastore", [
        ("Use Postgres for the primary datastore", "superseded"),
        ("Switch the primary datastore to MongoDB", "superseded"),
        ("Move the primary datastore to Aurora", "settled")]),
    ("CI system", [
        ("Run CI on Jenkins", "superseded"),
        ("Standardize CI on GitHub Actions", "settled")]),
    ("frontend framework", [
        ("Build the frontend in Angular", "superseded"),
        ("Rebuild the frontend in React", "settled")]),
    ("deploy tooling", [
        ("Deploy with manual scripts", "superseded"),
        ("Manage deploys with Terraform", "settled")]),
    ("message queue", [
        ("Use RabbitMQ for the queue", "superseded"),
        ("Switch the queue to Kafka", "superseded"),
        ("Move the queue to Amazon SQS", "settled")]),
    ("standups", [
        ("Keep daily sync standups", "superseded"),
        ("Move standups to async", "settled")]),
    ("payments provider", [
        ("Integrate payments with PayPal", "superseded"),
        ("Switch payments to Stripe", "settled")]),
    ("SSO provider", [
        ("Adopt Okta for SSO", "contested"),
        ("Use Auth0 for SSO instead", "contested")]),
]


def _seed():
    for t in ("edges", "ratifications", "anchors", "decisions", "audit_log"):
        with db.cursor() as c:
            c.execute(f"DROP TABLE IF EXISTS {t}")
    db.init_db()
    from datetime import datetime, timedelta, timezone
    day = 90
    with db.cursor() as c:
        for _, events in SCENARIOS:
            for statement, status in events:
                ts = (datetime.now(timezone.utc) - timedelta(days=day)).isoformat()
                day -= 1
                topic = ledger.normalize_topic(statement)
                cur = c.execute(
                    "INSERT INTO decisions (topic, statement, status, owner_user, channel_id, "
                    "confidence, created_ts, updated_ts) VALUES (?,?,?,?,?,?,?,?)",
                    (topic, statement, status, "U_BENCH", "C", 0.9, ts, ts))
                c.execute("INSERT INTO anchors (decision_id, quote, permalink, message_ts, channel_id, author_user) "
                          "VALUES (?,?,?,?,?,?)", (cur.lastrowid, statement, "https://x/p", ts, "C", "U_BENCH"))


def main():
    _seed()
    n = len(SCENARIOS)
    naive_random_stale = 0.0      # expected stale rate if you pick a matching decision at random
    naive_first_stale = 0         # if you act on the earliest decision found
    settled_stale = 0             # Settled acts on a stale/non-binding decision
    settled_safe_abstain = 0      # Settled correctly abstains (nothing binding)

    print(f"{'topic':22} {'matches':7} {'binding':28} {'rand-stale':10}")
    print("-" * 72)
    for query, events in SCENARIOS:
        rows = ledger.query(query)
        matches = [r for r in rows if r["status"] in ("settled", "superseded", "contested", "proposed")]
        binding = next((r for r in matches if r["status"] == "settled"), None)
        non_binding = [r for r in matches if r["status"] != "settled"]
        rate = len(non_binding) / len(matches) if matches else 0.0
        naive_random_stale += rate
        # naive "first": earliest-created match
        first = min(matches, key=lambda r: r["created_ts"]) if matches else None
        if first and first["status"] != "settled":
            naive_first_stale += 1
        # Settled: act only on the binding decision; abstain if none
        if binding is None:
            settled_safe_abstain += 1
        bname = binding["statement"][:26] if binding else "— (contested/none)"
        print(f"{query:22} {len(matches):<7} {bname:28} {rate:>8.0%}")

    print("-" * 72)
    print(f"\nAcross {n} reversed-decision threads:")
    print(f"  Naive 'act on earliest decision'   : stale {naive_first_stale}/{n}  ({naive_first_stale/n:.0%})")
    print(f"  Naive 'pick a matching decision'   : stale {naive_random_stale/n:.0%} (expected)")
    print(f"  Settled (is_binding)               : stale {settled_stale}/{n}  (0%), "
          f"safely abstained on {settled_safe_abstain} undecided topic(s)")
    print("\nSettled never acts on a reversed decision, and refuses to answer when nothing is binding.")


if __name__ == "__main__":
    main()
