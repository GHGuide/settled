#!/usr/bin/env sh
set -e
mkdir -p "$(dirname "$SETTLED_DB_PATH")"

# First boot: seed the ledger onto the persistent volume (real-permalink snapshot if baked,
# else generate). Subsequent boots keep judges' new decisions.
if [ ! -f "$SETTLED_DB_PATH" ]; then
  if [ -f /app/seed_ledger.db ]; then
    echo "Seeding ledger from baked snapshot..."
    cp /app/seed_ledger.db "$SETTLED_DB_PATH"
  else
    echo "Seeding ledger (generated)..."
    python -m seed.seed_demo || true
  fi
fi

# Optional: also run the decisions:// MCP server over HTTP (set SETTLED_RUN_MCP=1)
if [ "$SETTLED_RUN_MCP" = "1" ]; then
  echo "Starting MCP (decisions://) over HTTP..."
  SETTLED_MCP_TRANSPORT=http python -m mcp_server.server &
fi

echo "Starting Settled bot (Socket Mode)..."
exec python run.py
