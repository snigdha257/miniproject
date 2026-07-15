"""
backend/services/pipeline.py

Integrated detection pipeline that extracts text, runs NER, regex pattern detection,
context disambiguation, and merges the final entity list.
"""

from typing import List, Dict

from services.extractor import extract_text
from services.ner_detector import detect_entities as detect_ner_entities
from services.regex_detector import detect_patterns as detect_regex_patterns
from services.context_analyzer import detect_contextual_entities
from services.merger import merge_entities


def detect_text_entities(text: str) -> List[Dict]:
    """
    Detect sensitive entities in plain text by combining all detectors.

    Args:
        text: Plain text to analyze.

    Returns:
        Ordered merged list of entity dictionaries.
    """
    print("\n" + "="*80)
    print("[PIPELINE] 1. Extracted Text Received Exactly:")
    print(text)
    print("="*80)

    ner_results = detect_ner_entities(text)
    print(f"\n[PIPELINE] 2a. Detected NER Entities ({len(ner_results)}):")
    for ent in ner_results:
        print(f"  - Text: {repr(ent.get('text'))}, Type: {ent.get('label')}, Start: {ent.get('start')}, End: {ent.get('end')}")

    regex_results = detect_regex_patterns(text)
    print(f"\n[PIPELINE] 2b. Detected Regex Entities ({len(regex_results)}):")
    for ent in regex_results:
        print(f"  - Text: {repr(ent.get('text'))}, Type: {ent.get('label')}, Start: {ent.get('start')}, End: {ent.get('end')}")

    context_results = detect_contextual_entities(text)
    print(f"\n[PIPELINE] 2c. Detected Contextual Entities ({len(context_results)}):")
    for ent in context_results:
        print(f"  - Text: {repr(ent.get('text'))}, Type: {ent.get('label')}, Start: {ent.get('start')}, End: {ent.get('end')}")

    merged = merge_entities(ner_results, regex_results, context_results)
    print(f"\n[PIPELINE] 3. Merged Entity List ({len(merged)}):")
    for ent in merged:
        print(f"  - Text: {repr(ent.get('text'))}, Type: {ent.get('label')}, Start: {ent.get('start')}, End: {ent.get('end')}")
    print("="*80 + "\n")
    return merged


def detect_file_entities(file_path: str) -> List[Dict]:
    """
    Extract text from a supported file and detect entities.

    Args:
        file_path: Path to a .txt, .pdf, or .docx file.

    Returns:
        Ordered merged list of entity dictionaries.
    """
    text = extract_text(file_path)
    return detect_text_entities(text)


if __name__ == "__main__":
    from pathlib import Path

    sample_path = Path(__file__).parent / "sample.txt"
    sample_text = sample_path.read_text(encoding="utf-8")

    print("=" * 60)
    print("FULL DETECTION PIPELINE — sample.txt")
    print("=" * 60)

    entities = detect_text_entities(sample_text)
    print(f"Detected {len(entities)} merged entities:\n")
    print(f"{'LABEL':<15} {'TEXT':<35} {'START':>6} {'END':>6}")
    print("-" * 70)
    for entity in entities:
        print(
            f"{entity['label']:<15} {entity['text']:<35} {entity['start']:>6} {entity['end']:>6}"
        )

    print("\n[OK] Full pipeline completed.")
