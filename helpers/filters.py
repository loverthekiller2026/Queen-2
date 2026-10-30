
from typing import Union, List

from pyrogram import filters

from config import COMMAND_PREFIXES


# Pyrogram 2 compatible edited-message filter
not_edited = filters.create(
    lambda _, __, message: message.edit_date is None
)

other_filters = (
    filters.group
    & not_edited
    & ~filters.via_bot
    & ~filters.forwarded
)

other_filters2 = (
    filters.private
    & not_edited
    & ~filters.via_bot
    & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)
