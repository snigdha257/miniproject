import base64
import os
import tempfile
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import constr

from database.connection import db
from routes.auth import get_current_user
from routes.schemas import (
    DashboardResponse,
    DocumentHistoryItem,
    DocumentUploadResponse,
    HistoryResponse,
    MaskRequest,
    MaskResponse,
    UnmaskRequest,
    UnmaskResponse,
)
from services.extractor import extract_text
from services.masking_engine import mask_text
from services.pipeline import detect_text_entities
from services.privacy_analyzer import analyze_privacy
from services.secure_masking import generate_key, secure_mask_text, unmask_text as secure_unmask_text, WrongKeyError

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_TEXT_LENGTH = 20000


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    current_user: dict = Depends(get_current_user),
    file: Optional[UploadFile] = File(None),
    text: Optional[constr(strip_whitespace=True, min_length=1, max_length=MAX_TEXT_LENGTH)] = Form(None), # type: ignore
):
    if not file and not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either a file or raw text.")

    filename = None
    if file:
        filename = file.filename
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large.")

        suffix = os.path.splitext(filename)[1] or ".txt" # type: ignore
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(contents)
            temp_path = tmp_file.name
        try:
            raw_text = extract_text(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    else:
        raw_text = text

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document text is empty.")

    document = {
        "owner_email": current_user["email"],
        "filename": filename,
        "raw_text": raw_text,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "mode": None,
        "style": None,
        "masked_text": None,
        "privacy_report": None,
        "encrypted_mapping": None,
    }
    result = db["documents"].insert_one(document)
    return {"document_id": str(result.inserted_id)}


@router.post("/mask", response_model=MaskResponse)
async def mask_document(request: MaskRequest, current_user: dict = Depends(get_current_user)):
    try:
        document_id = ObjectId(request.document_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID.")

    document = db["documents"].find_one({"_id": document_id, "owner_email": current_user["email"]})
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if request.mode == "standard":
        if request.style not in {"placeholder", "partial", "full"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid masking style for standard mode.")

        entities = detect_text_entities(document["raw_text"])
        privacy_report = analyze_privacy(entities)
        masked_result = mask_text(document["raw_text"], entities, request.style)
        update_data = {
            "mode": request.mode,
            "style": request.style,
            "masked_text": masked_result["masked_text"],
            "privacy_report": privacy_report,
            "encrypted_mapping": None,
            "updated_at": datetime.utcnow(),
        }
        db["documents"].update_one({"_id": document["_id"]}, {"$set": update_data})
        return {
            "masked_text": update_data["masked_text"],
            "privacy_score": privacy_report["privacy_score"],
            "risk_level": privacy_report["risk_level"],
            "entity_counts": privacy_report["entity_counts"],
        }

    if request.mode == "secure":
        if request.style != "placeholder":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Secure mode only supports placeholder style.")
        key = generate_key()
        masked_text, encrypted_blob = secure_mask_text(document["raw_text"], key)
        entities = detect_text_entities(document["raw_text"])
        privacy_report = analyze_privacy(entities)
        encoded_blob = base64.b64encode(encrypted_blob).decode("utf-8")
        update_data = {
            "mode": request.mode,
            "style": "placeholder",
            "masked_text": masked_text,
            "privacy_report": privacy_report,
            "encrypted_mapping": encoded_blob,
            "updated_at": datetime.utcnow(),
        }
        db["documents"].update_one({"_id": document["_id"]}, {"$set": update_data})
        return {
            "masked_text": masked_text,
            "privacy_score": privacy_report["privacy_score"],
            "risk_level": privacy_report["risk_level"],
            "entity_counts": privacy_report["entity_counts"],
            "secure_key": key.decode("utf-8"),
        }

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mode.")


@router.post("/unmask", response_model=UnmaskResponse)
async def unmask_document(request: UnmaskRequest, current_user: dict = Depends(get_current_user)):
    document = db["documents"].find_one({"_id": ObjectId(request.document_id), "owner_email": current_user["email"]})
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if document.get("mode") != "secure" or not document.get("encrypted_mapping"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is not stored in secure mode.")

    try:
        restored = secure_unmask_text(document["masked_text"], base64.b64decode(document["encrypted_mapping"]), request.key)
    except WrongKeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"restored_text": restored}


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(current_user: dict = Depends(get_current_user)):
    docs = list(db["documents"].find({"owner_email": current_user["email"]}))
    documents_processed = len(docs)
    if documents_processed == 0:
        return {"documents_processed": 0, "average_privacy_score": 0.0, "entity_type_breakdown": {}}

    total_score = 0
    entity_type_breakdown = {}
    for doc in docs:
        privacy = doc.get("privacy_report", {})
        total_score += privacy.get("privacy_score", 0)
        for label, count in privacy.get("entity_counts", {}).items():
            entity_type_breakdown[label] = entity_type_breakdown.get(label, 0) + count

    return {
        "documents_processed": documents_processed,
        "average_privacy_score": round(total_score / documents_processed, 2),
        "entity_type_breakdown": entity_type_breakdown,
    }


@router.get("/history", response_model=HistoryResponse)
async def history(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    skip = (page - 1) * page_size
    total = db["documents"].count_documents({"owner_email": current_user["email"]})
    cursor = db["documents"].find({"owner_email": current_user["email"]}).sort("created_at", -1).skip(skip).limit(page_size)

    documents = []
    for doc in cursor:
        documents.append(
            {
                "document_id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "created_at": doc.get("created_at"),
                "mode": doc.get("mode") or "standard",
                "risk_level": doc.get("privacy_report", {}).get("risk_level", "LOW"),
            }
        )

    return {"documents": documents, "page": page, "page_size": page_size, "total": total}
