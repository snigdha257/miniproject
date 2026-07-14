import os
import sys
from typing import Any

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure


class InMemoryCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, field, direction):
        reverse = direction == -1
        self.docs.sort(key=lambda d: d.get(field), reverse=reverse)
        return self

    def skip(self, count):
        self.docs = self.docs[count:]
        return self

    def limit(self, count):
        self.docs = self.docs[:count]
        return self

    def __iter__(self):
        return iter(self.docs)


class InMemoryCollection:
    def __init__(self):
        self.documents = []

    def _match(self, doc, query):
        for key, value in query.items():
            if key not in doc:
                return False
            if doc[key] != value:
                return False
        return True

    def find_one(self, query):
        return next((doc for doc in self.documents if self._match(doc, query)), None)

    def insert_one(self, document):
        document = dict(document)
        document.setdefault("_id", object())
        self.documents.append(document)

        class Result:
            inserted_id = document["_id"]

        return Result()

    def update_one(self, filter_query, update):
        doc = self.find_one(filter_query)
        if not doc:
            return None
        if "$set" in update:
            doc.update(update["$set"])

        class Result:
            matched_count = 1
            modified_count = 1

        return Result()

    def count_documents(self, query):
        return sum(1 for doc in self.documents if self._match(doc, query))

    def find(self, query):
        return InMemoryCursor([doc for doc in self.documents if self._match(doc, query)])

    def delete_one(self, filter_query):
        self.documents = [doc for doc in self.documents if not self._match(doc, filter_query)]

        class Result:
            deleted_count = 1

        return Result()

    def create_index(self, *args, **kwargs):
        return None


class InMemoryDB:
    def __init__(self):
        self.users = InMemoryCollection()
        self.documents = InMemoryCollection()
        self.mappings = InMemoryCollection()
        self.history = InMemoryCollection()

    def __getitem__(self, name):
        return getattr(self, name)


class InMemoryClient:
    def __init__(self):
        self._db = InMemoryDB()

    def get_default_database(self, default=None):
        return self._db


def get_mongo_client() -> Any:
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("[WARNING] MONGO_URI is not set. Falling back to in-memory database for local testing.")
        return InMemoryClient()

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("[DB] MongoDB connection established successfully.")
        return client
    except (ConnectionFailure, ConfigurationError) as exc:
        sys.exit(
            f"\n[ERROR] Could not connect to MongoDB: {exc}\n"
            "  Check that MONGO_URI is correct and your IP is whitelisted in Atlas.\n"
        )


client = get_mongo_client()
db = client.get_default_database(default=os.getenv("MONGO_DB_NAME", "miniproject"))

from database.schema import ensure_indexes

ensure_indexes()
