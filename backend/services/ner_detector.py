"""
backend/services/ner_detector.py

Detect named entities using spaCy's en_core_web_sm model.

Model is loaded ONCE at module level so repeated calls to detect_entities()
pay no startup cost — critical for request-time performance.
"""

import spacy

# ---------------------------------------------------------------------------
# Module-level model load — do NOT move this inside detect_entities().
# Loading takes ~200 ms; keeping it here means every subsequent call is fast.
# ---------------------------------------------------------------------------
_nlp = spacy.load("en_core_web_sm")

# Entity labels we treat as potentially sensitive.
# spaCy label reference: https://spacy.io/models/en#en_core_web_sm-labels
SENSITIVE_LABELS = {
    "PERSON",   # People, including fictional
    "ORG",      # Companies, agencies, institutions
    "GPE",      # Countries, cities, states
    "LOC",      # Non-GPE locations (mountains, rivers, etc.)
    "NORP",     # Nationalities, religious or political groups
    "FAC",      # Buildings, airports, highways, bridges, etc.
    "EMAIL",    # Email addresses (spaCy 3.x detects these in some pipelines)
    "MONEY",    # Monetary values
    "DATE",     # Absolute or relative dates / periods
}


def _normalize_text_for_ner(text: str) -> str:
    """
    Normalize text for spaCy NER while preserving original offsets.

    Newline characters are replaced with spaces so that entities on adjacent
    lines do not bleed together, but text length remains unchanged.
    """
    if not text:
        return text

    normalized = text.replace("\r\n", "\n").replace("\t", " ")
    return normalized.replace("\n", " ")


def detect_entities(text: str) -> list[dict]:
    """
    Run spaCy NER on text and return sensitive entities.

    Args:
        text: Plain text string.

    Returns:
        List of dicts with keys: text, label, start, end.
    """
    normalized_text = _normalize_text_for_ner(text)
    doc = _nlp(normalized_text)
    results = []
    for ent in doc.ents:
        if ent.label_ in SENSITIVE_LABELS:
            results.append({
                "text": ent.text.strip(),
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            })
    return results


# ---------------------------------------------------------------------------
# Manual verification — run: python ner_detector.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from pathlib import Path

    sample_path = Path(__file__).parent / "sample.txt"
    sample_text = sample_path.read_text(encoding="utf-8")

    print("=" * 60)
    print("NER DETECTION — sample.txt")
    print("=" * 60)

    entities = detect_entities(sample_text)

    # Pretty-print with alignment
    print(f"{'LABEL':<15} {'TEXT':<35} {'START':>6} {'END':>6}")
    print("-" * 65)
    for e in entities:
        print(f"{e['label']:<15} {e['text']:<35} {e['start']:>6} {e['end']:>6}")

    print(f"\n[OK] {len(entities)} entities detected.\n")

    # Quick sanity checks
    labels_found = {e["label"] for e in entities}
    persons = [e for e in entities if e["label"] == "PERSON"]
    orgs    = [e for e in entities if e["label"] == "ORG"]
    gpes    = [e for e in entities if e["label"] == "GPE"]

    print(f"Label types seen : {sorted(labels_found)}")
    print(f"PERSON entities  : {[e['text'] for e in persons]}")
    print(f"ORG entities     : {[e['text'] for e in orgs]}")
    print(f"GPE entities     : {[e['text'] for e in gpes]}")
