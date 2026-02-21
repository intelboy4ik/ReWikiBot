from config import TOKEN
from database import db
from commands.base import BaseCommands
from commands.article import ArticleCommands

from telebot import TeleBot

bot = TeleBot(TOKEN)

base_commands = BaseCommands(bot, db)
base_commands.register_commands()

article_commands = ArticleCommands(bot, db)
article_commands.register_commands()


if __name__ == "__main__":
    bot.infinity_polling()