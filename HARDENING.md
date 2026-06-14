# Settled — Hardening Plan (make it work as intended)

Goal: production-grade behavior + a live judge demo that can't break. Honest: this maximizes
win odds; it cannot guarantee a % of first place in a ~2000-team subjective contest.

## P0 — core function (it must actually catch decisions + never hang)
1. **Recall fix** — current regex pre-filter only LLM-checks exact cue phrases → misses real
   decisions ("Aurora it is", "consensus:", terse approvals). FIX: pre-filter becomes a cheap
   *noise* gate (drop emoji/greetings/one-word/very-short); call the LLM classifier on every
   substantive message. Precision kept by LLM + confidence gate + human ✅.
2. **"Final decision:" bug** — cue regex fails on `decision:`+space. Fixed by #1 (regex no longer gatekeeps).
3. **Thread context** — pass the last ~6 channel/thread messages to the classifier so contextual
   decisions ("yes, let's do that") resolve against the proposal they answer.
4. **Multi-decision** — classifier returns a LIST; one ledger entry per decision ("Stripe + drop PayPal").
5. **Latency** — classify on a FAST model (deepseek-v4-flash) with a hard timeout + stub fallback;
   keep the quality model for assistant answers. Never block Slack > a few seconds.
6. **Dedup** — don't create a new entry if a near-identical recent decision exists on the topic.

## P1 — differentiation + qualifier strength (Quality-of-Idea is the weak score)
7. **MCP over HTTP** — host decisions:// so "any external agent can ask" is literally true,
   not just local stdio. Strengthens the qualifier + the whole pitch.
8. **Live external-agent demo** — a real Claude/Cursor/CI script that calls the MCP, gets
   "superseded → here's the binding one", and changes behavior. The undeniable wow that lifts
   both Idea and Tech scores.

## P2 — survive judging (Jul 14 – Aug 6)
9. **Deploy bot always-on** (Railway/Fly/Render free) so `/settled`, @mentions, assistant,
   ratify all work for 3 weeks. Local-only = dead commands during judging.
10. Richer seeded demo workspace; judge re-invite ~Jul 8-10 + sandbox URL; test access.

## P3 — submission assets
11. Devpost text (lead with agent-guardrail), architecture PNG, LICENSE + third-party notices,
    public repo + README, YouTube upload.

## Order of work
P0 (function) → P1 (wow + qualifier) → P2 (deploy) → P3 (submit). Hardening > more video polish.
