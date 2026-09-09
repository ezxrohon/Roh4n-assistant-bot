"""
Central configuration for the assistant bot.
Everything is read from environment variables so no personal/owner
details ever need to be hardcoded in the source code.
"""

import os


def _get_int(name, default=0):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    # Get these from https://my.telegram.org (API Development Tools)
    API_ID = _get_int("API_ID", 0)
    API_HASH = os.environ.get("API_HASH", "")

    # Get this from @BotFather on Telegram
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # Your personal Telegram numeric user ID (e.g. from @userinfobot)
    OWNER_ID = _get_int("OWNER_ID", 0)

    # Display name used in bot messages
    OWNER_NAME = os.environ.get("OWNER_NAME", "Owner")

    # Optional support link shown in menus. Leave blank to hide the button.
    SUPPORT_URL = os.environ.get("SUPPORT_URL", "")

    VERSION = "1.0.0"
    BRANCH = os.environ.get("BRANCH", "main")

    # Optional direct image URLs used for /alive and /ping cards
    DEFAULT_ALIVE_PIC = os.environ.get("DEFAULT_ALIVE_PIC", "")
    DEFAULT_PING_PIC = os.environ.get("DEFAULT_PING_PIC", "")

    @classmethod
    def validate(cls):
        missing = [
            name
            for name, value in [
                ("API_ID", cls.API_ID),
                ("API_HASH", cls.API_HASH),
                ("BOT_TOKEN", cls.BOT_TOKEN),
                ("OWNER_ID", cls.OWNER_ID),
            ]
            if not value
        ]
        if missing:
            raise SystemExit(
                "Missing required environment variable(s): "
                + ", ".join(missing)
                + "\nSet them in your .env file (local) or in the Render "
                "dashboard's Environment tab (deployed)."
            )
