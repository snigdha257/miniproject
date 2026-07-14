"""
backend/services/privacy_analyzer.py

Compute a simple privacy exposure score from a merged entity list.
"""

from typing import List, Dict

# Sensitivity weights for entity labels.
SENSITIVITY_WEIGHTS = {
    "AADHAAR": 25,
    "CREDIT_CARD": 25,
    "PAN": 15,
    "PASSPORT": 15,
    "EMAIL": 8,
    "PHONE": 8,
    "PERSON": 3,
    "ORG": 3,
}

RISK_LEVELS = [
    (0, 39, "LOW"),
    (40, 69, "MEDIUM"),
    (70, 100, "HIGH"),
]


def _compute_risk_level(score: int) -> str:
    for minimum, maximum, label in RISK_LEVELS:
        if minimum <= score <= maximum:
            return label
    return "HIGH"


def analyze_privacy(entities: List[Dict]) -> Dict:
    """
    Analyze merged entities and return a privacy exposure summary.

    Args:
        entities: A merged list of entity dicts with keys: text, label, start, end.

    Returns:
        A summary dict containing privacy_score, risk_level, entity_counts,
        and critical_findings.
    """
    entity_counts = {}
    critical_findings = []
    raw_score = 0
    sensitive_count = 0

    for entity in entities:
        label = entity.get("label", "UNKNOWN").upper()
        entity_counts[label] = entity_counts.get(label, 0) + 1
        weight = SENSITIVITY_WEIGHTS.get(label, 5)
        raw_score += weight

        if label in {"AADHAAR", "CREDIT_CARD", "PAN", "PASSPORT"}:
            critical_findings.append(
                {
                    "label": label,
                    "text": entity.get("text", ""),
                    "start": entity.get("start"),
                    "end": entity.get("end"),
                }
            )

        if label in {
            "AADHAAR",
            "CREDIT_CARD",
            "PAN",
            "PASSPORT",
            "EMAIL",
            "PHONE",
        }:
            sensitive_count += 1

    # Add a small exposure multiplier for repeated sensitive items so the score
    # reflects both the severity of each type and the volume of sensitive data.
    privacy_score = int(min(100, raw_score + sensitive_count * 3))
    risk_level = _compute_risk_level(privacy_score)

    return {
        "privacy_score": privacy_score,
        "risk_level": risk_level,
        "entity_counts": entity_counts,
        "critical_findings": critical_findings,
    }


if __name__ == "__main__":
    sample_entities = [
        {"text": "rajesh.kumar@acmecorp.in", "label": "EMAIL", "start": 0, "end": 24},
        {"text": "hr@acmecorp.in", "label": "EMAIL", "start": 25, "end": 40},
        {"text": "support@acme.in", "label": "EMAIL", "start": 41, "end": 56},
        {"text": "+91-98765-43210", "label": "PHONE", "start": 57, "end": 70},
        {"text": "+91 91234 56789", "label": "PHONE", "start": 71, "end": 85},
        {"text": "2345 6789 0123", "label": "AADHAAR", "start": 86, "end": 101},
    ]

    summary = analyze_privacy(sample_entities)
    print(f"Privacy Score {summary['privacy_score']}/100, Risk {summary['risk_level']}")
    print(summary)
