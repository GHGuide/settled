# Settled — Socket Mode bot (always-on for judging). No inbound port needed.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 SETTLED_DB_PATH=/data/ledger.db

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY settled/ ./settled/
COPY mcp_server/ ./mcp_server/
COPY seed/ ./seed/
COPY run.py start.sh ./
# Generate the demo ledger snapshot AT BUILD from the seeder — reproducible, and avoids
# depending on a git-ignored ledger.db (so `docker build` works from a fresh clone).
# start.sh copies this onto the persistent volume on first boot.
RUN SETTLED_DB_PATH=/app/seed_ledger.db python -m seed.seed_demo
RUN chmod +x start.sh

CMD ["./start.sh"]
