"""
Test the full secure_mask_text and unmask_text pipeline.
"""

import sys
import os
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(backend_dir, 'services'))
from secure_masking import generate_key, secure_mask_text, unmask_text

print("=" * 80)
print("FULL PIPELINE TEST - SAME SESSION")
print("=" * 80)

# Test 1: Same session round-trip
key = generate_key()
original = "Alice Patel from Acme Corp (alice.patel@acme.com)"
print(f"Original: {original}")
print(f"Key type: {type(key)}, length: {len(key)}")

masked_text, encrypted_blob = secure_mask_text(original, key)
print(f"\nMasked text: {masked_text}")
print(f"Encrypted blob type: {type(encrypted_blob)}, length: {len(encrypted_blob)}")

try:
    restored = unmask_text(masked_text, encrypted_blob, key)
    print(f"\nRestored: {restored}")
    print(f"Same session round-trip successful: {restored == original}")
except Exception as e:
    print(f"\nSame session round-trip FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("FULL PIPELINE TEST - CROSS SESSION (SIMULATED)")
print("=" * 80)

# Test 2: Cross session - simulate storing and retrieving
# This simulates what happens when you save the key and blob to storage
key_str = key.decode("utf-8")  # Simulate storing as string
blob_str = encrypted_blob.decode("utf-8")  # Simulate storing as string

print(f"Stored key as string: {key_str[:20]}...")
print(f"Stored blob as string: {blob_str[:40]}...")

# Now retrieve and use
retrieved_key = key_str.encode("utf-8")
retrieved_blob = blob_str.encode("utf-8")

try:
    restored_cross = unmask_text(masked_text, retrieved_blob, retrieved_key)
    print(f"\nRestored from storage: {restored_cross}")
    print(f"Cross session round-trip successful: {restored_cross == original}")
except Exception as e:
    print(f"\nCross session round-trip FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("FULL PIPELINE TEST - WITH PRE-DETECTED ENTITIES")
print("=" * 80)

# Test 3: With pre-detected entities (common usage pattern)
from pipeline import detect_text_entities

text2 = "John Smith works at Google. His email is john.smith@gmail.com"
entities = detect_text_entities(text2)
print(f"Text: {text2}")
print(f"Entities: {entities}")

key2 = generate_key()
masked2, encrypted2 = secure_mask_text(text2, key2, entities)
print(f"\nMasked: {masked2}")

try:
    restored2 = unmask_text(masked2, encrypted2, key2)
    print(f"Restored: {restored2}")
    print(f"Pre-detected entities round-trip successful: {restored2 == text2}")
except Exception as e:
    print(f"Pre-detected entities round-trip FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
