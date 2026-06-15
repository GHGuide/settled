"""Run the Settled Slack app over Socket Mode (no public URL needed)."""
import logging
import time

from slack_bolt.adapter.socket_mode import SocketModeHandler

from settled import config
from settled.slack_app import build

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("settled")


def main() -> None:
    config.require_runtime()  # fail fast with a clear message if misconfigured
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
