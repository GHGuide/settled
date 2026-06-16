"""Block Kit builders — structure + interactivity."""
from conftest import mk

from settled import blocks, ledger


def _action_ids(block):
    return [e.get("action_id") for e in block.get("elements", [])]


def test_ratification_prompt_has_buttons():
    bl = blocks.ratification_prompt(1, "Use Aurora", "Use Aurora", 0.9, "https://x/p")
    actions = [b for b in bl if b["type"] == "actions"]
    assert actions, "prompt must have an interactive actions block"
    ids = _action_ids(actions[0])
    assert "ratify_btn" in ids and "dismiss_btn" in ids and "view_decision" in ids


def test_app_home_buttons():
    d = mk("Move datastore to Aurora")
    home = blocks.app_home(ledger.counts(), ledger.awaiting_ratification(), ledger.all_decisions())
    assert home["type"] == "home"
    accessories = [b.get("accessory", {}).get("action_id") for b in home["blocks"] if b.get("accessory")]
    assert "ratify_home" in accessories  # awaiting item is ratifiable inline
    assert "view_decision" in accessories  # recent item opens detail


def test_decision_modal_builds():
    d = mk("Ship onboarding in Q3"); ledger.ratify(d, "U_H")
    modal = blocks.decision_modal(ledger.get_decision(d))
    assert modal["type"] == "modal" and modal["blocks"]


def test_outcome_blocks():
    assert blocks.outcome_blocks("settled", "x", "U_H", [2])[0]["type"] == "section"
    assert "Dismissed" in blocks.outcome_blocks("rejected", "x", "U_H")[0]["text"]["text"]
