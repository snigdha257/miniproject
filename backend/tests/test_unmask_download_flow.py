"""Test that after unmasking, download returns the restored document."""
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


def test_unmask_then_download_returns_restored_document(client):
    """Verify that after unmasking, download returns the restored (unmasked) document."""
    # Setup: Create user
    email = f'unmask-download-{uuid4().hex[:8]}@example.com'
    signup = client.post('/auth/signup', json={'email': email, 'password': 'secret123'})
    assert signup.status_code == 200

    login = client.post('/auth/login', json={'email': email, 'password': 'secret123'})
    assert login.status_code == 200
    token = login.json()['access_token']

    # Step 1: Upload document with PII
    original_text = 'My name is Alice Johnson, my email is alice@example.com and my phone is 555-1234.'
    upload = client.post(
        '/documents/upload',
        headers={'Authorization': f'Bearer {token}'},
        data={'text': original_text},
    )
    assert upload.status_code == 200
    document_id = upload.json()['document_id']

    # Step 2: Analyze to detect entities
    analyze = client.post(
        '/documents/analyze',
        headers={'Authorization': f'Bearer {token}'},
        json={'document_id': document_id, 'processing_mode': 'standard'},
    )
    assert analyze.status_code == 200

    # Step 3: Mask in secure mode (generates key)
    mask = client.post(
        '/documents/mask',
        headers={'Authorization': f'Bearer {token}'},
        json={'document_id': document_id, 'mode': 'secure', 'style': 'placeholder'},
    )
    assert mask.status_code == 200
    secure_key = mask.json()['secure_key']
    masked_text = mask.json()['masked_text']
    print(f"[TEST] Original: {original_text}")
    print(f"[TEST] Masked: {masked_text}")
    # Verify text is masked
    assert original_text != masked_text
    assert 'Alice' not in masked_text or masked_text.count('Alice') == 0  # Name should be masked

    # Step 4: Unmask with correct key
    unmask = client.post(
        '/documents/unmask',
        headers={'Authorization': f'Bearer {token}'},
        json={'document_id': document_id, 'key': secure_key},
    )
    assert unmask.status_code == 200
    restored_text = unmask.json()['restored_text']
    print(f"[TEST] Restored: {restored_text}")
    # Verify restored matches original
    assert restored_text == original_text

    # Step 5: Download and verify it returns the restored document (not the masked version) - TXT format
    response = client.get(
        f'/documents/{document_id}/download',
        headers={'Authorization': f'Bearer {token}'},
        params={'format': 'txt'},
    )
    assert response.status_code == 200
    assert 'text/plain' in response.headers['content-type']
    assert 'attachment' in response.headers['content-disposition']
    
    downloaded_text = response.text
    print(f"[TEST] Downloaded TXT: {downloaded_text}")
    
    # This is the key assertion: after unmasking, download should return the restored text, not masked
    assert downloaded_text == original_text, f"Downloaded text does not match original. Downloaded: {downloaded_text}, Expected: {original_text}"
    assert downloaded_text != masked_text, f"Downloaded text is still masked! Downloaded: {downloaded_text}, Masked was: {masked_text}"
    
    # Step 6: Also test PDF download to ensure it returns original PDF without redaction
    response_pdf = client.get(
        f'/documents/{document_id}/download',
        headers={'Authorization': f'Bearer {token}'},
        params={'format': 'pdf'},
    )
    assert response_pdf.status_code == 200
    assert 'application/pdf' in response_pdf.headers['content-type']
    assert 'attachment' in response_pdf.headers['content-disposition']
    assert len(response_pdf.content) > 0
    print(f"[TEST] Downloaded PDF: {len(response_pdf.content)} bytes")
