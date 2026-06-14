# Settled — architecture

```mermaid
flowchart TD
    subgraph Slack["Slack workspace (settledco.slack.com)"]
        U[Team members in threads]
        SC["/settled command"]
        HOME[App Home tab]
        RX[✅ / ❌ reactions]
    end

    subgraph App["Settled Bolt app — Socket Mode (no public URL)"]
        EV[message events]
        EX["extraction.py\npre-filter → classify → confidence gate"]
        LLM["llm.py adapter\nstub (keyless) | anthropic"]
        LED["ledger.py\nlifecycle + supersede edges\nhash-chained audit"]
        BK[blocks.py — Block Kit]
    end

    DB[(SQLite ledger\ndecisions · anchors · edges\nratifications · audit_log)]

    subgraph MCP["Settled MCP server — decisions://  (qualifying tech)"]
        R1[decisions://all · settled · awaiting · id]
        T1["is_binding(topic)"]
        T2["query_decisions(query)"]
    end

    EXT[External agents\nClaude · IDE bots · CI]

    U -->|new message| EV --> EX
    EX <-->|classify + verbatim quote| LLM
    EX -->|confidence ≥ threshold| LED
    EX -. below threshold: silent .-> EV
    LED --> BK -->|ratification prompt in-thread| U
    RX -->|human ✅ ratifies| LED
    SC --> LED
    LED --> HOME
    LED <--> DB
    MCP <--> DB
    EXT -->|"is X still binding?"| MCP
```

## Key design decisions
1. **Verbatim anchor is the source of truth.** Each decision stores the exact substring of
   the source message + permalink. Summaries are display-only. (CogCanvas: verbatim beats
   summarization 93% vs 19% on constraint recall.)
2. **Epistemic status is typed, transitions are signal-driven.** Extraction only ever
   produces `proposed`. `settled` requires a human ✅. A newer settled decision on the same
   topic supersedes the old one via a signed `supersedes` edge. (OIDA: epistemic class +
   signed contradiction edges.)
3. **Precision-first gate.** Two stages — cheap regex pre-filter, then an LLM classifier
   with a confidence threshold (default 0.72). Below threshold the agent stays silent. A
   wrong "settled" is worse than no answer.
4. **Ungated qualifying tech.** The MCP server is self-built over the same SQLite ledger.
   No dependency on gated Slack AI features or the Real-Time Search API.
5. **Audit-ready.** `audit_log` is append-only and hash-chained
   (`SHA-256(prev_hash + content + ts)`), toward EU AI Act / DORA traceability.

## Data model
- **decisions** — topic, statement, status, owner, channel, confidence, timestamps
- **anchors** — verbatim quote, permalink, message_ts (the binding evidence)
- **edges** — `supersedes` / `contests` / `relates` between decisions
- **ratifications** — human ✅/❌ votes
- **audit_log** — hash-chained append-only trail

## Transport
Socket Mode (WebSocket) — the app needs no public URL or tunnel, which keeps the demo and
judge sandbox setup friction-free.
```
