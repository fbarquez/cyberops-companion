"""Third-Party Risk Management service."""
import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.tprm import (
    Vendor, VendorAssessment, AssessmentFinding, VendorContract, QuestionnaireTemplate,
    VendorStatus, VendorTier, AssessmentStatus, FindingStatus, ContractStatus, RiskRating
)
from src.schemas.tprm import (
    VendorCreate, VendorUpdate, VendorResponse, VendorListResponse,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse, AssessmentListResponse,
    FindingCreate, FindingUpdate, FindingResponse, FindingListResponse,
    ContractCreate, ContractUpdate, ContractResponse, ContractListResponse,
    QuestionnaireTemplateCreate, QuestionnaireTemplateUpdate, QuestionnaireTemplateResponse,
    TPRMDashboardStats
)


class TPRMService:
    """Service for Third-Party Risk Management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== Vendor Operations ==============

    async def generate_vendor_id(self) -> str:
        """Generate unique vendor ID."""
        result = await self.db.execute(
            select(func.count(Vendor.id))
        )
        count = result.scalar() or 0
        return f"VND-{count + 1:04d}"

    async def create_vendor(self, data: VendorCreate, created_by: Optional[str] = None) -> Vendor:
        """Create a new vendor."""
        vendor_id = await self.generate_vendor_id()

        vendor = Vendor(
            vendor_id=vendor_id,
            name=data.name,
            legal_name=data.legal_name,
            description=data.description,
            tier=data.tier,
            category=data.category,
            website=data.website,
            primary_contact_name=data.primary_contact_name,
            primary_contact_email=data.primary_contact_email,
            primary_contact_phone=data.primary_contact_phone,
            address=data.address,
            country=data.country,
            services_provided=data.services_provided,
            data_types_shared=data.data_types_shared,
            has_pii_access=data.has_pii_access,
            has_phi_access=data.has_phi_access,
            has_pci_access=data.has_pci_access,
            has_network_access=data.has_network_access,
            has_physical_access=data.has_physical_access,
            certifications=data.certifications,
            compliance_frameworks=data.compliance_frameworks,
            business_owner=data.business_owner,
            risk_owner=data.risk_owner,
            notes=data.notes,
            tags=data.tags,
            created_by=created_by,
        )

        self.db.add(vendor)
        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor

    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID."""
        result = await self.db.execute(
            select(Vendor).where(
                or_(Vendor.id == vendor_id, Vendor.vendor_id == vendor_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_vendors(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[VendorStatus] = None,
        tier: Optional[VendorTier] = None,
        risk_rating: Optional[RiskRating] = None,
        search: Optional[str] = None,
    ) -> VendorListResponse:
        """List vendors with filtering and pagination."""
        query = select(Vendor)

        # Apply filters
        if status:
            query = query.where(Vendor.status == status)
        if tier:
            query = query.where(Vendor.tier == tier)
        if risk_rating:
            query = query.where(Vendor.current_risk_rating == risk_rating)
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Vendor.name.ilike(search_filter),
                    Vendor.vendor_id.ilike(search_filter),
                    Vendor.services_provided.ilike(search_filter),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(Vendor.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        vendors = result.scalars().all()

        return VendorListResponse(
            items=[VendorResponse.model_validate(v) for v in vendors],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    async def update_vendor(self, vendor_id: str, data: VendorUpdate) -> Optional[Vendor]:
        """Update a vendor."""
        vendor = await self.get_vendor(vendor_id)
        if not vendor:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)

        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor

    async def delete_vendor(self, vendor_id: str) -> bool:
        """Delete a vendor."""
        vendor = await self.get_vendor(vendor_id)
        if not vendor:
            return False

        await self.db.delete(vendor)
        await self.db.commit()
        return True

    async def onboard_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Onboard a vendor (mark as active)."""
        vendor = await self.get_vendor(vendor_id)
        if not vendor:
            return None

        vendor.status = VendorStatus.ACTIVE
        vendor.onboarding_date = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor

    async def offboard_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Offboard a vendor (mark as terminated)."""
        vendor = await self.get_vendor(vendor_id)
        if not vendor:
            return None

        vendor.status = VendorStatus.TERMINATED
        vendor.offboarding_date = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor

    # ============== Assessment Operations ==============

    async def generate_assessment_id(self) -> str:
        """Generate unique assessment ID."""
        year = datetime.utcnow().year
        result = await self.db.execute(
            select(func.count(VendorAssessment.id)).where(
                VendorAssessment.assessment_id.like(f"ASM-{year}-%")
            )
        )
        count = result.scalar() or 0
        return f"ASM-{year}-{count + 1:04d}"

    async def create_assessment(
        self, data: AssessmentCreate, created_by: Optional[str] = None
    ) -> VendorAssessment:
        """Create a new vendor assessment."""
        assessment_id = await self.generate_assessment_id()

        assessment = VendorAssessment(
            assessment_id=assessment_id,
            vendor_id=data.vendor_id,
            title=data.title,
            description=data.description,
            assessment_type=data.assessment_type,
            questionnaire_template=data.questionnaire_template,
            questionnaire_due_date=data.questionnaire_due_date,
            assessor=data.assessor,
            reviewer=data.reviewer,
            created_by=created_by,
        )

        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def get_assessment(self, assessment_id: str) -> Optional[VendorAssessment]:
        """Get assessment by ID."""
        result = await self.db.execute(
            select(VendorAssessment).where(
                or_(
                    VendorAssessment.id == assessment_id,
                    VendorAssessment.assessment_id == assessment_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        page: int = 1,
        size: int = 20,
        vendor_id: Optional[str] = None,
        status: Optional[AssessmentStatus] = None,
        assessment_type: Optional[str] = None,
    ) -> AssessmentListResponse:
        """List assessments with filtering and pagination."""
        query = select(VendorAssessment)

        if vendor_id:
            query = query.where(VendorAssessment.vendor_id == vendor_id)
        if status:
            query = query.where(VendorAssessment.status == status)
        if assessment_type:
            query = query.where(VendorAssessment.assessment_type == assessment_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(VendorAssessment.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        assessments = result.scalars().all()

        return AssessmentListResponse(
            items=[AssessmentResponse.model_validate(a) for a in assessments],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    async def update_assessment(
        self, assessment_id: str, data: AssessmentUpdate
    ) -> Optional[VendorAssessment]:
        """Update an assessment."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assessment, field, value)

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def send_questionnaire(self, assessment_id: str) -> Optional[VendorAssessment]:
        """Mark questionnaire as sent."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return None

        assessment.status = AssessmentStatus.QUESTIONNAIRE_SENT
        assessment.questionnaire_sent_date = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def complete_assessment(
        self,
        assessment_id: str,
        residual_risk: RiskRating,
        review_notes: Optional[str] = None,
    ) -> Optional[VendorAssessment]:
        """Complete an assessment and update vendor risk."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return None

        assessment.status = AssessmentStatus.COMPLETED
        assessment.residual_risk = residual_risk
        assessment.review_notes = review_notes
        assessment.completed_date = datetime.utcnow()
        assessment.valid_until = datetime.utcnow() + timedelta(days=365)

        # Update vendor risk rating and assessment dates
        vendor = await self.get_vendor(assessment.vendor_id)
        if vendor:
            vendor.current_risk_rating = residual_risk
            vendor.last_assessment_date = datetime.utcnow()
            vendor.next_assessment_due = datetime.utcnow() + timedelta(days=365)
            if assessment.overall_score:
                vendor.residual_risk_score = assessment.overall_score

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def accept_risk(
        self,
        assessment_id: str,
        accepted_by: str,
        expiry_days: int = 365,
    ) -> Optional[VendorAssessment]:
        """Accept residual risk for an assessment."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            return None

        assessment.risk_accepted = True
        assessment.risk_accepted_by = accepted_by
        assessment.risk_acceptance_date = datetime.utcnow()
        assessment.risk_acceptance_expiry = datetime.utcnow() + timedelta(days=expiry_days)

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    # ============== Finding Operations ==============

    async def generate_finding_id(self) -> str:
        """Generate unique finding ID."""
        year = datetime.utcnow().year
        result = await self.db.execute(
            select(func.count(AssessmentFinding.id)).where(
                AssessmentFinding.finding_id.like(f"FND-{year}-%")
            )
        )
        count = result.scalar() or 0
        return f"FND-{year}-{count + 1:04d}"

    async def create_finding(
        self, data: FindingCreate, created_by: Optional[str] = None
    ) -> AssessmentFinding:
        """Create a new assessment finding."""
        finding_id = await self.generate_finding_id()

        # Calculate risk score
        risk_score = None
        if data.likelihood and data.impact:
            risk_score = data.likelihood * data.impact

        finding = AssessmentFinding(
            finding_id=finding_id,
            assessment_id=data.assessment_id,
            vendor_id=data.vendor_id,
            title=data.title,
            description=data.description,
            severity=data.severity,
            control_domain=data.control_domain,
            control_reference=data.control_reference,
            risk_description=data.risk_description,
            business_impact=data.business_impact,
            likelihood=data.likelihood,
            impact=data.impact,
            risk_score=risk_score,
            recommendation=data.recommendation,
            created_by=created_by,
        )

        self.db.add(finding)
        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    async def get_finding(self, finding_id: str) -> Optional[AssessmentFinding]:
        """Get finding by ID."""
        result = await self.db.execute(
            select(AssessmentFinding).where(
                or_(
                    AssessmentFinding.id == finding_id,
                    AssessmentFinding.finding_id == finding_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_findings(
        self,
        page: int = 1,
        size: int = 20,
        vendor_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[FindingStatus] = None,
    ) -> FindingListResponse:
        """List findings with filtering and pagination."""
        query = select(AssessmentFinding)

        if vendor_id:
            query = query.where(AssessmentFinding.vendor_id == vendor_id)
        if assessment_id:
            query = query.where(AssessmentFinding.assessment_id == assessment_id)
        if severity:
            query = query.where(AssessmentFinding.severity == severity)
        if status:
            query = query.where(AssessmentFinding.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(AssessmentFinding.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        findings = result.scalars().all()

        return FindingListResponse(
            items=[FindingResponse.model_validate(f) for f in findings],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    async def update_finding(
        self, finding_id: str, data: FindingUpdate
    ) -> Optional[AssessmentFinding]:
        """Update a finding."""
        finding = await self.get_finding(finding_id)
        if not finding:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Recalculate risk score if likelihood or impact changed
        likelihood = update_data.get('likelihood', finding.likelihood)
        impact = update_data.get('impact', finding.impact)
        if likelihood and impact:
            update_data['risk_score'] = likelihood * impact

        for field, value in update_data.items():
            setattr(finding, field, value)

        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    async def remediate_finding(
        self, finding_id: str, remediation_notes: Optional[str] = None
    ) -> Optional[AssessmentFinding]:
        """Mark a finding as remediated."""
        finding = await self.get_finding(finding_id)
        if not finding:
            return None

        finding.status = FindingStatus.REMEDIATED
        finding.remediation_completed_date = datetime.utcnow()
        if remediation_notes:
            finding.remediation_plan = remediation_notes

        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    async def accept_finding(
        self,
        finding_id: str,
        accepted_by: str,
        justification: str,
        expiry_days: int = 365,
    ) -> Optional[AssessmentFinding]:
        """Accept risk for a finding."""
        finding = await self.get_finding(finding_id)
        if not finding:
            return None

        finding.status = FindingStatus.ACCEPTED
        finding.accepted_by = accepted_by
        finding.acceptance_justification = justification
        finding.acceptance_expiry = datetime.utcnow() + timedelta(days=expiry_days)

        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    # ============== Contract Operations ==============

    async def generate_contract_id(self) -> str:
        """Generate unique contract ID."""
        year = datetime.utcnow().year
        result = await self.db.execute(
            select(func.count(VendorContract.id)).where(
                VendorContract.contract_id.like(f"CTR-{year}-%")
            )
        )
        count = result.scalar() or 0
        return f"CTR-{year}-{count + 1:04d}"

    async def create_contract(
        self, data: ContractCreate, created_by: Optional[str] = None
    ) -> VendorContract:
        """Create a new vendor contract."""
        contract_id = await self.generate_contract_id()

        contract = VendorContract(
            contract_id=contract_id,
            vendor_id=data.vendor_id,
            title=data.title,
            description=data.description,
            contract_type=data.contract_type,
            effective_date=data.effective_date,
            expiration_date=data.expiration_date,
            renewal_date=data.renewal_date,
            auto_renewal=data.auto_renewal,
            notice_period_days=data.notice_period_days,
            contract_value=data.contract_value,
            annual_value=data.annual_value,
            currency=data.currency,
            has_security_addendum=data.has_security_addendum,
            has_dpa=data.has_dpa,
            has_sla=data.has_sla,
            has_nda=data.has_nda,
            has_right_to_audit=data.has_right_to_audit,
            has_breach_notification=data.has_breach_notification,
            breach_notification_hours=data.breach_notification_hours,
            has_data_deletion_clause=data.has_data_deletion_clause,
            has_subprocessor_restrictions=data.has_subprocessor_restrictions,
            cyber_insurance_required=data.cyber_insurance_required,
            cyber_insurance_minimum=data.cyber_insurance_minimum,
            contract_owner=data.contract_owner,
            legal_reviewer=data.legal_reviewer,
            security_reviewer=data.security_reviewer,
            document_url=data.document_url,
            related_documents=data.related_documents,
            notes=data.notes,
            created_by=created_by,
        )

        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def get_contract(self, contract_id: str) -> Optional[VendorContract]:
        """Get contract by ID."""
        result = await self.db.execute(
            select(VendorContract).where(
                or_(
                    VendorContract.id == contract_id,
                    VendorContract.contract_id == contract_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_contracts(
        self,
        page: int = 1,
        size: int = 20,
        vendor_id: Optional[str] = None,
        status: Optional[ContractStatus] = None,
        expiring_within_days: Optional[int] = None,
    ) -> ContractListResponse:
        """List contracts with filtering and pagination."""
        query = select(VendorContract)

        if vendor_id:
            query = query.where(VendorContract.vendor_id == vendor_id)
        if status:
            query = query.where(VendorContract.status == status)
        if expiring_within_days:
            expiry_date = datetime.utcnow().date() + timedelta(days=expiring_within_days)
            query = query.where(
                and_(
                    VendorContract.expiration_date <= expiry_date,
                    VendorContract.status == ContractStatus.ACTIVE
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(VendorContract.expiration_date.asc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        contracts = result.scalars().all()

        return ContractListResponse(
            items=[ContractResponse.model_validate(c) for c in contracts],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    async def update_contract(
        self, contract_id: str, data: ContractUpdate
    ) -> Optional[VendorContract]:
        """Update a contract."""
        contract = await self.get_contract(contract_id)
        if not contract:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def activate_contract(self, contract_id: str) -> Optional[VendorContract]:
        """Activate a contract."""
        contract = await self.get_contract(contract_id)
        if not contract:
            return None

        contract.status = ContractStatus.ACTIVE

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def terminate_contract(self, contract_id: str) -> Optional[VendorContract]:
        """Terminate a contract."""
        contract = await self.get_contract(contract_id)
        if not contract:
            return None

        contract.status = ContractStatus.TERMINATED

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    # ============== Questionnaire Template Operations ==============

    async def create_questionnaire_template(
        self, data: QuestionnaireTemplateCreate, created_by: Optional[str] = None
    ) -> QuestionnaireTemplate:
        """Create a new questionnaire template."""
        # Calculate total points
        total_points = 0
        sections_data = []
        for section in data.sections:
            section_dict = section.model_dump()
            for question in section_dict['questions']:
                total_points += question.get('weight', 1)
            sections_data.append(section_dict)

        template = QuestionnaireTemplate(
            name=data.name,
            description=data.description,
            version=data.version,
            sections=sections_data,
            applicable_tiers=data.applicable_tiers,
            applicable_categories=data.applicable_categories,
            total_points=total_points,
            passing_score=data.passing_score,
            created_by=created_by,
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_questionnaire_template(self, template_id: str) -> Optional[QuestionnaireTemplate]:
        """Get questionnaire template by ID or name."""
        result = await self.db.execute(
            select(QuestionnaireTemplate).where(
                or_(
                    QuestionnaireTemplate.id == template_id,
                    QuestionnaireTemplate.name == template_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_questionnaire_templates(
        self, active_only: bool = True
    ) -> List[QuestionnaireTemplate]:
        """List all questionnaire templates."""
        query = select(QuestionnaireTemplate)
        if active_only:
            query = query.where(QuestionnaireTemplate.is_active == True)
        query = query.order_by(QuestionnaireTemplate.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_questionnaire_template(
        self, template_id: str, data: QuestionnaireTemplateUpdate
    ) -> Optional[QuestionnaireTemplate]:
        """Update a questionnaire template."""
        template = await self.get_questionnaire_template(template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Recalculate total points if sections changed
        if 'sections' in update_data:
            total_points = 0
            sections_data = []
            for section in update_data['sections']:
                section_dict = section if isinstance(section, dict) else section.model_dump()
                for question in section_dict['questions']:
                    total_points += question.get('weight', 1)
                sections_data.append(section_dict)
            update_data['sections'] = sections_data
            update_data['total_points'] = total_points

        for field, value in update_data.items():
            setattr(template, field, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    # ============== Dashboard Statistics ==============

    async def get_dashboard_stats(self) -> TPRMDashboardStats:
        """Get TPRM dashboard statistics."""
        now = datetime.utcnow()
        today = now.date()

        # Vendor statistics
        total_vendors = (await self.db.execute(
            select(func.count(Vendor.id))
        )).scalar() or 0

        # Vendors by status
        status_counts = {}
        for status in VendorStatus:
            count = (await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.status == status)
            )).scalar() or 0
            status_counts[status.value] = count

        # Vendors by tier
        tier_counts = {}
        for tier in VendorTier:
            count = (await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.tier == tier)
            )).scalar() or 0
            tier_counts[tier.value] = count

        # Vendors by risk rating
        risk_counts = {}
        for rating in RiskRating:
            count = (await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.current_risk_rating == rating)
            )).scalar() or 0
            risk_counts[rating.value] = count

        # High risk vendors (critical or high)
        high_risk_vendors = (await self.db.execute(
            select(func.count(Vendor.id)).where(
                Vendor.current_risk_rating.in_([RiskRating.CRITICAL, RiskRating.HIGH])
            )
        )).scalar() or 0

        # Vendors requiring assessment (next_assessment_due passed)
        vendors_requiring_assessment = (await self.db.execute(
            select(func.count(Vendor.id)).where(
                and_(
                    Vendor.next_assessment_due <= now,
                    Vendor.status == VendorStatus.ACTIVE
                )
            )
        )).scalar() or 0

        # Assessment statistics
        total_assessments = (await self.db.execute(
            select(func.count(VendorAssessment.id))
        )).scalar() or 0

        assessments_pending = (await self.db.execute(
            select(func.count(VendorAssessment.id)).where(
                VendorAssessment.status.in_([
                    AssessmentStatus.DRAFT,
                    AssessmentStatus.QUESTIONNAIRE_SENT,
                    AssessmentStatus.UNDER_REVIEW
                ])
            )
        )).scalar() or 0

        assessments_overdue = (await self.db.execute(
            select(func.count(VendorAssessment.id)).where(
                and_(
                    VendorAssessment.questionnaire_due_date < now,
                    VendorAssessment.status.in_([
                        AssessmentStatus.QUESTIONNAIRE_SENT,
                        AssessmentStatus.DRAFT
                    ])
                )
            )
        )).scalar() or 0

        # Assessments completed this month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        assessments_completed_this_month = (await self.db.execute(
            select(func.count(VendorAssessment.id)).where(
                and_(
                    VendorAssessment.completed_date >= month_start,
                    VendorAssessment.status == AssessmentStatus.COMPLETED
                )
            )
        )).scalar() or 0

        # Finding statistics
        total_findings = (await self.db.execute(
            select(func.count(AssessmentFinding.id))
        )).scalar() or 0

        findings_by_severity = {}
        for severity in ["critical", "high", "medium", "low", "informational"]:
            count = (await self.db.execute(
                select(func.count(AssessmentFinding.id)).where(
                    AssessmentFinding.severity == severity
                )
            )).scalar() or 0
            findings_by_severity[severity] = count

        findings_open = (await self.db.execute(
            select(func.count(AssessmentFinding.id)).where(
                AssessmentFinding.status.in_([FindingStatus.OPEN, FindingStatus.IN_PROGRESS])
            )
        )).scalar() or 0

        findings_overdue = (await self.db.execute(
            select(func.count(AssessmentFinding.id)).where(
                and_(
                    AssessmentFinding.remediation_due_date < now,
                    AssessmentFinding.status.in_([FindingStatus.OPEN, FindingStatus.IN_PROGRESS])
                )
            )
        )).scalar() or 0

        # Contract expiration
        contracts_expiring_30 = (await self.db.execute(
            select(func.count(VendorContract.id)).where(
                and_(
                    VendorContract.expiration_date <= today + timedelta(days=30),
                    VendorContract.expiration_date >= today,
                    VendorContract.status == ContractStatus.ACTIVE
                )
            )
        )).scalar() or 0

        contracts_expiring_90 = (await self.db.execute(
            select(func.count(VendorContract.id)).where(
                and_(
                    VendorContract.expiration_date <= today + timedelta(days=90),
                    VendorContract.expiration_date >= today,
                    VendorContract.status == ContractStatus.ACTIVE
                )
            )
        )).scalar() or 0

        return TPRMDashboardStats(
            total_vendors=total_vendors,
            vendors_by_status=status_counts,
            vendors_by_tier=tier_counts,
            vendors_by_risk_rating=risk_counts,
            total_assessments=total_assessments,
            assessments_pending=assessments_pending,
            assessments_overdue=assessments_overdue,
            assessments_completed_this_month=assessments_completed_this_month,
            total_findings=total_findings,
            findings_by_severity=findings_by_severity,
            findings_open=findings_open,
            findings_overdue=findings_overdue,
            contracts_expiring_30_days=contracts_expiring_30,
            contracts_expiring_90_days=contracts_expiring_90,
            high_risk_vendors=high_risk_vendors,
            vendors_requiring_assessment=vendors_requiring_assessment,
        )
