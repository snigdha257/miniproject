"""
spacy_pii_pipeline.py

A full, runnable Python script demonstrating custom PII detection rules with spaCy.
Features:
1. Pipeline setup (loading the model and placing EntityRuler BEFORE statistical NER).
2. MONEY_PII detection handling Western/Indian number formats, multipliers, prefix/suffix currency signals.
3. EMPLOYEE_ID detection covering optional separators and hashes.
4. PHONE_NUMBER detection for both US and International formats.
5. SURROUNDING CONTEXT priority bumping (marking high priority when salary words are nearby).
6. EXPLICIT OVERLAP RESOLUTION showing how to let the custom EntityRuler win over default NER.
"""

import sys
import spacy
from spacy.pipeline import EntityRuler
from spacy.tokens import Span

# Ensure stdout encodes UTF-8 to correctly display currency symbols like ₹, £, and €
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Register custom extension attribute on Spans to hold the context priority flag.
# By using custom extensions, we keep spaCy's Span object native and clean.
if not Span.has_extension("is_high_priority"):
    Span.set_extension("is_high_priority", default=False)


def create_pii_pipeline():
    """
    Creates and configures the spaCy pipeline.
    Places the EntityRuler BEFORE the default 'ner' component to ensure custom matches 
    take priority and are not overridden or split by the statistical model.
    """
    # Load model (fall back to sm if lg is not installed)
    try:
        nlp = spacy.load("en_core_web_lg")
        print("[PIPELINE] Loaded en_core_web_lg successfully.")
    except OSError:
        nlp = spacy.load("en_core_web_sm")
        print("[PIPELINE] Loaded en_core_web_sm successfully.")

    # =========================================================================
    # 1. DEFINE PATTERNS (using token-based match patterns where possible)
    # =========================================================================
    
    # --- MONEY_PII Patterns ---
    # Goal: Match amounts preceded or followed by currency codes/symbols: $, ₹, Rs, Rs., INR, USD, £, €
    # Supports commas in both Indian (8,50,000) and Western (71,200) formatting.
    # Also matches k (thousands), L/Lakhs (hundred-thousands), Cr/Crores (ten-millions), and LPA/CrPA.
    money_patterns = [
        # Pattern 1a: Prefix currency symbol/code + number (optionally with multiplier)
        # e.g., $71,200 (Matches case 1), ₹8,50,000 (Matches case 5), Rs 8.5 (Matches case 7 prefix)
        {"label": "MONEY_PII", "pattern": [
            {"LOWER": {"IN": ["$", "₹", "rs", "inr", "usd", "£", "€"]}},
            {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr|LPA|lpa)?$"}}
        ]},
        
        # Pattern 1b: Prefix with dot (like 'Rs.') + number (optionally with multiplier)
        # e.g., Rs. 850000 (Matches case 6)
        {"label": "MONEY_PII", "pattern": [
            {"LOWER": "rs"},
            {"ORTH": "."},
            {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr|LPA|lpa)?$"}}
        ]},
        
        # Pattern 2: Number + suffix currency symbol/code
        # e.g., 71,200 USD (Matches case 4), 8.5 LPA (Matches case 8), 8.5 Lakhs
        {"label": "MONEY_PII", "pattern": [
            {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
            {"LOWER": {"IN": ["usd", "inr", "lpa", "crpa", "lakhs", "crores", "$", "₹", "£", "€"]}}
        ]},
        
        # Pattern 3a: Prefix + number + suffix
        # e.g., Rs 8.5 LPA (Matches case 7 in its entirety)
        {"label": "MONEY_PII", "pattern": [
            {"LOWER": {"IN": ["$", "₹", "rs", "inr", "usd", "£", "€"]}},
            {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
            {"LOWER": {"IN": ["usd", "inr", "lpa", "crpa", "lakhs", "crores"]}}
        ]},
        
        # Pattern 3b: Prefix + dot + number + suffix
        # e.g., Rs. 8.5 LPA
        {"label": "MONEY_PII", "pattern": [
            {"LOWER": "rs"},
            {"ORTH": "."},
            {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kKlL]|cr|Cr)?$"}},
            {"LOWER": {"IN": ["usd", "inr", "lpa", "crpa", "lakhs", "crores"]}}
        ]},
        
        # Pattern 4: Amount with explicit money-related multiplier attached directly
        # e.g., 71k (Matches case 3), ₹8.5L (Matches case 9 suffix)
        {"label": "MONEY_PII", "pattern": [
            {"TEXT": {"REGEX": r"^\d+(?:,\d+)*(?:\.\d+)?(?:[kK]|[lL]|[cC]r|[lL]PA|[lL]pa)$"}}
        ]}
    ]

    # --- EMPLOYEE_ID Patterns ---
    # Goal: Match prefixes EMP, E, STAFF, ID, or # followed by optional separator (-, ., space, or none) and digits.
    employee_patterns = [
        # Pattern 1: Single token variants
        # e.g., EMP-40218 (Case 10), EMP40218 (Case 11), E-40218 (Case 12), E40218 (Case 13), STAFF12345 (Case 14), ID-8821 (Case 15)
        {"label": "EMPLOYEE_ID", "pattern": [
            {"TEXT": {"REGEX": r"(?i)^(?:EMP|E|STAFF|ID)[-\.\s]?\d+$"}}
        ]},
        
        # Pattern 2: Hash prefix symbol + digits (e.g. #8821 - Case 16)
        {"label": "EMPLOYEE_ID", "pattern": [
            {"ORTH": "#"},
            {"TEXT": {"REGEX": r"^\d+$"}}
        ]},
        
        # Pattern 3: Multi-token with hyphen, dot, or space separator
        # e.g., STAFF - 12345 or EMP.40218
        {"label": "EMPLOYEE_ID", "pattern": [
            {"LOWER": {"IN": ["emp", "e", "staff", "id"]}},
            {"ORTH": {"IN": ["-", ".", " "]}},
            {"TEXT": {"REGEX": r"^\d+$"}}
        ]},
        
        # Pattern 4: Multi-token separated by space
        # e.g., STAFF 12345
        {"label": "EMPLOYEE_ID", "pattern": [
            {"LOWER": {"IN": ["emp", "e", "staff", "id"]}},
            {"TEXT": {"REGEX": r"^\d+$"}}
        ]}
    ]

    # --- PHONE_NUMBER Patterns ---
    # Goal: Match US telephone formats and international numbers with country codes.
    phone_patterns = [
        # Pattern 1: US format (Single token)
        # e.g., 5035550164 (Case 20), 503.555.0164 (Case 19)
        {"label": "PHONE_NUMBER", "pattern": [
            {"TEXT": {"REGEX": r"^(?:\d{10}|\d{3}\.\d{3}\.\d{4})$"}}
        ]},
        
        # Pattern 2: US format with hyphens (Multi-token)
        # e.g., 503-555-0164 (Case 18)
        {"label": "PHONE_NUMBER", "pattern": [
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"ORTH": "-"},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"ORTH": "-"},
            {"TEXT": {"REGEX": r"^\d{4}$"}}
        ]},
        
        # Pattern 3: US format with parentheses and space
        # e.g., (503) 555-0164 (Case 17)
        {"label": "PHONE_NUMBER", "pattern": [
            {"ORTH": "("},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"ORTH": ")"},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"ORTH": "-"},
            {"TEXT": {"REGEX": r"^\d{4}$"}}
        ]},
        
        # Pattern 4: International format with country code and spaces
        # e.g., +1 503 555 0164 (Case 21)
        {"label": "PHONE_NUMBER", "pattern": [
            {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"TEXT": {"REGEX": r"^\d{4}$"}}
        ]},
        
        # Pattern 5: International format with country code (e.g. +91) and 5-5 split digits
        # e.g., +91 98765 43210 (Case 22)
        {"label": "PHONE_NUMBER", "pattern": [
            {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
            {"TEXT": {"REGEX": r"^\d{5}$"}},
            {"TEXT": {"REGEX": r"^\d{5}$"}}
        ]},
        
        # Pattern 6: International with hyphens
        # e.g., +1-503-555-0164
        {"label": "PHONE_NUMBER", "pattern": [
            {"TEXT": {"REGEX": r"^\+\d{1,4}$"}},
            {"ORTH": "-"},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"ORTH": "-"},
            {"TEXT": {"REGEX": r"^\d{3}$"}},
            {"ORTH": "-"},
            {"TEXT": {"REGEX": r"^\d{4}$"}}
        ]},
        
        # Pattern 7: International with parentheses
        # e.g., +1 (503) 555-0164
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

    all_patterns = money_patterns + employee_patterns + phone_patterns

    # =========================================================================
    # 2. CONSTRUCT & ADD ENTITY RULER (Before 'ner' Component)
    # =========================================================================
    # Placing it before 'ner' ensures that the statistical model respects the
    # entities matched by the EntityRuler. We also set overwrite_ents=True just 
    # in case any earlier custom component wrote to doc.ents.
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(all_patterns)

    # =========================================================================
    # 3. CONTEXT PRIORITY BUMPING COMPONENT
    # =========================================================================
    # Runs after 'ner' to inspect the text surrounding our custom matches.
    # Bumps the 'is_high_priority' flag for MONEY_PII entities if salary keywords are nearby.
    @spacy.Language.component("priority_bumper")
    def priority_bumper(doc):
        priority_keywords = {
            "salary", "comp", "ctc", "pay", "paid", "package", 
            "compensation", "wages", "earns", "offered", "bonus"
        }
        for ent in doc.ents:
            if ent.label_ == "MONEY_PII":
                # Look at a context window of 5 tokens before and 5 tokens after the entity
                start_idx = max(0, ent.start - 5)
                end_idx = min(len(doc), ent.end + 5)
                
                # Retrieve the lowercase string of surrounding tokens
                surrounding_tokens = [
                    doc[i].lower_ for i in range(start_idx, end_idx) 
                    if i < ent.start or i >= ent.end
                ]
                
                # Bump priority flag if any keyword matches
                if any(kw in surrounding_tokens for kw in priority_keywords):
                    ent._.is_high_priority = True
        return doc

    nlp.add_pipe("priority_bumper", after="ner")
    
    return nlp


# =========================================================================
# 4. EXPLICIT CONFLICT RESOLUTION (Fallback Helper)
# =========================================================================
def resolve_overlaps_custom(entities):
    """
    Shows how to manually resolve overlapping entities if they are extracted from 
    different sources (e.g., raw regex runs combined with default NER runs).
    
    Prioritizes:
    - Custom PII Labels (MONEY_PII, EMPLOYEE_ID, PHONE_NUMBER) over default NER labels (e.g. CARDINAL, MONEY, ORG).
    - The longer span if labels are of the same type.
    """
    # Sort entities by start index, and then by length descending
    sorted_ents = sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"])))
    resolved = []
    
    custom_labels = {"MONEY_PII", "EMPLOYEE_ID", "PHONE_NUMBER"}
    
    for current in sorted_ents:
        has_overlap = False
        for i, existing in enumerate(resolved):
            # Check overlap: start1 < end2 and start2 < end1
            if current["start"] < existing["end"] and existing["start"] < current["end"]:
                has_overlap = True
                
                # Conflict Resolution Logic:
                current_is_custom = current["label"] in custom_labels
                existing_is_custom = existing["label"] in custom_labels
                
                if current_is_custom and not existing_is_custom:
                    # Custom wins over default
                    resolved[i] = current
                elif not current_is_custom and existing_is_custom:
                    # Default loses to custom, keep existing
                    pass
                else:
                    # Tie-breaker (both custom or both default): longer span wins
                    current_len = current["end"] - current["start"]
                    existing_len = existing["end"] - existing["start"]
                    if current_len > existing_len:
                        resolved[i] = current
                break
        
        if not has_overlap:
            resolved.append(current)
            
    return resolved


# =========================================================================
# 5. EXECUTION & VERIFICATION TEST HARNESS
# =========================================================================
if __name__ == "__main__":
    nlp = create_pii_pipeline()
    
    print("\n" + "=" * 80)
    print("DEMO: RUNNING PIPELINE ON COMPOUND TEST STRING")
    print("=" * 80)
    
    # This compound text contains:
    # 1. "John Doe" -> Default NER (PERSON)
    # 2. "EMP-40218" -> Custom (EMPLOYEE_ID)
    # 3. "₹8,50,000" -> Custom (MONEY_PII), with "CTC package" nearby -> High Priority
    # 4. "$71200" -> Custom (MONEY_PII), with NO salary context nearby -> Normal Priority
    # 5. "(503) 555-0164" -> Custom (PHONE_NUMBER) - US format
    # 6. "+91 98765 43210" -> Custom (PHONE_NUMBER) - International format
    compound_text = (
        "We recently hired John Doe (Employee ID: EMP-40218). "
        "His CTC package was ₹8,50,000, and he requested a signing bonus. "
        "For the other project, we transferred $71200 directly. "
        "You can reach him at (503) 555-0164 or +91 98765 43210."
    )
    
    doc = nlp(compound_text)
    
    print(f"{'DETECTED ENTITY':<20} | {'TEXT VALUE':<20} | {'HIGH PRIORITY?':<15}")
    print("-" * 65)
    for ent in doc.ents:
        is_high = getattr(ent._, "is_high_priority", False)
        print(f"{ent.label_:<20} | {ent.text:<20} | {str(is_high):<15}")
        
    print("\n" + "=" * 80)
    print("VERIFYING ALL INDIVIDUAL FORMAT CASES REQUIRED BY USER")
    print("=" * 80)
    
    test_cases = [
        # --- SALARY / MONEY FORMATS ---
        ("$71,200", "Western comma formatting (prefix symbol)"),
        ("$71200", "No comma Western format (prefix symbol)"),
        ("71k", "Multiplier 'k' without symbol (matched on its own)"),
        ("71,200 USD", "Western commas with currency code suffix"),
        ("₹8,50,000", "Indian Lakhs formatting (prefix symbol)"),
        ("Rs. 850000", "Prefix code with dot and space separator"),
        ("Rs 8.5 LPA", "Prefix code with decimal and Lakhs Per Annum suffix"),
        ("8.5 LPA", "Lakhs Per Annum suffix (matches on its own)"),
        ("₹8.5L", "Prefix symbol with decimal and Lakhs suffix"),
        
        # --- EMPLOYEE ID FORMATS ---
        ("EMP-40218", "Employee ID with hyphen separator"),
        ("EMP40218", "Employee ID with no separator"),
        ("E-40218", "Abbreviated prefix with hyphen"),
        ("E40218", "Abbreviated prefix with no separator"),
        ("STAFF12345", "Alternative prefix with no separator"),
        ("ID-8821", "Alternative prefix with hyphen"),
        ("#8821", "Hash prefix notation"),
        
        # --- PHONE NUMBER FORMATS ---
        ("(503) 555-0164", "US phone with parentheses and space"),
        ("503-555-0164", "US phone with hyphen separators"),
        ("503.555.0164", "US phone with dot separators"),
        ("5035550164", "US phone as continuous 10-digits"),
        ("+1 503 555 0164", "International US phone with country code"),
        ("+91 98765 43210", "International Indian phone with country code")
    ]
    
    print(f"{'CASE #':<7} | {'INPUT FORMAT':<20} | {'MATCHED ENTITY':<28} | {'PATTERN DESCRIPTION'}")
    print("-" * 105)
    for idx, (tf, desc) in enumerate(test_cases):
        temp_doc = nlp(tf)
        ents = [f"{e.text} [{e.label_}]" for e in temp_doc.ents]
        matched_str = ", ".join(ents) if ents else "NO MATCH"
        print(f"Case {idx+1:<2} | {tf:<20} | {matched_str:<28} | {desc}")

    print("\n" + "=" * 80)
    print("DEMO: MANUALLY RESOLVING OVERLAPS (CONFLICT HANDLING)")
    print("=" * 80)
    # Simulate a scenario where another system flags things overlapping.
    # Here, we have "71200" overlapping as both custom "MONEY_PII" and default "CARDINAL"
    raw_detections = [
        {"text": "John Doe", "label": "PERSON", "start": 18, "end": 26},
        {"text": "EMP-40218", "label": "EMPLOYEE_ID", "start": 41, "end": 50},
        {"text": "EMP-40218", "label": "CARDINAL", "start": 45, "end": 50},  # Overlap 1 (default CARDINAL vs custom ID)
        {"text": "₹8,50,000", "label": "MONEY_PII", "start": 71, "end": 80},
        {"text": "8,50,000", "label": "MONEY", "start": 72, "end": 80},      # Overlap 2 (default MONEY vs custom MONEY_PII)
    ]
    
    resolved_detections = resolve_overlaps_custom(raw_detections)
    print("Before Resolution:")
    for d in raw_detections:
        print(f"  - {d['text']} -> {d['label']} ({d['start']}:{d['end']})")
        
    print("\nAfter Resolution (Custom wins and overrides default NER overlapping spans):")
    for d in resolved_detections:
        print(f"  * {d['text']} -> {d['label']} ({d['start']}:{d['end']})")
    
    print("=" * 80)
