import os
import sys

LIST_OF_USERS = list(map(int, os.getenv("LIST_OF_USERS", "").split(",")))
GROUP_ID = int(os.getenv("GROUP_ID", ""))
PERSONAL_USER_ID = int(os.getenv("PERSONAL_USER_ID", ""))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("You have forgot to set BOT_TOKEN")
    sys.exit()
