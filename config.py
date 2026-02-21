import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

MONGO_DB_URI = os.getenv("MONGO_DB_URI")
print(MONGO_DB_URI)