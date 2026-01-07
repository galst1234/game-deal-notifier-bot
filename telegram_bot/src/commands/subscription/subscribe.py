import datetime
import logging
import re
from datetime import time
from zoneinfo import ZoneInfo

import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from config import BACKEND_URL, TIMEZONE
from utils import validate_allowed_chats_async

logger = logging.getLogger(__name__)

TIME_PATTERN = re.compile(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$")

CONVERSATION_STATE_ASKING_TIME = 0


@validate_allowed_chats_async
async def subscribe_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "What time should I send your daily notifications?\n"
        "Enter time in 24-hour format (HH:MM)\n"
        "Example: 18:00 or 09:30\n\n"
        "Send /cancel to cancel.",
    )
    return CONVERSATION_STATE_ASKING_TIME


def _convert_to_utc_time(local_time: time) -> time:
    local_tz = ZoneInfo(TIMEZONE)
    today = datetime.date.today()
    local_datetime = datetime.datetime.combine(today, local_time, tzinfo=local_tz)
    utc_datetime = local_datetime.astimezone(datetime.UTC)
    utc_time = utc_datetime.time()
    return utc_time


async def receive_time(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()
    match = TIME_PATTERN.match(user_input)
    if not match:
        await update.message.reply_text(
            "Invalid time format. Please use HH:MM (24-hour format).\nExample: 18:00 or 09:30",
        )
        return CONVERSATION_STATE_ASKING_TIME

    hours, minutes = int(match.group(1)), int(match.group(2))
    local_time = datetime.time(hours, minutes)

    utc_time = _convert_to_utc_time(local_time)

    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/subscriptions",
                json={
                    "chat_id": chat_id,
                    "time": utc_time.isoformat(),
                },
            )
            response.raise_for_status()

            await update.message.reply_text(
                f"Subscribed successfully!\n\n"
                f"You'll receive daily notifications at {local_time.strftime('%H:%M')} local time.",
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to subscribe: {e}")
            await update.message.reply_text("Failed to subscribe. Please try again later.")
            return ConversationHandler.END

    return ConversationHandler.END


async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Subscription cancelled.")
    return ConversationHandler.END


subscribe_handler = ConversationHandler(
    entry_points=[CommandHandler("subscribe", subscribe_start)],
    states={
        CONVERSATION_STATE_ASKING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
