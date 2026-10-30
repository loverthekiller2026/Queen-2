"""Owner-only Python evaluation and shell helper."""
import asyncio
import os
import sys
import traceback
from io import StringIO
from time import time

from pyrogram import Client, filters
from pyrogram.types import Message
from config import BOT_USERNAME
from helpers.decorators import sudo_users_only
from helpers.filters import command

async def aexec(code, client, message):
    scope = {}
    source = "async def __aexec(client, message):\n" + "".join("    " + line + "\n" for line in code.splitlines())
    exec(source, scope)
    return await scope["__aexec"](client, message)

async def reply_output(message, text):
    if message.from_user and message.from_user.is_self:
        await message.edit_text(text)
    else:
        await message.reply_text(text)

@Client.on_message(command(["eval", "eval@{}".format(BOT_USERNAME)]) & not_edited)
@sudo_users_only
async def executor(client, message: Message):
    if len(message.command) < 2:
        return await reply_output(message, "Provide Python code to execute.")
    code = message.text.split(" ", 1)[1]
    started = time()
    old_out, old_err = sys.stdout, sys.stderr
    out, err = StringIO(), StringIO()
    sys.stdout, sys.stderr = out, err
    error = None
    try:
        await aexec(code, client, message)
    except Exception:
        error = traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    result = error or err.getvalue() or out.getvalue() or "Success"
    result = result[:3500]
    await reply_output(message, "Output:\n{}\nElapsed: {:.3f}s".format(result, time() - started))

@Client.on_message(command(["sh", "sh@{}".format(BOT_USERNAME)]) & not_edited)
@sudo_users_only
async def shellrunner(client, message: Message):
    if len(message.command) < 2:
        return await reply_output(message, "Usage: /sh <command>")
    command_text = message.text.split(None, 1)[1]
    try:
        process = await asyncio.create_subprocess_shell(
            command_text,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        output = (stdout + stderr).decode("utf-8", "replace") or "No output"
    except Exception as exc:
        output = "{}: {}".format(type(exc).__name__, exc)
    await reply_output(message, output[:3500])
