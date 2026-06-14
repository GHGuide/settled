"""Run the Settled Slack app over Socket Mode (no public URL needed)."""
from slack_bolt.adapter.socket_mode import SocketModeHandler

from settled import config
from settled.slack_app import build


def main() -> None:
    app = build()
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    print("⚡ Settled is running (Socket Mode). Ctrl-C to stop.")
    handler.start()


if __name__ == "__main__":
    main()
