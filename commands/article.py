from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from telebot import types


class ArticleCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.message_handler(commands=['save'])(self.save_command)
        self.bot.message_handler(commands=['remove'])(self.remove_command)
        self.bot.message_handler(commands=['list'])(self.list_command)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("article_"))(
            self.article_callback_handler)
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("saved_next_") or call.data.startswith("saved_prev_"))(
            self.pagination_callback_handler)
        self.bot.message_handler(commands=['create'])(self.create_command)
        self.bot.message_handler(commands=['edit'])(self.edit_command)
        self.bot.message_handler(commands=['delete'])(self.delete_command)

    def save_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        name, _ = self._parse_command_args(message)
        if not name or not self._check_article_exists(name, message):
            return

        if name in user["saved_articles"]:
            reply_text = {
                "en": f"Article *{name}* is already in your saved list.",
                "ru": f"Статья *{name}* уже в избранных."
            }
            self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")
            return

        self._update_user_articles(user["uid"], name, "add")
        reply_text = {
            "en": f"Article *{name}* has been saved to your list.",
            "ru": f"Статья *{name}* добавлена в избранное."
        }
        self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")

    def remove_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        name, _ = self._parse_command_args(message)
        if not name or not self._check_article_exists(name, message):
            return

        if name not in user["saved_articles"]:
            reply_text = {
                "en": f"Article *{name}* is not in your list.",
                "ru": f"Статья *{name}* отсутствует в ваших избранных."
            }
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")
            return

        self._update_user_articles(user["uid"], name, "remove")
        reply_text = {
            "en": f"Article *{name}* has been removed from your list.",
            "ru": f"Статья *{name}* удалена из вашего избранных."
        }
        self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")

    def list_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        articles = self._get_user_articles(user)
        markup = self._build_articles_markup(articles, 0)

        reply_text = {
            "en": "Your saved articles list:",
            "ru": "Ваши избранные статьи: "
        }

        self.bot.reply_to(message, reply_text[user["lang"]], reply_markup=markup)

    def article_callback_handler(self, call):
        article_id = call.data.split("_")[1]
        article = self.db.articles.find_one({"_id": ObjectId(article_id)})
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"*{article['name']}*\n\n{article['content']}",
            parse_mode="Markdown"
        )

    def pagination_callback_handler(self, call):
        data_parts = call.data.split("_")
        page = int(data_parts[2])
        user = self._check_user_registered(call)
        if not user:
            return

        articles = self._get_user_articles(user)
        markup = self._build_articles_markup(articles, page)

        self.bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    def create_command(self, message):
        user = self._check_user_registered(message)
        if not user or not self._check_user_mod_status(user, message):
            return

        name, content = self._parse_command_args(message)
        if not name or not content:
            reply_text = {
                "en": "Usage: /create <name> <content>",
                "ru": "Использование: /create <название> <контент>."
            }
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        if len(content) > 512:
            reply_text = {
                "en": "Maximum article length is 512 symbols.",
                "ru": "Максимальная длинна статьи 512 символов."
            }
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        try:
            self.db.articles.insert_one({
                "name": name,
                "content": content,
                "author": message.from_user.id,
            })
            reply_text = {
                "en": f"Article *{name}* has been created.",
                "ru": f"Статья *{name}* создана."
            }
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")
        except DuplicateKeyError:
            reply_text = {
                "en": f"An article with the name *{name}* already exists.",
                "ru": f"Статья с названием *{name}* уже существует."
            }
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")

    def edit_command(self, message):
        user = self._check_user_registered(message)
        if not user or not self._check_user_mod_status(user, message):
            return

        name, content = self._parse_command_args(message)
        if not name or not content:
            reply_text = {
                "en": "Usage: /edit <name> <content>",
                "ru": "Использование: /edit <название> <контент>."
            }
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        if len(content) > 512:
            reply_text = {
                "en": "Maximum article length is 512 symbols.",
                "ru": "Максимальная длинна статьи 512 символов."
            }
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        self.db.articles.update_one({"name": name}, {"$set": {"content": content}})

        reply_text = {
            "en": f"Article *{name}* has been updated.",
            "ru": f"Статья *{name}* обновлена."
        }
        self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")

    def delete_command(self, message):
        user = self._check_user_registered(message)
        if not user or not self._check_user_mod_status(user, message):
            return

        name, _ = self._parse_command_args(message)
        if not name:
            reply_text = {
                "en": "Usage: /delete <name>",
                "ru": "Использование: /delete <название>."
            }
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        res = self.db.articles.delete_one({"name": name})

        if res.deleted_count == 0:
            reply_text = {
                "en": f"Article *{name}* not found.",
                "ru": f"Статья *{name}* не найдена."
            }
            self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")
            return

        self.db.users.update_many({"saved_articles": name}, {"$pull": {"saved_articles": name}})

        reply_text = {
            "en": f"Article *{name}* has been deleted.",
            "ru": f"Статья *{name}* удалена."
        }
        self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")

    @staticmethod
    def _parse_command_args(message):
        parts = message.text.split(" ")
        if len(parts) < 2:
            return None, None
        name = parts[1]
        content = " ".join(parts[2:]) if len(parts) > 2 else ""
        return name, content

    def _check_user_registered(self, obj):
        user_id = obj.from_user.id if hasattr(obj, 'from_user') else obj.message.from_user.id
        user = self.db.users.find_one({"uid": user_id})
        if not user:
            self.bot.reply_to(
                obj,
                "You need to start the bot first using /start. / Для начала воспользуйтесь командой /start."
            )
            return None
        return user

    def _check_user_mod_status(self, user, message):
        if not user["moderator"]:
            self.bot.reply_to(
                message,
                "You should be moderator to use this command! / Вы должны быть модератором чтобы использовать эту команду!"
            )
            return False
        return True

    def _check_article_exists(self, name, message):
        article = self.db.articles.find_one({"name": name})
        if not article:
            self.bot.reply_to(message, f"Article *{name}* not found. / Статья *{name}* не найдена.",
                              parse_mode="Markdown")
            return False
        return True

    def _update_user_articles(self, user_id, name, action):
        if action == "add":
            self.db.users.update_one({"uid": user_id}, {"$push": {"saved_articles": name}})
        elif action == "remove":
            self.db.users.update_one({"uid": user_id}, {"$pull": {"saved_articles": name}})

    def _get_user_articles(self, user):
        articles = []
        for article_name in user["saved_articles"]:
            article = self.db.articles.find_one({"name": article_name})
            if article:
                articles.append(article)
        return articles

    def _build_articles_markup(self, articles, page):
        markup = types.InlineKeyboardMarkup()
        start_index = page * 10
        end_index = start_index + 10
        page_articles = articles[start_index:end_index]

        for article in page_articles:
            article_button = types.InlineKeyboardButton(
                text=article["name"],
                callback_data=f"article_{article['_id']}"
            )
            markup.add(article_button)

        if end_index < len(articles):
            next_page_button = types.InlineKeyboardButton(text=">", callback_data=f"saved_next_{page + 1}")
            markup.add(next_page_button)

        if page > 0:
            previous_page_button = types.InlineKeyboardButton(text="<", callback_data=f"saved_prev_{page - 1}")
            markup.add(previous_page_button)

        return markup
