

class ModCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.message_handler(commands=["mod"])(self.add_moderator_command)
        self.bot.message_handler(commands=["unmod"])(self.remove_moderator_command)

    def add_moderator_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        if not self._check_user_mod_status(user, message):
            return

        user_id = self._parse_command_args(message)
        self._update_user_mod_status(user_id, "add")
        self.bot.reply_to(message, "Successfully added moderator status to user")

    def remove_moderator_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        if not self._check_user_mod_status(user, message):
            return

        user_id = self._parse_command_args(message)
        self._update_user_mod_status(user_id, "remove")
        self.bot.reply_to(message, "Successfully removed moderator status to user")

    @staticmethod
    def _parse_command_args(message):
        parts = message.text.split(" ")
        if len(parts) < 2:
            return None, None
        user_id = parts[1]
        return user_id

    def _check_user_registered(self, message):
        user = self.db.users.find_one({"uid": message.from_user.id})
        if not user:
            self.bot.reply_to(message, "You need to start the bot first using /start.")
            return None
        return user

    def _check_user_mod_status(self, user, message):
        if not user["moderator"]:
            self.bot.reply_to(message, "You should be moderator to use this command")
            return None
        return user

    def _update_user_mod_status(self, user_id, action):
        if action == "add":
            self.db.users.update_one({"uid": user_id}, {"$set": {"moderator": True}})
        elif action == "remove":
            self.db.users.update_one({"uid": user_id}, {"$set": {"moderator": False}})