import logging

import requests
from telegram import LinkPreviewOptions
from telegram.ext import CallbackContext

from config import BACKEND_URL
from isthereanydeal.giveaways import get_current_giveaways
from isthereanydeal.utils import format_deals_list

logger = logging.getLogger(__name__)


async def subscriptions_job(context: CallbackContext) -> None:
    response = requests.get(f"{BACKEND_URL}/api/v1/notifications/pending")
    response.raise_for_status()
    pending_chat_ids = response.json()
    if not pending_chat_ids:
        logger.info("No pending subscriptions found")
        return

    logger.info(f"Pending chat_ids: {pending_chat_ids}")
    for chat_id in pending_chat_ids:
        try:
            giveaways = get_current_giveaways()
            message = format_deals_list(giveaways, "Current giveaways:")
            if message:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
        except Exception as e:
            logger.error(f"Failed to send notification to chat_id {chat_id}: {e}")
