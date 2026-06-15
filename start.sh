#!/usr/bin/env sh
set -e
mkdir -p "$(dirname "$SETTLED_DB_PATH")"

# First boot only: seed the ledger onto the persistent volume. Subsequent boots keep
# judges' new decisions. Seeding never aborts startup (falls back, then continues).
if [ ! -f "$SETTLED_DB_PATH" ]; then
  if [ "$SETTLED_SEED_LIVE" = "1" ]; then
    # Post/reuse real Slack messages so anchors have RESOLVABLE permalinks (idempotent).
    echo "Seeding ledger from live Slack (real permalinks)..."
    python -m seed.seed_live \
      || { echo "seed_live failed; falling back to baked/demo seed"; \
           [ -f /app/seed_ledger.db ] && cp /app/seed_ledger.db "$SETTLED_DB_PATH" \
           || python -m seed.seed_demo || echo "WARN: seeding failed; starting empty"; }
  elif [ -f /app/seed_ledger.db ]; then
    echo "Seeding ledger from baked snapshot..."
    cp /app/seed_ledger.db "$SETTLED_DB_PATH"
  else
    echo "Seeding ledger (generated)..."
    python -m seed.seed_demo || echo "WARN: seeding failed; starting empty"
  fi
fi

# Optional: also run the decisions:// MCP server over HTTP (set SETTLED_RUN_MCP=1)
if [ "$SETTLED_RUN_MCP" = "1" ]; then
  echo "Starting MCP (decisions://) over HTTP..."
  SETTLED_MCP_TRANSPORT=http python -m mcp_server.server &
fi

echo "Starting Settled bot (Socket Mode)..."
exec python run.py
