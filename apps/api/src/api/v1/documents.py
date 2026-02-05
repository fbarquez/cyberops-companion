"""Document & Policy Management API endpoints."""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.documents import DocumentCategory, DocumentStatus, ApprovalStatus
from src.schemas.documents import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse, DocumentDetailResponse,
    DocumentVersionCreate, DocumentVersionResponse, DocumentVersionListResponse, VersionComparisonResponse,
    DocumentApprovalCreate, DocumentApprovalDecision, DocumentApprovalResponse, DocumentApprovalListResponse,
    PendingApprovalsResponse,
    AcknowledgmentAssignment, DocumentAcknowledgmentResponse, AcknowledgmentListResponse,
    PendingAcknowledgmentsResponse,
    DocumentReviewCreate, DocumentReviewResponse, DocumentReviewListResponse,
    DueForReviewResponse,
    SubmitForReviewRequest, RejectDocumentRequest, PublishDocumentRequest,
    DocumentDashboardStats, ComplianceReportResponse,
)
from src.services.document_service import DocumentService

router = APIRouter(prefix="/documents")


# ============== Dashboard ==============

@router.get("/dashboard", response_model=DocumentDashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document management dashboard statistics."""
    service = DocumentService(db)
    return await service.get_dashboard_stats(user_id=current_user.id)


@router.get("/stats", response_model=DocumentDashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias for dashboard stats."""
    service = DocumentService(db)
    return await service.get_dashboard_stats(user_id=current_user.id)


# ============== Document CRUD ==============

@router.post("", response_model=DocumentResponse)
async def create_document(
    data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new document."""
    service = DocumentService(db)
    document = await service.create_document(data, created_by=current_user.id)
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[DocumentCategory] = None,
    status: Optional[DocumentStatus] = None,
    framework: Optional[str] = None,
    owner_id: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents with filtering and pagination."""
    service = DocumentService(db)
    return await service.list_documents(
        page=page,
        size=size,
        category=category,
        status=status,
        framework=framework,
        owner_id=owner_id,
        search=search,
        tag=tag,
    )


@router.get("/due-for-review", response_model=DueForReviewResponse)
async def get_documents_due_for_review(
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get documents that are due for review."""
    service = DocumentService(db)
    return await service.get_documents_due_for_review(days_ahead=days_ahead)


@router.get("/compliance-report", response_model=ComplianceReportResponse)
async def get_compliance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get acknowledgment compliance report."""
    service = DocumentService(db)
    return await service.get_compliance_report(
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a document by ID with full details."""
    service = DocumentService(db)
    document = await service.get_document_detail(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a document."""
    service = DocumentService(db)
    try:
        document = await service.update_document(
            document_id, data, updated_by=current_user.id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document (soft delete)."""
    service = DocumentService(db)
    success = await service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}


# ============== Workflow Endpoints ==============

@router.post("/{document_id}/submit-review", response_model=DocumentResponse)
async def submit_for_review(
    document_id: str,
    request: SubmitForReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a document for review/approval."""
    service = DocumentService(db)
    try:
        document = await service.submit_for_review(
            document_id, request, submitted_by=current_user.id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/approve", response_model=DocumentResponse)
async def approve_document(
    document_id: str,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a document."""
    service = DocumentService(db)
    try:
        document = await service.approve_document(
            document_id,
            approver_id=current_user.id,
            comments=comments,
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/reject", response_model=DocumentResponse)
async def reject_document(
    document_id: str,
    request: RejectDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a document with comments."""
    service = DocumentService(db)
    try:
        document = await service.reject_document(
            document_id,
            approver_id=current_user.id,
            comments=request.comments,
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/request-changes", response_model=DocumentResponse)
async def request_changes(
    document_id: str,
    request: RejectDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request changes to a document."""
    service = DocumentService(db)
    try:
        document = await service.request_changes(
            document_id,
            approver_id=current_user.id,
            comments=request.comments,
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/publish", response_model=DocumentResponse)
async def publish_document(
    document_id: str,
    request: PublishDocumentRequest = PublishDocumentRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publish an approved document."""
    service = DocumentService(db)
    try:
        document = await service.publish_document(
            document_id, request, published_by=current_user.id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/archive", response_model=DocumentResponse)
async def archive_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive a document."""
    service = DocumentService(db)
    document = await service.archive_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


# ============== Version Endpoints ==============

@router.get("/{document_id}/versions", response_model=DocumentVersionListResponse)
async def list_versions(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all versions of a document."""
    service = DocumentService(db)
    return await service.list_versions(document_id)


@router.post("/{document_id}/versions", response_model=DocumentVersionResponse)
async def create_version(
    document_id: str,
    data: DocumentVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new version of a document."""
    service = DocumentService(db)
    version = await service.create_version(
        document_id, data, created_by=current_user.id
    )
    if not version:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentVersionResponse.model_validate(version)


@router.get("/{document_id}/versions/{version_id}", response_model=DocumentVersionResponse)
async def get_version(
    document_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific version of a document."""
    service = DocumentService(db)
    version = await service.get_version(version_id)
    if not version or version.document_id != document_id:
        raise HTTPException(status_code=404, detail="Version not found")

    response = DocumentVersionResponse.model_validate(version)
    response.has_content = bool(version.content)
    response.has_attachment = bool(version.attachment_id)
    return response


@router.get("/{document_id}/versions/{version_a}/compare/{version_b}", response_model=VersionComparisonResponse)
async def compare_versions(
    document_id: str,
    version_a: str,
    version_b: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare two versions of a document."""
    service = DocumentService(db)
    comparison = await service.compare_versions(document_id, version_a, version_b)
    if not comparison:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    return comparison


# ============== Approval Endpoints ==============

@router.get("/{document_id}/approvals", response_model=DocumentApprovalListResponse)
async def get_approval_chain(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the approval chain for a document."""
    service = DocumentService(db)
    chain = await service.get_approval_chain(document_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Document not found")
    return chain


@router.get("/approvals/pending", response_model=PendingApprovalsResponse)
async def get_my_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's pending approvals."""
    service = DocumentService(db)
    return await service.get_my_pending_approvals(current_user.id)


# ============== Acknowledgment Endpoints ==============

@router.get("/{document_id}/acknowledgments", response_model=AcknowledgmentListResponse)
async def list_acknowledgments(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all acknowledgments for a document."""
    service = DocumentService(db)
    return await service.list_acknowledgments(document_id)


@router.post("/{document_id}/acknowledgments", response_model=List[DocumentAcknowledgmentResponse])
async def assign_acknowledgments(
    document_id: str,
    data: AcknowledgmentAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign users to acknowledge a document."""
    service = DocumentService(db)
    acknowledgments = await service.assign_acknowledgments(
        document_id,
        user_ids=data.user_ids,
        due_date=data.due_date,
    )
    if not acknowledgments:
        raise HTTPException(status_code=404, detail="Document not found or already assigned")
    return [DocumentAcknowledgmentResponse.model_validate(a) for a in acknowledgments]


@router.post("/{document_id}/acknowledge", response_model=DocumentAcknowledgmentResponse)
async def acknowledge_document(
    document_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge a document (current user)."""
    service = DocumentService(db)
    try:
        # Get IP and user agent for audit
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

        ack = await service.acknowledge_document(
            document_id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if not ack:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentAcknowledgmentResponse.model_validate(ack)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/decline", response_model=DocumentAcknowledgmentResponse)
async def decline_acknowledgment(
    document_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Decline to acknowledge a document."""
    service = DocumentService(db)
    try:
        ack = await service.decline_acknowledgment(
            document_id,
            user_id=current_user.id,
            reason=reason,
        )
        if not ack:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentAcknowledgmentResponse.model_validate(ack)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/acknowledgments/pending", response_model=PendingAcknowledgmentsResponse)
async def get_my_pending_acknowledgments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's pending acknowledgments."""
    service = DocumentService(db)
    return await service.get_my_pending_acknowledgments(current_user.id)


@router.post("/acknowledgments/{acknowledgment_id}/remind", response_model=DocumentAcknowledgmentResponse)
async def send_acknowledgment_reminder(
    acknowledgment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a reminder for an acknowledgment."""
    service = DocumentService(db)
    ack = await service.send_acknowledgment_reminder(acknowledgment_id)
    if not ack:
        raise HTTPException(status_code=404, detail="Acknowledgment not found")
    return DocumentAcknowledgmentResponse.model_validate(ack)


# ============== Review Endpoints ==============

@router.get("/{document_id}/reviews", response_model=DocumentReviewListResponse)
async def list_reviews(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reviews for a document."""
    service = DocumentService(db)
    return await service.list_reviews(document_id)


@router.post("/{document_id}/reviews", response_model=DocumentReviewResponse)
async def record_review(
    document_id: str,
    data: DocumentReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a document review."""
    service = DocumentService(db)
    review = await service.record_review(
        document_id, data, reviewer_id=current_user.id
    )
    if not review:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentReviewResponse.model_validate(review)
