import logging
from datetime import datetime, timedelta, timezone
from pprint import pprint

from telegram import (
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

from db import (
    get_job_from_db,
    get_jobs_from_db,
    remove_job_from_db,
    save_job_to_db,
    update_job_next_run_time,
)
from utils.decorators import (
    mygroup_admins_or_personal_only,
    restricted,
    send_action,
    show_help_for_set,
)
from utils.helpers import format_time_left

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    user = update.effective_message.from_user
    chat = update.effective_chat
    logger.info(
        "User %s started %s the conversation in %s", user.first_name, user.id, chat.id
    )
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""

    current_jobs = context.job_queue.get_jobs_by_name(name)

    if not current_jobs:
        return False

    for job in current_jobs:
        job.schedule_removal()

    return True


async def reminder_callback(context: ContextTypes.DEFAULT_TYPE, *args):
    job = context.job
    chat_id = job.chat_id
    message = job.data
    job_id = job.job.id
    db_job = get_job_from_db(job_id)

    await context.bot.send_message(chat_id=chat_id, text=message)

    if db_job and db_job["interval"]:
        interval: str = db_job["interval"]
        intervals = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "hourly": timedelta(hours=1),
        }
        next_run_time = (datetime.now(timezone.utc) + intervals[interval]).isoformat()
        update_job_next_run_time(job_id, next_run_time)
    else:
        remove_job_from_db(job_id)


@mygroup_admins_or_personal_only
async def set_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # chat_id = update.effective_message.chat_id
    logger = logging.getLogger("telegram.ext.JobQueue")
    chat_id = update.effective_chat.id
    user = update.effective_message.from_user

    reply = (
        update.message.reply_to_message.text
        if update.message.reply_to_message
        else None
    )
    message = reply if reply else " ".join(context.args[:-1])
    # pprint(reply)
    # print("________________")
    try:
        time_period = context.args[-1]
        time_units = {
            "w": "weeks",
            "d": "days",
            "h": "hours",
            "hr": "hours",
            "m": "minutes",
            "s": "seconds",
        }
        time_unit_key = (
            time_period[-1:] if time_period[-1:] in time_units else time_period[-2:]
        ).lower()
        if time_unit_key not in time_units:
            await update.message.reply_text(
                "Invalid time unit. Use s, m, h, hr,d or w."
            )
            return

        time_value = float(time_period.replace(time_unit_key, ""))
        if time_value < 0:
            await update.effective_message.reply_text(
                "Sorry we can not go back to future!"
            )
            return
        time_kwargs = {time_units[time_unit_key]: time_value}
        scheduled_time = datetime.now(timezone.utc) + timedelta(**time_kwargs)

        time_message = format_time_left(scheduled_time)

        await update.message.reply_text(
            f"Message will be sent in {time_message.strip()}"
        )

        logger.info(
            "User %s set a message(%s) to be sent at %s",
            user.first_name,
            message,
            scheduled_time,
        )
        # job_removed = remove_job_if_exists(str(chat_id), context)

        job = context.job_queue.run_once(
            reminder_callback,
            scheduled_time,
            chat_id=chat_id,
            user_id=user.id,
            name=str(chat_id),
            data=message,
        )
        # print(job.job, "job instance")
        # print(job.job.id)
        # text = "Timer successfully set!"

        # if job_removed:
        #     text += " Old one was removed."

        # await update.effective_message.reply_text(text)
        # print(len(context.job_queue.jobs()))
        # job = context.job_queue.run_once(callback_minute, interval=5, first=5)
        context.chat_data["job"] = job
        # save the job to the db
        save_job_to_db(
            job.job.id, chat_id, user.id, message, None, scheduled_time.isoformat()
        )

    except (IndexError, ValueError) as e:
        logger.error("Error setting message: %s", e)
        await update.message.reply_text("Usage: /set <message>")


@mygroup_admins_or_personal_only
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger = logging.getLogger("telegram.ext.JobQueue")
    chat_id = update.effective_chat.id
    user = update.effective_message.from_user

    reply = (
        update.message.reply_to_message.text
        if update.message.reply_to_message
        else None
    )
    message = reply if reply else " ".join(context.args[:-1])
    # pprint(reply)
    # print("________________")
    try:
        interval = context.args[-1].lower()
        intervals = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "hourly": timedelta(hours=1),
        }
        if interval not in intervals:
            await update.message.reply_text(
                "Invalid interval. Use daily, weekly, or hourly."
            )
            return

        await update.message.reply_text(
            f"Message will be sent {interval} starting now."
        )

        logger.info(
            "User %s set a reminder(%s) to be sent %s",
            user.first_name,
            message,
            interval,
        )

        job = context.job_queue.run_repeating(
            reminder_callback,
            interval=intervals[interval],
            first=0,
            chat_id=chat_id,
            user_id=user.id,
            name=str(chat_id),
            data=message,
        )
        # print(len(context.job_queue.jobs()))
        context.chat_data["job"] = job
        # save the reminder job to the db
        next_run_time = (datetime.now(timezone.utc) + intervals[interval]).isoformat()
        save_job_to_db(job.job.id, chat_id, user.id, message, interval, next_run_time)

    except (IndexError, ValueError) as e:
        logger.error("Error setting reminder: %s", e)
        await update.message.reply_text("Usage: /remind <message> <interval>")


async def view_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    _jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    jobs = get_jobs_from_db(chat_id)
    # print(list(jobs), "current jobs")
    # is it necessary to get jobs from db?
    #  we have the jobs in the job queue
    if not jobs:
        await update.message.reply_text("No reminders set.")
        return
    text = "Reminders:\n"

    for i, job in enumerate(jobs):
        # job = job
        print(job, "single job")
        chat_member = await context.bot.get_chat_member(chat_id, job["user_id"])
        user = chat_member.user
        # print(job.next_t)
        next_run_time = datetime.fromisoformat(job["next_run_time"])
        text += f"#{i}. <a href='tg://user?id='>{str(job['message'])} </a> - <i>{format_time_left(next_run_time)} left - {user.mention_html()}</i>\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@mygroup_admins_or_personal_only
async def cancel_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger = logging.getLogger("telegram.ext.JobQueue")
    chat_id = update.effective_chat.id
    try:
        job_id = context.args[0]
        jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        db_jobs = get_jobs_from_db(chat_id)

        if not jobs or not db_jobs:
            await update.message.reply_text("No reminders set.")
            return

        if int(job_id) >= len(jobs) or int(job_id) >= len(list(db_jobs)):
            await update.message.reply_text("Invalid job ID.")
            return
        # get the job from db list using the index from telegram
        db_job = db_jobs[int(job_id)]
        job = jobs[int(job_id)]

        db_job_id = db_job["id"]
        if not db_job:
            await update.message.reply_text("No reminder found.")
            return
        job.schedule_removal()
        remove_job_from_db(db_job_id)
        await update.message.reply_text("Reminder canceled.")
        return

    except (IndexError, ValueError) as e:
        logger.error("Error canceling job: %s", e)
        await update.message.reply_text("Usage: /cancel <job_id>")


@show_help_for_set
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Commands:</b>\n"
        "/start - Start the bot\n"
        "/set &lt;message&gt; &lt;time&gt; - Set a message to be sent later (e.g., /set Hello 10m)\n"
        "/remind &lt;message&gt; &lt;interval&gt; - Set a recurring reminder (e.g., /remind Hello daily)\n"
        "/help - Display this message\n"
        "/all - View all reminders\n"
        "/cancel &lt;job_id&gt; - Cancel a reminder by its ID\n",
        parse_mode=ParseMode.HTML,
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )
