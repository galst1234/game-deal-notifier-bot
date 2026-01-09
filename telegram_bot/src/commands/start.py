from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from utils import validate_allowed_chats_async


@validate_allowed_chats_async
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is not None:
        welcome_message = (
            "Welcome to the Game Deal Notifier Bot!\n\n"
            "Available commands:\n\n"
            "/start - Show this help message\n"
            "/current_giveaways - View currently available game giveaways\n"
            "/subscribe - Subscribe to daily game deal notifications\n"
            "/unsubscribe - Unsubscribe from notifications"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)


start_handler = CommandHandler("start", start)
