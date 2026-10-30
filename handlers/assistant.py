"""Assistant membership helper."""
import logging
import runtime
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import Message
from helpers.filters import command
from helpers.decorators import authorized_users_only

log = logging.getLogger(__name__)

@Client.on_message(command(["join", "assistant"]) & filters.group & ~filters.bot)
@authorized_users_only
async def join_chat(client: Client, message: Message):
    assistant = runtime.assistant
    status = await message.reply_text("Checking assistant membership…")
    try:
        me = await assistant.get_me()
        member = await client.get_chat_member(message.chat.id, me.id)
        if member.status == "administrator" and member.can_manage_voice_chats:
            await status.edit_text("Assistant is already in the group with voice-chat permission.")
            return
        if member.status not in ("left", "kicked"):
            await status.edit_text("Assistant is already in the group. Promote it and enable Manage Video Chats.")
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
        await status.edit_text("Could not add assistant: {}: {}".format(type(exc).__name__, exc))
