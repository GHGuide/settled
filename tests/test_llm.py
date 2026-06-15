"""LLM layer: gates + parsing robustness (no network — pure functions)."""
from settled import llm


def test_pre_filter_keeps_short_decisions():
    assert llm.pre_filter("ship it") is True          # was wrongly dropped by len<8
    assert llm.pre_filter("Aurora it is") is True


def test_pre_filter_drops_fluff():
    assert llm.pre_filter("lol") is False
    assert llm.pre_filter("👍") is False
    assert llm.pre_filter("ok") is False


def test_pre_filter_terse_approval_needs_context():
    assert llm.pre_filter("+1") is False
    assert llm.pre_filter("+1", context="prev: use Aurora?") is True
    assert llm.pre_filter("lol", context="anything") is False  # fluff still dropped


def test_parse_verbatim_only_no_fabrication():
    msg = "Final call: we're going with Aurora for the datastore."
    # non-verbatim quote must be dropped, never replaced with a different sentence
    out = llm._parse('{"decisions":[{"confidence":0.9,"quote":"we picked Mongo","statement":"x"}]}', msg)
    assert out == []


def test_parse_accepts_verbatim_and_clamps_confidence():
    msg = "Final call: we're going with Aurora for the datastore."
    out = llm._parse(
        'noise {"decisions":[{"confidence":1.7,"quote":"going with Aurora for the datastore","statement":"Aurora"}]} tail',
        msg)
    assert len(out) == 1
    assert out[0].confidence == 1.0           # clamped to [0,1]
    assert out[0].quote in msg                # verbatim


def test_stub_precision():
    assert llm._stub("it is raining today") == []          # no bare "it is" false positive
    assert llm._stub("maybe we should use redis?") == []   # hedge + question
    assert len(llm._stub("Final call: we ship it")) >= 1
