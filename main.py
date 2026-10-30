"""Queen-2 process entry point for Render Web Services."""
import asyncio
import logging
import os
from pyrogram import Client, idle
from pytgcalls import PyTgCalls
from config import API_ID, API_HASH, BOT_TOKEN, SESSION_NAME
from health_server import start_health_server
from callsmusic.callsmusic import configure

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("queen")

bot = Client("queen_bot", api_id=API_ID, api_hash=API_HASH,
    bot_token=BOT_TOKEN, plugins={"root": "handlers"}, workers=8)
assistant = Client("queen_assistant", api_id=API_ID, api_hash=API_HASH,
    session_string=SESSION_NAME, workers=4)
pytgcalls = configure(PyTgCalls(assistant))

async def main():
    start_health_server()
    started_bot = started_assistant = started_calls = False
    try:
        log.info("Starting Queen-2 bot client")
        await bot.start()
        started_bot = True
        log.info("Starting assistant user session")
        await assistant.start()
        started_assistant = True
        me = await assistant.get_me()
        log.info("Assistant authorized as @%s (id=%s)", me.username, me.id)
        log.info("Starting PyTgCalls")
        await pytgcalls.start()
        started_calls = True
        log.info("Queen-2 is ready")
        await idle()
    finally:
        log.info("Stopping Queen-2")
        if started_calls:
            try: await pytgcalls.stop()
            except Exception: log.exception("Error stopping PyTgCalls")
        if started_assistant:
            try: await assistant.stop()
            except Exception: log.exception("Error stopping assistant")
        if started_bot:
            try: await bot.stop()
            except Exception: log.exception("Error stopping bot")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
