from config import check_user_registered, check_user_mod_status, parse_command_args

class ModCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.message_handler(commands=["mod"])(self.add_moderator_command)
        self.bot.message_handler(commands=["unmod"])(self.remove_moderator_command)

    def add_moderator_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user or not check_user_mod_status(self.bot, user, message):
            return

        user_id, _ = parse_command_args(message)
        self._update_user_mod_status(user_id, "add")
        self.bot.reply_to(message, "Successfully added moderator status to user")

    def remove_moderator_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user or not check_user_mod_status(self.bot, user, message):
            return

        user_id, _ = parse_command_args(message)
        self._update_user_mod_status(user_id, "remove")
        self.bot.reply_to(message, "Successfully removed moderator status to user")

    def _update_user_mod_status(self, user_id, action):
        if action == "add":
            self.db.users.update_one({"uid": user_id}, {"$set": {"moderator": True}})
        elif action == "remove":
            self.db.users.update_one({"uid": user_id}, {"$set": {"moderator": False}})
