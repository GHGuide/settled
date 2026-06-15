"""Central config. All env access goes through here."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")

# Extraction LLM. Provider is pluggable.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("SETTLED_ANTHROPIC_MODEL", "claude-opus-4-8")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("SETTLED_OPENROUTER_MODEL", "deepseek/deepseek-v4-pro")
# Default sensibly: if an OpenRouter key is present, use it (the real classifier);
# only fall back to the keyless "stub" when no key is configured. Explicit env wins.
_provider = os.environ.get("SETTLED_LLM_PROVIDER")
LLM_PROVIDER = _provider or ("openrouter" if OPENROUTER_API_KEY else "stub")  # stub|anthropic|openrouter
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


def require_runtime() -> None:
    """Fail fast with a clear, actionable message if required runtime config is missing.

    Socket Mode needs the bot + app tokens (signing secret is only for HTTP mode).
    Called from run.py at startup so a misconfigured deploy says exactly what's wrong
    instead of crashing deep inside the Slack SDK.
    """
    import logging
    missing = [k for k, v in (("SLACK_BOT_TOKEN", SLACK_BOT_TOKEN),
                              ("SLACK_APP_TOKEN", SLACK_APP_TOKEN)) if not v]
    if missing:
        raise SystemExit(
            "Settled cannot start — missing required env var(s): " + ", ".join(missing)
            + ".\nSet them in .env (see .env.example) or your host's secrets, then retry.")
    if LLM_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
        raise SystemExit("SETTLED_LLM_PROVIDER=openrouter but OPENROUTER_API_KEY is missing.")
    if LLM_PROVIDER == "anthropic":
        logging.getLogger("settled").warning(
            "SETTLED_LLM_PROVIDER=anthropic is not implemented — falling back to the keyless "
            "stub classifier. Set OPENROUTER_API_KEY + SETTLED_LLM_PROVIDER=openrouter for full quality.")
