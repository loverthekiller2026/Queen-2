"""Sudo-only broadcast to chats visible to the bot account."""
import asyncio
import logging
import runtime
from pyrogram import Client, filters
from pyrogram.types import Message
from config import SUDO_USERS

log = logging.getLogger(__name__)

@Client.on_message(filters.command(["broadcast", "gcast"]))
async def broadcast(_, message: Message):
    if not message.from_user or message.from_user.id not in SUDO_USERS:
        return
    if not message.reply_to_message:
        await message.reply_text("Reply to a text message to broadcast it.")
        return
    text = message.reply_to_message.text or message.reply_to_message.caption
    if not text:
        await message.reply_text("Only text messages are supported by this broadcast command.")
        return
    status = await message.reply_text("Broadcast started.")
    sent = failed = 0
    async for dialog in runtime.bot.get_dialogs():
        if dialog.chat.type not in ("group", "supergroup", "private", "channel"):
            continue
        try:
            await runtime.bot.send_message(dialog.chat.id, text)
            sent += 1
        except Exception as exc:
            failed += 1
            log.debug("Broadcast failed for %s: %s", dialog.chat.id, exc)
        if (sent + failed) % 10 == 0:
            await status.edit_text("Broadcasting…\nSent: {}\nFailed: {}".format(sent, failed))
        await asyncio.sleep(0.2)
    await status.edit_text("Broadcast finished.\nSent: {}\nFailed: {}".format(sent, failed))
