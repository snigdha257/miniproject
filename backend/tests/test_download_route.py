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


def test_txt_download_returns_attachment(client):
    email = f'download-{uuid4().hex[:8]}@example.com'
    signup = client.post('/auth/signup', json={'email': email, 'password': 'secret123'})
    assert signup.status_code == 200

    login = client.post('/auth/login', json={'email': email, 'password': 'secret123'})
    assert login.status_code == 200
    token = login.json()['access_token']

    upload = client.post(
        '/documents/upload',
        headers={'Authorization': f'Bearer {token}'},
        data={'text': 'My SSN is 123-45-6789 and email is demo@example.com'},
    )
    assert upload.status_code == 200
    document_id = upload.json()['document_id']

    mask = client.post(
        '/documents/mask',
        headers={'Authorization': f'Bearer {token}'},
        json={'document_id': document_id, 'mode': 'standard', 'style': 'placeholder'},
    )
    assert mask.status_code == 200

    response = client.get(
        f'/documents/{document_id}/download',
        headers={'Authorization': f'Bearer {token}'},
        params={'format': 'txt'},
    )

    assert response.status_code == 200
    assert 'text/plain' in response.headers['content-type']
    assert 'attachment' in response.headers['content-disposition']
    assert 'masked.txt' in response.headers['content-disposition']
