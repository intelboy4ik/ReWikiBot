import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

MONGO_DB_URI = os.getenv("MONGO_DB_URI")


def check_user_registered(bot, db, obj):
    user_id = obj.from_user.id if hasattr(obj, 'from_user') else obj.message.from_user.id
    user = db.users.find_one({"uid": user_id})
    if not user:
        bot.reply_to(
            obj,
            "You need to start the bot first using /start. / Для начала воспользуйтесь командой /start."
        )
        return None
    return user


def check_user_mod_status(bot, user, message):
    if not user["moderator"]:
        bot.reply_to(
            message,
            "You should be moderator to use this command! / Вы должны быть модератором чтобы использовать эту команду!"
        )
        return False
    return True


def parse_command_args(message):
    parts = message.text.split(" ")
    if len(parts) < 2:
        return None, None
    name = parts[1]
    content = " ".join(parts[2:]) if len(parts) > 2 else ""
    return name, content
