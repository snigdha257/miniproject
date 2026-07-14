import pytest

from privacy_analyzer import analyze_privacy


def test_analyze_privacy_computes_high_risk_for_sensitive_entities():
    entities = [
        {"text": "user1@example.com", "label": "EMAIL", "start": 0, "end": 17},
        {"text": "user2@example.com", "label": "EMAIL", "start": 18, "end": 35},
        {"text": "user3@example.com", "label": "EMAIL", "start": 36, "end": 53},
        {"text": "+91-98765-43210", "label": "PHONE", "start": 54, "end": 67},
        {"text": "+91 91234 56789", "label": "PHONE", "start": 68, "end": 82},
        {"text": "2345 6789 0123", "label": "AADHAAR", "start": 83, "end": 98},
    ]

    summary = analyze_privacy(entities)

    assert summary["privacy_score"] == 83
    assert summary["risk_level"] == "HIGH"
    assert summary["entity_counts"]["EMAIL"] == 3
    assert summary["entity_counts"]["PHONE"] == 2
    assert summary["entity_counts"]["AADHAAR"] == 1
    assert len(summary["critical_findings"]) == 1
    assert summary["critical_findings"][0]["label"] == "AADHAAR"


def test_analyze_privacy_returns_low_for_no_sensitive_entities():
    summary = analyze_privacy([])

    assert summary["privacy_score"] == 0
    assert summary["risk_level"] == "LOW"
    assert summary["entity_counts"] == {}
    assert summary["critical_findings"] == []
