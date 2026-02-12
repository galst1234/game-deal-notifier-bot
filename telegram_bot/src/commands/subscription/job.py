import logging
from typing import Any

import requests
from telegram import LinkPreviewOptions
from telegram.ext import CallbackContext

from config import BACKEND_URL
from isthereanydeal.deals_list import DealItem
from isthereanydeal.utils import format_deals_list

logger = logging.getLogger(__name__)


async def subscriptions_job(context: CallbackContext) -> None:
    response = requests.get(f"{BACKEND_URL}/api/v1/notifications/pending")
    response.raise_for_status()
    pending_notifications: list[dict[str, Any]] = response.json()
    if not pending_notifications:
        logger.info("No pending notifications found")
        return

    logger.info(f"Pending notifications: {len(pending_notifications)}")
    for notification in pending_notifications:
        chat_id: int = notification["chat_id"]
        deals = [DealItem.model_validate(deal) for deal in notification["deals"]]
        try:
            if deals:
                message = format_deals_list(deals, "Current giveaways:")
                if message:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="Markdown",
                        link_preview_options=LinkPreviewOptions(is_disabled=True),
                    )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="No new giveaways today. See you tomorrow!",
                )
        except Exception as e:
            logger.error(f"Failed to send notification to chat_id {chat_id}: {e}")
