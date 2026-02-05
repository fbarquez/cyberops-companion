"""Document & Policy Management schemas."""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from src.models.documents import (
    DocumentCategory, DocumentStatus, VersionType,
    ApprovalStatus, ApprovalType, AcknowledgmentStatus, ReviewOutcome
)


# ============== Document Schemas ==============

class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: DocumentCategory
    content: Optional[str] = None
    department: Optional[str] = None
    review_frequency_days: Optional[int] = Field(None, ge=1, le=730)  # Max 2 years
    frameworks: Optional[List[str]] = []
    control_references: Optional[List[str]] = []
    requires_acknowledgment: Optional[bool] = False
    acknowledgment_due_days: Optional[int] = Field(14, ge=1, le=90)
    approval_type: Optional[ApprovalType] = ApprovalType.SEQUENTIAL
    tags: Optional[List[str]] = []
    custom_metadata: Optional[dict] = {}


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    owner_id: Optional[str] = None  # Will default to current user if not provided
    attachment_id: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[DocumentCategory] = None
    content: Optional[str] = None
    department: Optional[str] = None
    owner_id: Optional[str] = None
    attachment_id: Optional[str] = None
    review_frequency_days: Optional[int] = Field(None, ge=1, le=730)
    frameworks: Optional[List[str]] = None
    control_references: Optional[List[str]] = None
    requires_acknowledgment: Optional[bool] = None
    acknowledgment_due_days: Optional[int] = Field(None, ge=1, le=90)
    approval_type: Optional[ApprovalType] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[dict] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: str
    document_id: str
    status: DocumentStatus
    current_version: str
    owner_id: str
    attachment_id: Optional[str] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Computed fields
    owner_name: Optional[str] = None
    acknowledgment_stats: Optional[dict] = None  # {total, acknowledged, pending, overdue}
    pending_approvals: Optional[int] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    items: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document response including related data."""
    versions: Optional[List["DocumentVersionResponse"]] = []
    current_approval_chain: Optional[List["DocumentApprovalResponse"]] = []
    recent_reviews: Optional[List["DocumentReviewResponse"]] = []


# ============== Document Version Schemas ==============

class DocumentVersionCreate(BaseModel):
    """Schema for creating a new document version."""
    change_summary: str = Field(..., min_length=1, max_length=500)
    change_details: Optional[str] = None
    version_type: Optional[VersionType] = VersionType.MINOR
    content: Optional[str] = None
    attachment_id: Optional[str] = None


class DocumentVersionResponse(BaseModel):
    """Schema for document version response."""
    id: str
    document_id: str
    version_number: str
    version_type: VersionType
    change_summary: str
    change_details: Optional[str] = None
    content_hash: Optional[str] = None
    is_current: bool
    is_published: bool
    created_at: datetime
    created_by: Optional[str] = None
    published_at: Optional[datetime] = None

    # Content available separately if needed
    has_content: bool = False
    has_attachment: bool = False

    class Config:
        from_attributes = True


class DocumentVersionListResponse(BaseModel):
    """Schema for version list."""
    items: List[DocumentVersionResponse]
    total: int


class VersionComparisonResponse(BaseModel):
    """Schema for version comparison."""
    version_a: DocumentVersionResponse
    version_b: DocumentVersionResponse
    content_diff: Optional[str] = None  # Unified diff format
    changes_summary: str


# ============== Document Approval Schemas ==============

class ApproverAssignment(BaseModel):
    """Schema for assigning an approver."""
    user_id: str
    approval_order: Optional[int] = 1


class DocumentApprovalCreate(BaseModel):
    """Schema for setting up approval chain."""
    approvers: List[ApproverAssignment]
    version_id: Optional[str] = None


class DocumentApprovalDecision(BaseModel):
    """Schema for making an approval decision."""
    decision: ApprovalStatus = Field(..., description="approved, rejected, or changes_requested")
    comments: Optional[str] = None


class DocumentApprovalResponse(BaseModel):
    """Schema for approval response."""
    id: str
    document_id: str
    version_id: Optional[str] = None
    approver_id: str
    approver_name: Optional[str] = None
    approval_order: int
    status: ApprovalStatus
    decision_at: Optional[datetime] = None
    comments: Optional[str] = None
    reminder_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentApprovalListResponse(BaseModel):
    """Schema for approval chain list."""
    items: List[DocumentApprovalResponse]
    approval_type: ApprovalType
    all_approved: bool
    pending_count: int
    next_approver_id: Optional[str] = None


class PendingApprovalItem(BaseModel):
    """Schema for pending approval item."""
    document_id: str
    document_title: str
    document_category: DocumentCategory
    current_version: str
    approval_id: str
    approval_order: int
    requested_at: datetime
    owner_name: Optional[str] = None


class PendingApprovalsResponse(BaseModel):
    """Schema for user's pending approvals."""
    items: List[PendingApprovalItem]
    total: int


# ============== Document Acknowledgment Schemas ==============

class AcknowledgmentAssignment(BaseModel):
    """Schema for assigning acknowledgments."""
    user_ids: List[str]
    due_date: Optional[date] = None  # Defaults to acknowledgment_due_days from document


class AcknowledgmentConfirm(BaseModel):
    """Schema for confirming acknowledgment."""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AcknowledgmentDecline(BaseModel):
    """Schema for declining acknowledgment."""
    reason: str = Field(..., min_length=1)


class DocumentAcknowledgmentResponse(BaseModel):
    """Schema for acknowledgment response."""
    id: str
    document_id: str
    version_id: Optional[str] = None
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    status: AcknowledgmentStatus
    due_date: date
    acknowledged_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    reminder_count: int
    is_overdue: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AcknowledgmentListResponse(BaseModel):
    """Schema for acknowledgment list."""
    items: List[DocumentAcknowledgmentResponse]
    total: int
    acknowledged: int
    pending: int
    overdue: int
    declined: int
    compliance_percentage: float


class PendingAcknowledgmentItem(BaseModel):
    """Schema for pending acknowledgment item."""
    document_id: str
    document_title: str
    document_category: DocumentCategory
    current_version: str
    acknowledgment_id: str
    due_date: date
    is_overdue: bool
    published_at: Optional[datetime] = None


class PendingAcknowledgmentsResponse(BaseModel):
    """Schema for user's pending acknowledgments."""
    items: List[PendingAcknowledgmentItem]
    total: int
    overdue: int


# ============== Document Review Schemas ==============

class DocumentReviewCreate(BaseModel):
    """Schema for recording a document review."""
    outcome: ReviewOutcome
    review_notes: Optional[str] = None
    action_items: Optional[List[dict]] = []  # [{"title": "...", "assigned_to": "...", "due_date": "..."}]
    next_review_date: Optional[date] = None  # Defaults to review_frequency_days from document


class DocumentReviewResponse(BaseModel):
    """Schema for review response."""
    id: str
    document_id: str
    review_date: date
    reviewer_id: str
    reviewer_name: Optional[str] = None
    outcome: ReviewOutcome
    review_notes: Optional[str] = None
    action_items: Optional[List[dict]] = []
    next_review_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentReviewListResponse(BaseModel):
    """Schema for review history list."""
    items: List[DocumentReviewResponse]
    total: int


class DueForReviewItem(BaseModel):
    """Schema for documents due for review."""
    document_id: str
    document_title: str
    document_category: DocumentCategory
    current_version: str
    owner_id: str
    owner_name: Optional[str] = None
    next_review_date: date
    days_until_due: int
    is_overdue: bool
    last_review_date: Optional[date] = None


class DueForReviewResponse(BaseModel):
    """Schema for documents due for review list."""
    items: List[DueForReviewItem]
    total: int
    overdue: int
    due_30_days: int


# ============== Workflow Schemas ==============

class SubmitForReviewRequest(BaseModel):
    """Schema for submitting document for review."""
    approvers: List[ApproverAssignment]
    comments: Optional[str] = None


class RejectDocumentRequest(BaseModel):
    """Schema for rejecting a document."""
    comments: str = Field(..., min_length=1)


class PublishDocumentRequest(BaseModel):
    """Schema for publishing a document."""
    assign_acknowledgments_to: Optional[List[str]] = None  # User IDs or "all"
    notify_subscribers: Optional[bool] = True


# ============== Dashboard & Reports ==============

class DocumentDashboardStats(BaseModel):
    """Dashboard statistics for Document Management."""
    total_documents: int
    documents_by_category: dict
    documents_by_status: dict

    draft_documents: int
    pending_review: int
    published_documents: int
    archived_documents: int

    documents_due_for_review: int
    documents_overdue_review: int

    pending_my_approval: int
    pending_my_acknowledgment: int

    acknowledgment_compliance_rate: float
    documents_requiring_acknowledgment: int
    acknowledgments_pending: int
    acknowledgments_overdue: int


class AcknowledgmentComplianceReport(BaseModel):
    """Acknowledgment compliance report."""
    document_id: str
    document_title: str
    category: DocumentCategory
    version: str
    published_at: Optional[datetime] = None

    total_assigned: int
    acknowledged: int
    pending: int
    overdue: int
    declined: int
    compliance_rate: float

    user_details: List[DocumentAcknowledgmentResponse]


class ComplianceReportResponse(BaseModel):
    """Schema for compliance report."""
    generated_at: datetime
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    total_documents: int
    published_documents: int
    documents_reviewed_on_time: int
    documents_with_overdue_review: int

    total_acknowledgments_required: int
    acknowledgments_completed: int
    acknowledgments_overdue: int
    overall_compliance_rate: float

    documents: List[AcknowledgmentComplianceReport]


# Forward reference updates
DocumentDetailResponse.model_rebuild()
