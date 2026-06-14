"""Central config. All env access goes through here."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")

# Extraction LLM. Provider is pluggable; default "stub" runs keyless.
LLM_PROVIDER = os.environ.get("SETTLED_LLM_PROVIDER", "stub")  # stub | anthropic | openrouter
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("SETTLED_ANTHROPIC_MODEL", "claude-opus-4-8")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("SETTLED_OPENROUTER_MODEL", "deepseek/deepseek-v4-pro")
# Fast model for the per-message classifier (latency-sensitive). Quality model above
# is reserved for the conversational assistant answers.
OPENROUTER_CLASSIFY_MODEL = os.environ.get(
    "SETTLED_CLASSIFY_MODEL", "deepseek/deepseek-v4-flash")
# Hard timeout (seconds) on the classify call so Slack never hangs.
CLASSIFY_TIMEOUT = float(os.environ.get("SETTLED_CLASSIFY_TIMEOUT", "18"))

DB_PATH = os.environ.get("SETTLED_DB_PATH", str(ROOT / "ledger.db"))

# Precision-first gate. Below this confidence the agent stays silent.
# A wrong "settled" is worse than no answer — keep this high.
CONFIDENCE_THRESHOLD = float(os.environ.get("SETTLED_CONFIDENCE_THRESHOLD", "0.72"))

# Reaction emoji used for the human ratification loop.
RATIFY_EMOJI = os.environ.get("SETTLED_RATIFY_EMOJI", "white_check_mark")
REJECT_EMOJI = os.environ.get("SETTLED_REJECT_EMOJI", "x")
