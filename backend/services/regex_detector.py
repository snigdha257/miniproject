"""
backend/services/regex_detector.py

Detect sensitive patterns in text with regex.
Returns a list of dicts with keys: text, label, start, end.
"""

import re
from typing import List

PATTERN_DEFINITIONS = [
    {
        "label": "AADHAAR",
        "regex": re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),
    },
    {
        "label": "PAN",
        "regex": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE),
    },
    {
        "label": "PASSPORT",
        "regex": re.compile(r"\b[A-Z][0-9]{7}\b", re.IGNORECASE),
    },
    {
        "label": "PHONE",
        "regex": re.compile(
            r"\b(?:\+91[\s-]?|0)?[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{4}\b"
        ),
    },
    {
        "label": "CREDIT_CARD",
        "regex": re.compile(
            r"\b(?:\d[ -]?){13,19}\b"
        ),
    },
]


def _is_luhn_valid(number: str) -> bool:
    digits = [int(ch) for ch in number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def detect_patterns(text: str) -> List[dict]:
    """
    Detect structured sensitive patterns in text.

    Args:
        text: Plain text string.

    Returns:
        List of dicts with keys: text, label, start, end.
    """
    results: List[dict] = []

    for pattern in PATTERN_DEFINITIONS:
        label = pattern["label"]
        regex = pattern["regex"]

        for match in regex.finditer(text):
            matched = match.group(0).strip()
            if label == "CREDIT_CARD":
                normalized = re.sub(r"[\s-]", "", matched)
                if not _is_luhn_valid(normalized):
                    continue
            results.append({
                "text": matched,
                "label": label,
                "start": match.start(),
                "end": match.end(),
            })

    return sorted(results, key=lambda item: (item["start"], -item["end"]))


if __name__ == "__main__":
    from pathlib import Path

    sample_text = Path(__file__).parent / "sample.txt"
    content = sample_text.read_text(encoding="utf-8")

    print("=" * 60)
    print("REGEX PATTERN DETECTION — sample.txt")
    print("=" * 60)
    matches = detect_patterns(content)
    print(f"Detected {len(matches)} patterns:\n")
    for match in matches:
        print(
            f"{match['label']:<12} {match['text']:<25} {match['start']:>6} {match['end']:>6}"
        )
    print("\n[OK] Regex detection completed.")
