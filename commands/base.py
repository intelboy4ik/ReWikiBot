from telebot import types


class BaseCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.message_handler(commands=['start'])(self.start_command)
        self.bot.message_handler(commands=['help'])(self.help_command)
        self.bot.message_handler(commands=['language'])(self.language_command)
        self.bot.callback_query_handler(func=lambda call: call.data in ["set_en", "set_ru"])(
            self.language_callback_handler)

    def start_command(self, message):
        user_id = message.from_user.id
        if not self.db.users.find_one({"uid": user_id}):
            self.db.users.insert_one({"uid": user_id, "moderator": False, "language": "en", "saved_articles": []})
        self.bot.reply_to(message, "Welcome to the ReWiki Bot! Use /help to see available commands.")

    def help_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        help_text = {
            "en": (
                "Available commands:\n"
                "/start - Start the bot and register yourself\n"
                "/help - Show this help message\n"
                "/save <text> - Save an article\n"
                "/remove <text> - Remove an article from your saved list\n"
                "/list - List of your saved articles\n"
                "/language - Change your language settings\n"
            ),
            "ru": (
                "Доступные команды:\n"
                "/start - Начать работу с ботом и зарегистрироваться\n"
                "/help - Отобразить сообщение с помощью\n"
                "/save <text> - Сохранить статью\n"
                "/remove <text> - Убрать статью из сохранённых\n"
                "/list - Список избранных статей\n"
                "/language - Изменить свои языковые настройки\n"
            )
        }

        if user["moderator"]:
            help_text = {
                "en": (
                    "/create <name> <content> - Create a new article\n"
                    "/edit <name> <content> - Edit an existing article\n"
                    "/delete <name> - Delete an article\n"
                ),
                "ru": (
                    "/create <name> <content> - Создать новую статью\n"
                    "/edit <name> <content> - Изменить существующую статью\n"
                    "/delete <name> - Удалить статью\n"
                )
            }

        self.bot.reply_to(message, help_text[user["language"]])

    def language_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        markup = types.InlineKeyboardMarkup()
        en_language_button = types.InlineKeyboardButton(
            text="🇬🇧",
            callback_data="set_en"
        )

        ru_language_button = types.InlineKeyboardButton(
            text="🇷🇺",
            callback_data="set_ru"
        )

        markup.row(en_language_button, ru_language_button)

        info_text = {
            "en": (
                "You opened language settings\n"
                "Select your language:\n"
            ),
            "ru": (
                "Вы открыли настройки смены языка\n"
                "Выберите язык:"
            )
        }

        self.bot.reply_to(message, info_text[user["language"]], reply_markup=markup)

    def language_callback_handler(self, call):
        user = self._check_user_registered(call)
        if call.data == "set_en":
            self.db.users.update_one({"uid": user["uid"]}, {"$set": {"language": "en"}})
        else:
            self.db.users.update_one({"uid": user["uid"]}, {"$set": {"language": "ru"}})

    def _check_user_registered(self, callback):
        user = self.db.users.find_one({"uid": callback.from_user.id})
        if not user:
            self.bot.reply_to(callback, "You need to start the bot first using /start.")
            return None
        return user
