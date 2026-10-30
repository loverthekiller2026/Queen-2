"""Reusable command authorization and error wrappers."""
import logging
from functools import wraps

from config import SUDO_USERS
from helpers.admins import get_administrators

log = logging.getLogger(__name__)

def errors(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as exc:
            log.exception("Handler %s failed", func.__name__)
            try:
                await message.reply_text("Error: {}: {}".format(type(exc).__name__, exc))
            except Exception:
                pass
    return wrapper

def authorized_users_only(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user = message.from_user
        if not user:
            return
        if user.id in SUDO_USERS:
            return await func(client, message, *args, **kwargs)
        if message.chat.type == "private":
            return
        admins = await get_administrators(client, message.chat)
        if user.id in admins:
            return await func(client, message, *args, **kwargs)
        return await message.reply_text("Only group administrators can use this command.")
    return wrapper

def sudo_users_only(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        if message.from_user and message.from_user.id in SUDO_USERS:
            return await func(client, message, *args, **kwargs)
        return await message.reply_text("This command is restricted to configured SUDO_USERS.")
    return wrapper
