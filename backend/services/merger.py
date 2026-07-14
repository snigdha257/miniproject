"""
backend/services/merger.py

Merge and deduplicate overlapping entity spans from multiple detectors.
"""

from typing import List, Dict


def merge_entities(
    ner_results: List[Dict],
    regex_results: List[Dict],
    context_results: List[Dict],
) -> List[Dict]:
    """
    Merge entity lists while deduplicating overlapping spans based on priority:
    1. NOT_SENSITIVE spans from context_results act as suppression zones.
    2. Overlapping spans are resolved by priority: context (3) > regex (2) > ner (1).
    3. If priority is equal, the longer span is preferred.

    Args:
        ner_results: spaCy NER entities.
        regex_results: regex pattern matches.
        context_results: disambiguation hints.

    Returns:
        Ordered list of merged entities.
    """
    ner_res = ner_results or []
    regex_res = regex_results or []
    context_res = context_results or []

    # 1. Gather all suppressed (NOT_SENSITIVE) spans from context_results
    suppressed_spans = []
    for ent in context_res:
        if ent.get("label", "").upper() == "NOT_SENSITIVE":
            suppressed_spans.append((ent["start"], ent["end"]))

    def is_suppressed(start: int, end: int) -> bool:
        for s_start, s_end in suppressed_spans:
            if max(start, s_start) < min(end, s_end):
                return True
        return False

    # 2. Build list of candidates that are not suppressed
    candidates = []

    for ent in ner_res:
        if not is_suppressed(ent["start"], ent["end"]):
            candidates.append({
                "text": ent["text"],
                "label": ent["label"],
                "start": ent["start"],
                "end": ent["end"],
                "priority": 1
            })

    for ent in regex_res:
        if not is_suppressed(ent["start"], ent["end"]):
            candidates.append({
                "text": ent["text"],
                "label": ent["label"],
                "start": ent["start"],
                "end": ent["end"],
                "priority": 2
            })

    for ent in context_res:
        if ent.get("label", "").upper() != "NOT_SENSITIVE":
            if not is_suppressed(ent["start"], ent["end"]):
                candidates.append({
                    "text": ent["text"],
                    "label": ent["label"],
                    "start": ent["start"],
                    "end": ent["end"],
                    "priority": 3
                })

    # Sort candidates: start ascending, end descending (longest span first)
    candidates.sort(key=lambda item: (item["start"], -item["end"]))

    merged: List[Dict] = []
    for candidate in candidates:
        keep = True
        overlapping_indices = [
            index
            for index, existing in enumerate(merged)
            if max(existing["start"], candidate["start"]) < min(existing["end"], candidate["end"])
        ]

        for index in reversed(overlapping_indices):
            existing = merged[index]
            if candidate["priority"] > existing["priority"]:
                merged.pop(index)
            elif candidate["priority"] < existing["priority"]:
                keep = False
                break
            else:
                last_len = existing["end"] - existing["start"]
                cand_len = candidate["end"] - candidate["start"]
                if cand_len > last_len:
                    merged.pop(index)
                else:
                    keep = False
                    break

        if keep:
            merged.append(candidate)

    # Strip priority before returning
    return [
        {
            "text": ent["text"],
            "label": ent["label"],
            "start": ent["start"],
            "end": ent["end"],
        }
        for ent in merged
    ]


if __name__ == "__main__":
    from pathlib import Path

    # Running as a standalone script from backend/services, so import locally.
    from ner_detector import detect_entities
    from regex_detector import detect_patterns
    from context_analyzer import detect_contextual_entities

    sample_text = Path(__file__).parent / "sample.txt"
    content = sample_text.read_text(encoding="utf-8")

    ner = detect_entities(content)
    regex = detect_patterns(content)
    context = detect_contextual_entities(content)
    merged = merge_entities(ner, regex, context)

    print("=" * 60)
    print("MERGED ENTITY LIST — sample.txt")
    print("=" * 60)
    for entity in merged:
        print(
            f"{entity['label']:<13} {entity['text']:<30} {entity['start']:>6} {entity['end']:>6}"
        )
    print(f"\n[OK] Merged {len(merged)} entities.")
