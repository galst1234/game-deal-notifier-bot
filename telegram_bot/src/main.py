import datetime
import logging

from telegram.ext import ApplicationBuilder

from commands import current_giveaways_handler, start_handler, unknown_handler
from commands.subscription import subscribe_handler, subscriptions_job, unsubscribe_handler
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(start_handler)
    application.add_handler(current_giveaways_handler)

    # Subscription commands
    application.add_handler(subscribe_handler)
    application.add_handler(unsubscribe_handler)

    # Fallback handler for unknown commands
    application.add_handler(unknown_handler)

    # Job queue
    application.job_queue.run_repeating(
        callback=subscriptions_job,
        interval=datetime.timedelta(seconds=30),
        first=0,
        name="subscriptions_job",
    )

    application.run_polling()


if __name__ == "__main__":
    main()
