import json
import os
import sys
from pathlib import Path
from threading import RLock
from typing import Any

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
    def __init__(self, db):
        self._db = db
        self.documents = []

    def _match(self, doc, query):
        for key, value in query.items():
            if key not in doc:
                return False
            v1 = doc[key]
            v2 = value
            if isinstance(v1, ObjectId) or isinstance(v2, ObjectId):
                if str(v1) != str(v2):
                    return False
            elif v1 != v2:
                return False
        return True

    def find_one(self, query):
        return next((doc for doc in self.documents if self._match(doc, query)), None)

    def insert_one(self, document):
        document = dict(document)
        document.setdefault("_id", ObjectId())
        self.documents.append(document)
        self._db._persist()

        class Result:
            inserted_id = document["_id"]

        return Result()

    def update_one(self, filter_query, update, upsert=False):
        doc = self.find_one(filter_query)
        if not doc:
            doc = filter_query.copy()
            if "$set" in update:
                doc.update(update["$set"])
            self.insert_one(doc)
            class Result:
                matched_count = 0
                modified_count = 0
                upserted_id = doc.get("_id")
            return Result()
        if "$set" in update:
            doc.update(update["$set"])
        self._db._persist()

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
        self._db._persist()

        class Result:
            deleted_count = 1

        return Result()

    def create_index(self, *args, **kwargs):
        return None


class InMemoryDB:
    def __init__(self, storage_path: str | None = None):
        self._storage_path = storage_path
        self._lock = RLock()
        self.users = InMemoryCollection(self)
        self.documents = InMemoryCollection(self)
        self.mappings = InMemoryCollection(self)
        self.history = InMemoryCollection(self)
        self._load()

    def _load(self):
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.users.documents = payload.get("users", [])
            self.documents.documents = payload.get("documents", [])
            self.mappings.documents = payload.get("mappings", [])
            self.history.documents = payload.get("history", [])
        except (json.JSONDecodeError, OSError):
            self.users.documents = []
            self.documents.documents = []
            self.mappings.documents = []
            self.history.documents = []

    def _persist(self):
        if not self._storage_path:
            return
        payload = {
            "users": self.users.documents,
            "documents": self.documents.documents,
            "mappings": self.mappings.documents,
            "history": self.history.documents,
        }
        storage_path = Path(self._storage_path)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(storage_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, default=str, indent=2)

    def __getitem__(self, name):
        return getattr(self, name)


class InMemoryClient:
    _shared_db: InMemoryDB | None = None

    def __init__(self):
        if InMemoryClient._shared_db is None:
            storage_path = os.getenv("MEMORY_DB_PATH")
            if not storage_path:
                storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".inmemory_db.json")
            InMemoryClient._shared_db = InMemoryDB(storage_path)
        self._db = InMemoryClient._shared_db

    def get_default_database(self, default=None):
        return self._db


def get_mongo_client() -> Any:
    uri = os.getenv("MONGO_URI")
    if not uri:
        # Default to file-based in-memory database for persistence
        storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".inmemory_db.json")
        os.environ["MEMORY_DB_PATH"] = storage_path
        print("[INFO] MONGO_URI not set, using file-based in-memory database for persistence.")
        print(f"[INFO] Database will be stored at: {storage_path}")
        return InMemoryClient()
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("[DB] MongoDB connection established successfully.")
        return client
    except (ConnectionFailure, ConfigurationError) as exc:
        print(f"[WARNING] Could not connect to MongoDB: {exc}")
        print("[WARNING] Falling back to file-based in-memory database for persistence.")
        storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".inmemory_db.json")
        os.environ["MEMORY_DB_PATH"] = storage_path
        return InMemoryClient()


client = get_mongo_client()
db = client.get_default_database(default=os.getenv("MONGO_DB_NAME", "miniproject"))
