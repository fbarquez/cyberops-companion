"""Attachment schemas for file uploads."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models.attachment import AttachmentEntityType, AttachmentCategory


class AttachmentCreate(BaseModel):
    """Schema for attachment upload metadata."""
    category: AttachmentCategory = AttachmentCategory.OTHER
    description: Optional[str] = Field(None, max_length=1000)


class AttachmentResponse(BaseModel):
    """Schema for attachment response."""
    id: str
    filename: str
    content_type: str
    file_size: int
    file_size_human: str
    file_hash: str
    category: AttachmentCategory
    description: Optional[str] = None
    entity_type: AttachmentEntityType
    entity_id: str
    uploaded_by: str
    uploaded_at: datetime
    download_count: int
    last_downloaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    """Schema for listing attachments."""
    items: List[AttachmentResponse]
    total: int


class AttachmentUploadResponse(BaseModel):
    """Schema for upload response."""
    attachment: AttachmentResponse
    message: str = "File uploaded successfully"


class AttachmentIntegrityResponse(BaseModel):
    """Schema for file integrity verification."""
    attachment_id: str
    is_valid: bool
    message: str
    verified_at: datetime


class AttachmentBulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    attachment_ids: List[str] = Field(..., min_length=1, max_length=100)
    permanent: bool = False
