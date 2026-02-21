from config import TOKEN, MONGO_DB_URI

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from telebot import TeleBot

bot = TeleBot(TOKEN)

uri = MONGO_DB_URI

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

if __name__ == "__main__":
    bot.infinity_polling()