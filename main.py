"""
Entry point for the assistant bot.

Local run:
    1. Copy .env.example to .env and fill in your values
    2. pip install -r requirements.txt
    3. python main.py

Render deploy: see README.md
"""

from telethon import TelegramClient

from config import Config
from plugins import assistant, alive, whisper

# Load .env automatically for local development if python-dotenv is installed.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    Config.validate()

    bot = TelegramClient("bot_session", Config.API_ID, Config.API_HASH).start(
        bot_token=Config.BOT_TOKEN
    )

    assistant.init_bot_plugin(bot, Config.OWNER_ID, Config.OWNER_NAME, Config.SUPPORT_URL)
    alive.init_bot_plugin(bot, Config.OWNER_ID, Config.OWNER_NAME, Config.VERSION, Config.BRANCH)
    whisper.init_bot_plugin(bot, Config.OWNER_ID, Config.OWNER_NAME)

    print("🤖 Bot is up and running. Press Ctrl+C to stop.")
    bot.run_until_disconnected()


if __name__ == "__main__":
    main()
