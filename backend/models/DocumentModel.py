from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    document_id: Optional[str] = None
    student_id: str
    doc_type: str
    status: str = "submitted"
    provider: str
    object_key: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    document_id: Optional[str] = None
    doc_type: str
    status: str
    provider: str
    object_key: str
    preview_url: str
