"""Bolt app (Socket Mode). Wires Slack events to the ledger. No business logic
lives here beyond glue — extraction and lifecycle are in their own modules."""
import logging

from slack_bolt import App, Assistant

from . import agent, blocks, config, db, extraction, ledger

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("settled")

app = App(token=config.SLACK_BOT_TOKEN, signing_secret=config.SLACK_SIGNING_SECRET)

# ----------------------------------------------------------- assistant surface
assistant = Assistant()


@assistant.thread_started
def assistant_started(say, set_suggested_prompts):
    say("Hi — I'm *Settled*, your decision ledger. Ask me what's binding, contested, "
        "or still open. I answer only from human-ratified decisions.")
    set_suggested_prompts(prompts=[{"title": p, "message": p}
                                   for p in agent.SUGGESTED_PROMPTS])


@assistant.user_message
def assistant_message(payload, say, set_status):
    set_status("checking the ledger…")
    say(agent.answer_question(payload.get("text", "")))


app.use(assistant)


def _permalink(client, channel: str, ts: str) -> str:
    try:
        r = client.chat_getPermalink(channel=channel, message_ts=ts)
        return r.get("permalink", "")
    except Exception as e:  # noqa: BLE001
        log.warning("permalink failed: %s", e)
        return ""


@app.event("app_mention")
def on_mention(event, client, say):
    """@Settled in a channel — conversational answer in-thread."""
    import re as _re

    question = _re.sub(r"<@[^>]+>", "", event.get("text", "")).strip()
    say(text=agent.answer_question(question),
        thread_ts=event.get("thread_ts") or event["ts"])


def _recent_context(client, channel: str, ts: str, thread_ts: str | None) -> str:
    """Last few messages before this one, so contextual decisions resolve."""
    try:
        if thread_ts:
            r = client.conversations_replies(channel=channel, ts=thread_ts, limit=8)
        else:
            r = client.conversations_history(channel=channel, latest=ts, limit=6, inclusive=False)
        msgs = list(reversed(r.get("messages", [])))  # oldest first
        lines = []
        for m in msgs:
            if m.get("ts") == ts or m.get("subtype"):
                continue
            who = m.get("user") or m.get("username") or "user"
            txt = (m.get("text") or "").strip().replace("\n", " ")
            if txt:
                lines.append(f"{who}: {txt}"[:200])
        return "\n".join(lines[-6:])
    except Exception:  # noqa: BLE001
        return ""


@app.event("message")
def on_message(event, client, logger):
    # Ignore bot messages, edits, joins, DMs (assistant handles those), etc.
    if event.get("subtype") or event.get("bot_id") or event.get("channel_type") == "im":
        return
    text = event.get("text", "")
    channel = event["channel"]
    ts = event["ts"]
    user = event.get("user")

    context = _recent_context(client, channel, ts, event.get("thread_ts"))
    candidates = extraction.extract(text, context)
    if not candidates:
        return  # silent — noise gate / below confidence

    permalink = _permalink(client, channel, ts)
    for candidate in candidates:
        if ledger.has_quote(candidate.quote):
            continue  # dedup — already recorded
        did = ledger.create_candidate(
            statement=candidate.statement, quote=candidate.quote, permalink=permalink,
            message_ts=ts, channel_id=channel, author_user=user, confidence=candidate.confidence,
        )
        posted = client.chat_postMessage(
            channel=channel, thread_ts=ts,
            blocks=blocks.ratification_prompt(did, candidate.statement, candidate.quote,
                                              candidate.confidence, permalink),
            text="Looks like a decision — react ✅ to settle it.",
        )
        ledger.set_ratify_msg_ts(did, posted["ts"])
        for emoji in (config.RATIFY_EMOJI, config.REJECT_EMOJI):
            try:
                client.reactions_add(channel=channel, timestamp=posted["ts"], name=emoji)
            except Exception:  # noqa: BLE001
                pass


def _handle_reaction(event, client, ratify: bool):
    item = event.get("item", {})
    msg_ts = item.get("ts")
    if not msg_ts:
        return
    row = ledger.find_by_ratify_msg(msg_ts)
    if not row:
        return
    user = event.get("user")
    if ratify:
        res = ledger.ratify(row["id"], user)
        note = "✅ *Settled.*"
        if res.get("superseded"):
            note += f" Superseded prior decision(s): {res['superseded']}."
    else:
        ledger.reject(row["id"], user)
        note = "❌ Dismissed — not recorded as a decision."
    try:
        client.chat_postMessage(channel=item["channel"], thread_ts=msg_ts, text=note)
    except Exception:  # noqa: BLE001
        pass
    _publish_home(client, user)


@app.event("reaction_added")
def on_reaction_added(event, client):
    name = event.get("reaction")
    if name == config.RATIFY_EMOJI:
        _handle_reaction(event, client, ratify=True)
    elif name == config.REJECT_EMOJI:
        _handle_reaction(event, client, ratify=False)


@app.command("/settled")
def on_settled(ack, command, respond):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        respond("Usage: `/settled <topic>` — e.g. `/settled postgres vs mongo`")
        return
    results = ledger.query(text)
    respond(blocks=blocks.query_result(text, results), text=f"Decisions for {text}")


def _publish_home(client, user_id: str):
    try:
        client.views_publish(
            user_id=user_id,
            view=blocks.app_home(ledger.counts(), ledger.awaiting_ratification(),
                                 ledger.all_decisions()),
        )
    except Exception as e:  # noqa: BLE001
        log.warning("home publish failed: %s", e)


@app.event("app_home_opened")
def on_home_opened(event, client):
    _publish_home(client, event["user"])


def build() -> App:
    db.init_db()
    return app
