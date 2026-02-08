"""
Evidence Bridge API Endpoints

API endpoints for the ISMS ↔ SOC evidence bridge.
Enables automatic linking of security operations to compliance controls.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_current_user, get_db
from src.models.user import User
from src.models.evidence_bridge import (
    ActivityType,
    ControlFramework,
)
from src.schemas.evidence_bridge import (
    EvidenceLinkCreate,
    EvidenceLinkResponse,
    EvidenceListResponse,
    ControlEffectivenessResponse,
    FrameworkEffectivenessResponse,
    EvidenceBridgeDashboard,
    LinkingRuleCreate,
    LinkingRuleResponse,
    ControlAuditView,
)
from src.services.evidence_bridge_service import EvidenceBridgeService

router = APIRouter(prefix="/evidence-bridge", tags=["Evidence Bridge"])


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=EvidenceBridgeDashboard)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get the evidence bridge dashboard.

    Shows:
    - Overall evidence statistics
    - Framework effectiveness summaries
    - Top controls by evidence
    - Controls needing attention
    - Recent evidence links
    """
    service = EvidenceBridgeService(db)
    return await service.get_dashboard(current_user.tenant_id)


# =============================================================================
# FRAMEWORK EFFECTIVENESS
# =============================================================================

@router.get("/frameworks", response_model=List[dict])
async def list_frameworks(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all supported frameworks with basic stats."""
    service = EvidenceBridgeService(db)

    frameworks = []
    for fw in [ControlFramework.ISO27001, ControlFramework.DORA, ControlFramework.NIS2]:
        eff = await service.get_framework_effectiveness(current_user.tenant_id, fw)
        frameworks.append({
            "framework": fw.value,
            "name": eff.framework_name,
            "overall_score": eff.overall_score,
            "overall_level": eff.overall_level.value,
            "controls_assessed": eff.controls_assessed,
            "controls_total": eff.controls_total,
            "controls_meeting_baseline": eff.controls_meeting_baseline,
        })

    return frameworks


@router.get("/frameworks/{framework}", response_model=FrameworkEffectivenessResponse)
async def get_framework_effectiveness(
    framework: ControlFramework,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get effectiveness summary for all controls in a framework.

    Returns:
    - Overall framework score and level
    - Per-control effectiveness summaries
    - Top gaps needing attention
    """
    service = EvidenceBridgeService(db)
    return await service.get_framework_effectiveness(current_user.tenant_id, framework)


@router.post("/frameworks/{framework}/recalculate")
async def recalculate_framework(
    framework: ControlFramework,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Recalculate effectiveness for all controls in a framework."""
    service = EvidenceBridgeService(db)
    result = await service.recalculate_framework_effectiveness(
        current_user.tenant_id, framework
    )
    return result


# =============================================================================
# CONTROL EFFECTIVENESS
# =============================================================================

@router.get(
    "/frameworks/{framework}/controls/{control_id}/effectiveness",
    response_model=ControlEffectivenessResponse,
)
async def get_control_effectiveness(
    framework: ControlFramework,
    control_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get effectiveness for a specific control.

    The effectiveness score is calculated from:
    - Number and strength of linked evidence
    - Recency of evidence
    - Operational metrics from linked activities
    """
    service = EvidenceBridgeService(db)
    result = await service.get_control_effectiveness(
        current_user.tenant_id, framework, control_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found in framework {framework.value}",
        )
    return result


@router.post("/frameworks/{framework}/controls/{control_id}/recalculate")
async def recalculate_control(
    framework: ControlFramework,
    control_id: str,
    period_days: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Recalculate effectiveness for a specific control."""
    service = EvidenceBridgeService(db)
    result = await service.recalculate_control_effectiveness(
        current_user.tenant_id, framework, control_id, period_days
    )
    return {
        "control_id": control_id,
        "effectiveness_score": result.effectiveness_score,
        "effectiveness_level": result.effectiveness_level.value,
        "evidence_count": result.total_evidence_count,
        "calculated_at": result.calculated_at.isoformat(),
    }


# =============================================================================
# CONTROL EVIDENCE
# =============================================================================

@router.get(
    "/frameworks/{framework}/controls/{control_id}/evidence",
    response_model=EvidenceListResponse,
)
async def get_control_evidence(
    framework: ControlFramework,
    control_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get all evidence linked to a control.

    This is the auditor view - shows all activities that demonstrate
    the control is operating effectively.
    """
    service = EvidenceBridgeService(db)
    return await service.get_control_evidence(
        current_user.tenant_id, framework, control_id, limit, offset
    )


@router.post(
    "/frameworks/{framework}/controls/{control_id}/link",
    response_model=EvidenceLinkResponse,
)
async def create_manual_link(
    framework: ControlFramework,
    control_id: str,
    data: EvidenceLinkCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Manually link an activity to a control.

    Use this when the automatic linking didn't capture a relevant activity,
    or when you want to link activities with custom evidence strength.
    """
    if data.control_framework != framework or data.control_id != control_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Control framework/ID in path must match request body",
        )

    service = EvidenceBridgeService(db)
    link = await service.create_manual_link(
        current_user.tenant_id,
        current_user.id,
        data,
    )
    return EvidenceLinkResponse(
        id=link.id,
        control_framework=link.control_framework,
        control_id=link.control_id,
        control_name=link.control_name,
        activity_type=link.activity_type,
        activity_id=link.activity_id,
        activity_title=link.activity_title,
        activity_date=link.activity_date,
        link_type=link.link_type,
        evidence_strength=link.evidence_strength,
        notes=link.notes,
        linked_at=link.linked_at,
        linked_by=link.linked_by,
    )


# =============================================================================
# ACTIVITY LINKING
# =============================================================================

@router.post("/activities/link")
async def link_activity(
    activity_type: ActivityType,
    activity_id: str,
    activity_title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Trigger automatic linking for an activity.

    This is called when an incident, alert, scan, etc. is created or updated.
    The system will automatically link it to all relevant controls.
    """
    service = EvidenceBridgeService(db)
    links = await service.link_activity_to_controls(
        current_user.tenant_id,
        activity_type,
        activity_id,
        activity_title,
    )
    return {
        "activity_type": activity_type.value,
        "activity_id": activity_id,
        "controls_linked": len(links),
        "links": [
            {
                "framework": l.control_framework.value,
                "control_id": l.control_id,
                "strength": l.evidence_strength.value,
            }
            for l in links
        ],
    }


@router.get("/activities/{activity_type}/{activity_id}/links")
async def get_activity_links(
    activity_type: ActivityType,
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get all controls an activity is linked to."""
    from sqlalchemy import select, and_
    from src.models.evidence_bridge import ControlEvidenceLink

    query = select(ControlEvidenceLink).where(
        and_(
            ControlEvidenceLink.tenant_id == current_user.tenant_id,
            ControlEvidenceLink.activity_type == activity_type,
            ControlEvidenceLink.activity_id == activity_id,
        )
    )

    result = await db.execute(query)
    links = result.scalars().all()

    return {
        "activity_type": activity_type.value,
        "activity_id": activity_id,
        "controls_linked": len(links),
        "links": [
            {
                "framework": l.control_framework.value,
                "control_id": l.control_id,
                "control_name": l.control_name,
                "strength": l.evidence_strength.value,
                "linked_at": l.linked_at.isoformat(),
            }
            for l in links
        ],
    }


# =============================================================================
# REFERENCE DATA
# =============================================================================

@router.get("/activity-types")
async def list_activity_types():
    """List all activity types that can be linked to controls."""
    return [
        {
            "id": at.value,
            "name": at.value.replace("_", " ").title(),
            "description": _get_activity_description(at),
        }
        for at in ActivityType
    ]


@router.get("/frameworks/{framework}/controls")
async def list_framework_controls(
    framework: ControlFramework,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all controls in a framework with their evidence mapping."""
    from src.models.evidence_bridge import CONTROL_ACTIVITY_MAPPING

    mapping = CONTROL_ACTIVITY_MAPPING.get(framework.value, {})

    service = EvidenceBridgeService(db)
    effectiveness_data = await service.get_framework_effectiveness(
        current_user.tenant_id, framework
    )

    # Create lookup for effectiveness
    eff_lookup = {c.control_id: c for c in effectiveness_data.controls}

    controls = []
    for control_id, config in mapping.items():
        eff = eff_lookup.get(control_id)
        controls.append({
            "control_id": control_id,
            "control_name": service._get_control_name(framework, control_id),
            "linked_activity_types": [a.value for a in config["activities"]],
            "default_strength": config["strength"].value,
            "metrics": config["metrics"],
            "effectiveness_score": eff.effectiveness_score if eff else 0,
            "evidence_count": eff.evidence_count if eff else 0,
        })

    return controls


def _get_activity_description(activity_type: ActivityType) -> str:
    """Get description for an activity type."""
    descriptions = {
        ActivityType.INCIDENT: "Security incidents from incident management",
        ActivityType.ALERT: "SOC alerts from monitoring systems",
        ActivityType.CASE: "Investigation cases from SOC",
        ActivityType.VULNERABILITY_SCAN: "Vulnerability scan executions",
        ActivityType.VULNERABILITY: "Individual vulnerabilities found",
        ActivityType.THREAT_IOC: "Threat intelligence indicators",
        ActivityType.PLAYBOOK_EXECUTION: "Automated playbook runs",
        ActivityType.RISK_ASSESSMENT: "Risk assessments performed",
        ActivityType.BCM_EXERCISE: "Business continuity exercises",
        ActivityType.TRAINING_COMPLETION: "Security training completions",
        ActivityType.DOCUMENT_APPROVAL: "Policy document approvals",
        ActivityType.AUDIT_LOG: "System audit log entries",
        ActivityType.VENDOR_ASSESSMENT: "Third-party vendor assessments",
        ActivityType.CHANGE_REQUEST: "Change management requests",
    }
    return descriptions.get(activity_type, "")
