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
from helpers.filters import command, not_edited
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
    source = await download_youtube(url)
    return await convert(source), title


async def _ensure_assistant_in_chat(client, message):
    # Always inspect membership through the user session that joins the call.
    assistant = runtime.assistant
    me = await assistant.get_me()
    try:
        member = await assistant.get_chat_member(message.chat.id, me.id)
    except Exception as exc:
        log.exception(
            "Assistant membership lookup failed: chat_id=%s assistant_id=%s",
            message.chat.id,
            me.id,
        )
        raise ValueError(
            "I couldn't verify the assistant's membership in this group. "
            "Check that the assistant user account has joined this exact group."
        ) from exc

    status = member.status
    # Telegram represents the group creator as OWNER, not ADMINISTRATOR.
    # Owners have all administrator rights implicitly, so do not reject them
    # because an individual can_manage_* flag is absent/None.
    if status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, ChatMemberStatus.RESTRICTED):
        raise ValueError("Assistant is not an active member of this group. Add the assistant account first.")

    if status == ChatMemberStatus.OWNER:
        log.info("Assistant membership verified: chat_id=%s assistant_id=%s status=OWNER", message.chat.id, me.id)
        return

    if status != ChatMemberStatus.ADMINISTRATOR:
        log.warning(
            "Assistant lacks administrator status: chat_id=%s assistant_id=%s status=%s",
            message.chat.id,
            me.id,
            status,
        )
        raise ValueError("The assistant account must be an administrator in this group.")

    # Pyrogram exposes administrator rights inside member.privileges.
    # Older code checked the ChatMember object itself, which returns None.
    privileges = getattr(member, "privileges", None)
    can_manage_calls = None
    if privileges is not None:
        can_manage_calls = getattr(privileges, "can_manage_video_chats", None)
        if can_manage_calls is None:
            can_manage_calls = getattr(privileges, "can_manage_voice_chats", None)

    # Compatibility fallback for wrappers exposing rights on ChatMember.
    if can_manage_calls is None:
        can_manage_calls = getattr(member, "can_manage_video_chats", None)
    if can_manage_calls is None:
        can_manage_calls = getattr(member, "can_manage_voice_chats", None)

    log.info(
        "Assistant admin rights: chat_id=%s assistant_id=%s status=%s "
        "privileges=%r can_manage_video_chats=%r",
        message.chat.id,
        me.id,
        status,
        privileges,
        can_manage_calls,
    )
    if can_manage_calls is not True:
        raise ValueError(
            "Telegram reports that the assistant admin lacks Manage Video Chats permission. "
            "Please recheck the permission on this exact group."
        )


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
