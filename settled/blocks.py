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
    actions = [
        {"type": "button", "action_id": "ratify_btn", "style": "primary",
         "text": {"type": "plain_text", "text": "✅ Settle"}, "value": str(decision_id)},
        {"type": "button", "action_id": "dismiss_btn", "style": "danger",
         "text": {"type": "plain_text", "text": "❌ Dismiss"}, "value": str(decision_id)},
        {"type": "button", "action_id": "view_decision",
         "text": {"type": "plain_text", "text": "Details"}, "value": str(decision_id)},
    ]
    if permalink:
        actions.append({"type": "button", "text": {"type": "plain_text", "text": "🔗 Source"},
                        "url": permalink, "action_id": "open_source"})
    return [
        {"type": "section", "text": {"type": "mrkdwn",
         "text": f"*Looks like a decision* (confidence {confidence:.0%}). "
                 f"A human settles it — click below, or react "
                 f":{config.RATIFY_EMOJI}:/:{config.REJECT_EMOJI}:."}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f">>> {quote}"}},
        {"type": "actions", "block_id": f"ratify:{decision_id}", "elements": actions},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"_ledger #{decision_id}_ · status: {status_label('proposed')}"}]},
    ]


def outcome_blocks(status: str, statement: str, by_user: str, superseded=None) -> list[dict]:
    """Replaces the prompt's buttons after a human acts, so the thread shows the result."""
    if status == "settled":
        head = f"✅ *Settled* by {owner_label(by_user)}"
        if superseded:
            head += f" · superseded {', '.join('#' + str(s) for s in superseded)}"
    elif status == "rejected":
        head = f"❌ *Dismissed* by {owner_label(by_user)} — not recorded as a decision."
    else:
        head = f"↩️ *Reopened* by {owner_label(by_user)} — back to proposed."
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{head}\n>>> {statement}"}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": status_label(status)}]},
    ]


def decision_modal(detail: dict) -> dict:
    """Full decision detail (status, verbatim anchors, source, relations) in a modal."""
    d = detail["decision"]
    blocks = [{"type": "section", "text": {"type": "mrkdwn",
               "text": f"*{status_label(d['status'])}*\n{d['statement']}"}}]
    for a in detail.get("anchors", []):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f">>> {a['quote']}"}})
        src = f" · <{a['permalink']}|source>" if a.get("permalink") else ""
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn",
                       "text": f"by {owner_label(d.get('owner_user'))} · {d['updated_ts'][:10]}{src}"}]})
    edges = detail.get("edges", [])
    if edges:
        rels = []
        for e in edges:
            other = e["to_id"] if e["from_id"] == d["id"] else e["from_id"]
            rels.append(f"{e['type']} #{other}")
        blocks.append({"type": "divider"})
        blocks.append({"type": "context", "elements": [
            {"type": "mrkdwn", "text": "relations: " + ", ".join(rels)}]})
    return {"type": "modal", "title": {"type": "plain_text", "text": "Decision detail"},
            "close": {"type": "plain_text", "text": "Close"}, "blocks": blocks}


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
                       "text": "*Awaiting ratification* — one click settles it:"}})
        for d in awaiting[:8]:
            blocks.append({"type": "section",
                           "text": {"type": "mrkdwn",
                                    "text": f"🟡 {d['statement']}  ·  _#{d['id']}_  ·  conf {d['confidence']:.0%}"},
                           "accessory": {"type": "button", "action_id": "ratify_home", "style": "primary",
                                         "text": {"type": "plain_text", "text": "Ratify"}, "value": str(d['id'])}})
        blocks.append({"type": "divider"})
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Recent ledger*"}})
    for d in recent[:12]:
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn",
                                "text": f"{STATUS_EMOJI.get(d['status'], '•')} {d['statement']}  "
                                        f"·  _{d['status']}_  ·  #{d['id']}"},
                       "accessory": {"type": "button", "action_id": "view_decision",
                                     "text": {"type": "plain_text", "text": "View"}, "value": str(d['id'])}})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn",
                   "text": "Query anywhere with `/settled <topic>` · external agents can ask "
                           "`decisions://` via the MCP server."}]})
    return {"type": "home", "blocks": blocks}
