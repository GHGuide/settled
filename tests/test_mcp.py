"""MCP server behaviour: binding resolution, contested surfacing, safety."""
import json

from conftest import mk

from settled import ledger
import mcp_server.server as srv


def _tool(fn, *a):
    """Call a FastMCP-decorated function whether it stayed callable or got wrapped."""
    target = getattr(fn, "fn", fn)
    return target(*a)


def test_binds_to_localhost_by_default():
    assert srv.mcp.settings.host == "127.0.0.1"  # never 0.0.0.0 by default


def test_binding_returns_newest_settled():
    d1 = mk("Use Postgres for the primary datastore"); ledger.ratify(d1, "U_H")
    d2 = mk("Move the primary datastore to Aurora, managed Postgres"); ledger.ratify(d2, "U_H")
    b = srv._binding_for("datastore")
    assert b is not None and b["id"] == d2  # the newer settled one, not the superseded


def test_is_binding_surfaces_contested():
    a = mk("Adopt Okta for SSO across internal tools")
    b = mk("Use Auth0 for SSO instead of Okta")
    # neither ratified -> not binding, but the tool should reveal they're pending/contested
    out = json.loads(_tool(srv.is_binding, "SSO"))
    assert out["binding"] is False
    assert out["status"] in ("proposed", "contested")
    assert len(out["pending"]) >= 1


def test_is_binding_true_when_settled():
    d = mk("Standardize CI on GitHub Actions"); ledger.ratify(d, "U_H")
    out = json.loads(_tool(srv.is_binding, "CI"))
    assert out["binding"] is True
    assert out["anchor_quote"] and out["permalink"]


def test_one_decision_rejects_non_integer():
    out = json.loads(_tool(srv.one_decision, "not-a-number"))
    assert "error" in out


def test_verify_audit_log_tool():
    d = mk("We'll use Redis for the cache"); ledger.ratify(d, "U_H")
    out = json.loads(_tool(srv.verify_audit_log))
    assert out["ok"] is True
