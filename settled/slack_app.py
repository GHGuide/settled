"""Bolt app (Socket Mode). Wires Slack events to the ledger. No business logic
lives here beyond glue — extraction and lifecycle are in their own modules."""
import logging

from slack_bolt import App, Assistant

from . import agent, blocks, config, db, extraction, ledger

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("settled")

# token_verification_enabled=False: don't make a live auth.test call at import time
# (keeps the module importable for tests/offline; the token is really validated when
# Socket Mode connects in run.py, and presence is checked by config.require_runtime()).
app = App(token=config.SLACK_BOT_TOKEN, signing_secret=config.SLACK_SIGNING_SECRET,
          token_verification_enabled=False)

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
    # Ignore bot messages (incl. our own), edits/joins/etc, and DMs (assistant handles those).
    if event.get("subtype") or event.get("bot_id") or event.get("channel_type") == "im":
        return
    text = event.get("text", "")
    channel = event["channel"]
    ts = event["ts"]
    user = event.get("user")

    try:
        context = _recent_context(client, channel, ts, event.get("thread_ts"))
        candidates = extraction.extract(text, context)
    except Exception as e:  # noqa: BLE001 — never let detection crash the listener
        log.warning("extraction failed in %s: %s", channel, e)
        return
    if not candidates:
        return  # silent — noise gate / below confidence

    permalink = _permalink(client, channel, ts)
    for candidate in candidates:
        try:
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
                except Exception as e:  # noqa: BLE001 — pre-seeding reactions is best-effort
                    log.debug("reactions_add failed: %s", e)
        except Exception as e:  # noqa: BLE001 — one bad candidate must not drop the rest
            log.warning("failed to record candidate in %s: %s", channel, e)


def _is_self(event, context) -> bool:
    """True if the reactor is our own bot (we pre-seed ✅/❌) — must never self-ratify."""
    return bool(context) and event.get("user") == context.get("bot_user_id")


def _handle_reaction(event, client, context, ratify: bool):
    if _is_self(event, context):
        return  # the bot's own pre-seeded reaction must not count as a human vote
    item = event.get("item", {})
    msg_ts = item.get("ts")
    if not msg_ts:
        return
    row = ledger.find_by_ratify_msg(msg_ts, item.get("channel"))
    if not row:
        return
    user = event.get("user")
    if ratify:
        res = ledger.ratify(row["id"], user)
        if not res.get("ok"):
            return
        note = "✅ *Settled.*"
        if res.get("superseded"):
            note += f" Superseded prior decision(s): {res['superseded']}."
    else:
        res = ledger.reject(row["id"], user)
        if not res.get("ok"):
            return
        note = "❌ Dismissed — not recorded as a decision."
    try:
        client.chat_postMessage(channel=item["channel"], thread_ts=msg_ts, text=note)
    except Exception as e:  # noqa: BLE001
        log.warning("reaction note post failed: %s", e)
    _publish_home(client, user)


@app.event("reaction_added")
def on_reaction_added(event, client, context):
    name = event.get("reaction")
    if name == config.RATIFY_EMOJI:
        _handle_reaction(event, client, context, ratify=True)
    elif name == config.REJECT_EMOJI:
        _handle_reaction(event, client, context, ratify=False)


@app.event("reaction_removed")
def on_reaction_removed(event, client, context):
    """Removing your ✅ reverses the ratification (restores anything it superseded),
    so an accidental settle is recoverable rather than permanent."""
    if _is_self(event, context) or event.get("reaction") != config.RATIFY_EMOJI:
        return
    item = event.get("item", {})
    row = ledger.find_by_ratify_msg(item.get("ts"), item.get("channel"))
    if not row:
        return
    res = ledger.unratify(row["id"], event.get("user"))
    if not res.get("ok"):
        return
    try:
        msg = "↩️ Ratification withdrawn — back to *proposed*."
        if res.get("restored"):
            msg += f" Restored prior decision(s): {res['restored']}."
        client.chat_postMessage(channel=item["channel"], thread_ts=item.get("ts"), text=msg)
    except Exception as e:  # noqa: BLE001
        log.warning("unratify note post failed: %s", e)
    _publish_home(client, event.get("user"))


# ----------------------------------------------------- interactive buttons / modal
def _act_on_prompt(body, client, ratify: bool):
    did = int(body["actions"][0]["value"])
    user = body["user"]["id"]
    detail = ledger.get_decision(did)
    if not detail:
        return
    statement = detail["decision"]["statement"]
    if ratify:
        res = ledger.ratify(did, user)
        if not res.get("ok"):
            return
        blks = blocks.outcome_blocks("settled", statement, user, res.get("superseded"))
    else:
        res = ledger.reject(did, user)
        if not res.get("ok"):
            return
        blks = blocks.outcome_blocks("rejected", statement, user)
    ch = (body.get("container") or {}).get("channel_id") or (body.get("channel") or {}).get("id")
    ts = (body.get("container") or {}).get("message_ts") or (body.get("message") or {}).get("ts")
    try:
        client.chat_update(channel=ch, ts=ts, blocks=blks, text="Decision updated.")
    except Exception as e:  # noqa: BLE001
        log.warning("chat_update failed: %s", e)
    _publish_home(client, user)


@app.action("ratify_btn")
def on_ratify_btn(ack, body, client):
    ack()
    _act_on_prompt(body, client, ratify=True)


@app.action("dismiss_btn")
def on_dismiss_btn(ack, body, client):
    ack()
    _act_on_prompt(body, client, ratify=False)


@app.action("ratify_home")
def on_ratify_home(ack, body, client):
    ack()
    did = int(body["actions"][0]["value"])
    user = body["user"]["id"]
    ledger.ratify(did, user)
    _publish_home(client, user)


@app.action("view_decision")
def on_view_decision(ack, body, client):
    ack()
    detail = ledger.get_decision(int(body["actions"][0]["value"]))
    if not detail:
        return
    try:
        client.views_open(trigger_id=body["trigger_id"], view=blocks.decision_modal(detail))
    except Exception as e:  # noqa: BLE001
        log.warning("views_open failed: %s", e)


@app.action("open_source")
def on_open_source(ack):
    ack()  # URL button — Slack opens the link; just ack the interaction


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
