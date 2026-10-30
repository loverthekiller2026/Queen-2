"""Runtime objects shared by Pyrogram plugin modules."""
bot = None
assistant = None
pytgcalls = None

def configure(bot_client, assistant_client, calls_client):
    global bot, assistant, pytgcalls
    bot = bot_client
    assistant = assistant_client
    pytgcalls = calls_client
