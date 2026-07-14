"""
database/connection.py
Reads MONGO_URI from the environment and verifies connectivity on import.
If no Mongo URI is configured, this module falls back to an in-memory database
for local development and manual UI testing.
"""
import os
import sys
from datetime import datetime

from bson import ObjectId
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
            if getattr(value, 'binary', None) is not None and doc[key] != value:
                return False
            if doc[key] != value:
                return False
        return True

    def find_one(self, query):
        for doc in self.documents:
            if self._match(doc, query):
                return doc
        return None

    def insert_one(self, document):
        document = document.copy()
        document.setdefault("_id", ObjectId())
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
        matched = [doc for doc in self.documents if self._match(doc, query)]
        return InMemoryCursor(matched)


class InMemoryDB:
    def __init__(self):
        self.users = InMemoryCollection()
        self.documents = InMemoryCollection()

    def __getitem__(self, name):
        return getattr(self, name)


class InMemoryClient:
    def __init__(self):
        self._db = InMemoryDB()

    def get_default_database(self, default=None):
        return self._db


def get_mongo_client() -> MongoClient:
    uri = os.getenv("MONGO_URI")
    if not uri:
        print(
            "[WARNING] MONGO_URI is not set. Falling back to in-memory database for local testing."
        )
        return InMemoryClient() # type: ignore

    try:
        client: MongoClient = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Trigger an actual connection attempt
        client.admin.command("ping")
        print("[DB] MongoDB connection established successfully.")
        return client
    except (ConnectionFailure, ConfigurationError) as exc:
        sys.exit(
            f"\n[ERROR] Could not connect to MongoDB: {exc}\n"
            "  Check that MONGO_URI is correct and your IP is whitelisted in Atlas.\n"
        )


# Module-level client — import this wherever you need DB access.
client = get_mongo_client()

# Convenience: expose the default database (name taken from the URI, fallback "miniproject")
db = client.get_default_database(default="miniproject")
