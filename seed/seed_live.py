"""Seed REAL Slack channels with persona-named demo threads, then rewrite the
DB ledger anchors to point at the real messages (real permalinks).

- Creates #platform #design #ops (idempotent: reuses if they exist).
- Posts decision threads via chat.postMessage with username/icon overrides
  (chat:write.customize) so the demo reads like a real team.
- Keeps the BACKDATED lifecycle dates in the DB (the story spans weeks);
  anchors point at the live messages.

Run:  python -m seed.seed_live
"""
import time

from slack_sdk import WebClient

from settled import config, db, ledger
from seed.seed_demo import DECISIONS, _insert

PERSONAS = {
    "U_DANA":  ("Dana Whitfield",  ":woman-tipping-hand:"),
    "U_SAM":   ("Sam Okafor",      ":man-raising-hand:"),
    "U_PRIYA": ("Priya Nair",      ":woman-technologist:"),
    "U_MAYA":  ("Maya Lindqvist",  ":art:"),
    "U_LEO":   ("Leo Marchetti",   ":male-office-worker:"),
}

CHANNELS = {"C_PLATFORM": "platform", "C_DESIGN": "design", "C_OPS": "ops"}

# Non-decision chatter to make threads look organic: (channel_key, persona, text)
CHATTER = [
    ("C_PLATFORM", "U_SAM",   "Postgres ops overhead is real though — who's on call for it?"),
    ("C_PLATFORM", "U_PRIYA", "Migration cost worries me, but the doc model does fit."),
    ("C_PLATFORM", "U_DANA",  "Benchmarks from the spike are in the doc, tl;dr Aurora wins on failover."),
    ("C_DESIGN",   "U_LEO",   "Onboarding mockups look great, ship it."),
]


def ensure_channel(client: WebClient, name: str) -> str:
    try:
        r = client.conversations_create(name=name)
        return r["channel"]["id"]
    except Exception:
        cursor = None
        while True:
            r = client.conversations_list(limit=200, cursor=cursor,
                                          types="public_channel")
            for ch in r["channels"]:
                if ch["name"] == name:
                    return ch["id"]
            cursor = r.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                raise RuntimeError(f"channel {name} not found")


def _retry(fn, *args, attempts=3, **kwargs):
    for i in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(2 * (i + 1))


def _existing_messages(client: WebClient, cid: str) -> dict[str, str]:
    """text -> ts for messages already in the channel (idempotent reruns)."""
    out = {}
    r = _retry(client.conversations_history, channel=cid, limit=200)
    for m in r["messages"]:
        out[m.get("text", "")] = m["ts"]
    return out


def main() -> None:
    client = WebClient(token=config.SLACK_BOT_TOKEN, timeout=60)
    db.init_db()

    chan_ids = {}
    history = {}
    for key, name in CHANNELS.items():
        cid = ensure_channel(client, name)
        chan_ids[key] = cid
        _retry(client.conversations_join, channel=cid)
        history[cid] = _existing_messages(client, cid)
        print(f"#{name} -> {cid} ({len(history[cid])} existing msgs)")

    # Post each decision's anchor message under its persona (skip if present).
    posted = []  # (index, channel_id, ts, permalink)
    for idx, (statement, quote, status, owner, chan_key, days_ago, _ph) in enumerate(DECISIONS):
        cid = chan_ids[chan_key]
        if quote in history[cid]:
            ts = history[cid][quote]
            print(f"skip  #{idx} (already posted)")
        else:
            uname, icon = PERSONAS[owner]
            r = _retry(client.chat_postMessage, channel=cid, text=quote,
                       username=uname, icon_emoji=icon)
            ts = r["ts"]
            print(f"posted #{idx}: {quote[:50]}…")
            time.sleep(1.2)
        pl = _retry(client.chat_getPermalink, channel=cid, message_ts=ts)["permalink"]
        posted.append((idx, cid, ts, pl))

    for chan_key, owner, text in CHATTER:
        cid = chan_ids[chan_key]
        if text in history[cid]:
            continue
        uname, icon = PERSONAS[owner]
        _retry(client.chat_postMessage, channel=cid, text=text,
               username=uname, icon_emoji=icon)
        time.sleep(1.2)

    # Rebuild the ledger with REAL channel ids + anchors, keeping backdated dates.
    with db.cursor() as c:
        c.execute("DELETE FROM edges")
        c.execute("DELETE FROM ratifications")
        c.execute("DELETE FROM anchors")
        c.execute("DELETE FROM decisions")
        ids = []
        for idx, (statement, quote, status, owner, chan_key, days_ago, _ph) in enumerate(DECISIONS):
            _, cid, ts, pl = posted[idx]
            row = list(DECISIONS[idx])
            did = _insert(c, statement, quote, status, owner, cid, days_ago, pl)
            c.execute("UPDATE anchors SET message_ts=? WHERE decision_id=?", (ts, did))
            ids.append(did)
        pg, mongo, aurora, okta, auth0 = ids[0], ids[1], ids[2], ids[3], ids[4]
        now = ledger._now()
        for frm, to in [(mongo, pg), (aurora, mongo)]:
            c.execute("INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                      (frm, to, "supersedes", now))
        for frm, to in [(auth0, okta), (okta, auth0)]:
            c.execute("INSERT INTO edges (from_id, to_id, type, created_ts) VALUES (?,?,?,?)",
                      (frm, to, "contests", now))
    print("Ledger rebuilt with real anchors:", len(posted), "decisions.")


if __name__ == "__main__":
    main()
