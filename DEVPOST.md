# Settled — Devpost submission

**Track:** New Slack Agent
**Tagline:** The decision layer your team — and your AI agents — check before they act.
**Qualifying technology:** our own MCP server exposing `decisions://` (no gated Slack AI / RTS).

---

## Try it — judges start here
Settled is **deployed always-on**, so it responds in real time during judging.

**1. Join the live workspace** — Slack developer sandbox **`settledco.slack.com`**, join via this
permanent link (no extra signup beyond Slack):
👉 **https://join.slack.com/t/settledco/shared_invite/zt-40u5d8u35-2u3iORV3gWEkIuYrnck70A**
You'll land in **#platform**, which already holds a worked example (datastore + SSO decisions).
*(Judges slackhack@salesforce.com and testing@devpost.com are also invited directly.)*

**2. See the dashboard** — left sidebar → **Apps → Settled → Home** tab: live counts
(proposed / contested / settled / superseded) + the full ledger.

**3. Watch it detect + ratify a decision** — post in **#platform**, e.g.
*"Final call: we're standardizing on Vitest for unit tests."* Settled replies in-thread with a
confidence score; react **✅** to settle it (❌ dismisses). The App Home updates instantly. Only a
human ✅ makes a decision binding.

**4. Query it** — type `/settled datastore` anywhere → the current binding decision (**Aurora**) plus
its full history (Postgres → MongoDB → Aurora), each anchored to a **verbatim quote + permalink**.

**5. Ask the agent** — DM the **Settled** app (Chat tab): *"what did we decide about SSO?"*

**6. The differentiator — agent guardrail (MCP)** — the same ledger is exposed over our `decisions://`
MCP server. An external agent calls `is_binding("datastore")` and gets the binding decision + permalink
*before it acts*, so it can't build on a reversed decision. Run it from the repo:
`python -m demo.agent_guardrail`.

---

## The problem
Teams are putting AI agents to work in Slack. But an agent acts on whatever it reads — and in
Slack, decisions change. A team picks Postgres, switches to Mongo, then settles on Aurora. Weeks
later that thread has scrolled away. A new teammate, or an agent, rebuilds on Postgres — a
decision that was already reversed. Days are lost to acting on context that no longer holds.

## What Settled does
Settled is a Slack agent that maintains a **decision ledger with epistemic status** — and exposes
it to other agents.

- **Watches channels** and detects decision-shaped moments behind a precision-first confidence
  gate (uses recent thread context, so "yes, let's do that" resolves to the proposal it answers).
- **Asks a human to confirm.** ✅ ratifies, ❌ dismisses. Only a human ✅ makes a decision binding
  — a wrong "settled" is worse than silence.
- **Tracks epistemic status over time:** proposed → contested → settled → **superseded**. Each
  entry is anchored to a **verbatim quote + permalink**, never a paraphrase.
- **Answer anywhere:** `/settled <topic>`, ask the assistant in natural language, or open the App
  Home dashboard (settled / contested / awaiting counts + the full ledger).

## What makes it different (the part no one else does)
There's a whole category of "capture decisions from Slack" tools. They all do the same thing:
**log a decision for a person to read later.**

Settled does the thing they can't: it runs its own **MCP server**, so any external agent — Claude,
an IDE bot, your CI — can ask **"is this still binding?" before it acts.** The agent about to build
on an old decision is stopped and handed the one that still holds. Settled is the guardrail that
keeps humans *and* agents acting on what the team actually decided.

> Retrieval tells you what was *said*. Settled tells you what was *decided* — and whether it still binds.

## How we built it
- **Slack:** Bolt for Python, Socket Mode (no public URL). Events API for messages/reactions,
  `/settled` slash command, Block Kit, App Home, and the Assistant (Agents & AI Apps) surface.
- **Extraction:** cheap noise gate → LLM classifier (DeepSeek via OpenRouter) returning a confidence
  score, verbatim anchor span, and *multiple* decisions per message. Precision held by the gate +
  the human ✅ loop.
- **Ledger:** SQLite — decisions, anchors, signed `supersedes`/`contests` edges, ratifications, and
  an **append-only, hash-chained audit log** (SHA-256(prev + content + ts)) toward EU AI Act / DORA
  traceability.
- **MCP server (`decisions://`):** built on the official MCP SDK; resources (`decisions://all`,
  `settled`, `awaiting`, `{id}`) + tools (`is_binding`, `query_decisions`). Runs over stdio for local
  agents and streamable-HTTP for remote ones. `demo/agent_guardrail.py` shows a real external agent
  course-correcting because of it.
- Deployed always-on (Railway) so the agent is live for judging.

## Grounded in research
- *Retrieval Is Not Enough: Why Organizational AI Needs Epistemic Infrastructure* (Bottino, Ferrero,
  Dosio, Beneventano, 2026) — org AI's ceiling is epistemic, not retrieval, fidelity: distinguishing
  binding decisions from abandoned hypotheses. Settled is a first implementation.
- *CogCanvas: Verbatim-Grounded Artifact Extraction for Long LLM Conversations* (Tao An, 2025) —
  verbatim extraction beats summarization 93% vs 19% on constraint recall. Justifies anchor quotes.

## What's next
Org-chart-aware ownership, embeddings for topic linking, connectors (wiki/Jira/HR) feeding context,
and a public MCP endpoint so any team's agents can consult their own decision layer.

## Built with
Python · Slack Bolt · SQLite · Model Context Protocol · OpenRouter (DeepSeek) · Remotion (video)
