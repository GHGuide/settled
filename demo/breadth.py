#!/usr/bin/env python3
"""Breadth: ONE decision ledger, many agents. Three different MCP clients — a CI
gate, an IDE assistant, and a coding agent — all consult the same `decisions://`
server before acting. Settled is infrastructure, not a single feature.

Run:  python -m demo.breadth
"""
import asyncio
import json
import os
import pathlib
import sys

OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
os.environ["SETTLED_DB_PATH"] = str(OUT / "demo_ledger.db")
os.environ.setdefault("SETTLED_LLM_PROVIDER", "stub")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

C = {"dim": "\033[2m", "red": "\033[31m", "grn": "\033[32m", "cyn": "\033[36m", "b": "\033[1m", "x": "\033[0m"}


def p(s=""):
    print(s, flush=True)


async def ask(session, topic):
    out = await session.call_tool("is_binding", {"topic": topic})
    return json.loads(out.content[0].text)


async def main():
    from seed import seed_demo
    seed_demo.main()

    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"],
                                   env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()

            # 1) CI gate — blocks a deploy that targets a reversed datastore
            v = await ask(s, "datastore")
            p(f"{C['b']}① CI gate{C['x']}  (pre-deploy check)")
            target = "Postgres"  # what the pipeline config still says
            ok = v.get("binding") and target.lower() in v.get("statement", "").lower()
            p(f"   pipeline targets {target}; binding = {C['b']}{v.get('statement')}{C['x']}")
            p(f"   {(C['grn']+'PASS') if ok else (C['red']+'BLOCK build')}{C['x']}  "
              f"{C['dim']}{v.get('permalink','')}{C['x']}")
            p("")

            # 2) IDE assistant — answers a dev in-editor
            v = await ask(s, "SSO")
            p(f"{C['b']}② IDE assistant{C['x']}  (dev asks: \"which SSO provider do we use?\")")
            if v.get("binding"):
                p(f"   → {v['statement']}")
            else:
                p(f"   → {C['cyn']}no binding decision — {v.get('status')}{C['x']}; "
                  f"don't scaffold either yet. {len(v.get('pending', []))} open proposal(s).")
            p("")

            # 3) Coding agent — picks the datastore client library to install
            v = await ask(s, "datastore")
            p(f"{C['b']}③ Coding agent{C['x']}  (selecting the client library)")
            lib = "aurora-data-api" if "aurora" in v.get("statement", "").lower() else "psycopg2"
            p(f"   binding = {v.get('statement')} → install {C['grn']}{lib}{C['x']}, not the Postgres-only driver")

    p("")
    p(f"{C['b']}One ledger, three agents.{C['x']} Each asked Settled before acting — none shipped on a reversed decision.")


if __name__ == "__main__":
    asyncio.run(main())
