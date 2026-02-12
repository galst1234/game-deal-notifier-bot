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
CONVERSATION_STATE_ASKING_TYPE = 1

SUBSCRIPTION_TYPES: dict[str, tuple[str, str]] = {
    "1": ("new_notify_empty", "New only (notify when none)"),
    "2": ("new_silent_empty", "New only (silent when none)"),
    "3": ("all", "All giveaways every time"),
}


@validate_allowed_chats_async
async def subscribe_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

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


async def receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return ConversationHandler.END

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

    if context.user_data is not None:
        context.user_data["subscribe_utc_time"] = utc_time.isoformat()
        context.user_data["subscribe_local_time"] = local_time.strftime("%H:%M")

    await update.message.reply_text(
        "What type of subscription would you like?\n\n"
        "1. New only (notify when none) - Only new giveaways; sends 'nothing new' if none\n"
        "2. New only (silent when none) - Only new giveaways; no message if none\n"
        "3. All giveaways - Show all current giveaways every time\n\n"
        "Reply with 1, 2, or 3.\n"
        "Send /cancel to cancel.",
    )
    return CONVERSATION_STATE_ASKING_TYPE


async def receive_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None or update.effective_chat is None:
        return ConversationHandler.END

    choice = update.message.text.strip()
    if choice not in SUBSCRIPTION_TYPES:
        await update.message.reply_text("Invalid choice. Please reply with 1, 2, or 3.")
        return CONVERSATION_STATE_ASKING_TYPE

    sub_type_value, sub_type_label = SUBSCRIPTION_TYPES[choice]

    if context.user_data is None:
        await update.message.reply_text("Something went wrong. Please try again with /subscribe.")
        return ConversationHandler.END

    utc_time: str = context.user_data.get("subscribe_utc_time", "")
    local_time: str = context.user_data.get("subscribe_local_time", "")
    chat_id = update.effective_chat.id

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/subscriptions",
            json={
                "chat_id": chat_id,
                "time": utc_time,
                "subscription_type": sub_type_value,
            },
        )
        response.raise_for_status()

        await update.message.reply_text(
            f"Subscribed successfully!\n\nTime: {local_time} daily\nType: {sub_type_label}",
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to subscribe: {e}")
        await update.message.reply_text("Failed to subscribe. Please try again later.")

    return ConversationHandler.END


async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    await update.message.reply_text("Subscription cancelled.")
    return ConversationHandler.END


subscribe_handler = ConversationHandler(
    entry_points=[CommandHandler("subscribe", subscribe_start)],
    states={  # type: ignore[arg-type]
        CONVERSATION_STATE_ASKING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_time)],
        CONVERSATION_STATE_ASKING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_type)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],  # type: ignore[arg-type]
)
