
class BaseCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.command_handler(['start'])(self.start_command)

    def start_command(self, message):
        user_id = message.from_user.id
        if not self.db.users.find_one({"uid": user_id}):
            self.db.users.insert_one({"uid": user_id, "moderator": False, "saved_articles": []})
        self.bot.reply_to(message, "Welcome to the ReWiki Bot! Use /help to see available commands.")

    def help_command(self, message):
        user_id = message.from_user.id
        user = self.db.users.find_one({"uid": user_id})

        help_text = (
            "Available commands:\n"
            "/start - Start the bot and register yourself\n"
            "/help - Show this help message\n"
            "/save <text> - Save an article\n"
            "/remove <text> - Remove an article from your saved list\n"
            "/list - List your saved articles\n"
        )

        if user["moderator"]:
            help_text = (
                "/create <name> <content> - Create a new article\n"
                "/edit <name> <content> - Edit an existing article\n"
                "/delete <name> - Delete an article\n"
            )

        self.bot.reply_to(message, help_text)
