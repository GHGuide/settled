# Deploy — keep Settled live through judging (Jul 14 – Aug 6)

The bot uses **Socket Mode** → no public URL/inbound port needed. It's a small always-on
worker. Fly.io's free allowance covers it. Artifacts ready: `Dockerfile`, `start.sh`, `fly.toml`
(pre-seeded ledger baked in; persistent volume keeps judges' new decisions).

## One thing only you can do: authenticate Fly
Fly needs an account (card for verification; the tiny VM stays within free allowance).
```
fly auth signup        # or: fly auth login   (opens browser)
```
Tell me when done — **then I run the rest** (creds persist in ~/.fly), or do it yourself below.

## The rest (I can run these once you're authed)
```
cd "<this folder>"
fly launch --no-deploy --copy-config --name settled-bot --region ams   # uses fly.toml
fly volumes create settled_data --size 1 --region ams -y               # persistent ledger
fly secrets set \
  SLACK_BOT_TOKEN="$(grep '^SLACK_BOT_TOKEN=' .env | cut -d= -f2-)" \
  SLACK_APP_TOKEN="$(grep '^SLACK_APP_TOKEN=' .env | cut -d= -f2-)" \
  SLACK_SIGNING_SECRET="$(grep '^SLACK_SIGNING_SECRET=' .env | cut -d= -f2-)" \
  OPENROUTER_API_KEY="$(grep '^OPENROUTER_API_KEY=' .env | cut -d= -f2-)"
fly deploy
fly logs            # expect: "⚡️ Bolt app is running!"
```
Verify: in Slack, run `/settled datastore` → should respond. Post a decision → ratify ping appears.

## Railway path (chosen) — simplest UX, ~$5 trial then ~$5/mo
Uses the same `Dockerfile` (Railway auto-detects it). One step only you can do:
```
railway login          # opens browser; may need a payment method to deploy
```
Then tell me — I run the rest (or you can):
```
cd "<this folder>"
railway init -n settled-bot                 # create project
railway up --detach                         # build Dockerfile + deploy
railway variables --set SLACK_BOT_TOKEN=... --set SLACK_APP_TOKEN=... \
  --set SLACK_SIGNING_SECRET=... --set OPENROUTER_API_KEY=... \
  --set SETTLED_LLM_PROVIDER=openrouter --set SETTLED_DB_PATH=/data/ledger.db
# add a Volume mounted at /data (dashboard → service → Volumes, or `railway volume add`)
railway redeploy
railway logs            # expect: "⚡️ Bolt app is running!"
```
Verify: `/settled datastore` in Slack responds; posting a decision triggers a ratify ping.
Note: without a /data volume the ledger resets on redeploy (baked seed still loads, so judges
always see the demo state — fine, but new decisions won't persist across redeploys).

## Notes
- Only the **Slack bot** must be deployed for judging. The `decisions://` MCP is demoed via
  the video + `demo/agent_guardrail.py`; to also host it, set `SETTLED_RUN_MCP=1` in fly.toml [env].
- After the contest: scale to zero (`fly scale count 0`) and rotate the API keys.
