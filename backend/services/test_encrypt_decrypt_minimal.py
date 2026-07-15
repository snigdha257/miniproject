"""
Minimal test to isolate the encrypt/decrypt bug.
Tests core encryption/decryption logic with hardcoded values.
"""

import sys
import os
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(backend_dir, 'services'))
from secure_masking import generate_key, encrypt_mapping, decrypt_mapping

# Hardcoded test values
original_text = "John Smith"
test_mapping = {"<Person_1>": original_text}

print("=" * 80)
print("MINIMAL ENCRYPT/DECRYPT TEST")
print("=" * 80)

# Generate key
key = generate_key()
print(f"Key type: {type(key)}")
print(f"Key length: {len(key)} bytes")
print(f"Key (first 20 chars): {key[:20]}...")

# Encrypt
print(f"\nOriginal mapping: {test_mapping}")
encrypted = encrypt_mapping(test_mapping, key)
print(f"Encrypted type: {type(encrypted)}")
print(f"Encrypted length: {len(encrypted)} bytes")
print(f"Encrypted (first 40 chars): {encrypted[:40]}...")

# Decrypt immediately
try:
    decrypted = decrypt_mapping(encrypted, key)
    print(f"\nDecrypted mapping: {decrypted}")
    print(f"Round-trip successful: {decrypted == test_mapping}")
except Exception as e:
    print(f"\nDecryption FAILED: {type(e).__name__}: {e}")

# Test with string key (common usage pattern)
print("\n" + "=" * 80)
print("TEST WITH STRING KEY")
print("=" * 80)
key_str = key.decode("utf-8")
print(f"Key string type: {type(key_str)}")
print(f"Key string length: {len(key_str)}")

encrypted_str = encrypt_mapping(test_mapping, key_str)
print(f"Encrypted with string key type: {type(encrypted_str)}")

try:
    decrypted_str = decrypt_mapping(encrypted_str, key_str)
    print(f"Decrypted with string key: {decrypted_str}")
    print(f"Round-trip with string key successful: {decrypted_str == test_mapping}")
except Exception as e:
    print(f"Decryption with string key FAILED: {type(e).__name__}: {e}")

# Test the problematic case: encrypted blob as string
print("\n" + "=" * 80)
print("TEST PROBLEMATIC CASE: ENCRYPTED BLOB AS STRING")
print("=" * 80)
# This simulates what might happen if the blob is stored as a string
encrypted_as_string = encrypted.decode("utf-8", errors="ignore")  # This will corrupt the data
print(f"Encrypted as string type: {type(encrypted_as_string)}")
print(f"Encrypted as string length: {len(encrypted_as_string)}")

try:
    decrypted_corrupted = decrypt_mapping(encrypted_as_string, key)
    print(f"Decrypted from corrupted string: {decrypted_corrupted}")
except Exception as e:
    print(f"Decryption from corrupted string FAILED: {type(e).__name__}: {e}")
