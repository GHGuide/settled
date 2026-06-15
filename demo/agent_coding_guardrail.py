#!/usr/bin/env python3
"""WOW demo — a coding agent about to ship a migration on a REVERSED decision,
caught by Settled over MCP, rewriting its own code before it merges.

Everything here is real: it spawns Settled's actual `decisions://` MCP server over
stdio, makes a real `is_binding` call against a seeded ledger, and writes real
migration files to demo/out/. The agent forms a plan from stale context (Postgres),
consults Settled, sees the binding decision is Aurora, and course-corrects.

This is the thing a decision *log* can't do — it's for humans to read. Settled
answers the agent, before it acts.

Run:  python -m demo.agent_coding_guardrail
"""
import asyncio
import difflib
import json
import os
import pathlib
import sys

OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

# Self-contained + reproducible: run against a freshly-seeded demo ledger so the
# spawned MCP server (which inherits this env) has the datastore lifecycle to answer from.
os.environ["SETTLED_DB_PATH"] = str(OUT / "demo_ledger.db")
os.environ.setdefault("SETTLED_LLM_PROVIDER", "stub")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

C = {"dim": "\033[2m", "red": "\033[31m", "grn": "\033[32m", "cyn": "\033[36m",
     "b": "\033[1m", "x": "\033[0m"}


def p(s=""):
    print(s, flush=True)


POSTGRES_MIGRATION = """\
-- migration: 0007_create_datastore.sql
-- target: PostgreSQL   (picked up from the team's April #platform thread)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE events (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    payload     jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
-- connection: postgresql://app@pg-primary.internal:5432/platform
"""

AURORA_MIGRATION = """\
-- migration: 0007_create_datastore.sql
-- target: Amazon Aurora (managed Postgres)   [binding decision #{did}]
-- source: {permalink}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE events (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    payload     jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
-- connection: postgresql://app@platform.cluster-ro.eu-west-1.rds.amazonaws.com:5432/platform
-- Aurora writer endpoint — failover-managed, per the team's ratified decision.
"""


def _seed():
    from seed import seed_demo
    seed_demo.main()


async def main():
    _seed()  # fresh datastore lifecycle: Postgres -> Mongo -> (settled) Aurora

    p(f"{C['b']}┌─ Coding agent{C['x']}  (Claude Code / Cursor / a CI bot)")
    p("│  Task: provision the platform datastore and write the migration.")
    p(f"│  {C['dim']}Plan from the April thread it scrolled back to → PostgreSQL.{C['x']}")
    p("│")

    pg = OUT / "0007_create_datastore.postgres.sql"
    pg.write_text(POSTGRES_MIGRATION)
    p(f"│  ✍️  wrote {C['b']}{pg.name}{C['x']}  {C['dim']}(targets Postgres){C['x']}")
    p("│")
    p(f"│  {C['cyn']}Guardrail: before opening the PR, ask Settled what actually binds.{C['x']}")

    # Pass our env so the spawned server uses the SAME seeded demo ledger (MCP's stdio
    # client otherwise hands the child a minimal env, and it'd read the wrong DB).
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"],
                                   env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            out = await s.call_tool("is_binding", {"topic": "datastore"})
            v = json.loads(out.content[0].text)

    shown = {k: v[k] for k in ("binding", "statement", "permalink") if k in v}
    p("│  → mcp.call(decisions://, is_binding, {topic: \"datastore\"})")
    p(f"│  ← {json.dumps(shown)}")
    p("│")

    if v.get("binding") and "aurora" in (v.get("statement", "").lower()):
        p(f"│  {C['red']}{C['b']}⛔ CONFLICT{C['x']}  my migration targets Postgres — but the team ratified:")
        p(f"│       {C['b']}\"{v['statement']}\"{C['x']}  {C['dim']}(settled {str(v.get('settled_on',''))[:10]}){C['x']}")
        p(f"│       {C['dim']}source: {v.get('permalink')}{C['x']}")
        aurora = OUT / "0007_create_datastore.aurora.sql"
        rewritten = AURORA_MIGRATION.format(did=v.get("decision_id"), permalink=v.get("permalink"))
        aurora.write_text(rewritten)
        p(f"│  {C['grn']}{C['b']}✅ rewrote → {aurora.name}{C['x']}  {C['grn']}(targets Aurora){C['x']}")
        p("│")
        p(f"│  {C['dim']}the one line that would have caused the incident:{C['x']}")
        for d in difflib.unified_diff(POSTGRES_MIGRATION.splitlines(),
                                      rewritten.splitlines(), lineterm=""):
            if d.startswith("-") and "pg-primary" in d:
                p(f"│    {C['red']}{d}{C['x']}")
            elif d.startswith("+") and "rds.amazonaws" in d:
                p(f"│    {C['grn']}{d}{C['x']}")
    elif v.get("binding"):
        p(f"│  {C['grn']}✅ binding decision: {v['statement']} — proceeding.{C['x']}")
    else:
        p(f"│  ⏸  nothing binding ({v.get('status')}) — escalating to a human before acting.")

    p("│")
    p(f"{C['b']}└─ Without Settled{C['x']}  the agent ships Postgres on a reversed decision → incident, days lost.")
    p(f"   {C['b']}With Settled{C['x']}     the agent caught it itself, before merge. The guardrail for every agent.")


if __name__ == "__main__":
    asyncio.run(main())
