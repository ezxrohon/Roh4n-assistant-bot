"""
Alive / Ping plugin
--------------------
- /alive  -> shows a customizable "I'm alive" card, with a menu to cycle
             styles, toggle showing a picture, and reset to default
- /ping   -> shows real round-trip latency and uptime, with a similar menu
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from telethon import events, Button, version as telethon_version

CONFIG_PATH = Path(__file__).parent.parent / "DB" / "alive_config.json"

START_TIME = time.time()

ALIVE_STYLES = [
    (
        "⚡ <b>{name}</b> is alive!\n\n"
        "🐍 <b>Telethon:</b> <code>{telethon}</code>\n"
        "🧩 <b>Plugins:</b> <code>{plugins}</code>\n"
        "⏱ <b>Uptime:</b> <code>{uptime}</code>\n"
        "🏷 <b>Version:</b> <code>{version}</code> (<code>{branch}</code>)\n"
        "{quote}"
    ),
    "🤖 <b>{name}</b> online and ready.\n⏱ Up for <code>{uptime}</code>.\n{quote}",
    "✅ <b>{name}</b> — systems nominal.\n📦 Telethon <code>{telethon}</code> · v<code>{version}</code>\n⏱ <code>{uptime}</code>\n{quote}",
    "🌟 Hey, it's <b>{name}</b>!\nRunning smoothly for <code>{uptime}</code>.\n{quote}",
    "🔋 <b>{name}</b> is fully charged and alive.\n🏷 <code>{version}</code>-<code>{branch}</code> · ⏱ <code>{uptime}</code>\n{quote}",
]

PING_STYLES = [
    "🏓 <b>Pong!</b>\n⏱ <code>{speed}ms</code> · Up <code>{uptime}</code>",
    "🚀 <b>{speed}ms</b> round trip.\nUptime: <code>{uptime}</code>",
    "📶 Latency: <code>{speed}ms</code>\n⏱ Uptime: <code>{uptime}</code>",
    "⚡️ Snappy! <code>{speed}ms</code>\n🕒 <code>{uptime}</code> since last restart",
    "🛰 Ping: <code>{speed}ms</code> | Uptime: <code>{uptime}</code>",
]

QUOTES = [
    "\n💬 <i>\"Small steps every day.\"</i>",
    "\n💬 <i>\"Stay curious.\"</i>",
    "\n💬 <i>\"Code, ship, repeat.\"</i>",
]


class UserConfig:
    def __init__(self):
        self.alive_style_index = 0
        self.ping_style_index = 0
        self.use_pic_for_alive = False
        self.use_pic_for_ping = False
        self.show_quotes = True
        self.custom_alive_text = None
        self.custom_ping_text = None
        self.alive_pic = ""
        self.ping_pic = ""
        self._load()

    def _load(self):
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                self.__dict__.update(data)
            except Exception as e:
                print(f"Error loading alive config: {e}")

    def to_dict(self):
        return dict(self.__dict__)


user_config = UserConfig()


def save_config():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(user_config.to_dict(), indent=2), encoding="utf-8")


def format_uptime():
    seconds = int(time.time() - START_TIME)
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hrs}:{mins:02d}:{secs:02d}"


def _alive_text(owner_name, version, branch, plugins_count):
    quote = QUOTES[user_config.alive_style_index % len(QUOTES)] if user_config.show_quotes else ""
    if user_config.custom_alive_text:
        return user_config.custom_alive_text
    template = ALIVE_STYLES[user_config.alive_style_index]
    return template.format(
        name=owner_name,
        telethon=telethon_version.__version__,
        plugins=plugins_count,
        uptime=format_uptime(),
        version=version,
        branch=branch,
        quote=quote,
    )


def _ping_text(speed_ms):
    if user_config.custom_ping_text:
        return user_config.custom_ping_text
    template = PING_STYLES[user_config.ping_style_index]
    return template.format(speed=speed_ms, uptime=format_uptime())


def _alive_buttons():
    return [
        [Button.inline(f"🎨 Style: {user_config.alive_style_index + 1}/{len(ALIVE_STYLES)}", b"alive_nextstyle")],
        [Button.inline(f"{'✅' if user_config.use_pic_for_alive else '❌'} Show Pic", b"alive_togglepic")],
        [Button.inline(f"{'✅' if user_config.show_quotes else '❌'} Show Quotes", b"alive_togglequotes")],
        [Button.inline("🔄 Reset to Default", b"alive_reset")],
    ]


def _ping_buttons():
    return [
        [Button.inline(f"🎨 Style: {user_config.ping_style_index + 1}/{len(PING_STYLES)}", b"ping_nextstyle")],
        [Button.inline("🔄 Reset to Default", b"ping_reset")],
    ]


def init_bot_plugin(bot, owner_id, owner_name, version="1.0.0", branch="main"):

    def plugins_count():
        plugins_dir = Path(__file__).parent
        return len([f for f in plugins_dir.glob("*.py") if f.stem != "__init__"])

    @bot.on(events.NewMessage(pattern=r"^/alive$"))
    async def alive_cmd(event):
        text = (
            "⚡ <b>Alive Customization</b>\n\n"
            f"Current Style: <b>{user_config.alive_style_index + 1}/{len(ALIVE_STYLES)}</b>\n\n"
            + _alive_text(owner_name, version, branch, plugins_count())
        )
        if event.sender_id == owner_id:
            await event.reply(text, buttons=_alive_buttons(), parse_mode="html")
        else:
            await event.reply(_alive_text(owner_name, version, branch, plugins_count()), parse_mode="html")

    @bot.on(events.NewMessage(pattern=r"^/ping$"))
    async def ping_cmd(event):
        start = time.time()
        msg = await event.reply("🏓 Pinging...")
        speed_ms = round((time.time() - start) * 1000)
        text = _ping_text(speed_ms)
        if event.sender_id == owner_id:
            text = (
                "🏓 <b>Ping Customization</b>\n\n"
                f"Current Style: <b>{user_config.ping_style_index + 1}/{len(PING_STYLES)}</b>\n\n"
                + text
            )
            await msg.edit(text, buttons=_ping_buttons(), parse_mode="html")
        else:
            await msg.edit(text, parse_mode="html")

    @bot.on(events.CallbackQuery(pattern=r"^alive_(.+)$"))
    async def alive_callback(event):
        if event.sender_id != owner_id:
            await event.answer("⛔ Owner only!", alert=True)
            return

        data = event.data_match.group(1).decode()
        if data == "nextstyle":
            user_config.alive_style_index = (user_config.alive_style_index + 1) % len(ALIVE_STYLES)
            save_config()
        elif data == "togglepic":
            user_config.use_pic_for_alive = not user_config.use_pic_for_alive
            save_config()
        elif data == "togglequotes":
            user_config.show_quotes = not user_config.show_quotes
            save_config()
        elif data == "reset":
            user_config.alive_style_index = 0
            user_config.custom_alive_text = None
            user_config.use_pic_for_alive = False
            user_config.show_quotes = True
            save_config()

        text = (
            "⚡ <b>Alive Customization</b>\n\n"
            f"Current Style: <b>{user_config.alive_style_index + 1}/{len(ALIVE_STYLES)}</b>\n\n"
            + _alive_text(owner_name, version, branch, plugins_count())
        )
        await event.answer("✅ Updated")
        await event.edit(text, buttons=_alive_buttons(), parse_mode="html")

    @bot.on(events.CallbackQuery(pattern=r"^ping_(.+)$"))
    async def ping_callback(event):
        if event.sender_id != owner_id:
            await event.answer("⛔ Owner only!", alert=True)
            return

        data = event.data_match.group(1).decode()
        if data == "nextstyle":
            user_config.ping_style_index = (user_config.ping_style_index + 1) % len(PING_STYLES)
            save_config()
        elif data == "reset":
            user_config.ping_style_index = 0
            user_config.custom_ping_text = None
            save_config()

        text = (
            "🏓 <b>Ping Customization</b>\n\n"
            f"Current Style: <b>{user_config.ping_style_index + 1}/{len(PING_STYLES)}</b>\n\n"
            + _ping_text(0)
        )
        await event.answer("✅ Updated")
        await event.edit(text, buttons=_ping_buttons(), parse_mode="html")

    print("✅ Alive/Ping plugin loaded")
