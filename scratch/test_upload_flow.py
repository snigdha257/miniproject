import os
import requests

BASE_URL = "http://localhost:8000"

def run_tests():
    # 1. Sign up / login
    email = "test_upload_user@example.com"
    password = "password123"
    
    # Try signup, fallback to login
    print("Signing up...")
    resp = requests.post(f"{BASE_URL}/auth/signup", json={"email": email, "password": password})
    if resp.status_code == 200:
        token = resp.json()["access_token"]
    else:
        print("Signup failed (probably already exists), logging in...")
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
        token = resp.json()["access_token"]
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload text file
    txt_path = "backend/services/sample.txt"
    print(f"Uploading file: {txt_path}")
    with open(txt_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": (os.path.basename(txt_path), f, "text/plain")},
            headers=headers
        )
    print("Upload status:", resp.status_code)
    print("Upload response:", resp.json())
    assert resp.status_code == 200
    doc_id = resp.json()["document_id"]
    
    # Mask document standard
    print("Masking standard placeholder...")
    resp = requests.post(
        f"{BASE_URL}/documents/mask",
        json={"document_id": doc_id, "mode": "standard", "style": "placeholder"},
        headers=headers
    )
    print("Mask status:", resp.status_code)
    print("Mask response:", resp.json())
    assert resp.status_code == 200
    
    # Mask document secure
    print("Masking secure...")
    resp = requests.post(
        f"{BASE_URL}/documents/mask",
        json={"document_id": doc_id, "mode": "secure", "style": "placeholder"},
        headers=headers
    )
    print("Mask status:", resp.status_code)
    print("Mask response:", resp.json())
    assert resp.status_code == 200

    # 3. Upload docx file
    docx_path = "backend/services/sample.docx"
    print(f"Uploading file: {docx_path}")
    with open(docx_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"file": (os.path.basename(docx_path), f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers
        )
    print("Upload status:", resp.status_code)
    print("Upload response:", resp.json())
    assert resp.status_code == 200

if __name__ == "__main__":
    run_tests()
