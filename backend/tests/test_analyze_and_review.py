import sys
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_analyze_and_custom_mask(client):
    email = f"review-{uuid4().hex[:8]}@example.com"
    signup = client.post("/auth/signup", json={"email": email, "password": "secret123"})
    assert signup.status_code == 200

    login = client.post("/auth/login", json={"email": email, "password": "secret123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    # 1. Upload Document
    upload = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"text": "Amit lives in Bangalore. His email is amit@example.com"},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    # 2. Analyze Document (Standard Mode)
    analyze = client.post(
        "/documents/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"document_id": document_id, "processing_mode": "standard"},
    )
    assert analyze.status_code == 200
    entities = analyze.json()["entities"]
    
    # We should have PERSON (Amit) and EMAIL (amit@example.com)
    assert len(entities) > 0
    assert any(ent["text"] == "amit@example.com" for ent in entities)

    # 3. Mask with ONLY the email selected (deselect the Person name)
    selected_entities = [ent for ent in entities if ent["label"] == "EMAIL"]
    
    mask = client.post(
        "/documents/mask",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "document_id": document_id,
            "mode": "standard",
            "style": "placeholder",
            "entities": selected_entities,
        },
    )
    assert mask.status_code == 200
    masked_text = mask.json()["masked_text"]
    
    # Since we deselected Amit, Amit should remain unmasked.
    assert "Amit" in masked_text
    # Since email was selected, email should be masked.
    assert "<Email_1>" in masked_text
