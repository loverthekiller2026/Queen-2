"""Shared PyTgCalls instance and per-chat playback lifecycle."""
import asyncio
import logging

from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputAudioStream, InputStream

from . import queues

log = logging.getLogger(__name__)
pytgcalls = None

def configure(instance):
    global pytgcalls
    pytgcalls = instance
    instance.on_stream_end()(on_stream_end)
    return instance

async def on_stream_end(client, update: Update):
    chat_id = int(update.chat_id)
    try:
        next_item = queues.get(chat_id)
        if not next_item:
            await client.leave_group_call(chat_id)
            queues.reset(chat_id)
            log.info("Playback finished in chat %s", chat_id)
            return
        await client.change_stream(
            chat_id,
            InputStream(InputAudioStream(next_item["file"])),
        )
        log.info("Started queued track in chat %s", chat_id)
    except Exception:
        log.exception("Could not advance playback queue in chat %s", chat_id)
        try:
            await client.leave_group_call(chat_id)
        except Exception:
            pass
        queues.reset(chat_id)
