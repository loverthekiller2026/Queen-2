"""Health and runtime statistics command."""
import time
import psutil
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from handlers import StartTime
from helpers.filters import command
from config import BOT_NAME, SUPPORT_GROUP, CHANNEL_UPDATES

def readable_time(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days: parts.append("{}d".format(days))
    if hours: parts.append("{}h".format(hours))
    if minutes: parts.append("{}m".format(minutes))
    parts.append("{}s".format(seconds))
    return " ".join(parts)

@Client.on_message(command(["ping", "alive"]) & filters.group & ~filters.edited)
async def ping(_, message: Message):
    started = time.perf_counter()
    sent = await message.reply_text("Checking…")
    latency = (time.perf_counter() - started) * 1000
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime = readable_time(time.time() - StartTime)
    buttons = []
    if SUPPORT_GROUP:
        buttons.append(InlineKeyboardButton("Support", url="https://t.me/{}".format(SUPPORT_GROUP)))
    if CHANNEL_UPDATES:
        buttons.append(InlineKeyboardButton("Updates", url="https://t.me/{}".format(CHANNEL_UPDATES)))
    markup = InlineKeyboardMarkup([buttons]) if buttons else None
    text = ("**{} status**\n\nPing: {:.1f} ms\nUptime: {}\nCPU: {}%\nRAM: {}%\nDisk: {}%").format(
        BOT_NAME, latency, uptime, cpu, ram, disk
    )
    await sent.edit_text(text, reply_markup=markup)
