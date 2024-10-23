import random
from functools import cache, wraps

from telegram import Update
from telegram.ext import (
    ContextTypes,
)

from settings import LIST_OF_USERS, GROUP_ID, PERSONAL_USER_ID


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id, action=action
            )
            return await func(update, context, *args, **kwargs)

        return command_func

    return decorator


def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context, *args, **kwargs):
        user_id = update.effective_user.id
        unauthorized_messages = [
            "Access denied, mortal!",
            "You shall not pass!",
            "Nice try, but no.",
            "This is not for you, buddy.",
            "Keep dreaming!",
            "Nope, not happening.",
            "You're not on the list!",
            "Denied. Try again never.",
        ]
        message = random.choice(unauthorized_messages)
        if user_id not in LIST_OF_USERS:
            print(f"Unauthorized access denied for {user_id}.")
            await update.message.reply_text(message)
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


@cache
def group_admin_only(func):
    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Get the list of administrators in the chat
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_admins]

        unauthorized_messages = [
            "Access denied, mortal!",
            "You shall not pass!",
            "Nice try, but no.",
            "This is not for you, buddy.",
            "Keep dreaming!",
            "Nope, not happening.",
            "You're not on the list!",
            "Denied. Try again never.",
        ]
        message = random.choice(unauthorized_messages)

        if user_id not in admin_ids:
            print(f"Unauthorized access denied for {user_id}.")
            await update.message.reply_text(message)
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


@cache
def mygroup_admins_or_personal_only(func):
    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        unauthorized_messages = [
            "Access denied, mortal!",
            "You shall not pass!",
            "Nice try, but no.",
            "This is not for you, buddy.",
            "Keep dreaming!",
            "Nope, not happening.",
            "You're not on the list!",
            "Denied. Try again never.",
        ]
        if chat_id != GROUP_ID and user_id != PERSONAL_USER_ID:
            message = random.choice(unauthorized_messages)
            print(f"Unauthorized access denied for {user_id}.")
            await update.message.reply_text(message)
            return

        if chat_id == GROUP_ID:
            chat_admins = await context.bot.get_chat_administrators(chat_id)
            admin_ids = (admin.user.id for admin in chat_admins)
            if user_id not in admin_ids:
                print(f"Unauthorized access denied for {user_id}.")
                await update.message.reply_text(message)
                return

        return await func(update, context, *args, **kwargs)

    return wrapped


def show_help_for_set(func):
    @wraps(func)
    async def wrapped(update: Update, context, *args, **kwargs):
        if len(context.args) == 1 and context.args[0].lower() == "set":
            await update.message.reply_text(
                "Set\n"
                "Usage: /set <message> <time>\n"
                "Example: /set Hello 10m\n"
                "Time units: s (seconds), m (minutes), h (hours), d (days), w (weeks)"
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapped
