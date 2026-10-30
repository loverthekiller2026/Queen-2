"""Administrator lookup with a short-lived in-process cache."""
import time
from typing import Dict, List, Tuple

from pyrogram.enums import ChatMembersFilter

_cache: Dict[int, Tuple[float, List[int]]] = {}
TTL = 60


async def get_administrators(client, chat):
    now = time.monotonic()
    cached = _cache.get(chat.id)
    if cached and now - cached[0] < TTL:
        return list(cached[1])
    admins = []
    async for member in client.get_chat_members(
        chat.id, filter=ChatMembersFilter.ADMINISTRATORS
    ):
        admins.append(member.user.id)
    _cache[chat.id] = (now, admins)
    return list(admins)
