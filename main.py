"""Queen-2 process entry point for the legacy PyTgCalls 0.8.6 sync API."""
import logging
import os

from pyrogram import Client, idle
from pytgcalls import PyTgCalls

# py-tgcalls 0.8.6 expects Pyrogram's get_me() result to be a dict.
# Pyrogram 2.0.106 returns a User object, so adapt this one bridge method.
from pytgcalls.mtproto.pyrogram_client import PyrogramClient as _PyrogramClient


async def _pyrogram_get_id_compat(self):
    me = await self._app.get_me()
    return me.id if hasattr(me, "id") else me["id"]


_PyrogramClient.get_id = _pyrogram_get_id_compat

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_NAME
from health_server import start_health_server, set_ready
from callsmusic.callsmusic import configure as configure_playback
import runtime

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("queen")

bot = Client(
    "queen_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "handlers"},
    workers=8,
)
# Pyrogram 2.0.106 supports the session_string keyword and includes
# the newer MTProto message-id/time synchronization fixes.
assistant = Client(
    "queen_assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_NAME,
    workers=4,
)
pytgcalls = configure_playback(PyTgCalls(assistant))
runtime.configure(bot, assistant, pytgcalls)


def main():
    start_health_server()
    started_bot = started_assistant = started_calls = False
    try:
        log.info("Starting Queen-2 bot client")
        bot.start()
        started_bot = True
        log.info("Starting assistant user session")
        assistant.start()
        started_assistant = True
        me = assistant.get_me()
        log.info("Assistant authorized as @%s (id=%s)", me.username, me.id)
        log.info("Starting PyTgCalls 0.8.6")
        pytgcalls.start()
        started_calls = True
        set_ready(True)
        log.info("Queen-2 is ready")
        idle()
    finally:
        set_ready(False)
        log.info("Stopping Queen-2")
        if started_calls:
            try:
                pytgcalls.stop()
            except Exception:
                log.exception("Error stopping PyTgCalls")
        if started_assistant:
            try:
                assistant.stop()
            except Exception:
                log.exception("Error stopping assistant")
        if started_bot:
            try:
                bot.stop()
            except Exception:
                log.exception("Error stopping bot")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
