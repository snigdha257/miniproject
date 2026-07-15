"""
Test the actual API flow for secure masking/unmasking.
Simulates what happens in the routes.
"""

import sys
import os
import base64
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(backend_dir, 'services'))
from secure_masking import generate_key, secure_mask_text, unmask_text

print("=" * 80)
print("SIMULATING API FLOW - MASK")
print("=" * 80)

# Simulate mask_document route
original_text = "Alice Patel from Acme Corp (alice.patel@acme.com)"
key = generate_key()
print(f"Generated key type: {type(key)}, length: {len(key)}")

# Mask with the key
masked_text, encrypted_blob = secure_mask_text(original_text, key)
print(f"Masked text: {masked_text}")
print(f"Encrypted blob type: {type(encrypted_blob)}, length: {len(encrypted_blob)}")

# Encode blob as base64 (like the API does)
encoded_blob = base64.b64encode(encrypted_blob).decode("utf-8")
print(f"Base64 encoded blob type: {type(encoded_blob)}, length: {len(encoded_blob)}")

# Return key as UTF-8 string (like the API does)
secure_key = key.decode("utf-8")
print(f"Secure key type: {type(secure_key)}, length: {len(secure_key)}")
print(f"Secure key (first 20 chars): {secure_key[:20]}...")

print("\n" + "=" * 80)
print("SIMULATING API FLOW - UNMASK")
print("=" * 80)

# Simulate unmask_document route
# User provides the key as a string (from the API response)
request_key = secure_key  # This is what the user would send back
print(f"Request key type: {type(request_key)}, length: {len(request_key)}")

# Retrieve the base64-encoded blob from storage
retrieved_encoded_blob = encoded_blob
print(f"Retrieved encoded blob type: {type(retrieved_encoded_blob)}")

# Decode the blob from base64 (like the API does)
decoded_blob = base64.b64decode(retrieved_encoded_blob)
print(f"Decoded blob type: {type(decoded_blob)}, length: {len(decoded_blob)}")

# Try to unmask
try:
    restored = unmask_text(masked_text, decoded_blob, request_key)
    print(f"\nRestored text: {restored}")
    print(f"API flow round-trip successful: {restored == original_text}")
except Exception as e:
    print(f"\nAPI flow round-trip FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("CHECKING KEY CONSISTENCY")
print("=" * 80)

# Check if the key round-trips correctly
key_bytes = secure_key.encode("utf-8")
print(f"Original key: {key[:20]}...")
print(f"Key from string: {key_bytes[:20]}...")
print(f"Keys match: {key == key_bytes}")
