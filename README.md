# Settled — the decision layer for Slack

[![tests](https://github.com/GHGuide/settled/actions/workflows/test.yml/badge.svg)](https://github.com/GHGuide/settled/actions/workflows/test.yml)
&nbsp;Python · Slack Bolt · Model Context Protocol · SQLite (hash-chained audit) · MIT

**Retrieval tells you what was *said*. Settled tells you what was *decided* — and whether it still binds.**

Teams run AI agents in Slack now. An agent acts on whatever it reads — even a decision the team
already reversed. Settled maintains a **decision ledger with epistemic status** and, uniquely,
exposes it over an **MCP server** so any agent can ask *"is this still binding?"* **before it acts.**

> Slack Agent Builder Challenge · New Slack Agent track · Qualifying tech: our own `decisions://` MCP server (ungated).

## What it does
- **Watches channels**, detects decisions behind a precision-first confidence gate (uses thread
  context, catches multiple decisions per message).
- **Human ✅ ratifies** — only a human makes a decision binding. Wrong "settled" > silence.
- **Epistemic lifecycle:** proposed → contested → settled → **superseded**, each anchored to a
  **verbatim quote + permalink**.
- **Query:** `/settled <topic>`, the assistant (DM/@mention), or the App Home dashboard.
- **MCP `decisions://`** — `is_binding(topic)`, `query_decisions(q)` + resources, over stdio & HTTP.

## What makes it different
Plenty of tools log decisions for a *person* to read later. Settled is the one an **agent** can
query before acting — the guardrail that keeps humans *and* agents on what the team actually decided.

|  | Decision-log tools | RAG / Slack search | **Settled** |
|---|---|---|---|
| Captures decisions | ✅ | ➖ | ✅ |
| Knows which one still **binds** | ❌ | ❌ | ✅ (epistemic status) |
| Verbatim quote + permalink anchor | ➖ | ❌ | ✅ |
| Human ratifies before "settled" | ➖ | ❌ | ✅ |
| **An agent can query it before acting** | ❌ | ❌ | ✅ **(MCP `decisions://`)** |
| Tamper-evident audit trail | ❌ | ❌ | ✅ (hash chain + verify) |

See it live — a coding agent rewrites its own migration before merge:
```text
$ python -m demo.agent_coding_guardrail
│  ✍️  wrote 0007_create_datastore.postgres.sql  (targets Postgres)
│  → mcp.call(decisions://, is_binding, {topic: "datastore"})
│  ← {"binding": true, "statement": "Move primary datastore to Aurora", "permalink": …}
│  ⛔ CONFLICT  my migration targets Postgres — but the team ratified Aurora
│  ✅ rewrote → 0007_create_datastore.aurora.sql  (targets Aurora)
│      - conn: pg-primary.internal   + conn: …cluster.rds.amazonaws.com
```
Also: `python -m bench.benchmark` (naive agents act on a stale decision ~60% of the time, Settled 0%)
and `python -m demo.breadth` (a CI gate, an IDE assistant, and a coding agent on one ledger).

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill Slack tokens + OPENROUTER_API_KEY
python -m seed.seed_demo        # seed the ledger (fictional demo data)
python run.py                   # Slack bot (Socket Mode)
python -m mcp_server.server     # MCP server (stdio); SETTLED_MCP_TRANSPORT=http for HTTP
```

Create the Slack app from [`slack_manifest.yaml`](slack_manifest.yaml) (declares App Home,
`/settled`, the Assistant surface, and events incl. `reaction_removed`).

**Tests:** `pip install -r requirements-dev.txt && pytest -q` — covers the ledger lifecycle,
supersede/topic guards, the hash-chained audit log (incl. tamper detection), the classifier
gates, and the MCP `is_binding` / `verify_audit_log` tools.

## Deploy (always-on for judging)
See `DEPLOY.md` — Railway or Fly, same `Dockerfile`. Currently live on Railway.

## Layout
| Path | Role |
|---|---|
| `settled/` | config, db, ledger, **llm** (classify+answer), extraction, blocks, slack_app, agent |
| `mcp_server/server.py` | `decisions://` MCP server (stdio + streamable-HTTP): `is_binding`, `query_decisions`, `verify_audit_log` |
| `demo/agent_coding_guardrail.py` | the wow demo: a coding agent rewrites its own migration after checking Settled |
| `demo/breadth.py` · `demo/agent_guardrail.py` | 3 agents on one ledger · the minimal guardrail |
| `bench/benchmark.py` | quantified impact: stale-action rate, naive vs Settled |
| `tests/` | 29 pytest tests (lifecycle, audit-chain tamper detection, MCP, blocks) |
| `seed/` · `video/` | demo ledger seeders · Remotion video project + architecture PNG |

## Stack
Python · Slack Bolt · SQLite (hash-chained audit) · Model Context Protocol · OpenRouter (DeepSeek).

Licensed MIT (see `LICENSE`); third-party components in `NOTICE.md`. Demo data is fictional.
