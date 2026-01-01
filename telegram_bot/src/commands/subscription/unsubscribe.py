import logging

import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config import BACKEND_URL
from utils import validate_allowed_chats_async

logger = logging.getLogger(__name__)


@validate_allowed_chats_async
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        response = requests.delete(f"{BACKEND_URL}/api/v1/subscriptions/{chat_id}")
        if response.status_code == requests.status_codes.codes.NOT_FOUND:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="No active subscription found")
            return

        response.raise_for_status()

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Successfully unsubscribed")


unsubscribe_handler = CommandHandler("unsubscribe", unsubscribe)
