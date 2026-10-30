"""Assistant membership helper."""
import logging

from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import Message

from main import assistant
from helpers.filters import command
from helpers.decorators import authorized_users_only

log = logging.getLogger(__name__)

@Client.on_message(command(["join", "assistant"]) & filters.group & ~filters.bot)
@authorized_users_only
async def join_chat(client: Client, message: Message):
    status = await message.reply_text("Checking assistant membership…")
    try:
        await assistant.get_chat(message.chat.id)
        member = await client.get_chat_member(message.chat.id, (await assistant.get_me()).id)
        if member.status == "administrator" and member.can_manage_voice_chats:
            await status.edit_text("Assistant is already in the group with voice-chat permission.")
            return
        await status.edit_text("Assistant is already a member. Please grant it permission to manage voice chats.")
        return
    except Exception:
        pass

    try:
        invite = await client.export_chat_invite_link(message.chat.id)
        try:
            await assistant.join_chat(invite)
        except UserAlreadyParticipant:
            pass
        await status.edit_text("Assistant joined. Promote it and enable Manage Video Chats before using /play.")
    except Exception as exc:
        log.exception("Assistant join failed")
        await status.edit_text(f"Could not add assistant: {type(exc).__name__}: {exc}")
