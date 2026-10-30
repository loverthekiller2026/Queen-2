"""Download a YouTube audio track and send it as a Telegram audio message."""
import asyncio
import logging
import os

from pyrogram import Client, filters
from pyrogram.types import Message
from youtube_search import YoutubeSearch

from config import BOT_NAME
from downloaders.youtube import download
from helpers.filters import command

log = logging.getLogger(__name__)

@Client.on_message(command(["song", "music", "vsong", "video"]) & filters.group & ~filters.channel)
async def song(client: Client, message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Usage: /song <song name>")
        return
    query = parts[1].strip()
    status = await message.reply_text("Searching and downloading…")
    audio_path = None
    try:
        results = await asyncio.to_thread(lambda: YoutubeSearch(query, max_results=1).to_dict())
        if not results:
            await status.edit_text("No matching song found.")
            return
        item = results[0]
        url = "https://www.youtube.com" + item["url_suffix"]
        title = item.get("title", "Audio")
        audio_path = await asyncio.to_thread(download, url)
        await client.send_audio(
            message.chat.id,
            audio_path,
            title=title[:64],
            performer=BOT_NAME,
            caption="Uploaded by {}. Requested by {}.".format(BOT_NAME, message.from_user.mention),
            reply_to_message_id=message.id,
        )
        await status.delete()
    except Exception as exc:
        log.exception("Song download failed")
        await status.edit_text("Download failed: {}: {}".format(type(exc).__name__, exc))
    finally:
        if audio_path and os.path.isfile(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                log.warning("Could not remove temporary audio file %s", audio_path)
