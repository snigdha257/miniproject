"""
backend/services/masking_engine.py

Mask detected entities in text in one of three modes:
- placeholder: typed tags like <Person_1>
- partial: keep the first letter of each word/segment and mask the rest
- full: replace the entire span with full redaction blocks

The engine preserves original formatting and whitespace by rebuilding the text
around ordered entity spans.
"""

from typing import List, Dict, Tuple

REDACT_CHAR = "█"
PLACEHOLDER_LABELS = {
    "PERSON": "Person",
    "ORG": "Org",
    "EMAIL": "Email",
    "PHONE": "Phone",
    "AADHAAR": "Aadhaar",
    "PAN": "PAN",
    "PASSPORT": "Passport",
    "CREDIT_CARD": "CreditCard",
}


def _mask_word(word: str, preserve_last: bool = False) -> str:
    if len(word) <= 1:
        return word
    if preserve_last and len(word) > 2:
        return word[0] + "*" * (len(word) - 2) + word[-1]
    return word[0] + "*" * (len(word) - 1)


def _mask_email(email: str) -> str:
    if "@" not in email:
        return _mask_word(email, preserve_last=True)

    local, domain = email.split("@", 1)
    masked_local_parts = []
    for segment in local.split("."):
        masked_local_parts.append(_mask_word(segment, preserve_last=False))
    return f"{'.'.join(masked_local_parts)}@{domain}"


def _make_placeholder(label: str, text: str, counters: Dict[str, int], cache: Dict[Tuple[str, str], str]) -> str:
    normalized = (label, text)
    if normalized in cache:
        return cache[normalized]

    counters[label] = counters.get(label, 0) + 1
    placeholder_label = PLACEHOLDER_LABELS.get(label, label.title())
    tag = f"<{placeholder_label}_{counters[label]}>"
    cache[normalized] = tag
    return tag


def _mask_entity_text(entity: Dict, mode: str) -> str:
    label = entity.get("label", "UNKNOWN").upper()
    original = entity.get("text", "")

    if mode == "full":
        return REDACT_CHAR * len(original)

    if mode == "placeholder":
        raise RuntimeError("placeholder mode should be handled separately")

    if mode == "partial":
        if label == "EMAIL":
            return _mask_email(original)
        if label == "ORG":
            words = original.split()
            return " ".join(_mask_word(word, preserve_last=True) for word in words)
        return " ".join(_mask_word(word, preserve_last=False) for word in original.split())

    raise ValueError(f"Unknown masking mode: {mode}")


def mask_text(text: str, entities: List[Dict], mode: str) -> Dict:
    """
    Mask the given text according to detected entities and return the masked text
    plus a mapping of original/replacement spans.

    Args:
        text: Original document text.
        entities: Ordered list of entity dicts with keys text, label, start, end.
        mode: One of "placeholder", "partial", or "full".

    Returns:
        A dict containing masked_text and mapping list.
    """
    if mode not in {"placeholder", "partial", "full"}:
        raise ValueError(f"Unsupported mode: {mode}")

    ordered = sorted(entities, key=lambda ent: (ent["start"], -ent["end"]))
    output_parts: List[str] = []
    mapping: List[Dict] = []
    last_index = 0
    placeholder_counters: Dict[str, int] = {}
    placeholder_cache: Dict[Tuple[str, str], str] = {}

    for entity in ordered:
        start = entity["start"]
        end = entity["end"]
        if start < last_index:
            # Skip overlapping or nested entities that have already been covered.
            continue
        if start > len(text) or end > len(text):
            raise ValueError("Entity span is out of bounds")

        output_parts.append(text[last_index:start])

        if mode == "placeholder":
            replacement = _make_placeholder(entity["label"].upper(), entity["text"], placeholder_counters, placeholder_cache)
        else:
            replacement = _mask_entity_text(entity, mode)

        output_parts.append(replacement)
        mapping.append({
            "original": entity["text"],
            "replacement": replacement,
            "type": entity["label"].upper(),
            "position": (start, end),
        })
        last_index = end

    output_parts.append(text[last_index:])
    return {
        "masked_text": "".join(output_parts),
        "mapping": mapping,
    }


if __name__ == "__main__":
    sample = "John Doe from Google (john.doe@gmail.com)"
    entities = [
        {"text": "John Doe", "label": "PERSON", "start": 0, "end": 8},
        {"text": "Google", "label": "ORG", "start": 14, "end": 20},
        {"text": "john.doe@gmail.com", "label": "EMAIL", "start": 22, "end": 40},
    ]

    for mode in ["placeholder", "partial", "full"]:
        result = mask_text(sample, entities, mode)
        print(f"MODE={mode}")
        print(result["masked_text"])
        print(result["mapping"])
        print()
