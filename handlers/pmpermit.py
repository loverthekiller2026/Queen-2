"""Optional private-message guard for the assistant account."""
import runtime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_NAME, BOT_USERNAME, PMPERMIT, OWNER_USERNAME, SUPPORT_GROUP, SUDO_USERS

PMSET = True
approved_chats = set()

@runtime.assistant.on_message(filters.text & filters.private & ~filters.me & ~filters.bot)
async def pm_permit(_, message: Message):
    if PMPERMIT != "ENABLE" or not PMSET:
        return
    chat_id = message.chat.id
    if chat_id in approved_chats:
        return
    buttons = [[InlineKeyboardButton("Bot", url="https://t.me/{}".format(BOT_USERNAME))]]
    if SUPPORT_GROUP:
        buttons[0].append(InlineKeyboardButton("Support", url="https://t.me/{}".format(SUPPORT_GROUP)))
    if OWNER_USERNAME:
        buttons.append([InlineKeyboardButton("Owner", url="https://t.me/{}".format(OWNER_USERNAME))])
    await message.reply_text(
        "This is the assistant account for {}. Please contact the bot or support group instead of messaging the assistant.".format(BOT_NAME),
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@Client.on_message(filters.command(["pm", "pmpermit"]))
async def toggle_pm_permit(_, message: Message):
    global PMSET
    if not message.from_user or message.from_user.id not in SUDO_USERS:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or parts[1].lower() not in ("on", "off"):
        await message.reply_text("Usage: /pm on or /pm off")
        return
    PMSET = parts[1].lower() == "on"
    await message.reply_text("Assistant PM permit {}.".format("enabled" if PMSET else "disabled"))

@runtime.assistant.on_message(filters.text & filters.private & filters.me)
async def auto_approve(_, message: Message):
    if message.chat.id not in approved_chats:
        approved_chats.add(message.chat.id)
        await message.reply_text("This chat is approved for assistant messages.")

@runtime.assistant.on_message(filters.command("a", ["!", ".", ""]) & filters.me & filters.private)
async def approve_chat(_, message: Message):
    approved_chats.add(message.chat.id)
    await message.reply_text("Private chat approved.")

@runtime.assistant.on_message(filters.command("da", ["!", ".", ""]) & filters.me & filters.private)
async def disapprove_chat(_, message: Message):
    approved_chats.discard(message.chat.id)
    await message.reply_text("Private chat approval removed.")
