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
# pre-seeded ledger (real permalinks) baked in; copied to the volume on first boot
COPY ledger.db ./seed_ledger.db
RUN chmod +x start.sh

CMD ["./start.sh"]
