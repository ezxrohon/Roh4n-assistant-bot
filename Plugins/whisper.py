"""
Whisper plugin
--------------
Reply to someone's message with:  /whisper <secret text>
The bot posts a button; only the original sender and the replied-to
person can reveal the text (shown as a popup alert to them only).

Whispers are kept in memory only (they intentionally don't survive a
restart -- that's the point of a short-lived "secret").
"""

import uuid

from telethon import events, Button

WHISPERS = {}


def create_whisper(sender_id, target_id, target_name, text):
    whisper_id = uuid.uuid4().hex[:8]
    WHISPERS[whisper_id] = {
        "sender": sender_id,
        "target": target_id,
        "target_name": target_name,
        "text": text,
    }
    return whisper_id


def init_bot_plugin(bot, owner_id, owner_name):

    @bot.on(events.NewMessage(pattern=r"^/whisper(?:\s+([\s\S]+))?"))
    async def whisper_command(event):
        if not event.is_reply:
            await event.reply(
                "↩️ Reply to someone's message with `/whisper <secret text>` "
                "to send them a private note.",
                parse_mode="markdown",
            )
            return

        text = event.pattern_match.group(1)
        if not text:
            await event.reply(
                "✏️ Usage: reply to someone's message with `/whisper <secret text>`",
                parse_mode="markdown",
            )
            return

        replied = await event.get_reply_message()
        target = await replied.get_sender()
        if target is None:
            await event.reply("❌ Couldn't identify who you're replying to.")
            return

        target_name = getattr(target, "first_name", None) or "User"
        whisper_id = create_whisper(event.sender_id, target.id, target_name, text)

        try:
            await event.delete()
        except Exception:
            pass  # bot may lack delete rights in some chats; not fatal

        await event.respond(
            f"🤫 A secret whisper for <b>{target_name}</b>",
            buttons=[Button.inline("👁 View Whisper", data=f"w_{whisper_id}")],
            parse_mode="html",
        )

    @bot.on(events.CallbackQuery(pattern=r"^w_(.+)$"))
    async def view_whisper(event):
        whisper_id = event.data_match.group(1).decode()
        whisper = WHISPERS.get(whisper_id)

        if not whisper:
            await event.answer("🛑 This whisper has expired or the bot restarted.", alert=True)
            return

        if event.sender_id in (whisper["target"], whisper["sender"]):
            await event.answer(whisper["text"], alert=True)
        else:
            await event.answer(
                f"🛑 This whisper is only for {whisper['target_name']}.",
                alert=True,
            )

    print("✅ Whisper plugin loaded")
