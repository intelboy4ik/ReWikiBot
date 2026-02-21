# database.py

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from config import MONGO_DB_URI


class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(MONGO_DB_URI, server_api=ServerApi('1'))
        self.db = self.client['WikiDatabase']
        self._init_collections()
        self._init_indexes()

    def _init_collections(self):
        if 'users' not in self.db.list_collection_names():
            self.db.create_collection('users')

        if 'articles' not in self.db.list_collection_names():
            self.db.create_collection('articles')


    def _init_indexes(self):
        self.db.users.create_index('uid', unique=True)
        self.db.articles.create_index('name', unique=True)

    def close(self):
        self.client.close()

db_manager = DatabaseManager()
db = db_manager.db