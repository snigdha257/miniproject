"""
Debug script to check what's stored in the database for a specific document.
"""

import sys
import os
from bson import ObjectId

backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from database.connection import db
from database.schema import get_document_for_user, get_mapping_by_document_id

document_id = "6a57bcc6405805e3beb5adf3"

print("=" * 80)
print("DEBUGGING DATABASE FOR DOCUMENT: " + document_id)
print("=" * 80)

# Try to get the document
try:
    doc = db.documents.find_one({"_id": ObjectId(document_id)})
    if doc:
        print("DOCUMENT FOUND:")
        print(f"  _id: {doc.get('_id')}")
        print(f"  user_id: {doc.get('user_id')}")
        print(f"  mode: {doc.get('mode')}")
        print(f"  maskedText: {doc.get('maskedText', 'N/A')[:100] if doc.get('maskedText') else 'N/A'}...")
        print(f"  originalText: {doc.get('originalText', 'N/A')[:100] if doc.get('originalText') else 'N/A'}...")
        print(f"  created_at: {doc.get('created_at')}")
    else:
        print("DOCUMENT NOT FOUND")
except Exception as e:
    print(f"ERROR GETTING DOCUMENT: {e}")

print("\n" + "=" * 80)
print("CHECKING MAPPING")
print("=" * 80)

try:
    mapping = db.mappings.find_one({"document_id": document_id})
    if mapping:
        print("MAPPING FOUND:")
        print(f"  document_id: {mapping.get('document_id')}")
        print(f"  encryptedMapping: {mapping.get('encryptedMapping', 'N/A')[:100] if mapping.get('encryptedMapping') else 'N/A'}...")
    else:
        print("MAPPING NOT FOUND")
except Exception as e:
    print(f"ERROR GETTING MAPPING: {e}")

print("\n" + "=" * 80)
print("ALL DOCUMENTS IN DATABASE")
print("=" * 80)

try:
    all_docs = list(db.documents.find({}))
    print(f"Total documents: {len(all_docs)}")
    for doc in all_docs:
        print(f"  - {doc.get('_id')}: mode={doc.get('mode')}, user={doc.get('user_id')}")
except Exception as e:
    print(f"ERROR GETTING ALL DOCUMENTS: {e}")

print("\n" + "=" * 80)
print("ALL MAPPINGS IN DATABASE")
print("=" * 80)

try:
    all_mappings = list(db.mappings.find({}))
    print(f"Total mappings: {len(all_mappings)}")
    for mapping in all_mappings:
        print(f"  - document_id={mapping.get('document_id')}, has_encrypted={bool(mapping.get('encryptedMapping'))}")
except Exception as e:
    print(f"ERROR GETTING ALL MAPPINGS: {e}")
