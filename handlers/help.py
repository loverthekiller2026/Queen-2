import asyncio
from helpers.filters import command
from config import BOT_NAME, SUPPORT_GROUP, CHANNEL_UPDATES, START_IMG
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery



@Client.on_message(command("help") & filters.private & ~filters.group & not_edited)
async def help_cmd(client: Client, message: Message):
    await message.reply_sticker("CAACAgUAAx0CZ80CewABAn7iY0QmDt7nsecHlSDH7oMXmtavNH4AAhMHAALnnCFW1zONdkHrocAeBA")
    await message.reply_photo(f"{START_IMG}", caption=f"""
🔴 **AVAILABLE COMMAND IN {BOT_NAME} :**

✅ /play : Start streaming the requested track on videochat.
✅ /pause : Pause the stream.
✅ /resume : Resume the paused stream.
✅ /skip : Skip the current playing stream and start streaming the nexttrack in queue.
✅ /end : Clears the queue and the current playing stream.
✅ /ping : Show the ping and system stats of the bot.
✅ /join : Request the assistant to join your chat.
✅ /id : Sends you the id of the user or replied file.
✅ /song : Downloads the requested the song and send it to you .
✅ /search : Search the given query on youtube and shows you the result.

🔵 **SUDO COMMAND :**

✅ /broadcast : Broadcast a massage to served chats of the bot.
✅ /eval or /sh : Runs the gives codes on the bot's terminal.
✅ /rmw : Clears all the cache photos on the bot's server.
✅ /rmp : Clears the raw files of the bot.
✅ /rmd : Clears the download files on the bot's server.""",
    reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📨 Support", url=f"https://t.me/{SUPPORT_GROUP}"
                    ),
                    InlineKeyboardButton(
                        "📨 Channel", url=f"https://t.me/{CHANNEL_UPDATES}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗑️ Close", callback_data="close_play"
                    )
                ]
            ]
       ),
    )
