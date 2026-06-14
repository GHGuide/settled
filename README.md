# Settled — the decision layer for Slack

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
See it live: `python -m demo.agent_guardrail` (an external agent course-corrects Postgres → Aurora).

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill Slack tokens + OPENROUTER_API_KEY
python -m seed.seed_demo        # seed the ledger
python run.py                   # Slack bot (Socket Mode)
python -m mcp_server.server     # MCP server (stdio); SETTLED_MCP_TRANSPORT=http for HTTP
```

## Deploy (always-on for judging)
See `DEPLOY.md` — Railway or Fly, same `Dockerfile`. Currently live on Railway.

## Layout
| Path | Role |
|---|---|
| `settled/` | config, db, ledger, **llm** (classify+answer), extraction, blocks, slack_app, agent |
| `mcp_server/server.py` | `decisions://` MCP server (stdio + streamable-HTTP) |
| `demo/agent_guardrail.py` | live proof: external agent blocked by a superseded decision |
| `seed/` | demo ledger seeders (DB-only + live-Slack) |
| `video/` | Remotion video project + pipeline (the demo film) + architecture PNG |

## Stack
Python · Slack Bolt · SQLite (hash-chained audit) · Model Context Protocol · OpenRouter (DeepSeek).

Licensed MIT (see `LICENSE`); third-party components in `NOTICE.md`. Demo data is fictional.
