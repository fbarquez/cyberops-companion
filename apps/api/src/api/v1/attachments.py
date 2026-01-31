"""Attachment management endpoints for file uploads."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
import io

from src.api.deps import DBSession, CurrentUser
from src.models.attachment import AttachmentEntityType, AttachmentCategory
from src.schemas.attachment import (
    AttachmentResponse,
    AttachmentListResponse,
    AttachmentUploadResponse,
    AttachmentIntegrityResponse,
    AttachmentBulkDeleteRequest,
)
from src.services.storage_service import StorageService


router = APIRouter(prefix="/attachments")


@router.post(
    "/upload/{entity_type}/{entity_id}",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    entity_type: AttachmentEntityType,
    entity_id: str,
    db: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    category: AttachmentCategory = Form(AttachmentCategory.OTHER),
    description: Optional[str] = Form(None),
):
    """
    Upload a file attachment to an entity.

    Supported entity types: incident, vulnerability, case, alert, risk, vendor, asset, evidence, report, general

    File constraints:
    - Maximum size: 50MB (configurable)
    - Allowed extensions: documents, images, archives, security/forensics files
    """
    service = StorageService(db)
    attachment = await service.upload(
        file=file,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=current_user.id,
        category=category,
        description=description,
    )
    await db.commit()

    return AttachmentUploadResponse(
        attachment=AttachmentResponse.model_validate(attachment),
        message="File uploaded successfully",
    )


@router.get(
    "/{entity_type}/{entity_id}",
    response_model=AttachmentListResponse,
)
async def list_attachments(
    entity_type: AttachmentEntityType,
    entity_id: str,
    db: DBSession,
    current_user: CurrentUser,
    category: Optional[AttachmentCategory] = None,
):
    """
    List all attachments for an entity.

    Optionally filter by category.
    """
    service = StorageService(db)
    attachments = await service.list_attachments(
        entity_type=entity_type,
        entity_id=entity_id,
        category=category,
    )

    return AttachmentListResponse(
        items=[AttachmentResponse.model_validate(a) for a in attachments],
        total=len(attachments),
    )


@router.get(
    "/download/{attachment_id}",
)
async def download_attachment(
    attachment_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Download an attachment file.

    Returns the file as a streaming response with appropriate headers.
    """
    service = StorageService(db)
    content, attachment = await service.download(attachment_id, current_user.id)
    await db.commit()  # Save download tracking

    # Create streaming response
    return StreamingResponse(
        io.BytesIO(content),
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
            "Content-Length": str(attachment.file_size),
            "X-File-Hash": attachment.file_hash,
        },
    )


@router.get(
    "/metadata/{attachment_id}",
    response_model=AttachmentResponse,
)
async def get_attachment_metadata(
    attachment_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get attachment metadata without downloading the file."""
    service = StorageService(db)
    attachment = await service.get_attachment(attachment_id)

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )

    return AttachmentResponse.model_validate(attachment)


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    attachment_id: str,
    db: DBSession,
    current_user: CurrentUser,
    permanent: bool = Query(False, description="Permanently delete file and record"),
):
    """
    Delete an attachment.

    By default, performs a soft delete. Use permanent=true for hard delete.
    """
    service = StorageService(db)
    await service.delete(attachment_id, current_user.id, permanent=permanent)
    await db.commit()


@router.post(
    "/bulk-delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bulk_delete_attachments(
    request: AttachmentBulkDeleteRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """Delete multiple attachments at once."""
    service = StorageService(db)

    for attachment_id in request.attachment_ids:
        try:
            await service.delete(attachment_id, current_user.id, permanent=request.permanent)
        except HTTPException:
            pass  # Skip attachments that don't exist

    await db.commit()


@router.post(
    "/verify/{attachment_id}",
    response_model=AttachmentIntegrityResponse,
)
async def verify_attachment_integrity(
    attachment_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Verify file integrity by comparing stored hash with actual file hash.

    This is useful for detecting file corruption or tampering.
    """
    service = StorageService(db)
    is_valid, message = await service.verify_integrity(attachment_id)

    return AttachmentIntegrityResponse(
        attachment_id=attachment_id,
        is_valid=is_valid,
        message=message,
        verified_at=datetime.utcnow(),
    )


@router.get(
    "/count/{entity_type}/{entity_id}",
)
async def get_attachment_count(
    entity_type: AttachmentEntityType,
    entity_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get the count of attachments for an entity."""
    service = StorageService(db)
    count = await service.get_entity_attachment_count(entity_type, entity_id)

    return {"entity_type": entity_type.value, "entity_id": entity_id, "count": count}
