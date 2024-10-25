from telegram import (
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
)

from db import init_db, load_jobs_from_db
from handlers.command_handlers import (
    cancel_job,
    help,
    remind,
    reminder_callback,
    set_msg,
    start,
    view_reminders,
)
from settings import BOT_TOKEN


async def post_init(application: Application):
    await application.bot.set_my_commands(
        [
            ("start", "Start the bot"),
            ("set", "Set a message to be sent later"),
            ("remind", "Set a recurring reminder"),
            ("help", "Display this message"),
            ("all", "View all reminders"),
            ("cancel", "Cancel a reminder by job ID"),
        ]
    )


def main():
    """Start the bot."""
    init_db()

    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    load_jobs_from_db(application, reminder_callback)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_msg))
    application.add_handler(CommandHandler("remind", remind))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("all", view_reminders))
    application.add_handler(CommandHandler("cancel", cancel_job))
    # application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
