from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, constr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class DocumentUploadResponse(BaseModel):
    document_id: str


class MaskMode(str, Enum):
    standard = "standard"
    secure = "secure"


class MaskRequest(BaseModel):
    document_id: str
    mode: MaskMode
    style: constr(strip_whitespace=True, min_length=1)
    entities: Optional[List[dict]] = None


class AnalyzeRequest(BaseModel):
    document_id: str
    processing_mode: constr(strip_whitespace=True, min_length=1)


class EntityItem(BaseModel):
    text: str
    label: str
    recommendMask: bool
    reason: str
    start: int
    end: int


class AnalyzeResponse(BaseModel):
    entities: List[EntityItem]


class MaskResponse(BaseModel):
    masked_text: str
    privacy_score: int
    risk_level: str
    entity_counts: dict
    secure_key: Optional[str] = None


class UnmaskRequest(BaseModel):
    document_id: str
    key: str = Field(..., min_length=44, max_length=44)


class UnmaskResponse(BaseModel):
    restored_text: str


class DashboardResponse(BaseModel):
    documents_processed: int
    average_privacy_score: float
    entity_type_breakdown: dict


class DocumentHistoryItem(BaseModel):
    document_id: str
    filename: Optional[str]
    created_at: datetime
    mode: MaskMode
    risk_level: str


class HistoryResponse(BaseModel):
    documents: List[DocumentHistoryItem]
    page: int
    page_size: int
    total: int
