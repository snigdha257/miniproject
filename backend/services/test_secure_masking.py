import pytest

from secure_masking import WrongKeyError, decrypt_mapping, encrypt_mapping, generate_key, secure_mask_text, unmask_text


def test_secure_mask_text_and_unmask_with_correct_key():
    key = generate_key()
    original = "Alice Patel from Acme Corp (alice.patel@acme.com)"

    masked_text, encrypted_blob = secure_mask_text(original, key)
    restored = unmask_text(masked_text, encrypted_blob, key)

    assert restored == original
    assert "<Person_1>" in masked_text
    assert "<Org_1>" in masked_text


def test_unmask_with_wrong_key_raises_wrongkeyerror():
    key = generate_key()
    wrong_key = generate_key()
    original = "Bob Singh has email bob.singh@example.com"

    masked_text, encrypted_blob = secure_mask_text(original, key)

    with pytest.raises(WrongKeyError):
        unmask_text(masked_text, encrypted_blob, wrong_key)


def test_unmask_with_tampered_blob_raises_wrongkeyerror():
    key = generate_key()
    original = "Carol Kumar from Example Ltd"

    masked_text, encrypted_blob = secure_mask_text(original, key)
    tampered_blob = encrypted_blob[:-1] + (b"A" if encrypted_blob[-1:] != b"A" else b"B")

    with pytest.raises(WrongKeyError):
        unmask_text(masked_text, tampered_blob, key)
