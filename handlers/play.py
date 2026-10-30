"""Non-blocking /play pipeline with a per-chat playback queue."""
import asyncio
import logging
import os
import re
from urllib.parse import urlparse

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserAlreadyParticipant
from pytgcalls.types.input_stream import InputAudioStream, InputStream
from pytgcalls import StreamType

from config import DURATION_LIMIT, SUPPORT_GROUP, CHANNEL_UPDATES
from helpers.filters import command
from helpers.decorators import errors
from helpers.errors import DurationLimitError
from helpers.admins import get_administrators
from callsmusic import queues
from main import assistant, pytgcalls
from converter import convert
from downloaders.youtube import download as download_youtube

log = logging.getLogger(__name__)
PLAY_LOCKS = {}

def _lock(chat_id):
    return PLAY_LOCKS.setdefault(int(chat_id), asyncio.Lock())

def _is_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

async def _find_youtube_url(query):
    from youtube_search import YoutubeSearch
    results = await asyncio.to_thread(lambda: YoutubeSearch(query, max_results=1).to_dict())
    if not results:
        raise ValueError("No matching track was found.")
    return "https://www.youtube.com" + results[0]["url_suffix"], results[0]["title"]

async def _prepare_audio(message):
    reply = message.reply_to_message
    if reply and (reply.audio or reply.voice):
        media = reply.audio or reply.voice
        if media.duration and media.duration > DURATION_LIMIT * 60:
            raise DurationLimitError(f"Maximum allowed duration is {DURATION_LIMIT} minutes.")
        os.makedirs("downloads", exist_ok=True)
        downloaded = await reply.download(file_name=os.path.join("downloads", f"{media.file_unique_id}.media"))
        title = getattr(media, "file_name", None) or "Telegram audio"
        return await convert(downloaded), title

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        raise ValueError("Usage: /play <song name or YouTube URL>, or reply to an audio file.")
    query = parts[1].strip()
    if _is_url(query):
        url = query
        title = query
    else:
        url, title = await _find_youtube_url(query)
    source = await asyncio.to_thread(download_youtube, url)
    return await convert(source), title

async def _ensure_assistant_in_chat(client, message):
    me = await assistant.get_me()
    try:
        member = await client.get_chat_member(message.chat.id, me.id)
        if member.status in ("left", "kicked"):
            raise ValueError("Assistant is not a member of this group. Use /join first.")
    except Exception as exc:
        if "Assistant is not a member" in str(exc):
            raise
        raise ValueError("I cannot verify assistant membership. Add the assistant to the group and grant Manage Video Chats permission.") from exc

@Client.on_message(
    command(["play", "p"]) & filters.group & ~filters.edited & ~filters.forwarded & ~filters.via_bot
)
@errors
async def play(client: Client, message: Message):
    status = await message.reply_text("Preparing your track…")
    try:
        file_path, title = await _prepare_audio(message)
        async with _lock(message.chat.id):
            await _ensure_assistant_in_chat(client, message)
            if message.chat.id in {int(call.chat_id) for call in pytgcalls.active_calls}:
                position = await queues.put(message.chat.id, file=file_path, title=title)
                await status.edit_text(f"Added to queue at position #{position}: {title}")
            else:
                await pytgcalls.join_group_call(
                    message.chat.id,
                    InputStream(InputAudioStream(file_path)),
                    stream_type=StreamType().local_stream,
                )
                await status.edit_text(f"Now playing: {title}")
    except Exception as exc:
        log.exception("Play request failed in chat %s", message.chat.id)
        await status.edit_text(f"Unable to play this track: {type(exc).__name__}: {exc}")

