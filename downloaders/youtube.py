"""Async YouTube audio downloader using the same Shruti API flow as ShizuMusic.

The API key is supplied through the hosting environment; never commit it.
"""
import asyncio
import logging
import os
import re
from urllib.parse import parse_qs, urlparse

import aiofiles
import aiohttp

log = logging.getLogger(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
_download_locks: dict[str, asyncio.Lock] = {}


def _video_id(value: str) -> str:
    value = (value or "").strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        query_id = parse_qs(parsed.query).get("v", [None])[0]
        parts = [part for part in parsed.path.split("/") if part]
        candidate = query_id or (parts[1] if len(parts) > 1 and parts[0] in {"shorts", "embed", "live"} else "")
    else:
        candidate = value
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate or ""):
        raise ValueError("Please provide a valid YouTube video URL.")
    return candidate


async def download(url: str) -> str:
    """Download a YouTube audio track through the configured Shruti API."""
    video_id = _video_id(url)
    api_url = os.getenv("YT_API_URL", "https://api01.shrutibots.site").strip().rstrip("/")
    api_key = os.getenv("YT_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("YT_API_KEY is missing in Render environment variables.")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    lock = _download_locks.setdefault(video_id, asyncio.Lock())
    async with lock:
        if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        temp_path = f"{file_path}.{os.getpid()}.part"
        timeout = aiohttp.ClientTimeout(total=900, connect=20, sock_read=900)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{api_url}/download",
                    params={"url": video_id, "type": "audio", "api_key": api_key},
                ) as response:
                    if response.status != 200:
                        detail = (await response.text())[:300]
                        raise RuntimeError(f"YouTube audio API returned HTTP {response.status}: {detail}")
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "json" in content_type or "text/" in content_type:
                        detail = (await response.text())[:300]
                        raise RuntimeError(f"YouTube audio API returned an error: {detail}")
                    async with aiofiles.open(temp_path, "wb") as output:
                        async for chunk in response.content.iter_chunked(128 * 1024):
                            await output.write(chunk)

            if not os.path.isfile(temp_path) or os.path.getsize(temp_path) == 0:
                raise RuntimeError("YouTube audio API returned an empty audio file.")
            os.replace(temp_path, file_path)
            log.info("YouTube audio downloaded: %s (%s bytes)", video_id, os.path.getsize(file_path))
            return file_path
        except Exception:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
            raise
