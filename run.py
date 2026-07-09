"""Run the Settled Slack app over Socket Mode (no public URL needed)."""
import logging
import time

from slack_bolt.adapter.socket_mode import SocketModeHandler

from settled import config
from settled.slack_app import build

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("settled")


def _llm_boot_check() -> None:
    """Log the active LLM provider and ping it once, so a misconfigured key surfaces
    in the logs instead of the detect/answer flows silently no-opping in production."""
    log.info("LLM provider: %s", config.LLM_PROVIDER)
    if config.LLM_PROVIDER == "openrouter":
        try:
            from settled import llm
            n = len(llm.classify("Final call: we ship the boot self-check."))
            log.info("LLM boot check OK — classifier reachable (detected %d).", n)
        except Exception as e:  # noqa: BLE001
            log.warning("LLM boot check FAILED — detection/assistant may no-op: %s", e)
    else:
        log.warning("LLM provider is '%s' (keyless stub) — set OPENROUTER_API_KEY for full quality.",
                    config.LLM_PROVIDER)


def main() -> None:
    config.require_runtime()  # fail fast with a clear message if misconfigured
    _llm_boot_check()
    app = build()
    backoff = 2
    while True:  # supervisor: survive transient Socket Mode disconnects/crashes
        try:
            handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
            print("⚡ Settled is running (Socket Mode). Ctrl-C to stop.")
            handler.start()
            return  # clean exit
        except KeyboardInterrupt:
            print("Shutting down.")
            return
        except Exception as e:  # noqa: BLE001
            log.error("Socket Mode handler crashed: %s — reconnecting in %ss", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    main()
