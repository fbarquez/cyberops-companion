"""Document & Policy Management service."""
import hashlib
import math
from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from src.models.documents import (
    Document, DocumentVersion, DocumentApproval, DocumentAcknowledgment, DocumentReview,
    DocumentCategory, DocumentStatus, VersionType,
    ApprovalStatus, ApprovalType, AcknowledgmentStatus, ReviewOutcome
)
from src.schemas.documents import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse, DocumentDetailResponse,
    DocumentVersionCreate, DocumentVersionResponse, DocumentVersionListResponse, VersionComparisonResponse,
    DocumentApprovalCreate, DocumentApprovalDecision, DocumentApprovalResponse, DocumentApprovalListResponse,
    PendingApprovalItem, PendingApprovalsResponse,
    AcknowledgmentAssignment, AcknowledgmentConfirm, DocumentAcknowledgmentResponse, AcknowledgmentListResponse,
    PendingAcknowledgmentItem, PendingAcknowledgmentsResponse,
    DocumentReviewCreate, DocumentReviewResponse, DocumentReviewListResponse,
    DueForReviewItem, DueForReviewResponse,
    SubmitForReviewRequest, PublishDocumentRequest,
    DocumentDashboardStats, AcknowledgmentComplianceReport, ComplianceReportResponse,
    ApproverAssignment
)
from src.services.base_service import TenantAwareService

logger = logging.getLogger(__name__)


class DocumentService(TenantAwareService[Document]):
    """Service for Document & Policy Management operations."""

    model_class = Document

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.db = db

    # ============== Document ID Generation ==============

    async def generate_document_id(self, category: DocumentCategory) -> str:
        """Generate unique document ID based on category."""
        prefix_map = {
            DocumentCategory.POLICY: "POL",
            DocumentCategory.PROCEDURE: "PRO",
            DocumentCategory.STANDARD: "STD",
            DocumentCategory.GUIDELINE: "GDL",
            DocumentCategory.FORM: "FRM",
            DocumentCategory.RECORD: "REC",
            DocumentCategory.MANUAL: "MAN",
            DocumentCategory.INSTRUCTION: "INS",
        }
        prefix = prefix_map.get(category, "DOC")

        result = await self.db.execute(
            select(func.count(Document.id)).where(
                Document.document_id.like(f"{prefix}-%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}-{count + 1:03d}"

    # ============== Document CRUD ==============

    async def create_document(
        self,
        data: DocumentCreate,
        created_by: str,
    ) -> Document:
        """Create a new document."""
        document_id = await self.generate_document_id(data.category)

        document = Document(
            document_id=document_id,
            title=data.title,
            description=data.description,
            category=data.category,
            content=data.content,
            attachment_id=data.attachment_id,
            owner_id=data.owner_id or created_by,
            department=data.department,
            review_frequency_days=data.review_frequency_days,
            frameworks=data.frameworks or [],
            control_references=data.control_references or [],
            requires_acknowledgment=data.requires_acknowledgment or False,
            acknowledgment_due_days=data.acknowledgment_due_days or 14,
            approval_type=data.approval_type or ApprovalType.SEQUENTIAL,
            tags=data.tags or [],
            custom_metadata=data.custom_metadata or {},
            status=DocumentStatus.DRAFT,
            current_version="0.1",
            created_by=created_by,
        )

        self._set_tenant_on_create(document)
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        # Create initial version
        await self._create_version(
            document=document,
            change_summary="Initial draft",
            version_type=VersionType.MINOR,
            created_by=created_by,
        )

        logger.info(f"Created document {document_id}: {data.title}")
        return document

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID or document_id."""
        query = self._base_query().where(
            and_(
                or_(Document.id == document_id, Document.document_id == document_id),
                Document.is_deleted == False
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_document_detail(self, document_id: str) -> Optional[DocumentDetailResponse]:
        """Get document with full details including versions and approvals."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Get versions
        versions = await self.list_versions(document.id)

        # Get current approval chain
        approval_chain = await self.get_approval_chain(document.id)

        # Get recent reviews
        reviews = await self.list_reviews(document.id)

        # Build response
        response = DocumentDetailResponse.model_validate(document)
        response.versions = versions.items[:5]  # Last 5 versions
        response.current_approval_chain = approval_chain.items if approval_chain else []
        response.recent_reviews = reviews.items[:3] if reviews else []

        return response

    async def list_documents(
        self,
        page: int = 1,
        size: int = 20,
        category: Optional[DocumentCategory] = None,
        status: Optional[DocumentStatus] = None,
        framework: Optional[str] = None,
        owner_id: Optional[str] = None,
        search: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> DocumentListResponse:
        """List documents with filtering and pagination."""
        query = self._base_query().where(Document.is_deleted == False)

        # Apply filters
        if category:
            query = query.where(Document.category == category)
        if status:
            query = query.where(Document.status == status)
        if framework:
            query = query.where(Document.frameworks.contains([framework]))
        if owner_id:
            query = query.where(Document.owner_id == owner_id)
        if tag:
            query = query.where(Document.tags.contains([tag]))
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Document.title.ilike(search_filter),
                    Document.document_id.ilike(search_filter),
                    Document.description.ilike(search_filter),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(Document.updated_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        documents = result.scalars().all()

        # Enrich with acknowledgment stats
        items = []
        for doc in documents:
            doc_response = DocumentResponse.model_validate(doc)
            doc_response.acknowledgment_stats = await self._get_acknowledgment_stats(doc.id)
            doc_response.pending_approvals = await self._get_pending_approval_count(doc.id)
            items.append(doc_response)

        return DocumentListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    async def update_document(
        self,
        document_id: str,
        data: DocumentUpdate,
        updated_by: str,
    ) -> Optional[Document]:
        """Update a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Check if document can be edited
        if document.status in [DocumentStatus.PUBLISHED, DocumentStatus.ARCHIVED]:
            raise ValueError(f"Cannot edit document in {document.status.value} status")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)

        document.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Updated document {document.document_id}")
        return document

    async def delete_document(self, document_id: str) -> bool:
        """Soft delete a document."""
        document = await self.get_document(document_id)
        if not document:
            return False

        document.is_deleted = True
        document.deleted_at = datetime.utcnow()
        document.status = DocumentStatus.ARCHIVED

        await self.db.commit()
        logger.info(f"Deleted document {document.document_id}")
        return True

    # ============== Version Management ==============

    async def _create_version(
        self,
        document: Document,
        change_summary: str,
        version_type: VersionType,
        created_by: str,
        change_details: Optional[str] = None,
    ) -> DocumentVersion:
        """Create a new version snapshot."""
        # Parse current version
        parts = document.current_version.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0

        # Increment version
        if version_type == VersionType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif version_type == VersionType.MINOR:
            minor += 1
            patch = 0
        else:  # PATCH
            patch += 1

        new_version = f"{major}.{minor}" if patch == 0 else f"{major}.{minor}.{patch}"

        # Mark previous current version as not current
        await self.db.execute(
            select(DocumentVersion)
            .where(
                and_(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.is_current == True
                )
            )
        )
        result = await self.db.execute(
            select(DocumentVersion).where(
                and_(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.is_current == True
                )
            )
        )
        old_version = result.scalar_one_or_none()
        if old_version:
            old_version.is_current = False

        # Calculate content hash
        content_hash = None
        if document.content:
            content_hash = hashlib.sha256(document.content.encode()).hexdigest()

        version = DocumentVersion(
            document_id=document.id,
            version_number=new_version,
            version_type=version_type,
            content=document.content,
            attachment_id=document.attachment_id,
            content_hash=content_hash,
            change_summary=change_summary,
            change_details=change_details,
            is_current=True,
            is_published=False,
            created_by=created_by,
        )

        self._set_tenant_on_create(version)
        self.db.add(version)

        # Update document current version
        document.current_version = new_version

        await self.db.commit()
        await self.db.refresh(version)

        return version

    async def create_version(
        self,
        document_id: str,
        data: DocumentVersionCreate,
        created_by: str,
    ) -> Optional[DocumentVersion]:
        """Create a new version of a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Update document content if provided
        if data.content is not None:
            document.content = data.content
        if data.attachment_id is not None:
            document.attachment_id = data.attachment_id

        # Reset status to draft for review
        document.status = DocumentStatus.DRAFT

        version = await self._create_version(
            document=document,
            change_summary=data.change_summary,
            version_type=data.version_type or VersionType.MINOR,
            change_details=data.change_details,
            created_by=created_by,
        )

        logger.info(f"Created version {version.version_number} for document {document.document_id}")
        return version

    async def get_version(self, version_id: str) -> Optional[DocumentVersion]:
        """Get a specific version."""
        query = select(DocumentVersion).where(DocumentVersion.id == version_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_versions(self, document_id: str) -> DocumentVersionListResponse:
        """List all versions of a document."""
        document = await self.get_document(document_id)
        if not document:
            return DocumentVersionListResponse(items=[], total=0)

        query = select(DocumentVersion).where(
            DocumentVersion.document_id == document.id
        ).order_by(DocumentVersion.created_at.desc())

        result = await self.db.execute(query)
        versions = result.scalars().all()

        items = []
        for v in versions:
            vr = DocumentVersionResponse.model_validate(v)
            vr.has_content = bool(v.content)
            vr.has_attachment = bool(v.attachment_id)
            items.append(vr)

        return DocumentVersionListResponse(items=items, total=len(items))

    async def compare_versions(
        self,
        document_id: str,
        version_a_id: str,
        version_b_id: str,
    ) -> Optional[VersionComparisonResponse]:
        """Compare two versions of a document."""
        version_a = await self.get_version(version_a_id)
        version_b = await self.get_version(version_b_id)

        if not version_a or not version_b:
            return None

        # Simple diff summary
        if version_a.content == version_b.content:
            diff_summary = "No content changes"
        else:
            diff_summary = f"Content changed from version {version_a.version_number} to {version_b.version_number}"

        return VersionComparisonResponse(
            version_a=DocumentVersionResponse.model_validate(version_a),
            version_b=DocumentVersionResponse.model_validate(version_b),
            content_diff=None,  # Full diff would require a diff library
            changes_summary=diff_summary,
        )

    # ============== Workflow: Submit, Approve, Reject, Publish ==============

    async def submit_for_review(
        self,
        document_id: str,
        request: SubmitForReviewRequest,
        submitted_by: str,
    ) -> Optional[Document]:
        """Submit document for review/approval."""
        document = await self.get_document(document_id)
        if not document:
            return None

        if document.status not in [DocumentStatus.DRAFT, DocumentStatus.UNDER_REVISION]:
            raise ValueError(f"Cannot submit document in {document.status.value} status")

        # Get current version
        current_version = await self._get_current_version(document.id)
        version_id = current_version.id if current_version else None

        # Clear existing pending approvals
        await self._clear_pending_approvals(document.id)

        # Create approval chain
        for approver in request.approvers:
            approval = DocumentApproval(
                document_id=document.id,
                version_id=version_id,
                approver_id=approver.user_id,
                approval_order=approver.approval_order,
                status=ApprovalStatus.PENDING,
            )
            self._set_tenant_on_create(approval)
            self.db.add(approval)

        document.status = DocumentStatus.PENDING_REVIEW

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Document {document.document_id} submitted for review")
        return document

    async def approve_document(
        self,
        document_id: str,
        approver_id: str,
        comments: Optional[str] = None,
    ) -> Optional[Document]:
        """Approve a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Find approver's pending approval
        approval = await self._get_user_pending_approval(document.id, approver_id)
        if not approval:
            raise ValueError("No pending approval found for this user")

        # Check if it's their turn (for sequential approvals)
        if document.approval_type == ApprovalType.SEQUENTIAL:
            if not await self._is_next_approver(document.id, approver_id):
                raise ValueError("Not your turn to approve (sequential approval)")

        # Update approval
        approval.status = ApprovalStatus.APPROVED
        approval.decision_at = datetime.utcnow()
        approval.comments = comments

        # Check if all approvals are complete
        if await self._all_approvals_complete(document.id):
            document.status = DocumentStatus.APPROVED

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Document {document.document_id} approved by {approver_id}")
        return document

    async def reject_document(
        self,
        document_id: str,
        approver_id: str,
        comments: str,
    ) -> Optional[Document]:
        """Reject a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Find approver's pending approval
        approval = await self._get_user_pending_approval(document.id, approver_id)
        if not approval:
            raise ValueError("No pending approval found for this user")

        # Update approval
        approval.status = ApprovalStatus.REJECTED
        approval.decision_at = datetime.utcnow()
        approval.comments = comments

        # Document goes back to draft
        document.status = DocumentStatus.DRAFT

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Document {document.document_id} rejected by {approver_id}")
        return document

    async def request_changes(
        self,
        document_id: str,
        approver_id: str,
        comments: str,
    ) -> Optional[Document]:
        """Request changes to a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        approval = await self._get_user_pending_approval(document.id, approver_id)
        if not approval:
            raise ValueError("No pending approval found for this user")

        approval.status = ApprovalStatus.CHANGES_REQUESTED
        approval.decision_at = datetime.utcnow()
        approval.comments = comments

        document.status = DocumentStatus.UNDER_REVISION

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Changes requested for document {document.document_id}")
        return document

    async def publish_document(
        self,
        document_id: str,
        request: PublishDocumentRequest,
        published_by: str,
    ) -> Optional[Document]:
        """Publish an approved document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        if document.status != DocumentStatus.APPROVED:
            raise ValueError(f"Document must be approved before publishing (current: {document.status.value})")

        # Update document
        document.status = DocumentStatus.PUBLISHED
        document.published_at = datetime.utcnow()
        document.published_by = published_by

        # Set next review date if frequency is configured
        if document.review_frequency_days:
            document.last_review_date = datetime.utcnow().date()
            document.next_review_date = (
                datetime.utcnow() + timedelta(days=document.review_frequency_days)
            ).date()

        # Mark current version as published
        current_version = await self._get_current_version(document.id)
        if current_version:
            current_version.is_published = True
            current_version.published_at = datetime.utcnow()

        # Create acknowledgments if required
        if document.requires_acknowledgment and request.assign_acknowledgments_to:
            due_date = (
                datetime.utcnow() + timedelta(days=document.acknowledgment_due_days)
            ).date()
            await self.assign_acknowledgments(
                document_id=document.id,
                user_ids=request.assign_acknowledgments_to,
                due_date=due_date,
            )

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Document {document.document_id} published")
        return document

    async def archive_document(
        self,
        document_id: str,
    ) -> Optional[Document]:
        """Archive a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        document.status = DocumentStatus.ARCHIVED

        await self.db.commit()
        await self.db.refresh(document)

        logger.info(f"Document {document.document_id} archived")
        return document

    # ============== Approval Helpers ==============

    async def _get_current_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Get the current version of a document."""
        query = select(DocumentVersion).where(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.is_current == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _clear_pending_approvals(self, document_id: str):
        """Clear existing pending approvals for a document."""
        query = select(DocumentApproval).where(
            and_(
                DocumentApproval.document_id == document_id,
                DocumentApproval.status == ApprovalStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        approvals = result.scalars().all()
        for approval in approvals:
            await self.db.delete(approval)

    async def _get_user_pending_approval(
        self, document_id: str, user_id: str
    ) -> Optional[DocumentApproval]:
        """Get user's pending approval for a document."""
        query = select(DocumentApproval).where(
            and_(
                DocumentApproval.document_id == document_id,
                DocumentApproval.approver_id == user_id,
                DocumentApproval.status == ApprovalStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _is_next_approver(self, document_id: str, user_id: str) -> bool:
        """Check if user is the next approver in sequential workflow."""
        # Get all pending approvals ordered by approval_order
        query = select(DocumentApproval).where(
            and_(
                DocumentApproval.document_id == document_id,
                DocumentApproval.status == ApprovalStatus.PENDING
            )
        ).order_by(DocumentApproval.approval_order)

        result = await self.db.execute(query)
        approvals = result.scalars().all()

        if not approvals:
            return False

        # User must be the first pending approver
        return approvals[0].approver_id == user_id

    async def _all_approvals_complete(self, document_id: str) -> bool:
        """Check if all approvals are complete."""
        query = select(func.count(DocumentApproval.id)).where(
            and_(
                DocumentApproval.document_id == document_id,
                DocumentApproval.status == ApprovalStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        pending_count = result.scalar() or 0
        return pending_count == 0

    async def _get_pending_approval_count(self, document_id: str) -> int:
        """Get count of pending approvals."""
        query = select(func.count(DocumentApproval.id)).where(
            and_(
                DocumentApproval.document_id == document_id,
                DocumentApproval.status == ApprovalStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_approval_chain(self, document_id: str) -> Optional[DocumentApprovalListResponse]:
        """Get the approval chain for a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        query = select(DocumentApproval).where(
            DocumentApproval.document_id == document.id
        ).order_by(DocumentApproval.approval_order)

        result = await self.db.execute(query)
        approvals = result.scalars().all()

        items = [DocumentApprovalResponse.model_validate(a) for a in approvals]

        all_approved = all(a.status == ApprovalStatus.APPROVED for a in approvals) if approvals else False
        pending_count = sum(1 for a in approvals if a.status == ApprovalStatus.PENDING)

        # Find next approver
        next_approver_id = None
        if document.approval_type == ApprovalType.SEQUENTIAL:
            for a in approvals:
                if a.status == ApprovalStatus.PENDING:
                    next_approver_id = a.approver_id
                    break

        return DocumentApprovalListResponse(
            items=items,
            approval_type=document.approval_type,
            all_approved=all_approved,
            pending_count=pending_count,
            next_approver_id=next_approver_id,
        )

    async def get_my_pending_approvals(
        self, user_id: str
    ) -> PendingApprovalsResponse:
        """Get all pending approvals for a user."""
        query = (
            select(DocumentApproval)
            .join(Document, Document.id == DocumentApproval.document_id)
            .where(
                and_(
                    DocumentApproval.approver_id == user_id,
                    DocumentApproval.status == ApprovalStatus.PENDING,
                    Document.is_deleted == False
                )
            )
            .order_by(DocumentApproval.created_at.desc())
        )

        query = self._add_tenant_filter(query, Document)
        result = await self.db.execute(query)
        approvals = result.scalars().all()

        items = []
        for approval in approvals:
            document = await self.get_document(approval.document_id)
            if document:
                items.append(PendingApprovalItem(
                    document_id=document.document_id,
                    document_title=document.title,
                    document_category=document.category,
                    current_version=document.current_version,
                    approval_id=approval.id,
                    approval_order=approval.approval_order,
                    requested_at=approval.created_at,
                ))

        return PendingApprovalsResponse(items=items, total=len(items))

    # ============== Acknowledgments ==============

    async def assign_acknowledgments(
        self,
        document_id: str,
        user_ids: List[str],
        due_date: Optional[date] = None,
    ) -> List[DocumentAcknowledgment]:
        """Assign acknowledgments to users."""
        document = await self.get_document(document_id)
        if not document:
            return []

        current_version = await self._get_current_version(document.id)
        version_id = current_version.id if current_version else None

        if due_date is None:
            due_date = (datetime.utcnow() + timedelta(days=document.acknowledgment_due_days)).date()

        acknowledgments = []
        for user_id in user_ids:
            # Check if already assigned
            existing = await self._get_user_acknowledgment(document.id, user_id)
            if existing and existing.status == AcknowledgmentStatus.PENDING:
                continue

            ack = DocumentAcknowledgment(
                document_id=document.id,
                version_id=version_id,
                user_id=user_id,
                status=AcknowledgmentStatus.PENDING,
                due_date=due_date,
            )
            self._set_tenant_on_create(ack)
            self.db.add(ack)
            acknowledgments.append(ack)

        await self.db.commit()
        for ack in acknowledgments:
            await self.db.refresh(ack)

        logger.info(f"Assigned acknowledgments for document {document.document_id} to {len(acknowledgments)} users")
        return acknowledgments

    async def _get_user_acknowledgment(
        self, document_id: str, user_id: str
    ) -> Optional[DocumentAcknowledgment]:
        """Get user's acknowledgment for a document."""
        query = select(DocumentAcknowledgment).where(
            and_(
                DocumentAcknowledgment.document_id == document_id,
                DocumentAcknowledgment.user_id == user_id,
            )
        ).order_by(DocumentAcknowledgment.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().first()

    async def acknowledge_document(
        self,
        document_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[DocumentAcknowledgment]:
        """Acknowledge a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        ack = await self._get_user_acknowledgment(document.id, user_id)
        if not ack:
            raise ValueError("No acknowledgment request found for this user")

        if ack.status == AcknowledgmentStatus.ACKNOWLEDGED:
            return ack  # Already acknowledged

        ack.status = AcknowledgmentStatus.ACKNOWLEDGED
        ack.acknowledged_at = datetime.utcnow()
        ack.ip_address = ip_address
        ack.user_agent = user_agent

        await self.db.commit()
        await self.db.refresh(ack)

        logger.info(f"User {user_id} acknowledged document {document.document_id}")
        return ack

    async def decline_acknowledgment(
        self,
        document_id: str,
        user_id: str,
        reason: str,
    ) -> Optional[DocumentAcknowledgment]:
        """Decline to acknowledge a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        ack = await self._get_user_acknowledgment(document.id, user_id)
        if not ack:
            raise ValueError("No acknowledgment request found for this user")

        ack.status = AcknowledgmentStatus.DECLINED
        ack.decline_reason = reason

        await self.db.commit()
        await self.db.refresh(ack)

        logger.info(f"User {user_id} declined to acknowledge document {document.document_id}")
        return ack

    async def list_acknowledgments(
        self, document_id: str
    ) -> AcknowledgmentListResponse:
        """List all acknowledgments for a document."""
        document = await self.get_document(document_id)
        if not document:
            return AcknowledgmentListResponse(
                items=[], total=0, acknowledged=0, pending=0,
                overdue=0, declined=0, compliance_percentage=0.0
            )

        query = select(DocumentAcknowledgment).where(
            DocumentAcknowledgment.document_id == document.id
        ).order_by(DocumentAcknowledgment.created_at.desc())

        result = await self.db.execute(query)
        acknowledgments = result.scalars().all()

        today = datetime.utcnow().date()
        items = []
        acknowledged = 0
        pending = 0
        overdue = 0
        declined = 0

        for ack in acknowledgments:
            is_overdue = ack.status == AcknowledgmentStatus.PENDING and ack.due_date < today

            response = DocumentAcknowledgmentResponse.model_validate(ack)
            response.is_overdue = is_overdue
            items.append(response)

            if ack.status == AcknowledgmentStatus.ACKNOWLEDGED:
                acknowledged += 1
            elif ack.status == AcknowledgmentStatus.DECLINED:
                declined += 1
            elif is_overdue:
                overdue += 1
            else:
                pending += 1

        total = len(acknowledgments)
        compliance_rate = (acknowledged / total * 100) if total > 0 else 0.0

        return AcknowledgmentListResponse(
            items=items,
            total=total,
            acknowledged=acknowledged,
            pending=pending,
            overdue=overdue,
            declined=declined,
            compliance_percentage=round(compliance_rate, 1),
        )

    async def _get_acknowledgment_stats(self, document_id: str) -> dict:
        """Get acknowledgment statistics for a document."""
        ack_list = await self.list_acknowledgments(document_id)
        return {
            "total": ack_list.total,
            "acknowledged": ack_list.acknowledged,
            "pending": ack_list.pending,
            "overdue": ack_list.overdue,
        }

    async def get_my_pending_acknowledgments(
        self, user_id: str
    ) -> PendingAcknowledgmentsResponse:
        """Get all pending acknowledgments for a user."""
        today = datetime.utcnow().date()

        query = (
            select(DocumentAcknowledgment)
            .join(Document, Document.id == DocumentAcknowledgment.document_id)
            .where(
                and_(
                    DocumentAcknowledgment.user_id == user_id,
                    DocumentAcknowledgment.status == AcknowledgmentStatus.PENDING,
                    Document.is_deleted == False
                )
            )
            .order_by(DocumentAcknowledgment.due_date.asc())
        )

        query = self._add_tenant_filter(query, Document)
        result = await self.db.execute(query)
        acknowledgments = result.scalars().all()

        items = []
        overdue_count = 0

        for ack in acknowledgments:
            document = await self.get_document(ack.document_id)
            if document:
                is_overdue = ack.due_date < today
                if is_overdue:
                    overdue_count += 1

                items.append(PendingAcknowledgmentItem(
                    document_id=document.document_id,
                    document_title=document.title,
                    document_category=document.category,
                    current_version=document.current_version,
                    acknowledgment_id=ack.id,
                    due_date=ack.due_date,
                    is_overdue=is_overdue,
                    published_at=document.published_at,
                ))

        return PendingAcknowledgmentsResponse(
            items=items,
            total=len(items),
            overdue=overdue_count,
        )

    async def send_acknowledgment_reminder(
        self, acknowledgment_id: str
    ) -> Optional[DocumentAcknowledgment]:
        """Send a reminder for an acknowledgment."""
        query = select(DocumentAcknowledgment).where(
            DocumentAcknowledgment.id == acknowledgment_id
        )
        result = await self.db.execute(query)
        ack = result.scalar_one_or_none()

        if not ack:
            return None

        ack.reminder_sent_at = datetime.utcnow()
        ack.reminder_count += 1

        await self.db.commit()
        await self.db.refresh(ack)

        # TODO: Trigger notification to user

        return ack

    # ============== Reviews ==============

    async def record_review(
        self,
        document_id: str,
        data: DocumentReviewCreate,
        reviewer_id: str,
    ) -> Optional[DocumentReview]:
        """Record a document review."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Calculate next review date
        next_review = data.next_review_date
        if not next_review and document.review_frequency_days:
            next_review = (datetime.utcnow() + timedelta(days=document.review_frequency_days)).date()

        review = DocumentReview(
            document_id=document.id,
            review_date=datetime.utcnow().date(),
            reviewer_id=reviewer_id,
            outcome=data.outcome,
            review_notes=data.review_notes,
            action_items=data.action_items or [],
            next_review_date=next_review,
            created_by=reviewer_id,
        )

        self._set_tenant_on_create(review)
        self.db.add(review)

        # Update document review dates
        document.last_review_date = review.review_date
        document.next_review_date = next_review

        # Update status based on outcome
        if data.outcome == ReviewOutcome.RETIRE:
            document.status = DocumentStatus.ARCHIVED
        elif data.outcome in [ReviewOutcome.MINOR_UPDATE, ReviewOutcome.MAJOR_REVISION]:
            document.status = DocumentStatus.UNDER_REVISION

        await self.db.commit()
        await self.db.refresh(review)

        logger.info(f"Recorded review for document {document.document_id}")
        return review

    async def list_reviews(
        self, document_id: str
    ) -> DocumentReviewListResponse:
        """List all reviews for a document."""
        document = await self.get_document(document_id)
        if not document:
            return DocumentReviewListResponse(items=[], total=0)

        query = select(DocumentReview).where(
            DocumentReview.document_id == document.id
        ).order_by(DocumentReview.review_date.desc())

        result = await self.db.execute(query)
        reviews = result.scalars().all()

        items = [DocumentReviewResponse.model_validate(r) for r in reviews]

        return DocumentReviewListResponse(items=items, total=len(items))

    async def get_documents_due_for_review(
        self,
        days_ahead: int = 30,
    ) -> DueForReviewResponse:
        """Get documents that are due for review."""
        today = datetime.utcnow().date()
        future_date = today + timedelta(days=days_ahead)

        query = self._base_query().where(
            and_(
                Document.is_deleted == False,
                Document.status == DocumentStatus.PUBLISHED,
                Document.next_review_date.isnot(None),
                Document.next_review_date <= future_date
            )
        ).order_by(Document.next_review_date.asc())

        result = await self.db.execute(query)
        documents = result.scalars().all()

        items = []
        overdue_count = 0
        due_30_days = 0

        for doc in documents:
            is_overdue = doc.next_review_date < today
            days_until = (doc.next_review_date - today).days

            if is_overdue:
                overdue_count += 1
            elif days_until <= 30:
                due_30_days += 1

            items.append(DueForReviewItem(
                document_id=doc.document_id,
                document_title=doc.title,
                document_category=doc.category,
                current_version=doc.current_version,
                owner_id=doc.owner_id,
                next_review_date=doc.next_review_date,
                days_until_due=days_until,
                is_overdue=is_overdue,
                last_review_date=doc.last_review_date,
            ))

        return DueForReviewResponse(
            items=items,
            total=len(items),
            overdue=overdue_count,
            due_30_days=due_30_days,
        )

    # ============== Dashboard & Reports ==============

    async def get_dashboard_stats(
        self, user_id: Optional[str] = None
    ) -> DocumentDashboardStats:
        """Get document management dashboard statistics."""
        today = datetime.utcnow().date()

        # Total documents
        total_docs = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(Document.id)).where(Document.is_deleted == False)
            )
        )).scalar() or 0

        # By category
        docs_by_category = {}
        for cat in DocumentCategory:
            count = (await self.db.execute(
                self._add_tenant_filter(
                    select(func.count(Document.id)).where(
                        and_(Document.category == cat, Document.is_deleted == False)
                    )
                )
            )).scalar() or 0
            docs_by_category[cat.value] = count

        # By status
        docs_by_status = {}
        for status in DocumentStatus:
            count = (await self.db.execute(
                self._add_tenant_filter(
                    select(func.count(Document.id)).where(
                        and_(Document.status == status, Document.is_deleted == False)
                    )
                )
            )).scalar() or 0
            docs_by_status[status.value] = count

        # Documents due/overdue for review
        docs_due_review = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(Document.id)).where(
                    and_(
                        Document.next_review_date <= today + timedelta(days=30),
                        Document.next_review_date >= today,
                        Document.is_deleted == False,
                        Document.status == DocumentStatus.PUBLISHED
                    )
                )
            )
        )).scalar() or 0

        docs_overdue_review = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(Document.id)).where(
                    and_(
                        Document.next_review_date < today,
                        Document.is_deleted == False,
                        Document.status == DocumentStatus.PUBLISHED
                    )
                )
            )
        )).scalar() or 0

        # User-specific stats
        pending_my_approval = 0
        pending_my_ack = 0
        if user_id:
            my_approvals = await self.get_my_pending_approvals(user_id)
            pending_my_approval = my_approvals.total

            my_acks = await self.get_my_pending_acknowledgments(user_id)
            pending_my_ack = my_acks.total

        # Acknowledgment stats
        docs_requiring_ack = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(Document.id)).where(
                    and_(
                        Document.requires_acknowledgment == True,
                        Document.status == DocumentStatus.PUBLISHED,
                        Document.is_deleted == False
                    )
                )
            )
        )).scalar() or 0

        acks_pending = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(DocumentAcknowledgment.id)).where(
                    DocumentAcknowledgment.status == AcknowledgmentStatus.PENDING
                ),
                DocumentAcknowledgment
            )
        )).scalar() or 0

        acks_overdue = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(DocumentAcknowledgment.id)).where(
                    and_(
                        DocumentAcknowledgment.status == AcknowledgmentStatus.PENDING,
                        DocumentAcknowledgment.due_date < today
                    )
                ),
                DocumentAcknowledgment
            )
        )).scalar() or 0

        total_acks = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(DocumentAcknowledgment.id)),
                DocumentAcknowledgment
            )
        )).scalar() or 0

        acks_completed = (await self.db.execute(
            self._add_tenant_filter(
                select(func.count(DocumentAcknowledgment.id)).where(
                    DocumentAcknowledgment.status == AcknowledgmentStatus.ACKNOWLEDGED
                ),
                DocumentAcknowledgment
            )
        )).scalar() or 0

        compliance_rate = (acks_completed / total_acks * 100) if total_acks > 0 else 100.0

        return DocumentDashboardStats(
            total_documents=total_docs,
            documents_by_category=docs_by_category,
            documents_by_status=docs_by_status,
            draft_documents=docs_by_status.get(DocumentStatus.DRAFT.value, 0),
            pending_review=docs_by_status.get(DocumentStatus.PENDING_REVIEW.value, 0),
            published_documents=docs_by_status.get(DocumentStatus.PUBLISHED.value, 0),
            archived_documents=docs_by_status.get(DocumentStatus.ARCHIVED.value, 0),
            documents_due_for_review=docs_due_review,
            documents_overdue_review=docs_overdue_review,
            pending_my_approval=pending_my_approval,
            pending_my_acknowledgment=pending_my_ack,
            acknowledgment_compliance_rate=round(compliance_rate, 1),
            documents_requiring_acknowledgment=docs_requiring_ack,
            acknowledgments_pending=acks_pending,
            acknowledgments_overdue=acks_overdue,
        )

    async def get_compliance_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ComplianceReportResponse:
        """Generate acknowledgment compliance report."""
        today = datetime.utcnow().date()

        # Get all published documents requiring acknowledgment
        query = self._base_query().where(
            and_(
                Document.requires_acknowledgment == True,
                Document.status == DocumentStatus.PUBLISHED,
                Document.is_deleted == False
            )
        )

        result = await self.db.execute(query)
        documents = result.scalars().all()

        doc_reports = []
        total_acks_required = 0
        total_completed = 0
        total_overdue = 0

        for doc in documents:
            acks = await self.list_acknowledgments(doc.id)

            total_acks_required += acks.total
            total_completed += acks.acknowledged
            total_overdue += acks.overdue

            doc_reports.append(AcknowledgmentComplianceReport(
                document_id=doc.document_id,
                document_title=doc.title,
                category=doc.category,
                version=doc.current_version,
                published_at=doc.published_at,
                total_assigned=acks.total,
                acknowledged=acks.acknowledged,
                pending=acks.pending,
                overdue=acks.overdue,
                declined=acks.declined,
                compliance_rate=acks.compliance_percentage,
                user_details=acks.items,
            ))

        overall_rate = (total_completed / total_acks_required * 100) if total_acks_required > 0 else 100.0

        # Review stats
        docs_reviewed_on_time = 0
        docs_overdue = 0
        for doc in documents:
            if doc.next_review_date:
                if doc.next_review_date >= today:
                    docs_reviewed_on_time += 1
                else:
                    docs_overdue += 1

        return ComplianceReportResponse(
            generated_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            total_documents=len(documents),
            published_documents=len(documents),
            documents_reviewed_on_time=docs_reviewed_on_time,
            documents_with_overdue_review=docs_overdue,
            total_acknowledgments_required=total_acks_required,
            acknowledgments_completed=total_completed,
            acknowledgments_overdue=total_overdue,
            overall_compliance_rate=round(overall_rate, 1),
            documents=doc_reports,
        )
