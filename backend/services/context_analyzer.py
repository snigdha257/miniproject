"""
backend/services/context_analyzer.py

Simple rule-based disambiguation for a small set of known ambiguous terms.
This is designed to remain lightweight and rule-based; it can be swapped
for a transformer-based zero-shot classifier later if time allows.
"""

from typing import List, Tuple

# The keys are ambiguous tokens and the values are lists of keywords that
# favour an ORG interpretation vs a NON-SENSITIVE interpretation.
CONTEXT_RULES = {
    "apple": {
        "org": {"launched", "inc", "ceo", "headquarters", "hq", "iphone", "macbook", "company", "subsidiary"},
        "not_sensitive": {"ate", "fruit", "juice", "pie", "orchard", "apple"},
    },
    "amazon": {
        "org": {"web services", "aws", "inc", "ceo", "cloud", "studio", "company", "logistics", "prime"},
        "not_sensitive": {"river", "basin", "rainforest", "jungle", "boat", "fish", "flood"},
    },
    "raja": {
        "org": {"foundation", "hospital", "group", "technologies"},
        "not_sensitive": {"Mr", "Ms", "Dr", "surnames", "family"},
    },
}

WINDOW_SIZE = 40


def _window_tokens(text: str, start: int, end: int) -> str:
    left = max(0, start - WINDOW_SIZE)
    right = min(len(text), end + WINDOW_SIZE)
    return text[left:right].lower()


def detect_contextual_entities(text: str) -> List[dict]:
    """
    Use a lightweight windowed keyword lookup to disambiguate ambiguous terms.

    Args:
        text: Plain text string.

    Returns:
        List of dicts with keys: text, label, start, end.
    """
    results: List[dict] = []
    lowered = text.lower()

    for token, rules in CONTEXT_RULES.items():
        start = 0
        while True:
            index = lowered.find(token, start)
            if index == -1:
                break
            end = index + len(token)
            window = _window_tokens(text, index, end)

            org_hits = sum(1 for kw in rules["org"] if kw in window)
            non_hits = sum(1 for kw in rules["not_sensitive"] if kw in window)

            if org_hits > non_hits:
                label = "ORG"
            elif non_hits > org_hits:
                label = "NOT_SENSITIVE"
            else:
                label = "AMBIGUOUS"

            results.append({
                "text": text[index:end],
                "label": label,
                "start": index,
                "end": end,
            })
            start = end

    return results


if __name__ == "__main__":
    from pathlib import Path

    sample_text = Path(__file__).parent / "sample.txt"
    content = sample_text.read_text(encoding="utf-8")

    print("=" * 60)
    print("CONTEXT ANALYSIS — sample.txt")
    print("=" * 60)
    disambiguations = detect_contextual_entities(content)
    for item in disambiguations:
        print(
            f"{item['label']:<13} {item['text']:<10} {item['start']:>6} {item['end']:>6}"
        )
    print("\n[OK] Context analyzer completed.")
