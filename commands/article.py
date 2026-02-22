from pymongo.errors import DuplicateKeyError


class ArticleCommands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    def register_commands(self):
        self.bot.message_handler(commands=['save'])(self.save_command)
        self.bot.message_handler(commands=['remove'])(self.remove_command)
        self.bot.message_handler(commands=['list'])(self.list_command)
        self.bot.message_handler(commands=['create'])(self.create_command)
        self.bot.message_handler(commands=['edit'])(self.edit_command)
        self.bot.message_handler(commands=['delete'])(self.delete_command)

    def save_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        name = self._parse_command_args(message)
        if not name:
            return

        if not self._check_article_exists(name, message):
            return
        
        reply_text = {
            "en": f"Article **{name}** is already in your saved list.",
            "ru": f"Статья **{name} уже в избранных."
        }

        if name in user["saved_articles"]:
            self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")
            return

        reply_text = {
            "en":  f"Article **{name}** has been saved to your list.",
            "ru": f"Статья **{name} добавлена в избранное."
        }

        self._update_user_articles(user["uid"], name, "add")
        self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")

    def remove_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        name = self._parse_command_args(message)
        if not name:
            return

        if not self._check_article_exists(name, message):
            return

        reply_text = {
            "en": f"Article **{name}** is not in your list.",
            "ru": f"Статья **{name}** отсутствует в ваших избранных."
        }

        if name not in user["saved_articles"]:
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")
            return

        reply_text = {
            "en": f"Article **{name}** has been removed from your list.",
            "ru": f"Статья **{name}** удалена из вашего избранных."
        }

        self._update_user_articles(user["uid"], name, "remove")
        self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")

    def list_command(self, message):
        pass

    def create_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        if not self._check_user_mod_status(user, message):
            return

        reply_text = {
            "en": f"Usage: /create <name> <content>",
            "ru": f"Использование: /create <название> <контент>."
        }

        name, content = self._parse_command_args(message, user)
        if not name or not content:
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        reply_text = {
            "en": f"Maximum article length is 512 symbols.",
            "ru": f"Максимальная длинна статьи 512 символов."
        }

        if len(content) > 512:
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")
            return


        author = message.from_user.id

        try:
            self.db.articles.insert_one({
                "name": name,
                "content": content,
                "author": author,
            })
            
            reply_text = {
                "en": f"Article **{name}** has been created.",
                "ru": f"Статья **{name}** создана."
            }
            
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")
        except DuplicateKeyError:

            reply_text = {
                "en": f"An article with the name **{name}** already exists.",
                "ru": f"Статья с названием **{name}** уже существует."
            }
            
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")

    def edit_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        if not self._check_user_mod_status(user, message):
            return

        reply_text = {
            "en": f"Usage: /create <name> <content>",
            "ru": f"Использование: /create <название> <контент>."
        }

        name, content = self._parse_command_args(message, user)
        if not name or not content:
            self.bot.reply_to(message, reply_text[user["lang"]])
            return

        reply_text = {
            "en": f"Maximum article length is 512 symbols.",
            "ru": f"Максимальная длинна статьи 512 символов."
        }

        if len(content) > 512:
            self.bot.reply_to(message, reply_text[user["lang"]], parse_mode="Markdown")
            return

        self.db.articles.update_one({
            "name": name,
        }, {
            "$set": {
                "content": content,
            }
        })

        reply_text = {
            "en": f"Article **{name}** has been updated.",
            "ru": f"Статья **{name}** обновлена."
        }

        self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")

    def delete_command(self, message):
        user = self._check_user_registered(message)
        if not user:
            return

        if not self._check_user_mod_status(user, message):
            return

        reply_text = {
            "en": f"Usage: /delete <name>",
            "ru": f"Использование: /delete <название>."
        }

        name = self._parse_command_args(message)
        if not name:
            self.bot.reply_to(message, reply_text)
            return

        reply_text = {
            "en": f"Article **{name}** has been deleted.",
            "ru": f"Статья **{name}** удалена."
        }

        self.db.articles.delete_one({"name": name})
        self.bot.reply_to(message, reply_text[user['lang']], parse_mode="Markdown")

    @staticmethod
    def _parse_command_args(message, user = None):
        parts = message.text.split(" ")
        if len(parts) < 2:
            return None, None
        name = parts[1]
        content = " ".join(parts[2:]) if len(parts) > 2 else ""
        return name, content

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

    def _check_article_exists(self, name, message):
        article = self.db.articles.find_one({"name": name})
        if not article:
            self.bot.reply_to(message, f"Article **{name}** not found.", parse_mode="Markdown")
            return None
        return article

    def _update_user_articles(self, user_id, name, action):
        if action == "add":
            self.db.users.update_one({"uid": user_id}, {"$push": {"saved_articles": name}})
        elif action == "remove":
            self.db.users.update_one({"uid": user_id}, {"$pull": {"saved_articles": name}})

