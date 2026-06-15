"""Settled MCP server — exposes the decision ledger as `decisions://` resources
plus tools any external agent (Claude, an IDE bot, CI) can call to ask
"is this still binding?" BEFORE acting.

This is Settled's qualifying technology for the hackathon: an ungated, self-built
MCP server. It depends on no gated Slack AI feature and no Real-Time Search API.

Run:  python -m mcp_server.server                    (stdio, for local agents)
      SETTLED_MCP_TRANSPORT=http python -m mcp_server.server   (network)

Security: HTTP mode binds 127.0.0.1 by default. The ledger is an org's decisions —
do NOT expose it on 0.0.0.0 without putting an authenticating reverse proxy in front.
"""
import json
import logging
import os

from mcp.server.fastmcp import FastMCP

from settled import db, ledger

log = logging.getLogger("settled.mcp")

# Default to localhost — never expose the org's decision ledger on all interfaces by accident.
_HOST = os.environ.get("SETTLED_MCP_HOST", "127.0.0.1")
mcp = FastMCP("settled", host=_HOST, port=int(os.environ.get("SETTLED_MCP_PORT", "8000")))

# Ensure tables exist even if the server is started before the bot (handlers assume schema).
try:
    db.init_db()
except Exception as e:  # noqa: BLE001
    log.warning("init_db at import failed (will retry in main): %s", e)


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)})


def _binding_for(topic_query: str):
    """The current binding decision for a topic = NEWEST `settled`, not superseded."""
    settled = [r for r in ledger.query(topic_query) if r["status"] == "settled"]
    if not settled:
        return None
    return max(settled, key=lambda r: r["updated_ts"])  # truly newest, not first-by-score


# ------------------------------------------------------------------ resources
@mcp.resource("decisions://all")
def all_decisions() -> str:
    """Every decision in the ledger with its epistemic status + verbatim anchor."""
    try:
        return json.dumps(ledger.decisions_with_anchors(), indent=2)
    except Exception as e:  # noqa: BLE001
        return _err(e)


@mcp.resource("decisions://settled")
def settled_decisions() -> str:
    """Only currently-settled (binding) decisions, with anchor quote + permalink."""
    try:
        rows = [d for d in ledger.decisions_with_anchors() if d["status"] == "settled"]
        return json.dumps(rows, indent=2)
    except Exception as e:  # noqa: BLE001
        return _err(e)


@mcp.resource("decisions://awaiting")
def awaiting() -> str:
    """Decisions proposed but not yet ratified by a human."""
    try:
        return json.dumps(ledger.awaiting_ratification(), indent=2)
    except Exception as e:  # noqa: BLE001
        return _err(e)


@mcp.resource("decisions://{decision_id}")
def one_decision(decision_id: str) -> str:
    """A single decision with its verbatim anchor(s) and supersede edges."""
    try:
        did = int(decision_id)
    except (TypeError, ValueError):
        return json.dumps({"error": f"decision_id must be an integer, got {decision_id!r}"})
    try:
        d = ledger.get_decision(did)
        return json.dumps(d, indent=2) if d else json.dumps({"error": "not found"})
    except Exception as e:  # noqa: BLE001
        return _err(e)


# ---------------------------------------------------------------------- tools
@mcp.tool()
def query_decisions(query: str) -> str:
    """Search the ledger for decisions relevant to a topic. Returns status,
    verbatim anchor quote, permalink, and owner for each match."""
    try:
        return json.dumps(ledger.query(query), indent=2)
    except Exception as e:  # noqa: BLE001
        return _err(e)


@mcp.tool()
def is_binding(topic: str) -> str:
    """Answer 'is there a current binding decision on this topic?'.

    Returns the settled decision (with verbatim anchor + permalink) when one exists.
    When none is settled, it does NOT just say false — it surfaces any unratified or
    CONTESTED proposals, so the calling agent knows the topic is actively disputed
    rather than simply unknown. Precision-first: only a human-ratified, non-superseded
    decision counts as binding."""
    try:
        b = _binding_for(topic)
        if b:
            return json.dumps({
                "binding": True,
                "decision_id": b["id"],
                "statement": b["statement"],
                "owner": b.get("owner_user"),
                "settled_on": b["updated_ts"],
                "anchor_quote": (b.get("anchor") or {}).get("quote"),
                "permalink": (b.get("anchor") or {}).get("permalink"),
            }, indent=2)
        pending = [m for m in ledger.query(topic) if m["status"] in ("proposed", "contested")]
        status = ("contested" if any(m["status"] == "contested" for m in pending)
                  else "proposed" if pending else "none")
        note = ("No binding decision yet — "
                f"{len(pending)} unratified/contested proposal(s) exist. Do not assume."
                if pending else "No decision on this topic.")
        return json.dumps({
            "binding": False, "topic": topic, "status": status, "note": note,
            "pending": [{"id": m["id"], "statement": m["statement"], "status": m["status"]}
                        for m in pending[:5]],
        }, indent=2)
    except Exception as e:  # noqa: BLE001
        return _err(e)


@mcp.tool()
def verify_audit_log() -> str:
    """Verify the append-only audit log's SHA-256 hash chain end to end. Returns
    {"ok": true, "rows": N} or the first tampered/broken row. Lets an agent or judge
    confirm the ledger's integrity claim live, not just take it on faith."""
    try:
        return json.dumps(ledger.verify_chain(), indent=2)
    except Exception as e:  # noqa: BLE001
        return _err(e)


def main() -> None:
    db.init_db()
    # SETTLED_MCP_TRANSPORT = stdio (default, for local agents) | http (network-accessible)
    transport = os.environ.get("SETTLED_MCP_TRANSPORT", "stdio")
    if transport in ("http", "streamable-http"):
        if mcp.settings.host == "0.0.0.0" and not os.environ.get("SETTLED_MCP_ALLOW_PUBLIC"):
            log.warning("MCP HTTP bound to 0.0.0.0 — the decision ledger would be reachable by "
                        "anyone on the network. Put an authenticating proxy in front, or set "
                        "SETTLED_MCP_HOST=127.0.0.1. (Set SETTLED_MCP_ALLOW_PUBLIC=1 to silence.)")
        print(f"Settled MCP (decisions://) on http://{mcp.settings.host}:{mcp.settings.port}/mcp")
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
