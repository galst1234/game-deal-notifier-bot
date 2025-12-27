import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import requests
from telegram import Update
from telegram.ext import ContextTypes

from config import ALLOWED_CHATS, BACKEND_URL

logger = logging.getLogger(__name__)


# Potentially replace this with an automatic thing that happens on `Application.add_handler`
def validate_allowed_chats_async(
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Any],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Any]:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat is None:
            return await func(update, context)

        chat_id: int = update.effective_chat.id
        try:
            response = requests.get(f"{BACKEND_URL}/api/v1/allowed-chats/{chat_id}")
            response.raise_for_status()
            data = response.json()
            is_allowed = data.get("is_allowed", False)
        except requests.HTTPError:
            is_allowed = chat_id in ALLOWED_CHATS

        if is_allowed:
            return await func(update, context)
        else:
            logger.info(f"Unauthorized chat id: {chat_id}")
            # Ideally, I want to implement an option to request access, that will send me a message allowing me to
            # approve or deny access, updating the DB accordingly
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry but you are currently an unrecognized user. To gain access to the bot please ask the "
                f"owner to add you to the allowed users. Your chat id: {chat_id}",
            )

    return wrapper
