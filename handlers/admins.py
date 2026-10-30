"""Voice-chat playback controls."""
import logging
from pyrogram import Client
from pyrogram.types import Message
from pytgcalls.types.input_stream import InputAudioStream, InputStream

from helpers.decorators import authorized_users_only, errors
from helpers.filters import command, other_filters
from main import pytgcalls
from callsmusic import queues

log = logging.getLogger(__name__)

@Client.on_message(command(["pause", "rukja"]) & other_filters)
@errors
@authorized_users_only
async def pause(_, message: Message):
    await pytgcalls.pause_stream(message.chat.id)
    await message.reply_text(f"Playback paused by {message.from_user.mention}.")

@Client.on_message(command(["resume"]) & other_filters)
@errors
@authorized_users_only
async def resume(_, message: Message):
    await pytgcalls.resume_stream(message.chat.id)
    await message.reply_text(f"Playback resumed by {message.from_user.mention}.")

@Client.on_message(command(["end", "stop"]) & other_filters)
@errors
@authorized_users_only
async def stop(_, message: Message):
    queues.reset(message.chat.id)
    try:
        await pytgcalls.leave_group_call(message.chat.id)
    except Exception as exc:
        log.info("Leave call returned: %s", exc)
    await message.reply_text(f"Playback and queue cleared by {message.from_user.mention}.")

@Client.on_message(command(["skip", "next"]) & other_filters)
@errors
@authorized_users_only
async def skip(_, message: Message):
    chat_id = message.chat.id
    next_item = queues.get(chat_id)
    if not next_item:
        try:
            await pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        queues.reset(chat_id)
        await message.reply_text("Queue is empty. Playback stopped.")
        return
    try:
        await pytgcalls.change_stream(
            chat_id,
            InputStream(InputAudioStream(next_item["file"])),
        )
        await message.reply_text(f"Skipped to the next track — requested by {message.from_user.mention}.")
    except Exception:
        log.exception("Skip failed in chat %s", chat_id)
        queues.reset(chat_id)
        try:
            await pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        await message.reply_text("Could not switch tracks. The voice-chat stream was stopped; use /play to start again.")
