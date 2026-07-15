"""
Test that demonstrates the bug in decrypt_mapping when encrypted_blob is passed as a string.
"""

import sys
import os
import base64
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(backend_dir, 'services'))
from secure_masking import generate_key, encrypt_mapping, decrypt_mapping

print("=" * 80)
print("DEMONSTRATING THE BUG: ENCRYPTED BLOB AS STRING")
print("=" * 80)

# Generate key and encrypt
key = generate_key()
test_mapping = {"<Person_1>": "John Smith"}
encrypted_bytes = encrypt_mapping(test_mapping, key)

print(f"Original mapping: {test_mapping}")
print(f"Encrypted bytes type: {type(encrypted_bytes)}, length: {len(encrypted_bytes)}")

# This works fine with bytes
decrypted_from_bytes = decrypt_mapping(encrypted_bytes, key)
print(f"Decrypted from bytes: {decrypted_from_bytes}")
print(f"Bytes round-trip successful: {decrypted_from_bytes == test_mapping}")

print("\n" + "=" * 80)
print("BUG SCENARIO: BLOB PASSED AS STRING (CORRUPTS DATA)")
print("=" * 80)

# Simulate what happens if the blob is stored/transmitted as a UTF-8 string
# This is what the current buggy code tries to handle
encrypted_as_utf8_string = encrypted_bytes.decode("utf-8", errors="ignore")  # This will corrupt the data
print(f"Encrypted as UTF-8 string type: {type(encrypted_as_utf8_string)}, length: {len(encrypted_as_utf8_string)}")
print(f"First_chars: {encrypted_as_utf8_string[:40]}...")

try:
    # This is what the current buggy code does - it tries to encode the corrupted string back
    decrypted_corrupted = decrypt_mapping(encrypted_as_utf8_string, key)
    print(f"Decrypted from corrupted UTF-8 string: {decrypted_corrupted}")
    print(f"BUG: This should have failed but didn't!")
except Exception as e:
    print(f"Decryption from corrupted UTF-8 string FAILED: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("CORRECT APPROACH: BLOB AS BASE64-ENCODED STRING")
print("=" * 80)

# The correct way to store/transmit the blob as a string is base64 encoding
encrypted_as_base64_string = base64.b64encode(encrypted_bytes).decode("utf-8")
print(f"Encrypted as base64 string type: {type(encrypted_as_base64_string)}, length: {len(encrypted_as_base64_string)}")
print(f"First_chars: {encrypted_as_base64_string[:40]}...")

# But the current decrypt_mapping doesn't handle base64 strings correctly
# It will try to UTF-8 encode the base64 string, which will fail
try:
    decrypted_wrong = decrypt_mapping(encrypted_as_base64_string, key)
    print(f"Decrypted with current code (WRONG): {decrypted_wrong}")
except Exception as e:
    print(f"Current code fails on base64 string: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("WHAT SHOULD HAPPEN: DECODE BASE64 FIRST")
print("=" * 80)

# The correct approach: decode base64 string back to bytes before decrypting
decoded_blob = base64.b64decode(encrypted_as_base64_string)
decrypted_correct = decrypt_mapping(decoded_blob, key)
print(f"Decrypted from base64 string (CORRECT): {decrypted_correct}")
print(f"Base64 round-trip successful: {decrypted_correct == test_mapping}")
