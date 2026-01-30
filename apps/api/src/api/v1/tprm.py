"""Third-Party Risk Management API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.tprm import VendorStatus, VendorTier, AssessmentStatus, FindingStatus, ContractStatus, RiskRating
from src.schemas.tprm import (
    VendorCreate, VendorUpdate, VendorResponse, VendorListResponse,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse, AssessmentListResponse,
    FindingCreate, FindingUpdate, FindingResponse, FindingListResponse,
    ContractCreate, ContractUpdate, ContractResponse, ContractListResponse,
    QuestionnaireTemplateCreate, QuestionnaireTemplateUpdate, QuestionnaireTemplateResponse,
    TPRMDashboardStats
)
from src.services.tprm_service import TPRMService

router = APIRouter(prefix="/tprm")


# ============== Dashboard ==============

@router.get("/dashboard", response_model=TPRMDashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get TPRM dashboard statistics."""
    service = TPRMService(db)
    return await service.get_dashboard_stats()


# ============== Vendor Endpoints ==============

@router.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vendor."""
    service = TPRMService(db)
    vendor = await service.create_vendor(data, created_by=current_user.id)
    return VendorResponse.model_validate(vendor)


@router.get("/vendors", response_model=VendorListResponse)
async def list_vendors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[VendorStatus] = None,
    tier: Optional[VendorTier] = None,
    risk_rating: Optional[RiskRating] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List vendors with filtering and pagination."""
    service = TPRMService(db)
    return await service.list_vendors(
        page=page,
        size=size,
        status=status,
        tier=tier,
        risk_rating=risk_rating,
        search=search,
    )


@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a vendor by ID."""
    service = TPRMService(db)
    vendor = await service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


@router.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a vendor."""
    service = TPRMService(db)
    vendor = await service.update_vendor(vendor_id, data)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a vendor."""
    service = TPRMService(db)
    success = await service.delete_vendor(vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"message": "Vendor deleted successfully"}


@router.post("/vendors/{vendor_id}/onboard", response_model=VendorResponse)
async def onboard_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Onboard a vendor (mark as active)."""
    service = TPRMService(db)
    vendor = await service.onboard_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


@router.post("/vendors/{vendor_id}/offboard", response_model=VendorResponse)
async def offboard_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Offboard a vendor (mark as terminated)."""
    service = TPRMService(db)
    vendor = await service.offboard_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


# ============== Assessment Endpoints ==============

@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    data: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vendor assessment."""
    service = TPRMService(db)
    assessment = await service.create_assessment(data, created_by=current_user.id)
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    vendor_id: Optional[str] = None,
    status: Optional[AssessmentStatus] = None,
    assessment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List assessments with filtering and pagination."""
    service = TPRMService(db)
    return await service.list_assessments(
        page=page,
        size=size,
        vendor_id=vendor_id,
        status=status,
        assessment_type=assessment_type,
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an assessment by ID."""
    service = TPRMService(db)
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: str,
    data: AssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an assessment."""
    service = TPRMService(db)
    assessment = await service.update_assessment(assessment_id, data)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/send-questionnaire", response_model=AssessmentResponse)
async def send_questionnaire(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send questionnaire to vendor."""
    service = TPRMService(db)
    assessment = await service.send_questionnaire(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: str,
    residual_risk: RiskRating,
    review_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete an assessment."""
    service = TPRMService(db)
    assessment = await service.complete_assessment(
        assessment_id, residual_risk, review_notes
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


@router.post("/assessments/{assessment_id}/accept-risk", response_model=AssessmentResponse)
async def accept_assessment_risk(
    assessment_id: str,
    expiry_days: int = 365,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept residual risk for an assessment."""
    service = TPRMService(db)
    assessment = await service.accept_risk(
        assessment_id, accepted_by=current_user.id, expiry_days=expiry_days
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)


# ============== Finding Endpoints ==============

@router.post("/findings", response_model=FindingResponse)
async def create_finding(
    data: FindingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new assessment finding."""
    service = TPRMService(db)
    finding = await service.create_finding(data, created_by=current_user.id)
    return FindingResponse.model_validate(finding)


@router.get("/findings", response_model=FindingListResponse)
async def list_findings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    vendor_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[FindingStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List findings with filtering and pagination."""
    service = TPRMService(db)
    return await service.list_findings(
        page=page,
        size=size,
        vendor_id=vendor_id,
        assessment_id=assessment_id,
        severity=severity,
        status=status,
    )


@router.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a finding by ID."""
    service = TPRMService(db)
    finding = await service.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


@router.put("/findings/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    data: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a finding."""
    service = TPRMService(db)
    finding = await service.update_finding(finding_id, data)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


@router.post("/findings/{finding_id}/remediate", response_model=FindingResponse)
async def remediate_finding(
    finding_id: str,
    remediation_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a finding as remediated."""
    service = TPRMService(db)
    finding = await service.remediate_finding(finding_id, remediation_notes)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


@router.post("/findings/{finding_id}/accept", response_model=FindingResponse)
async def accept_finding_risk(
    finding_id: str,
    justification: str,
    expiry_days: int = 365,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept risk for a finding."""
    service = TPRMService(db)
    finding = await service.accept_finding(
        finding_id,
        accepted_by=current_user.id,
        justification=justification,
        expiry_days=expiry_days,
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


# ============== Contract Endpoints ==============

@router.post("/contracts", response_model=ContractResponse)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vendor contract."""
    service = TPRMService(db)
    contract = await service.create_contract(data, created_by=current_user.id)
    return ContractResponse.model_validate(contract)


@router.get("/contracts", response_model=ContractListResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    vendor_id: Optional[str] = None,
    status: Optional[ContractStatus] = None,
    expiring_within_days: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List contracts with filtering and pagination."""
    service = TPRMService(db)
    return await service.list_contracts(
        page=page,
        size=size,
        vendor_id=vendor_id,
        status=status,
        expiring_within_days=expiring_within_days,
    )


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a contract by ID."""
    service = TPRMService(db)
    contract = await service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse.model_validate(contract)


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a contract."""
    service = TPRMService(db)
    contract = await service.update_contract(contract_id, data)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse.model_validate(contract)


@router.post("/contracts/{contract_id}/activate", response_model=ContractResponse)
async def activate_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a contract."""
    service = TPRMService(db)
    contract = await service.activate_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse.model_validate(contract)


@router.post("/contracts/{contract_id}/terminate", response_model=ContractResponse)
async def terminate_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Terminate a contract."""
    service = TPRMService(db)
    contract = await service.terminate_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractResponse.model_validate(contract)


# ============== Questionnaire Template Endpoints ==============

@router.post("/questionnaire-templates", response_model=QuestionnaireTemplateResponse)
async def create_questionnaire_template(
    data: QuestionnaireTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new questionnaire template."""
    service = TPRMService(db)
    template = await service.create_questionnaire_template(data, created_by=current_user.id)
    return QuestionnaireTemplateResponse.model_validate(template)


@router.get("/questionnaire-templates")
async def list_questionnaire_templates(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List questionnaire templates."""
    service = TPRMService(db)
    templates = await service.list_questionnaire_templates(active_only)
    return [QuestionnaireTemplateResponse.model_validate(t) for t in templates]


@router.get("/questionnaire-templates/{template_id}", response_model=QuestionnaireTemplateResponse)
async def get_questionnaire_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a questionnaire template by ID."""
    service = TPRMService(db)
    template = await service.get_questionnaire_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return QuestionnaireTemplateResponse.model_validate(template)


@router.put("/questionnaire-templates/{template_id}", response_model=QuestionnaireTemplateResponse)
async def update_questionnaire_template(
    template_id: str,
    data: QuestionnaireTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a questionnaire template."""
    service = TPRMService(db)
    template = await service.update_questionnaire_template(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return QuestionnaireTemplateResponse.model_validate(template)
