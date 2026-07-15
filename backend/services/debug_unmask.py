"""
Debug script to test the unmask endpoint directly.
"""

import sys
import os
import base64
from bson import ObjectId

backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

from database.connection import db
from services.secure_masking import generate_key, secure_mask_text, unmask_text

print("=" * 80)
print("TESTING SECURE MASKING AND UNMASKING WITH DATABASE")
print("=" * 80)

# Test text
test_text = "John Smith from Acme Corp (john.smith@acme.com)"
print(f"Original text: {test_text}")

# Generate key and mask
key = generate_key()
print(f"Generated key: {key.decode('utf-8')}")

# Mask the text
masked_text, encrypted_blob = secure_mask_text(test_text, key)
print(f"Masked text: {masked_text}")
print(f"Encrypted blob length: {len(encrypted_blob)}")

# Store in database like the API would
print("\n" + "=" * 80)
print("STORING IN DATABASE")
print("=" * 80)

# Create a test user
user_result = db.users.insert_one({
    "email": "test@example.com",
    "password_hash": "test_hash",
})
user_id = user_result.inserted_id
print(f"Created user: {user_id}")

# Create document
doc_result = db.documents.insert_one({
    "user_id": user_id,
    "filename": None,
    "originalText": test_text,
    "maskedText": masked_text,
    "mode": "secure",
    "privacy_report": {},
    "entities": [],
})
document_id = doc_result.inserted_id
print(f"Created document: {document_id}")

# Store mapping
encoded_blob = base64.b64encode(encrypted_blob).decode("utf-8")
mapping_result = db.mappings.insert_one({
    "document_id": str(document_id),
    "encryptedMapping": encoded_blob,
})
print(f"Created mapping for document: {document_id}")

print("\n" + "=" * 80)
print("TESTING UNMASK FROM DATABASE")
print("=" * 80)

# Retrieve like the API would
retrieved_doc = db.documents.find_one({"_id": document_id})
retrieved_mapping = db.mappings.find_one({"document_id": str(document_id)})

print(f"Retrieved document mode: {retrieved_doc.get('mode')}")
print(f"Retrieved document has maskedText: {bool(retrieved_doc.get('maskedText'))}")
print(f"Retrieved mapping exists: {bool(retrieved_mapping)}")
print(f"Retrieved mapping has encryptedMapping: {bool(retrieved_mapping.get('encryptedMapping'))}")

# Test unmask
try:
    if retrieved_doc.get("mode") != "secure":
        print("ERROR: Document mode is not secure")
    elif not retrieved_mapping or not retrieved_mapping.get("encryptedMapping"):
        print("ERROR: Mapping or encryptedMapping missing")
    else:
        masked_text_from_db = retrieved_doc.get("maskedText") or retrieved_doc.get("masked_text") or ""
        encrypted_blob_from_db = base64.b64decode(retrieved_mapping["encryptedMapping"])
        
        restored = unmask_text(masked_text_from_db, encrypted_blob_from_db, key)
        print(f"Restored text: {restored}")
        print(f"SUCCESS: Round-trip worked! {restored == test_text}")
except Exception as e:
    print(f"ERROR during unmask: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n" + "=" * 80)
print("CLEANUP")
print("=" * 80)
db.documents.delete_one({"_id": document_id})
db.mappings.delete_one({"document_id": str(document_id)})
db.users.delete_one({"_id": user_id})
print("Cleaned up test data")
