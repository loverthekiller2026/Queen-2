"""Non-blocking /play pipeline with a per-chat playback queue."""
import asyncio
import logging
import os
from urllib.parse import urlparse

import runtime
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from pytgcalls.types.input_stream import InputAudioStream, InputStream
from pytgcalls import StreamType

from config import DURATION_LIMIT
from helpers.filters import command
from helpers.decorators import errors
from helpers.errors import DurationLimitError
from callsmusic import queues
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
            raise DurationLimitError("Maximum allowed duration is {} minutes.".format(DURATION_LIMIT))
        os.makedirs("downloads", exist_ok=True)
        downloaded = await reply.download(file_name=os.path.join("downloads", "{}.media".format(media.file_unique_id)))
        title = getattr(media, "file_name", None) or "Telegram audio"
        return await convert(downloaded), title

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        raise ValueError("Usage: /play <song name or YouTube URL>, or reply to an audio file.")
    query = parts[1].strip()
    if _is_url(query):
        url, title = query, query
    else:
        url, title = await _find_youtube_url(query)
    source = await asyncio.to_thread(download_youtube, url)
    return await convert(source), title


async def _ensure_assistant_in_chat(client, message):
    me = await runtime.assistant.get_me()
    try:
        member = await client.get_chat_member(message.chat.id, me.id)
    except Exception as exc:
        raise ValueError("Assistant is not in this group. Add it with /join first.") from exc
    if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
        raise ValueError("Assistant is not in this group. Add it with /join first.")
    if member.status != ChatMemberStatus.ADMINISTRATOR or not getattr(member, "can_manage_voice_chats", False):
        raise ValueError("Promote the assistant and enable Manage Video Chats permission.")


@Client.on_message(command(["play", "p"]) & filters.group & not_edited & ~filters.forwarded & ~filters.via_bot)
@errors
async def play(client: Client, message: Message):
    status = await message.reply_text("Preparing your track…")
    try:
        file_path, title = await _prepare_audio(message)
        async with _lock(message.chat.id):
            await _ensure_assistant_in_chat(client, message)
            active = {int(call.chat_id) for call in runtime.pytgcalls.active_calls}
            if message.chat.id in active:
                position = await queues.put(message.chat.id, file=file_path, title=title)
                await status.edit_text("Added to queue at position #{}: {}".format(position, title))
            else:
                await runtime.pytgcalls.join_group_call(
                    message.chat.id,
                    InputStream(InputAudioStream(file_path)),
                    stream_type=StreamType().local_stream,
                )
                await status.edit_text("Now playing: {}".format(title))
    except Exception as exc:
        log.exception("Play request failed in chat %s", message.chat.id)
        await status.edit_text("Unable to play this track: {}: {}".format(type(exc).__name__, exc))
