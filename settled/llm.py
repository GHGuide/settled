"""LLM adapter — the ONLY place provider calls happen.

Two jobs:
  classify(message, context)  -> list[Extraction]   (per-message decision detection)
  answer(question, ledger)    -> str                (conversational assistant)

Design for real-world recall + precision:
  - The cheap pre_filter is only a NOISE gate (drops emoji/greetings/one-word noise).
    Every substantive message is sent to the classifier — recall is not gatekept by regex.
  - Precision comes from the LLM classifier + a confidence gate + the human ✅ loop.
  - Thread context is passed so contextual decisions ("yes, let's do that") resolve.
  - The classifier runs on a FAST model with a hard timeout so Slack never hangs.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass

from . import config


@dataclass
class Extraction:
    is_decision: bool
    confidence: float
    quote: str
    statement: str


# --- noise gate: skip the LLM only on obvious non-decisions (cheap) ----------
_NOISE = re.compile(
    r"^(?:\s*[\U0001F000-\U0001FAFF☀-➿]+\s*|hi|hey|hello|thanks|thank you|"
    r"ty|lol|lmao|nice|cool|ok|okay|yep|yes|no|same|\+1|👍|👀|haha|gm|gn|wfh)\s*[.!?]*$",
    re.IGNORECASE)


def pre_filter(text: str) -> bool:
    """True = worth classifying. Drops trivial noise; keeps everything substantive."""
    t = (text or "").strip()
    if len(t) < 8:
        return False
    if _NOISE.match(t):
        return False
    return True


def _best_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?\n])\s+", text.strip())
    return max(parts, key=len).strip() if parts else text.strip()


# --------------------------------------------------------------- classifier
_CLASSIFY_PROMPT = """You extract DECISIONS a team commits to, from a Slack MESSAGE. \
Recent CONTEXT is given only to resolve what the message refers to.

A decision = a commitment the team makes: "we'll use X", "going with Y", "final call: Z", \
"X it is", "ship it", "we have consensus: ...", or an explicit approval of a prior proposal. \
NOT a question, hypothesis, hedge, a defer ("let's table it", "circle back"), or a historical \
mention of an old decision.

Return STRICT JSON: {"decisions":[{"confidence":<0..1>,"quote":<string>,"statement":<string>}]}.
- A message may contain MULTIPLE decisions — return one object per decision.
- "quote" MUST be an exact verbatim substring of the MESSAGE (never paraphrase, never from context).
- "statement" is a short (<140 char) summary; you may use context to make it clear.
- Return {"decisions":[]} if there is no decision.
- Be precise. If unsure, lower confidence. A false decision is worse than a miss.

CONTEXT (recent messages, oldest first; may be empty):
{context}

MESSAGE:
\"\"\"{message}\"\"\""""


def _post_openrouter(model: str, prompt: str, max_tokens: int, timeout: float) -> str:
    payload = json.dumps({
        "model": model, "max_tokens": max_tokens, "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=payload,
        headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def _parse(raw: str, message: str) -> list[Extraction]:
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    data = json.loads(raw)
    out: list[Extraction] = []
    for d in data.get("decisions", []):
        quote = (d.get("quote") or "").strip()
        if quote and quote not in message:
            quote = _best_sentence(message)
        if not quote:
            continue
        out.append(Extraction(
            is_decision=True,
            confidence=float(d.get("confidence", 0.0)),
            quote=quote,
            statement=(d.get("statement") or quote)[:140],
        ))
    return out


def _stub(text: str) -> list[Extraction]:
    """Keyless fallback. Coarse: fires on common commitment cues."""
    cues = [r"\bfinal call\b", r"\bdecision[:\s]", r"\bwe'?ll use\b", r"\bgoing with\b",
            r"\blet'?s go with\b", r"\bagreed\b", r"\bwe'?re going to\b", r"\bit is\b",
            r"\bship it\b", r"\bconsensus\b", r"\bgoing forward\b", r"\bwe'?ve decided\b"]
    hedge = [r"\bmaybe\b", r"\bwhat if\b", r"\bcould we\b", r"\btable\b", r"\bcircle back\b", r"\?\s*$"]
    hits = sum(1 for c in cues if re.search(c, text.lower()))
    if not hits or any(re.search(h, text.lower()) for h in hedge):
        return []
    conf = max(0.0, min(0.95, 0.6 + 0.15 * hits))
    q = _best_sentence(text)
    return [Extraction(True, round(conf, 2), q, q[:140])]


def classify(text: str, context: str = "") -> list[Extraction]:
    """Detect decisions in a message. Returns a list (multi-decision). Never raises."""
    if config.LLM_PROVIDER == "openrouter" and config.OPENROUTER_API_KEY:
        try:
            prompt = _CLASSIFY_PROMPT.replace("{context}", context or "(none)").replace("{message}", text)
            raw = _post_openrouter(config.OPENROUTER_CLASSIFY_MODEL, prompt, 500, config.CLASSIFY_TIMEOUT)
            return _parse(raw, text)
        except Exception:
            return _stub(text)
    return _stub(text)


# ------------------------------------------------------------------- answer
_ANSWER_PROMPT = """You are Settled, a Slack agent that answers questions about an \
organization's DECISION LEDGER. Each decision has an epistemic status:
- settled    = ratified by a human, currently BINDING
- superseded = was binding, replaced by a newer settled decision
- contested  = competing proposals exist, NOT binding
- proposed   = awaiting human ratification, NOT binding
- rejected   = dismissed by a human

LEDGER (JSON):
{ledger}

QUESTION: {question}

Rules:
- Answer ONLY from the ledger. Never invent decisions.
- Lead with the current binding decision if one exists; include its verbatim anchor quote in a \
blockquote and its permalink as <URL|source>.
- Show lifecycle when relevant ("X superseded Y on <date>").
- If nothing is settled, say exactly that. Silence beats a wrong answer.
- Slack mrkdwn only. Under 150 words."""


def _openrouter_chat(prompt: str, max_tokens: int = 600) -> str:
    return _post_openrouter(config.OPENROUTER_MODEL, prompt, max_tokens, 45)


def answer(question: str, ledger_json: str) -> str:
    prompt = _ANSWER_PROMPT.replace("{ledger}", ledger_json).replace("{question}", question)
    if config.LLM_PROVIDER == "openrouter" and config.OPENROUTER_API_KEY:
        try:
            return _openrouter_chat(prompt)
        except Exception:
            pass
    return ("I can't reach my reasoning model right now. Try `/settled <topic>` for a "
            "direct ledger lookup.")
