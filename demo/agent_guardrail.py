#!/usr/bin/env python3
"""Live proof of Settled's differentiator: an EXTERNAL agent checks the decision
ledger over MCP *before acting* — and is stopped from building on a reversed decision.

This is the thing decision-logs can't do: they're for humans to read. Settled answers
the agent. Run:  python -m demo.agent_guardrail

It spawns Settled's real MCP server (decisions://) over stdio and acts as a coding
agent would: form a plan from stale context, query is_binding, then course-correct.
"""
import asyncio
import json
import os
import pathlib
import sys

# Self-contained + reproducible: seed a demo ledger and make sure the spawned MCP
# server reads it (MCP's stdio client hands the child a minimal env otherwise).
os.environ["SETTLED_DB_PATH"] = str(pathlib.Path(__file__).resolve().parent / "out" / "demo_ledger.db")
os.environ.setdefault("SETTLED_LLM_PROVIDER", "stub")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def line(s=""):
    print(s, flush=True)


async def main():
    from seed import seed_demo
    pathlib.Path(os.environ["SETTLED_DB_PATH"]).parent.mkdir(exist_ok=True)
    seed_demo.main()  # fresh datastore lifecycle so is_binding has something to answer

    line("┌─ External coding agent  (e.g. Claude Code / Cursor / CI bot)")
    line("│  Task: \"Set up the database migration for the platform service.\"")
    line("│  Stale context it picked up from an April thread: → use Postgres")
    line("│")
    line("│  Responsible move: ask Settled what's BINDING before touching anything.")

    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"],
                                   env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            out = await s.call_tool("is_binding", {"topic": "datastore"})
            verdict = json.loads(out.content[0].text)

    line("│")
    line("│  → mcp.call(decisions://, is_binding, {topic: \"datastore\"})")
    line("│  ← " + json.dumps(verdict))
    line("│")

    if verdict.get("binding"):
        binding = verdict["statement"]
        if "aurora" in binding.lower():
            line("│  ⚠️  STOP. My plan used Postgres — but the binding decision is:")
            line(f"│        \"{binding}\"  (settled {verdict.get('settled_on','')[:10]})")
            line(f"│        source: {verdict.get('permalink')}")
            line("│  ✅  Course-correcting: provisioning Aurora, not Postgres.")
        else:
            line(f"│  ✅  Binding decision: {binding}. Proceeding accordingly.")
    else:
        line("│  ⏸  Nothing binding on this topic — escalating to a human before acting.")

    line("└─ Without Settled, the agent ships on Postgres. Three days lost.")
    line("   With Settled, every agent acts on what the team actually decided.")


if __name__ == "__main__":
    asyncio.run(main())
