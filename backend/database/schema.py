from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from pymongo import ASCENDING
from pymongo.collection import Collection

from database.connection import db


COLLECTIONS = {
    "users": "users",
    "documents": "documents",
    "mappings": "mappings",
    "history": "history",
}


def _collection(name: str) -> Collection:
    return db[name]


def ensure_indexes() -> None:
    users = _collection("users")
    users.create_index("email", unique=True)

    documents = _collection("documents")
    documents.create_index([("user_id", ASCENDING)])

    mappings = _collection("mappings")
    mappings.create_index([("document_id", ASCENDING)], unique=True)


# ----- users -----
def create_user(document: Dict[str, Any]) -> ObjectId:
    result = _collection("users").insert_one(document)
    return result.inserted_id


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return _collection("users").find_one({"email": email})


def get_user_by_id(user_id: Any) -> Optional[Dict[str, Any]]:
    return _collection("users").find_one({"_id": user_id})


def update_user(user_id: Any, updates: Dict[str, Any]) -> None:
    _collection("users").update_one({"_id": user_id}, {"$set": updates})


def delete_user(user_id: Any) -> None:
    _collection("users").delete_one({"_id": user_id})


# ----- documents -----
def create_document(document: Dict[str, Any]) -> ObjectId:
    result = _collection("documents").insert_one(document)
    return result.inserted_id


def get_document_by_id(document_id: Any) -> Optional[Dict[str, Any]]:
    return _collection("documents").find_one({"_id": document_id})


def get_documents_for_user(user_id: Any) -> List[Dict[str, Any]]:
    return list(_collection("documents").find({"user_id": user_id}))


def get_document_for_user(document_id: Any, user_id: Any) -> Optional[Dict[str, Any]]:
    return _collection("documents").find_one({"_id": document_id, "user_id": user_id})


def update_document(document_id: Any, updates: Dict[str, Any]) -> None:
    _collection("documents").update_one({"_id": document_id}, {"$set": updates})


def delete_document(document_id: Any) -> None:
    _collection("documents").delete_one({"_id": document_id})


def count_documents_for_user(user_id: Any) -> int:
    return _collection("documents").count_documents({"user_id": user_id})


def list_documents_for_user(user_id: Any, skip: int = 0, limit: int = 10):
    return list(
        _collection("documents")
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )


# ----- mappings -----
def create_mapping(document: Dict[str, Any]) -> ObjectId:
    result = _collection("mappings").insert_one(document)
    return result.inserted_id


def get_mapping_by_document_id(document_id: Any) -> Optional[Dict[str, Any]]:
    return _collection("mappings").find_one({"document_id": document_id})


def update_mapping(document_id: Any, updates: Dict[str, Any]) -> None:
    _collection("mappings").update_one({"document_id": document_id}, {"$set": updates})


def delete_mapping(document_id: Any) -> None:
    _collection("mappings").delete_one({"document_id": document_id})


# ----- history -----
def create_history_entry(document: Dict[str, Any]) -> ObjectId:
    result = _collection("history").insert_one(document)
    return result.inserted_id


def get_history_for_user(user_id: Any, skip: int = 0, limit: int = 10):
    return list(
        _collection("history")
        .find({"user_id": user_id})
        .sort("date", -1)
        .skip(skip)
        .limit(limit)
    )


def update_history_entry(history_id: Any, updates: Dict[str, Any]) -> None:
    _collection("history").update_one({"_id": history_id}, {"$set": updates})


def delete_history_entry(history_id: Any) -> None:
    _collection("history").delete_one({"_id": history_id})
