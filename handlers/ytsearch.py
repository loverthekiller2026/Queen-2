"""YouTube search command."""
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from youtube_search import YoutubeSearch

@Client.on_message(filters.command(["search"]))
async def ytsearch(_, message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Give a song or artist name to search.")
        return
    status = await message.reply_text("Searching…")
    try:
        results = await asyncio.to_thread(
            lambda: YoutubeSearch(parts[1], max_results=5).to_dict()
        )
        if not results:
            await status.edit_text("No results found.")
            return
        lines = []
        for item in results:
            lines.append(
                "Title: {title}\nDuration: {duration}\nChannel: {channel}\nLink: https://youtube.com{url}\n".format(
                    title=item.get("title", "Unknown"),
                    duration=item.get("duration", "Unknown"),
                    channel=item.get("channel", "Unknown"),
                    url=item.get("url_suffix", ""),
                )
            )
        await status.edit_text("\n".join(lines), disable_web_page_preview=True)
    except Exception as exc:
        await status.edit_text("Search failed: {}: {}".format(type(exc).__name__, exc))
