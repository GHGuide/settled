"""Conversational agent: grounded Q&A over the decision ledger.

The agent answers ONLY from the ledger snapshot (statements, statuses, verbatim
anchors, permalinks). At demo scale the full snapshot fits in one prompt, which
beats keyword retrieval for robustness — judges can ask in their own words.
"""
import json

from . import blocks, ledger, llm

SUGGESTED_PROMPTS = [
    "What's our current datastore decision?",
    "Is anything still contested?",
    "What did we decide about SSO?",
    "Which decisions are awaiting ratification?",
]


def _snapshot_json(limit: int = 100) -> str:
    rows = ledger.decisions_with_anchors(limit)
    compact = []
    for r in rows:
        a = r.get("anchor") or {}
        compact.append({
            "id": r["id"],
            "statement": r["statement"],
            "status": r["status"],
            "owner": blocks.SEED_NAMES.get(r.get("owner_user") or "", r.get("owner_user")),
            "updated": (r.get("updated_ts") or "")[:10],
            "quote": a.get("quote"),
            "permalink": a.get("permalink"),
        })
    return json.dumps(compact, ensure_ascii=False)


def answer_question(question: str) -> str:
    question = (question or "").strip()
    if not question:
        return ("Ask me about any decision — e.g. _\"what's our datastore choice?\"_ "
                "I answer only from the ratified ledger.")
    return llm.answer(question, _snapshot_json())
