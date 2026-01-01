import datetime
import logging

import requests
from telegram import LinkPreviewOptions, Update
from telegram.ext import CallbackContext, CommandHandler, ContextTypes

from config import BACKEND_URL
from isthereanydeal.giveaways import get_current_giveaways
from isthereanydeal.utils import format_deals_list
from utils import validate_allowed_chats_async

NOTIFICATION_TIME = datetime.time(7, 0, tzinfo=datetime.UTC)

logger = logging.getLogger(__name__)


@validate_allowed_chats_async
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        response = requests.post(
            f"{BACKEND_URL}/api/v1/subscriptions",
            json={
                "chat_id": chat_id,
                "time": NOTIFICATION_TIME.isoformat(),
            },
        )
        response.raise_for_status()

        await context.bot.send_message(chat_id=chat_id, text="Subscribed to daily notifications successfully")


async def _send_notification(context: CallbackContext) -> None:
    job = context.job
    if job is None:
        logger.error("No job found in context")
        return
    if job.chat_id is None:
        logger.error("No chat_id found in job")
        return

    giveaways = get_current_giveaways()
    message = format_deals_list(giveaways, "Current giveaways:")
    if message:
        await context.bot.send_message(
            chat_id=job.chat_id,
            text=message,
            parse_mode="Markdown",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


subscribe_handler = CommandHandler("subscribe", subscribe)
