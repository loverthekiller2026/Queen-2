"""Synchronous yt-dlp helpers; call them through asyncio.to_thread in handlers."""
import os
from yt_dlp import YoutubeDL

from config import DURATION_LIMIT
from helpers.errors import DurationLimitError

os.makedirs("downloads", exist_ok=True)

def _options():
    return {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 20,
        "cachedir": False,
    }

def download(url: str) -> str:
    with YoutubeDL(_options()) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration")
        if duration and duration > DURATION_LIMIT * 60:
            raise DurationLimitError(
                f"Tracks longer than {DURATION_LIMIT} minutes are not allowed."
            )
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.isfile(filename):
            # Some post-processors can change the extension; find the downloaded ID.
            media_id = info.get("id", "")
            matches = [
                os.path.join("downloads", name)
                for name in os.listdir("downloads")
                if name.startswith(media_id + ".")
            ]
            if not matches:
                raise FileNotFoundError("yt-dlp completed without producing an audio file")
            filename = matches[0]
        return filename
