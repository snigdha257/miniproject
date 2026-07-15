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
    "SSN": "SSN",
    "CREDIT_CARD": "CreditCard",
    "IP_ADDRESS": "IPAddress",
    "MAC_ADDRESS": "MACAddress",
    "IBAN": "IBAN",
    "TAX_ID": "TaxID",
    "ROUTING_NUMBER": "RoutingNumber",
    "VIN": "VIN",
    "GENDER": "Gender",
    "AGE": "Age",
    "MONEY_PII": "Money",
    "EMPLOYEE_ID": "EmployeeID",
    "PHONE_NUMBER": "Phone",
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
        if label in {"SSN", "CREDIT_CARD", "IP_ADDRESS", "MAC_ADDRESS", "IBAN", "TAX_ID", "ROUTING_NUMBER", "VIN", "EMPLOYEE_ID", "PHONE_NUMBER"}:
            sep = " "
            for char in ["-", ":", "."]:
                if char in original:
                    sep = char
                    break
            parts = original.split(sep)
            return sep.join(_mask_word(part) for part in parts)
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

    # 1. Sort left-to-right: start ascending, end descending (longest span first)
    sorted_left_to_right = sorted(entities, key=lambda ent: (ent["start"], -ent["end"]))

    # 2. Filter out overlapping and duplicate entities (left-to-right) AND pre-calculate replacements
    filtered_entities: List[Dict] = []
    last_end = 0
    placeholder_counters: Dict[str, int] = {}
    placeholder_cache: Dict[Tuple[str, str], str] = {}

    print("\n" + "="*80)
    print("[MASKING] Filtering overlaps and pre-calculating replacements (left-to-right):")
    for ent in sorted_left_to_right:
        start = ent["start"]
        end = ent["end"]
        if start >= last_end:
            # Calculate replacement
            if mode == "placeholder":
                replacement = _make_placeholder(ent["label"].upper(), ent["text"], placeholder_counters, placeholder_cache)
            else:
                replacement = _mask_entity_text(ent, mode)
            
            # Save replacement on the entity dictionary
            ent_copy = dict(ent)
            ent_copy["replacement"] = replacement
            
            filtered_entities.append(ent_copy)
            last_end = end
            print(f"  - Keeping: '{ent['text']}' at {start}:{end} -> replacement: '{replacement}'")
        else:
            print(f"  - Skipping overlap/duplicate: '{ent['text']}' at {start}:{end} (overlaps with index < {last_end})")
    print("="*80 + "\n")

    # 3. Sort from highest start index to lowest start index (right-to-left)
    ordered_right_to_left = sorted(filtered_entities, key=lambda ent: ent["start"], reverse=True)

    current_text = text
    mapping: List[Dict] = []

    print("="*80)
    print(f"[MASKING] Starting right-to-left replacement (mode={mode}):")
    
    for entity in ordered_right_to_left:
        start = entity["start"]
        end = entity["end"]
        if start > len(text) or end > len(text):
            raise ValueError("Entity span is out of bounds")

        replacement = entity["replacement"]

        # Logging before replacement
        print(f"  - BEFORE: Text segment at {start}:{end} is {repr(current_text[start:end])}")
        
        # Replace using character slice
        current_text = current_text[:start] + replacement + current_text[end:]
        
        # Logging after replacement
        print(f"    AFTER: Replaced with {repr(replacement)}")

        mapping.append({
            "original": entity["text"],
            "replacement": replacement,
            "type": entity["label"].upper(),
            "position": (start, end),
        })

    # Since we processed right-to-left, reverse the mapping list to restore left-to-right order
    mapping.reverse()
    print(f"[MASKING] Masking complete. Final length: {len(current_text)}")
    print("="*80 + "\n")

    return {
        "masked_text": current_text,
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
