import base64
import os
import sys
import types
from datetime import datetime

from bson import ObjectId
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

# Ensure the backend directory is importable as the current working directory.
sys.path.insert(0, os.getcwd())

# Create a fake in-memory database module for route testing.
class InMemoryCollection:
    def __init__(self):
        self.documents = []

    def _match(self, doc, query):
        for key, value in query.items():
            if key not in doc:
                return False
            if isinstance(value, ObjectId):
                if doc[key] != value:
                    return False
            elif doc[key] != value:
                return False
        return True

    def find_one(self, query):
        for doc in self.documents:
            if self._match(doc, query):
                return doc
        return None

    def insert_one(self, document):
        document = document.copy()
        if "_id" not in document:
            document["_id"] = ObjectId()
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


class FakeDB:
    def __init__(self):
        self.users = InMemoryCollection()
        self.documents = InMemoryCollection()

    def __getitem__(self, name):
        return getattr(self, name)


fake_db = FakeDB()

fake_database_module = types.ModuleType("database")
fake_connection_module = types.ModuleType("database.connection")
fake_connection_module.db = fake_db
sys.modules["database"] = fake_database_module
sys.modules["database.connection"] = fake_connection_module

# Configure environment for secure mode and JWT
os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
os.environ["JWT_SECRET"] = "test-secret-for-jwt"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import importlib.util

main_path = os.path.join(os.getcwd(), "main.py")
spec = importlib.util.spec_from_file_location("backend_main", main_path)
backend_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_main)

client = TestClient(backend_main.app)

print("=== Signup ===")
resp = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
print(resp.status_code, resp.json())
assert resp.status_code == 200

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== Login ===")
resp = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
print(resp.status_code, resp.json())
assert resp.status_code == 200

print("=== Protected route without JWT should be rejected ===")
for path in ["/documents/dashboard", "/documents/history"]:
    resp = client.get(path)
    print(path, resp.status_code, resp.json())
    assert resp.status_code == 401

print("=== Upload document ===")
text_data = "John Doe from ACME (john.doe@example.com)"
resp = client.post("/documents/upload", data={"text": text_data}, headers=headers)
print(resp.status_code, resp.json())
assert resp.status_code == 200

document_id = resp.json()["document_id"]

print("=== Mask document (secure) ===")
resp = client.post(
    "/documents/mask",
    json={"document_id": document_id, "mode": "secure", "style": "placeholder"},
    headers=headers,
)
print(resp.status_code, resp.json())
assert resp.status_code == 200
masked_text = resp.json()["masked_text"]
secure_key = resp.json()["secure_key"]
assert "<Person_1>" in masked_text
assert secure_key is not None

print("=== Unmask with correct key ===")
resp = client.post(
    "/documents/unmask",
    json={"document_id": document_id, "key": secure_key},
    headers=headers,
)
print(resp.status_code, resp.json())
assert resp.status_code == 200
assert resp.json()["restored_text"] == text_data

print("=== Unmask with wrong key should fail cleanly ===")
wrong_key = Fernet.generate_key().decode()
resp = client.post(
    "/documents/unmask",
    json={"document_id": document_id, "key": wrong_key},
    headers=headers,
)
print(resp.status_code, resp.json())
assert resp.status_code == 400
assert "Decryption failed" in resp.json()["detail"]

print("=== Dashboard ===")
resp = client.get("/documents/dashboard", headers=headers)
print(resp.status_code, resp.json())
assert resp.status_code == 200

print("=== History ===")
resp = client.get("/documents/history", headers=headers)
print(resp.status_code, resp.json())
assert resp.status_code == 200

print("ALL ROUTES PASSED")
