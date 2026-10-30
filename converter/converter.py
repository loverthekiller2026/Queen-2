"""Convert audio into the PCM format expected by the legacy PyTgCalls API."""
import asyncio
import os
import hashlib

from helpers.errors import FFmpegReturnCodeError

async def convert(file_path: str) -> str:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)
    os.makedirs("raw_files", exist_ok=True)
    stem = hashlib.sha256(os.path.abspath(file_path).encode()).hexdigest()[:20]
    output = os.path.join("raw_files", "{}.raw".format(stem))
    if os.path.isfile(output) and os.path.getsize(output) > 0:
        return output
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", file_path, "-vn", "-f", "s16le", "-ac", "1",
        "-ar", "48000", "-acodec", "pcm_s16le", output,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0 or not os.path.isfile(output) or os.path.getsize(output) == 0:
        detail = stderr.decode("utf-8", "replace")[-1500:] if stderr else "unknown FFmpeg error"
        raise FFmpegReturnCodeError(detail)
    return output
