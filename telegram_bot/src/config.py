import os

ALLOWED_CHATS: list[int] = [int(chat_id) for chat_id in os.getenv("ALLOWED_CHATS", "").split(",")]
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
ISTHEREANYDEAL_API_KEY: str = os.getenv("ISTHEREANYDEAL_API_KEY", "")
TIMEZONE: str = os.getenv("TIMEZONE", "UTC")

BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
