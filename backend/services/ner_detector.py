"""
backend/services/ner_detector.py

Detect named entities using spaCy's en_core_web_sm model.

Model is loaded ONCE at module level so repeated calls to detect_entities()
pay no startup cost — critical for request-time performance.
"""

import spacy
from spacy.pipeline import EntityRuler
from spacy.tokens import Span

# Register custom extension attribute on Spans to hold the context priority flag.
if not Span.has_extension("is_high_priority"):
    Span.set_extension("is_high_priority", default=False)

# ---------------------------------------------------------------------------
# Module-level model load — do NOT move this inside detect_entities().
# Loading takes ~200 ms; keeping it here means every subsequent call is fast.
# ---------------------------------------------------------------------------
_nlp = spacy.load("en_core_web_sm")

# Define Custom Patterns
money_patterns = [
    # Prefix currency symbol/code + number (which may have multiplier or trailing /-)
    {"label": "MONEY_PII", "pattern": [
        {"LOWER": {"IN": ["$", "₹", "rs", "inr", "usd", "£", "€"]}},
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr|LPA|lpa)?(?:/-)?$"}}
    ]},
    # Prefix with dot + number (which may have multiplier or trailing /-)
    {"label": "MONEY_PII", "pattern": [
        {"LOWER": "rs"},
        {"ORTH": "."},
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr|LPA|lpa)?(?:/-)?$"}}
    ]},
    # Number + suffix currency symbol/code
    {"label": "MONEY_PII", "pattern": [
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?(?:/-)?$"}},
        {"LOWER": {"IN": ["usd", "inr", "lpa", "crpa", "lakhs", "crores", "$", "₹", "£", "€"]}}
    ]},
    # Prefix + number + suffix
    {"label": "MONEY_PII", "pattern": [
        {"LOWER": {"IN": ["$", "₹", "rs", "inr", "usd", "£", "€"]}},
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
        {"LOWER": {"IN": ["usd", "inr", "lpa", "crpa", "lakhs", "crores", "/-"]}}
    ]},
    # Prefix + dot + number + suffix
    {"label": "MONEY_PII", "pattern": [
        {"LOWER": "rs"},
        {"ORTH": "."},
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
        {"LOWER": {"IN": ["usd", "inr", "lpa", "crpa", "lakhs", "crores", "/-"]}}
    ]},
    # Multiplier or trailing /- only
    {"label": "MONEY_PII", "pattern": [
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kK]|[lL]|[cC]r|[lL]PA|[lL]pa|/-)$"}}
    ]},
    # Number followed by separate /- token
    {"label": "MONEY_PII", "pattern": [
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
        {"ORTH": "/-"}
    ]},
    # Number followed by separate / and - tokens
    {"label": "MONEY_PII", "pattern": [
        {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
        {"ORTH": "/"},
        {"ORTH": "-"}
    ]}
]

employee_patterns = [
    # Single token variant (EMP-40218, EMP40218, etc.)
    {"label": "EMPLOYEE_ID", "pattern": [
        {"TEXT": {"REGEX": r"(?i)^(?:EMP|E|STAFF|ID)[-\.\s]?\d+$"}}
    ]},
    # Hash format
    {"label": "EMPLOYEE_ID", "pattern": [
        {"ORTH": "#"},
        {"TEXT": {"REGEX": r"^\d+$"}}
    ]},
    # Multi-token with hyphen, dot, or space separator
    {"label": "EMPLOYEE_ID", "pattern": [
        {"LOWER": {"IN": ["emp", "e", "staff", "id"]}},
        {"ORTH": {"IN": ["-", ".", " "]}},
        {"TEXT": {"REGEX": r"^\d+$"}}
    ]},
    # Multi-token space separation
    {"label": "EMPLOYEE_ID", "pattern": [
        {"LOWER": {"IN": ["emp", "e", "staff", "id"]}},
        {"TEXT": {"REGEX": r"^\d+$"}}
    ]}
]

phone_patterns = [
    # US format (Single token)
    {"label": "PHONE_NUMBER", "pattern": [
        {"TEXT": {"REGEX": r"^(?:\d{10}|\d{3}\.\d{3}\.\d{4})$"}}
    ]},
    # US format with hyphens
    {"label": "PHONE_NUMBER", "pattern": [
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{4}$"}}
    ]},
    # US format with parentheses
    {"label": "PHONE_NUMBER", "pattern": [
        {"ORTH": "("},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": ")"},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{4}$"}}
    ]},
    # International with spaces
    {"label": "PHONE_NUMBER", "pattern": [
        {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"TEXT": {"REGEX": r"^\d{4}$"}}
    ]},
    # International with 5-5 split
    {"label": "PHONE_NUMBER", "pattern": [
        {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
        {"TEXT": {"REGEX": r"^\d{5}$"}},
        {"TEXT": {"REGEX": r"^\d{5}$"}}
    ]},
    # International with hyphens
    {"label": "PHONE_NUMBER", "pattern": [
        {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{4}$"}}
    ]},
    # International with parentheses
    {"label": "PHONE_NUMBER", "pattern": [
        {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
        {"ORTH": "("},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": ")"},
        {"TEXT": {"REGEX": r"^\d{3}$"}},
        {"ORTH": "-"},
        {"TEXT": {"REGEX": r"^\d{4}$"}}
    ]}
]

# Add EntityRuler BEFORE NER
_ruler = _nlp.add_pipe("entity_ruler", before="ner")
_ruler.add_patterns(money_patterns + employee_patterns + phone_patterns)

# Context priority bumping component
@spacy.Language.component("priority_bumper")
def priority_bumper(doc):
    priority_keywords = {
        "salary", "comp", "ctc", "pay", "paid", "package", 
        "compensation", "wages", "earns", "offered", "bonus"
    }
    for ent in doc.ents:
        if ent.label_ == "MONEY_PII":
            start_idx = max(0, ent.start - 5)
            end_idx = min(len(doc), ent.end + 5)
            surrounding_tokens = [
                doc[i].lower_ for i in range(start_idx, end_idx) 
                if i < ent.start or i >= ent.end
            ]
            if any(kw in surrounding_tokens for kw in priority_keywords):
                ent._.is_high_priority = True
                print(f"[PIPELINE][BUMP] High-priority MONEY_PII detected: '{ent.text}' (salary context matched nearby)")
    return doc

# Add priority bumper AFTER NER
_nlp.add_pipe("priority_bumper", after="ner")

# Entity labels we treat as potentially sensitive.
SENSITIVE_LABELS = {
    "PERSON",   # People, including fictional
    "ORG",      # Companies, agencies, institutions
    "GPE",      # Countries, cities, states
    "LOC",      # Non-GPE locations (mountains, rivers, etc.)
    "NORP",     # Nationalities, religious or political groups
    "FAC",      # Buildings, airports, highways, bridges, etc.
    "EMAIL",    # Email addresses
    "MONEY",    # Monetary values
    "DATE",     # Absolute or relative dates / periods
    "MONEY_PII",    # Custom high-precision Money/Salary detection
    "EMPLOYEE_ID",  # Custom Employee ID detection
    "PHONE_NUMBER", # Custom Phone Number detection
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
        List of dicts with keys: text, label, start, end, is_high_priority.
    """
    normalized_text = _normalize_text_for_ner(text)
    doc = _nlp(normalized_text)
    results = []
    for ent in doc.ents:
        if ent.label_ in SENSITIVE_LABELS:
            is_high = False
            if ent.label_ == "MONEY_PII" and hasattr(ent._, "is_high_priority"):
                is_high = ent._.is_high_priority
            results.append({
                "text": ent.text.strip(),
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "is_high_priority": is_high,
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
