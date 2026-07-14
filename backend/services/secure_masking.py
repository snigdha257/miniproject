"""
backend/services/secure_masking.py

Secure masking pipeline for the flagship feature.

This module performs: NER -> placeholder masking -> mapping generation -> mapping encryption.
The generated key must be saved by the caller because it cannot be recovered if lost.
"""

import json
from typing import Any, Dict, List, Tuple, Union

from cryptography.fernet import Fernet, InvalidToken

from services.pipeline import detect_text_entities
from services.masking_engine import mask_text


class WrongKeyError(Exception):
    """Raised when decryption fails because the provided Fernet key is wrong."""


def generate_key() -> bytes:
    """
    Generate a new Fernet key.

    Returns:
        A bytes key that must be saved securely by the caller. It cannot be recovered
        if lost, so store it safely outside the application.
    """
    return Fernet.generate_key()


def _normalize_key(key: Union[str, bytes]) -> bytes:
    if isinstance(key, str):
        return key.encode("utf-8")
    return key


def _mapping_list_to_dict(mapping_list: List[Dict[str, Any]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for item in mapping_list:
        placeholder = item.get("replacement")
        original = item.get("original")
        if placeholder is None or original is None:
            continue
        mapping[placeholder] = original
    return mapping


def encrypt_mapping(mapping: Union[List[Dict[str, Any]], Dict[str, str]], key: Union[str, bytes]) -> bytes:
    """
    Encrypt a placeholder-to-original mapping with the provided Fernet key.

    Args:
        mapping: A list of mapping dicts or a direct placeholder->original dict.
        key: Fernet key bytes or its utf-8 string form.

    Returns:
        Encrypted bytes blob.
    """
    key_bytes = _normalize_key(key)
    if isinstance(mapping, list):
        mapping_dict = _mapping_list_to_dict(mapping)
    else:
        mapping_dict = mapping

    serialized = json.dumps(mapping_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return Fernet(key_bytes).encrypt(serialized)


def decrypt_mapping(encrypted_blob: Union[bytes, str], key: Union[str, bytes]) -> Dict[str, str]:
    """
    Decrypt an encrypted mapping blob into the original placeholder mapping.

    Raises:
        WrongKeyError: When the provided key is incorrect or the blob is invalid.
    """
    key_bytes = _normalize_key(key)
    blob_bytes = encrypted_blob.encode("utf-8") if isinstance(encrypted_blob, str) else encrypted_blob

    try:
        decrypted = Fernet(key_bytes).decrypt(blob_bytes)
    except InvalidToken as exc:
        raise WrongKeyError("Decryption failed: wrong key or corrupted blob") from exc

    return json.loads(decrypted.decode("utf-8"))


def unmask_text(masked_text: str, encrypted_mapping: Union[bytes, str], key: Union[str, bytes]) -> str:
    """
    Restore a masked document by decrypting the mapping and replacing placeholders.

    Args:
        masked_text: Text containing placeholder tags.
        encrypted_mapping: Encrypted mapping blob.
        key: Fernet key.

    Returns:
        The fully restored document text.
    """
    mapping = decrypt_mapping(encrypted_mapping, key)

    replacements = sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True)
    restored = masked_text
    for placeholder, original in replacements:
        restored = restored.replace(placeholder, original)

    return restored


def secure_mask_text(text: str, key: Union[str, bytes]) -> Tuple[str, bytes]:
    """
    Perform the full detection pipeline on text, mask it in placeholder mode,
    and encrypt the placeholder mapping.

    Args:
        text: Original document text.
        key: Fernet key used to encrypt the mapping.

    Returns:
        A tuple of (masked_text, encrypted_mapping_blob).
    """
    entities = detect_text_entities(text)
    masked_result = mask_text(text, entities, "placeholder")
    encrypted_blob = encrypt_mapping(masked_result["mapping"], key)
    return masked_result["masked_text"], encrypted_blob
