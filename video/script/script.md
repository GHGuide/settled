# Settled — demo video script (~165s, target <180s)

Narrator: Brian (ElevenLabs, calm). Tone: keynote, confident, not salesy.
Rule guards: shows only working features · no "Slack is broken" framing (Slack = the surface
that makes this possible) · no copyrighted music · fictional personas only.

---

## s01_hook  (~14s)  — motion graphic
VO: "The next era of work runs on agents. And agents act on what your team has already
decided. But decisions don't live in a database — they live in the conversation."
Visual: black → "Settled" wordmark assembles · subtitle "the decision layer for Slack".

## s02_problem  (~22s)  — capture: thread scroll
VO: "A team picks Postgres. Weeks later they move to Mongo, then to Aurora. The thread
scrolls away. Now a new teammate — or an AI agent — acts on a decision that no longer holds.
The information was there. What's missing is whether it still binds."
Visual: #platform thread, gentle auto-scroll past the three datastore messages, dates ticking.

## s03_capture  (~26s)  — capture: live extraction
VO: "Settled watches the conversation. When someone makes a real decision —"
[on screen: Leonardo posts "Final call: we're standardizing on GitHub Actions for CI."]
VO: "— it catches it, with a confidence score, and asks a human to confirm. Precision first:
if it isn't sure, it stays silent. A wrong answer is worse than none."
Visual: message posts → Settled replies in-thread: 98%, verbatim quote, "react ✅ to settle".

## s04_ratify  (~14s)  — capture: ratify
VO: "One check mark settles it. The human stays in the loop — that's the feature, not a
workaround."
Visual: ✅ reaction → "✅ Settled." reply. Zoom on the green check.

## s05_lifecycle  (~24s)  — capture: /settled query
VO: "Ask Settled anything. Every decision carries a status — proposed, contested, settled,
superseded — anchored to the exact words and a permalink. Never a paraphrase."
Visual: /settled datastore → lifecycle Postgres ⚪ → Mongo ⚪ → Aurora 🟢, quotes + sources.

## s06_mcp  (~34s)  — capture: MCP, the wow
VO: "Here's what makes Settled different. It runs its own MCP server. So any external
agent — Claude, an IDE bot, your CI — can ask 'is this still binding?' before it acts."
[on screen: external Claude calls is_binding("datastore") → returns Aurora + permalink]
VO: "An agent about to act on the old decision is stopped, and handed the one that still
holds. Settled becomes the guardrail for every agent in the workspace."
Visual: terminal/MCP call → JSON verdict → "binding: Aurora" highlighted.

## s07_close  (~26s)  — App Home + tagline
VO: "Retrieval tells you what was said. Settled tells you what was decided — and whether it
still binds. The shared source of truth, for the humans and the agents working side by side
in Slack."
Visual: App Home dashboard (counts, lifecycle) → "Settled" wordmark + tagline + research credit
line: "First implementation of epistemic infrastructure for organizational AI (arXiv 2026)."
