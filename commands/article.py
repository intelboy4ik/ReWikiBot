from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from telebot import types
from datetime import datetime

from config import check_user_registered, check_user_mod_status, parse_command_args


class ArticleCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.message_handler(commands=['save'])(self.save_command)
        self.bot.message_handler(commands=['remove'])(self.remove_command)
        self.bot.message_handler(commands=['list'])(self.list_command)
        self.bot.message_handler(commands=['search'])(self.search_command)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("article_"))(
            self.article_callback_handler)
        self.bot.callback_query_handler(
            func=lambda call: call.data.startswith("saved_next_") or call.data.startswith("saved_prev_"))(
            self.pagination_callback_handler)
        self.bot.message_handler(commands=['create'])(self.create_command)
        self.bot.message_handler(commands=['edit'])(self.edit_command)
        self.bot.message_handler(commands=['delete'])(self.delete_command)

    def save_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user:
            return

        name, _ = parse_command_args(message)
        if not name or not self._check_article_exists(name, message):
            return

        if name in user["saved_articles"]:
            reply_text = {
                "en": f"Article *{name}* is already in your saved list.",
                "ru": f"Статья *{name}* уже в избранных."
            }
            self.bot.reply_to(message, reply_text[user['language']], parse_mode="Markdown")
            return

        self._update_user_articles(user["uid"], name, "add")
        reply_text = {
            "en": f"Article *{name}* has been saved to your list.",
            "ru": f"Статья *{name}* добавлена в избранное."
        }
        self.bot.reply_to(message, reply_text[user["language"]], parse_mode="Markdown")

    def remove_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user:
            return

        name, _ = parse_command_args(message)
        if not name or not self._check_article_exists(name, message):
            return

        if name not in user["saved_articles"]:
            reply_text = {
                "en": f"Article *{name}* is not in your list.",
                "ru": f"Статья *{name}* отсутствует в ваших избранных."
            }
            self.bot.reply_to(message, reply_text[user["language"]], parse_mode="Markdown")
            return

        self._update_user_articles(user["uid"], name, "remove")
        reply_text = {
            "en": f"Article *{name}* has been removed from your list.",
            "ru": f"Статья *{name}* удалена из вашего избранных."
        }
        self.bot.reply_to(message, reply_text[user["language"]], parse_mode="Markdown")

    def list_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user:
            return

        articles = self._get_user_articles(user)
        markup = self._build_articles_markup(articles, 0)

        reply_text = {
            "en": "Your saved articles list:",
            "ru": "Ваши избранные статьи:"
        }

        self.bot.reply_to(message, reply_text[user["language"]], reply_markup=markup)

    def search_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user:
            return

        query = message.text.split(" ")[1]
        articles = list(self.db.articles.find({"name": {"$regex": query, "$options": "i"}}))
        if not articles:
            reply_text = {
                "en": f"No articles found matching *{query}*.",
                "ru": f"Статьи, соответствующие *{query}*, не найдены."
            }
            self.bot.reply_to(message, reply_text[user["language"]], parse_mode="Markdown")
            return

        markup = self._build_articles_markup(articles, 0)
        reply_text = {
            "en": f"Search results for *{query}*:",
            "ru": f"Результаты поиска по запросу *{query}*:"
        }

        self.bot.reply_to(message, reply_text[user['language']], reply_markup=markup, parse_mode="Markdown")

    def article_callback_handler(self, call):
        user = check_user_registered(self.bot, self.db, call)
        article_id = call.data.split("_")[1]
        article = self.db.articles.find_one({"_id": ObjectId(article_id)})

        extra_text = {
            "en": f"Created at: {article['created_at']}",
            "ru": f"Создано: {article['created_at']}"
        }
        if article["updated_at"]:
            extra_text = {
                "en": f"Update at: {article['created_at']}",
                "ru": f"Обновлено: {article['created_at']}"
            }

        self.bot.send_message(
            chat_id=call.message.chat.id,
            text=f"*{article['name']}*\n\n{article['content']}\n\n{extra_text[user['language']]}",
            parse_mode="Markdown"
        )

    def pagination_callback_handler(self, call):
        data_parts = call.data.split("_")
        page = int(data_parts[2])
        user = check_user_registered(self.bot, self.db, call)
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
        user = check_user_registered(self.bot, self.db, message)
        if not user or not check_user_mod_status(self.bot, user, message):
            return

        name, content = parse_command_args(message)
        if not name or not content:
            reply_text = {
                "en": "Usage: /create <name> <content>",
                "ru": "Использование: /create <название> <контент>."
            }
            self.bot.reply_to(message, reply_text[user["language"]])
            return

        if len(content) > 512:
            reply_text = {
                "en": "Maximum article length is 512 symbols.",
                "ru": "Максимальная длинна статьи 512 символов."
            }
            self.bot.reply_to(message, reply_text[user["language"]])
            return

        try:
            self.db.articles.insert_one({
                "name": name,
                "content": content,
                "author": message.from_user.id,
                "created_at": datetime.now().date(),
                "updated_at": None
            })
            reply_text = {
                "en": f"Article *{name}* has been created.",
                "ru": f"Статья *{name}* создана."
            }
            self.bot.reply_to(message, reply_text[user["language"]], parse_mode="Markdown")
        except DuplicateKeyError:
            reply_text = {
                "en": f"An article with the name *{name}* already exists.",
                "ru": f"Статья с названием *{name}* уже существует."
            }
            self.bot.reply_to(message, reply_text[user["language"]], parse_mode="Markdown")

    def edit_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user or not check_user_mod_status(seelf.bot, user, message):
            return

        name, content = parse_command_args(message)
        if not name or not content:
            reply_text = {
                "en": "Usage: /edit <name> <content>",
                "ru": "Использование: /edit <название> <контент>."
            }
            self.bot.reply_to(message, reply_text[user["language"]])
            return

        if len(content) > 512:
            reply_text = {
                "en": "Maximum article length is 512 symbols.",
                "ru": "Максимальная длинна статьи 512 символов."
            }
            self.bot.reply_to(message, reply_text[user["language"]])
            return

        self.db.articles.update_one({"name": name}, {"$set": {"content": content, "updated_at": datetime.now().date()}})

        reply_text = {
            "en": f"Article *{name}* has been updated.",
            "ru": f"Статья *{name}* обновлена."
        }
        self.bot.reply_to(message, reply_text[user['language']], parse_mode="Markdown")

    def delete_command(self, message):
        user = check_user_registered(self.bot, self.db, message)
        if not user or not check_user_mod_status(self.bot, user, message):
            return

        name, _ = parse_command_args(message)
        if not name:
            reply_text = {
                "en": "Usage: /delete <name>",
                "ru": "Использование: /delete <название>."
            }
            self.bot.reply_to(message, reply_text[user["language"]])
            return

        res = self.db.articles.delete_one({"name": name})

        if res.deleted_count == 0:
            reply_text = {
                "en": f"Article *{name}* not found.",
                "ru": f"Статья *{name}* не найдена."
            }
            self.bot.reply_to(message, reply_text[user['language']], parse_mode="Markdown")
            return

        self.db.users.update_many({"saved_articles": name}, {"$pull": {"saved_articles": name}})

        reply_text = {
            "en": f"Article *{name}* has been deleted.",
            "ru": f"Статья *{name}* удалена."
        }
        self.bot.reply_to(message, reply_text[user['language']], parse_mode="Markdown")

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

    @staticmethod
    def _build_articles_markup(articles, page):
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
