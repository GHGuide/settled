"""Settled MCP server — exposes the decision ledger as `decisions://` resources
plus tools any external agent (Claude, an IDE bot, CI) can call to ask
"is this still binding?" BEFORE acting.

This is Settled's qualifying technology for the hackathon: an ungated, self-built
MCP server. It depends on no gated Slack AI feature and no Real-Time Search API.

Run:  python -m mcp_server.server      (stdio transport)
"""
import json
import os

from mcp.server.fastmcp import FastMCP

from settled import db, ledger

# host/port used when running over HTTP (streamable-http transport)
mcp = FastMCP(
    "settled",
    host=os.environ.get("SETTLED_MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("SETTLED_MCP_PORT", "8000")),
)


def _binding_for(topic_query: str):
    """The current binding decision for a topic = newest `settled`, not superseded."""
    results = ledger.query(topic_query)
    for r in results:
        if r["status"] == "settled":
            return r
    return None


# ------------------------------------------------------------------ resources
@mcp.resource("decisions://all")
def all_decisions() -> str:
    """Every decision in the ledger with its epistemic status."""
    return json.dumps(ledger.all_decisions(), indent=2)


@mcp.resource("decisions://settled")
def settled_decisions() -> str:
    """Only decisions that are currently settled (binding)."""
    rows = [d for d in ledger.all_decisions() if d["status"] == "settled"]
    return json.dumps(rows, indent=2)


@mcp.resource("decisions://awaiting")
def awaiting() -> str:
    """Decisions proposed but not yet ratified by a human."""
    return json.dumps(ledger.awaiting_ratification(), indent=2)


@mcp.resource("decisions://{decision_id}")
def one_decision(decision_id: str) -> str:
    """A single decision with its verbatim anchor(s) and supersede edges."""
    d = ledger.get_decision(int(decision_id))
    return json.dumps(d, indent=2) if d else json.dumps({"error": "not found"})


# ---------------------------------------------------------------------- tools
@mcp.tool()
def query_decisions(query: str) -> str:
    """Search the ledger for decisions relevant to a topic. Returns status,
    verbatim anchor quote, permalink, and owner for each match."""
    return json.dumps(ledger.query(query), indent=2)


@mcp.tool()
def is_binding(topic: str) -> str:
    """Answer 'is there a current binding decision on this topic?'. Returns the
    settled decision (with its verbatim anchor + permalink) or {"binding": false}.
    Precision-first: only a human-ratified, non-superseded decision counts as binding."""
    b = _binding_for(topic)
    if not b:
        return json.dumps({"binding": False, "topic": topic,
                           "note": "No human-ratified decision on this topic."})
    return json.dumps({
        "binding": True,
        "decision_id": b["id"],
        "statement": b["statement"],
        "owner": b.get("owner_user"),
        "settled_on": b["updated_ts"],
        "anchor_quote": (b.get("anchor") or {}).get("quote"),
        "permalink": (b.get("anchor") or {}).get("permalink"),
    }, indent=2)


def main() -> None:
    db.init_db()
    # SETTLED_MCP_TRANSPORT = stdio (default, for local agents) | http (network-accessible)
    transport = os.environ.get("SETTLED_MCP_TRANSPORT", "stdio")
    if transport in ("http", "streamable-http"):
        print(f"Settled MCP (decisions://) on http://{mcp.settings.host}:{mcp.settings.port}/mcp")
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
