"""Extraction pipeline: noise-gate -> classify (LLM) -> confidence gate.

Recall-first: the noise gate only drops trivial messages; every substantive message is
classified. Precision is held by the LLM + the confidence gate + the human ✅ loop.
Returns a LIST of candidates (a message may hold multiple decisions).
"""
from dataclasses import dataclass

from . import config, llm


@dataclass
class Candidate:
    statement: str
    quote: str
    confidence: float


def extract(text: str, context: str = "") -> list[Candidate]:
    """Return decision candidates worth a ratification ping (may be empty)."""
    if not llm.pre_filter(text, context):
        return []
    out = []
    for e in llm.classify(text, context):
        if e.is_decision and e.quote and e.confidence >= config.CONFIDENCE_THRESHOLD:
            out.append(Candidate(statement=e.statement, quote=e.quote, confidence=e.confidence))
    return out
