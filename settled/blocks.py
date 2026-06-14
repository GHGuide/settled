"""Block Kit builders for ratification prompts, /settled results, and App Home."""
from . import config

STATUS_EMOJI = {
    "proposed": "🟡",
    "contested": "🟠",
    "settled": "🟢",
    "superseded": "⚪",
    "rejected": "🔴",
}

# Seed personas use synthetic ids that Slack can't resolve to mentions.
SEED_NAMES = {
    "U_DANA": "Dana Whitfield",
    "U_SAM": "Sam Okafor",
    "U_PRIYA": "Priya Nair",
    "U_MAYA": "Maya Lindqvist",
    "U_LEO": "Leo Marchetti",
}


def owner_label(user_id: str | None) -> str:
    if not user_id:
        return "unknown"
    if user_id in SEED_NAMES:
        return SEED_NAMES[user_id]
    return f"<@{user_id}>"


def status_label(status: str) -> str:
    return f"{STATUS_EMOJI.get(status, '•')} {status.capitalize()}"


def ratification_prompt(decision_id: int, statement: str, quote: str,
                        confidence: float, permalink: str) -> list[dict]:
    return [
        {"type": "section", "text": {"type": "mrkdwn",
         "text": f"*Looks like a decision* (confidence {confidence:.0%}). React "
                 f":{config.RATIFY_EMOJI}: to settle it or :{config.REJECT_EMOJI}: to dismiss."}},
        {"type": "section", "text": {"type": "mrkdwn",
         "text": f">>> {quote}"}},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"<{permalink}|source> · _ledger #{decision_id}_ · "
                                       f"status: {status_label('proposed')}"}]},
    ]


def query_result(text: str, results: list[dict]) -> list[dict]:
    if not results:
        return [{"type": "section", "text": {"type": "mrkdwn",
                 "text": f"No decisions found for *{text}*. Silence beats a wrong answer — "
                         f"nothing has been settled on this yet."}}]
    blocks = [{"type": "header", "text": {"type": "plain_text",
               "text": f"Decisions: {text}"[:150]}}]
    for r in results:
        anchor = r.get("anchor") or {}
        line = f"*{status_label(r['status'])}* — {r['statement']}"
        meta = f"by {owner_label(r.get('owner_user'))} · {r['updated_ts'][:10]} · _#{r['id']}_"
        if anchor.get("permalink"):
            meta += f" · <{anchor['permalink']}|source>"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": line}})
        if anchor.get("quote"):
            blocks.append({"type": "section", "text": {"type": "mrkdwn",
                           "text": f">>> {anchor['quote']}"}})
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": meta}]})
        blocks.append({"type": "divider"})
    return blocks


def app_home(counts: dict, awaiting: list[dict], recent: list[dict]) -> dict:
    def n(k):
        return counts.get(k, 0)

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "📒 Settled — decision ledger"}},
        {"type": "section", "text": {"type": "mrkdwn",
         "text": f"{status_label('proposed')}  *{n('proposed')}* awaiting  ·  "
                 f"{status_label('contested')}  *{n('contested')}* contested  ·  "
                 f"{status_label('settled')}  *{n('settled')}* settled  ·  "
                 f"{status_label('superseded')}  *{n('superseded')}* superseded"}},
        {"type": "divider"},
    ]
    if awaiting:
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
                       "text": "*Awaiting ratification* — react ✅ in-thread to settle:"}})
        for d in awaiting[:8]:
            blocks.append({"type": "section", "text": {"type": "mrkdwn",
                           "text": f"🟡 {d['statement']}  ·  _#{d['id']}_  ·  conf {d['confidence']:.0%}"}})
        blocks.append({"type": "divider"})
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Recent ledger*"}})
    for d in recent[:12]:
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
                       "text": f"{STATUS_EMOJI.get(d['status'], '•')} {d['statement']}  "
                               f"·  _{d['status']}_  ·  #{d['id']}"}})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn",
                   "text": "Query anywhere with `/settled <topic>` · external agents can ask "
                           "`decisions://` via the MCP server."}]})
    return {"type": "home", "blocks": blocks}
