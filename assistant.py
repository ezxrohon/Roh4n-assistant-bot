"""
Assistant plugin
----------------
- /start, /help  -> menus (different view for owner vs. regular users)
- /assistant on|off|status -> toggles whether the bot forwards DMs to the owner
- Forwards any DM from a regular user to the owner, with sender info
- Lets the owner reply to a forwarded message and have it delivered back
"""

import html
import json
from pathlib import Path

from telethon import events, Button

DB_PATH = Path(__file__).parent.parent / "DB" / "assistant_db.json"

DEFAULT_DB = {
    "assistant_enabled": True,
    "users": [],
    "user_message_map": {},
    "stats": {
        "total_messages": 0,
        "total_replies": 0,
    },
}


def load_database():
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Make sure any keys added in later versions still exist
                for key, value in DEFAULT_DB.items():
                    data.setdefault(key, value)
                return data
        except Exception as e:
            print(f"Error loading assistant database: {e}")
    return json.loads(json.dumps(DEFAULT_DB))


def save_database(db):
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"Error saving assistant database: {e}")


def add_user(user_id):
    db = load_database()
    if isinstance(db["users"], dict):
        db["users"] = list(db["users"].keys())
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_database(db)
    return len(db["users"])


def get_stats():
    db = load_database()
    return {
        "users_count": len(db["users"]),
        "assistant_enabled": db["assistant_enabled"],
        "total_messages": db["stats"]["total_messages"],
        "total_replies": db["stats"]["total_replies"],
    }


def init_bot_plugin(bot, owner_id, owner_name, support_url=""):
    """Register all assistant handlers on the given Telethon bot client."""

    def main_menu_text_and_buttons(bot_username):
        stats = get_stats()
        text = (
            f"👋 <b>Welcome, {html.escape(owner_name)}!</b>\n\n"
            f"🤖 <b>Bot:</b> @{bot_username}\n"
            f"👥 <b>Total Users:</b> <code>{stats['users_count']}</code>\n"
            f"🔧 <b>Assistant:</b> {'🟢 Enabled' if stats['assistant_enabled'] else '🔴 Disabled'}\n\n"
            f"<i>Use the buttons below to manage your bot</i>"
        )
        buttons = [
            [Button.inline("📚 Help", b"menu_help")],
            [Button.inline("🤖 Assistant", b"menu_assistant")],
            [Button.inline("📊 Stats", b"menu_stats")],
            [Button.inline("⚙️ Settings", b"menu_settings")],
        ]
        if support_url:
            buttons.append([Button.url("💬 Support", support_url)])
        return text, buttons

    # -------------------------------------------------------------------
    # /start
    # -------------------------------------------------------------------
    @bot.on(events.NewMessage(pattern=r"^/start"))
    async def start_handler(event):
        user_id = event.sender_id
        users_count = add_user(user_id)

        if user_id == owner_id:
            bot_me = await bot.get_me()
            text, buttons = main_menu_text_and_buttons(bot_me.username)
            await event.reply(text, buttons=buttons, parse_mode="html")
        else:
            db = load_database()
            if db["assistant_enabled"]:
                text = (
                    f"👋 <b>Hello!</b>\n\n"
                    f"I'm the personal assistant of <b>{html.escape(owner_name)}</b>.\n\n"
                    f"📩 Send me any message and I'll deliver it.\n"
                    f"💬 You'll get a reply right here when they respond!"
                )
            else:
                text = (
                    f"👋 <b>Hello!</b>\n\n"
                    f"I'm the personal assistant of <b>{html.escape(owner_name)}</b>.\n\n"
                    f"⚠️ <b>Assistant mode is currently disabled.</b>\n"
                    f"Please check back later!"
                )
            await event.reply(text, parse_mode="html")
            _ = users_count  # kept for clarity / future use

    # -------------------------------------------------------------------
    # Main menu callbacks (owner only)
    # -------------------------------------------------------------------
    @bot.on(events.CallbackQuery(pattern=r"^menu_(.+)$"))
    async def menu_handler(event):
        if event.sender_id != owner_id:
            await event.answer("⛔ This is only for the bot owner!", alert=True)
            return

        menu = event.data_match.group(1).decode()
        db = load_database()

        if menu == "help":
            text = "📚 <b>Bot Commands Help</b>\n\n👇 <i>Select a category below</i>"
            buttons = [
                [Button.inline("🤖 Assistant", b"cat_assistant")],
                [Button.inline("⚡ Alive / Ping", b"cat_alive")],
                [Button.inline("🤫 Whisper", b"cat_whisper")],
                [Button.inline("◀️ Back", b"menu_main")],
            ]
            await event.edit(text, buttons=buttons, parse_mode="html")

        elif menu == "assistant":
            await _render_assistant_menu(event, db)

        elif menu == "stats":
            stats = get_stats()
            text = (
                "📊 <b>Bot Statistics</b>\n\n"
                f"👥 <b>Total Users:</b> <code>{stats['users_count']}</code>\n"
                f"💬 <b>Messages Received:</b> <code>{stats['total_messages']}</code>\n"
                f"📤 <b>Replies Sent:</b> <code>{stats['total_replies']}</code>\n"
                f"🔧 <b>Assistant:</b> {'🟢 Enabled' if stats['assistant_enabled'] else '🔴 Disabled'}"
            )
            buttons = [[Button.inline("◀️ Back", b"menu_main")]]
            await event.edit(text, buttons=buttons, parse_mode="html")

        elif menu == "settings":
            text = (
                "⚙️ <b>General Settings</b>\n\n"
                "<b>Coming soon:</b>\n"
                "• Auto-response templates\n"
                "• Block/unblock users\n"
                "• Custom welcome messages\n\n"
                "<i>More features can be added here later.</i>"
            )
            buttons = [[Button.inline("◀️ Back", b"menu_main")]]
            await event.edit(text, buttons=buttons, parse_mode="html")

        elif menu == "main":
            bot_me = await bot.get_me()
            text, buttons = main_menu_text_and_buttons(bot_me.username)
            await event.edit(text, buttons=buttons, parse_mode="html")

    async def _render_assistant_menu(event, db):
        text = (
            "🤖 <b>Assistant Settings</b>\n\n"
            f"<b>Status:</b> {'🟢 Enabled' if db['assistant_enabled'] else '🔴 Disabled'}\n"
            f"<b>Total Messages:</b> <code>{db['stats']['total_messages']}</code>\n"
            f"<b>Total Replies:</b> <code>{db['stats']['total_replies']}</code>\n\n"
            "<b>Features:</b>\n"
            "• Forward user messages to you\n"
            "• Reply to users through the bot\n"
            "• Track multiple conversations\n\n"
            "<i>Use /assistant on|off|status to control</i>"
        )
        toggle_label = "🔴 Disable Assistant" if db["assistant_enabled"] else "🟢 Enable Assistant"
        buttons = [
            [Button.inline(toggle_label, b"assistant_toggle")],
            [Button.inline("◀️ Back", b"menu_main")],
        ]
        await event.edit(text, buttons=buttons, parse_mode="html")

    # -------------------------------------------------------------------
    # Help category callbacks
    # -------------------------------------------------------------------
    @bot.on(events.CallbackQuery(pattern=r"^cat_(.+)$"))
    async def category_help_handler(event):
        if event.sender_id != owner_id:
            await event.answer("⛔ This is only for the bot owner!", alert=True)
            return

        category = event.data_match.group(1).decode()
        categories = {
            "assistant": {
                "icon": "🤖",
                "title": "Assistant Commands",
                "commands": [
                    ("/start", "Show main menu"),
                    ("/help", "Show help menu"),
                    ("/assistant", "Show assistant status"),
                    ("/assistant on", "Enable assistant mode"),
                    ("/assistant off", "Disable assistant mode"),
                ],
            },
            "alive": {
                "icon": "⚡",
                "title": "Alive / Ping Commands",
                "commands": [
                    ("/alive", "Customize the alive message"),
                    ("/ping", "Check bot latency"),
                ],
            },
            "whisper": {
                "icon": "🤫",
                "title": "Whisper Commands",
                "commands": [
                    ("/whisper <text> (as a reply)", "Send a secret message only the replied-to user can view"),
                ],
            },
        }
        if category not in categories:
            await event.answer("❌ Category not found!", alert=True)
            return

        info = categories[category]
        text = f"{info['icon']} <b>{info['title']}</b>\n\n"
        for cmd, desc in info["commands"]:
            text += f"❯ <code>{cmd}</code>\n   <i>{desc}</i>\n\n"

        buttons = [
            [Button.inline("◀️ Back to Categories", b"menu_help")],
            [Button.inline("🏠 Main Menu", b"menu_main")],
        ]
        await event.edit(text, buttons=buttons, parse_mode="html")

    # -------------------------------------------------------------------
    # Assistant toggle
    # -------------------------------------------------------------------
    @bot.on(events.CallbackQuery(pattern=r"^assistant_toggle$"))
    async def assistant_toggle_handler(event):
        if event.sender_id != owner_id:
            await event.answer("⛔ This is only for the bot owner!", alert=True)
            return

        db = load_database()
        db["assistant_enabled"] = not db["assistant_enabled"]
        save_database(db)

        await event.answer(
            f"✅ Assistant is now {'Enabled' if db['assistant_enabled'] else 'Disabled'}",
            alert=True,
        )
        await _render_assistant_menu(event, db)

    # -------------------------------------------------------------------
    # /assistant on|off|status
    # -------------------------------------------------------------------
    @bot.on(events.NewMessage(pattern=r"^/assistant(?:\s+(.+))?"))
    async def assistant_command_handler(event):
        if event.sender_id != owner_id:
            await event.reply("⛔ This command is only for the bot owner!")
            return

        action = event.pattern_match.group(1)
        db = load_database()

        if not action:
            status = "🟢 Enabled" if db["assistant_enabled"] else "🔴 Disabled"
            await event.reply(
                f"🤖 <b>Assistant Status:</b> {status}\n\n"
                "<b>Commands:</b>\n"
                "• <code>/assistant on</code>\n"
                "• <code>/assistant off</code>\n"
                "• <code>/assistant status</code>",
                parse_mode="html",
            )
            return

        action = action.strip().lower()
        if action == "on":
            db["assistant_enabled"] = True
            save_database(db)
            await event.reply("✅ <b>Assistant mode enabled.</b>", parse_mode="html")
        elif action == "off":
            db["assistant_enabled"] = False
            save_database(db)
            await event.reply("🔴 <b>Assistant mode disabled.</b>", parse_mode="html")
        elif action == "status":
            status = "🟢 Enabled" if db["assistant_enabled"] else "🔴 Disabled"
            await event.reply(
                f"🤖 <b>Assistant Status:</b> {status}\n"
                f"• Messages: <code>{db['stats']['total_messages']}</code>\n"
                f"• Replies: <code>{db['stats']['total_replies']}</code>\n"
                f"• Users: <code>{len(db['users'])}</code>",
                parse_mode="html",
            )
        else:
            await event.reply("❌ Invalid action! Use: <code>/assistant on|off|status</code>", parse_mode="html")

    # -------------------------------------------------------------------
    # Forward regular-user DMs to the owner
    # -------------------------------------------------------------------
    @bot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def user_message_handler(event):
        if event.text and event.text.startswith("/"):
            return
        if event.sender_id == owner_id:
            return

        db = load_database()
        if not db["assistant_enabled"]:
            return

        try:
            sender = await event.get_sender()
            sender_name = sender.first_name or "Unknown"
            sender_username = f"@{sender.username}" if sender.username else "No username"

            forward_text = (
                "📩 <b>New Message from User</b>\n\n"
                f"👤 <b>Name:</b> {html.escape(sender_name)}\n"
                f"🆔 <b>User ID:</b> <code>{sender.id}</code>\n"
                f"📝 <b>Username:</b> {html.escape(sender_username)}\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            message_text = html.escape(event.text) if event.text else "[Media/Sticker/Other]"

            forwarded = await bot.send_message(
                owner_id,
                forward_text + f"<b>Message:</b> {message_text}",
                parse_mode="html",
            )

            if event.photo or event.video or event.document or event.sticker:
                await event.forward_to(owner_id)

            db["user_message_map"][str(forwarded.id)] = sender.id
            db["stats"]["total_messages"] += 1
            save_database(db)

            await event.reply(
                "✅ <b>Message sent!</b>\n\nPlease wait for a response...",
                parse_mode="html",
            )
        except Exception as e:
            print(f"Error forwarding user message: {e}")

    # -------------------------------------------------------------------
    # Owner replies to a forwarded message -> delivered back to the user
    # -------------------------------------------------------------------
    @bot.on(events.NewMessage(from_users=owner_id))
    async def owner_reply_handler(event):
        if not event.is_reply:
            return

        try:
            replied_msg = await event.get_reply_message()
            db = load_database()
            replied_msg_id = str(replied_msg.id)

            if replied_msg_id in db["user_message_map"]:
                user_id = db["user_message_map"][replied_msg_id]
                reply_message = html.escape(event.text) if event.text else "[Media/Sticker/Other]"
                reply_text = f"💬 <b>Reply from {html.escape(owner_name)}:</b>\n\n{reply_message}"

                await bot.send_message(user_id, reply_text, parse_mode="html")
                if event.photo or event.video or event.document or event.sticker:
                    await event.forward_to(user_id)

                db["stats"]["total_replies"] += 1
                save_database(db)
                await event.reply("✅ <b>Reply sent to user!</b>", parse_mode="html")
        except Exception as e:
            print(f"Error handling owner reply: {e}")

    # -------------------------------------------------------------------
    # /help
    # -------------------------------------------------------------------
    @bot.on(events.NewMessage(pattern=r"^/help"))
    async def help_command_handler(event):
        if event.sender_id == owner_id:
            text = "📚 <b>Bot Commands Help</b>\n\n👇 <i>Select a category below</i>"
            buttons = [
                [Button.inline("🤖 Assistant", b"cat_assistant")],
                [Button.inline("⚡ Alive / Ping", b"cat_alive")],
                [Button.inline("🤫 Whisper", b"cat_whisper")],
                [Button.inline("🏠 Main Menu", b"menu_main")],
            ]
            await event.reply(text, buttons=buttons, parse_mode="html")
        else:
            text = (
                "📚 <b>Help</b>\n\n"
                "This is a personal assistant bot.\n"
                "Simply send your message and it will be forwarded to the owner.\n\n"
                "Use /start to begin."
            )
            await event.reply(text, parse_mode="html")

    print("✅ Assistant plugin loaded")
