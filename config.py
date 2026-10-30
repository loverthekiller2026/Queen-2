"""Validated runtime configuration for Queen-2."""
import os
from dotenv import load_dotenv

load_dotenv()

def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def _int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be at least {minimum}")
    return value

API_ID = _int("API_ID", 0)
API_HASH = _required("API_HASH")
BOT_TOKEN = _required("BOT_TOKEN")
SESSION_NAME = _required("SESSION_NAME")  # Pyrogram assistant String Session
BOT_NAME = os.getenv("BOT_NAME", "Queen Music").strip() or "Queen Music"
BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip().lstrip("@")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "").strip().lstrip("@")
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "helping_support").strip().lstrip("@")
CHANNEL_UPDATES = os.getenv("CHANNEL_UPDATES", "QN_Bot_Updates").strip().lstrip("@")
DURATION_LIMIT = _int("DURATION_LIMIT", 90)
START_IMG = os.getenv("START_IMG", "https://te.legra.ph/file/eb7410fffe276ae21d118.jpg")
PING_IMG = os.getenv("PING_IMG", "https://te.legra.ph/file/262e434f76a5f2e414178.jpg")
COMMAND_PREFIXES = list(os.getenv("COMMAND_PREFIXES", "/").strip() or "/")
PMPERMIT = os.getenv("PMPERMIT", "ENABLE").upper()
SUDO_USERS = []
for item in os.getenv("SUDO_USERS", "").replace(",", " ").split():
    try:
        SUDO_USERS.append(int(item))
    except ValueError:
        raise RuntimeError("SUDO_USERS must contain numeric Telegram user IDs separated by spaces or commas")
