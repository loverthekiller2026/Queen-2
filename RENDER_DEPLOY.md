# Queen-2 Render deployment

## Runtime

- Python 3.10
- Pyrogram 1.4.16
- PyTgCalls 0.8.6
- FFmpeg installed by the Dockerfile (for Docker deployments) or provided by the Render build environment if using the native Python runtime.

## Required Render environment variables

| Variable | Value |
| --- | --- |
| API_ID | Telegram application ID from my.telegram.org |
| API_HASH | Telegram application hash |
| BOT_TOKEN | Token for the bot created with BotFather |
| SESSION_NAME | Assistant account's Pyrogram String Session |
| SUDO_USERS | Telegram user IDs separated by spaces or commas |

Optional variables: BOT_NAME, BOT_USERNAME, OWNER_USERNAME, SUPPORT_GROUP, CHANNEL_UPDATES, DURATION_LIMIT, COMMAND_PREFIXES.

Never commit .env files, bot tokens, API hashes, or String Sessions. Store them only in Render's environment-variable settings. Do not paste a String Session into issues, logs, or chat messages.

## Deploy as a Render Web Service

1. Push or select the branch codex/complete-render-rewrite.
2. In Render, create a Blueprint from the repository and use render.yaml, or create a Python Web Service manually.
3. Set the required environment variables above.
4. Use build command: pip install --upgrade pip wheel && pip install -r requirements.txt
5. Use start command: python main.py
6. Set the health-check path to /health.

The HTTP health server binds to 0.0.0.0 and uses Render's PORT environment variable (default 10000).

## Telegram setup

Add the assistant account to the target group and promote it with the Manage Video Chats permission. The bot itself needs the permissions required by the commands and group settings. Use /join if the assistant is not already in the group.

## Important hosting limitation

Render's free Web Services can spin down after inactivity. A health endpoint helps Render verify that the process is alive, but it does not guarantee uninterrupted 24/7 voice-chat playback. Use a paid always-on instance or a suitable always-on host if continuous playback is essential.

## Local syntax check

Run:

    python -m compileall -q .

The GitHub Actions workflow runs this check on pushes to the development branch and pull requests targeting main.
