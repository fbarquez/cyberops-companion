"""
Risk Management API Endpoints.

REST API for managing risks, controls, assessments, and treatment plans.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.services.risk_service import RiskService
from src.schemas.risk import (
    RiskCreate, RiskUpdate, RiskResponse, RiskListResponse,
    RiskAssessmentCreate, RiskAssessmentResponse, RiskAcceptanceRequest,
    RiskControlCreate, RiskControlUpdate, RiskControlResponse, RiskControlListResponse,
    TreatmentActionCreate, TreatmentActionUpdate, TreatmentActionResponse,
    RiskMatrix, RiskStats, RiskCategory, RiskStatus, RiskLevel,
    RiskAppetiteCreate, RiskAppetiteResponse
)

router = APIRouter(prefix="/risks", tags=["Risk Management"])


# Risk CRUD Endpoints
@router.post("", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
async def create_risk(
    risk_data: RiskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new risk entry."""
    service = RiskService(db)
    return await service.create_risk(risk_data)


@router.get("", response_model=RiskListResponse)
async def list_risks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[RiskCategory] = None,
    status: Optional[RiskStatus] = None,
    risk_level: Optional[RiskLevel] = None,
    risk_owner: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List risks with filtering and pagination."""
    service = RiskService(db)
    filters = {}
    if category:
        filters["category"] = category
    if status:
        filters["status"] = status
    if risk_level:
        filters["risk_level"] = risk_level
    if risk_owner:
        filters["risk_owner"] = risk_owner
    if department:
        filters["department"] = department
    if search:
        filters["search"] = search

    return await service.list_risks(page=page, page_size=page_size, filters=filters)


@router.get("/statistics", response_model=RiskStats)
async def get_risk_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get risk statistics and summary metrics."""
    service = RiskService(db)
    return await service.get_statistics()


@router.get("/matrix", response_model=RiskMatrix)
async def get_risk_matrix(
    db: AsyncSession = Depends(get_db)
):
    """Get the risk matrix showing risk distribution by likelihood and impact."""
    service = RiskService(db)
    cells = await service.get_risk_matrix()
    return RiskMatrix(
        cells=cells,
        likelihood_levels=["rare", "unlikely", "possible", "likely", "almost_certain"],
        impact_levels=["negligible", "minor", "moderate", "major", "catastrophic"]
    )


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(
    risk_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific risk by ID."""
    service = RiskService(db)
    risk = await service.get_risk(risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: str,
    risk_data: RiskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing risk."""
    service = RiskService(db)
    risk = await service.update_risk(risk_id, risk_data)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(
    risk_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a risk."""
    service = RiskService(db)
    success = await service.delete_risk(risk_id)
    if not success:
        raise HTTPException(status_code=404, detail="Risk not found")
    return None


# Risk Assessment Endpoints
@router.post("/{risk_id}/assess", response_model=RiskAssessmentResponse)
async def assess_risk(
    risk_id: str,
    assessment_data: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Perform a risk assessment."""
    service = RiskService(db)
    assessment = await service.assess_risk(risk_id, assessment_data)
    if not assessment:
        raise HTTPException(status_code=404, detail="Risk not found")
    return assessment


@router.get("/{risk_id}/assessments", response_model=List[RiskAssessmentResponse])
async def get_risk_assessments(
    risk_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get assessment history for a risk."""
    service = RiskService(db)
    return await service.get_assessments(risk_id)


# Risk Acceptance
@router.post("/{risk_id}/accept", response_model=RiskResponse)
async def accept_risk(
    risk_id: str,
    acceptance_data: RiskAcceptanceRequest,
    db: AsyncSession = Depends(get_db)
):
    """Accept a risk with justification."""
    service = RiskService(db)
    risk = await service.accept_risk(
        risk_id,
        acceptance_data.acceptance_reason,
        acceptance_data.acceptance_expiry
    )
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


# Risk Closure
@router.post("/{risk_id}/close", response_model=RiskResponse)
async def close_risk(
    risk_id: str,
    closure_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Close a risk."""
    service = RiskService(db)
    risk = await service.close_risk(risk_id, closure_reason)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


# Control Endpoints
@router.post("/controls", response_model=RiskControlResponse, status_code=status.HTTP_201_CREATED)
async def create_control(
    control_data: RiskControlCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new risk control."""
    service = RiskService(db)
    return await service.create_control(control_data)


@router.get("/controls", response_model=RiskControlListResponse)
async def list_controls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all risk controls."""
    service = RiskService(db)
    return await service.list_controls(page=page, page_size=page_size)


@router.get("/controls/{control_id}", response_model=RiskControlResponse)
async def get_control(
    control_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific control by ID."""
    service = RiskService(db)
    control = await service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.put("/controls/{control_id}", response_model=RiskControlResponse)
async def update_control(
    control_id: str,
    control_data: RiskControlUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing control."""
    service = RiskService(db)
    control = await service.update_control(control_id, control_data)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.delete("/controls/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control(
    control_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a control."""
    service = RiskService(db)
    success = await service.delete_control(control_id)
    if not success:
        raise HTTPException(status_code=404, detail="Control not found")
    return None


# Link Controls to Risks
@router.post("/{risk_id}/controls/{control_id}", response_model=RiskResponse)
async def link_control_to_risk(
    risk_id: str,
    control_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Link a control to a risk."""
    service = RiskService(db)
    risk = await service.link_control_to_risk(risk_id, control_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk or control not found")
    return risk


@router.delete("/{risk_id}/controls/{control_id}", response_model=RiskResponse)
async def unlink_control_from_risk(
    risk_id: str,
    control_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Unlink a control from a risk."""
    service = RiskService(db)
    risk = await service.unlink_control_from_risk(risk_id, control_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk or control not found")
    return risk


# Treatment Action Endpoints
@router.post("/{risk_id}/treatments", response_model=TreatmentActionResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment_action(
    risk_id: str,
    action_data: TreatmentActionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a treatment action for a risk."""
    service = RiskService(db)
    action = await service.create_treatment_action(risk_id, action_data)
    if not action:
        raise HTTPException(status_code=404, detail="Risk not found")
    return action


@router.get("/{risk_id}/treatments", response_model=List[TreatmentActionResponse])
async def get_treatment_actions(
    risk_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get treatment actions for a risk."""
    service = RiskService(db)
    return await service.get_treatment_actions(risk_id)


@router.put("/treatments/{action_id}", response_model=TreatmentActionResponse)
async def update_treatment_action(
    action_id: str,
    action_data: TreatmentActionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a treatment action."""
    service = RiskService(db)
    action = await service.update_treatment_action(action_id, action_data)
    if not action:
        raise HTTPException(status_code=404, detail="Treatment action not found")
    return action


@router.delete("/treatments/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_treatment_action(
    action_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a treatment action."""
    service = RiskService(db)
    success = await service.delete_treatment_action(action_id)
    if not success:
        raise HTTPException(status_code=404, detail="Treatment action not found")
    return None


# Risk Appetite Endpoints
@router.post("/appetite", response_model=RiskAppetiteResponse, status_code=status.HTTP_201_CREATED)
async def set_risk_appetite(
    appetite_data: RiskAppetiteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set or update risk appetite for a category."""
    service = RiskService(db)
    return await service.set_risk_appetite(appetite_data)


@router.get("/appetite", response_model=List[RiskAppetiteResponse])
async def get_risk_appetite(
    db: AsyncSession = Depends(get_db)
):
    """Get all risk appetite settings."""
    service = RiskService(db)
    return await service.get_risk_appetite()


@router.get("/appetite/{category}", response_model=RiskAppetiteResponse)
async def get_risk_appetite_by_category(
    category: RiskCategory,
    db: AsyncSession = Depends(get_db)
):
    """Get risk appetite for a specific category."""
    service = RiskService(db)
    appetite = await service.get_risk_appetite_by_category(category)
    if not appetite:
        raise HTTPException(status_code=404, detail="Risk appetite not found for this category")
    return appetite
