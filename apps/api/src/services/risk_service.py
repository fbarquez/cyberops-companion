"""
Risk Management Service.

Business logic for risk management operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.risk import (
    Risk, RiskControl, RiskAssessment, TreatmentAction, RiskAppetite,
    RiskCategory, RiskStatus, LikelihoodLevel, ImpactLevel, RiskLevel,
    TreatmentType, ControlType, ControlStatus
)
from src.schemas.risk import (
    RiskCreate, RiskUpdate, RiskAssessmentCreate,
    RiskControlCreate, RiskControlUpdate,
    TreatmentActionCreate, TreatmentActionUpdate,
    RiskAppetiteCreate, RiskMatrixCell
)

logger = logging.getLogger(__name__)


class RiskService:
    """Service for risk management operations."""

    # Likelihood and Impact scores (1-5)
    LIKELIHOOD_SCORES = {
        LikelihoodLevel.RARE: 1,
        LikelihoodLevel.UNLIKELY: 2,
        LikelihoodLevel.POSSIBLE: 3,
        LikelihoodLevel.LIKELY: 4,
        LikelihoodLevel.ALMOST_CERTAIN: 5,
    }

    IMPACT_SCORES = {
        ImpactLevel.NEGLIGIBLE: 1,
        ImpactLevel.MINOR: 2,
        ImpactLevel.MODERATE: 3,
        ImpactLevel.MAJOR: 4,
        ImpactLevel.CATASTROPHIC: 5,
    }

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    def calculate_risk_score(
        self,
        likelihood: LikelihoodLevel,
        impact: ImpactLevel
    ) -> float:
        """Calculate risk score as likelihood * impact."""
        return self.LIKELIHOOD_SCORES[likelihood] * self.IMPACT_SCORES[impact]

    def determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        if score <= 4:
            return RiskLevel.LOW
        elif score <= 9:
            return RiskLevel.MEDIUM
        elif score <= 16:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    async def generate_risk_id(self) -> str:
        """Generate unique risk ID."""
        year = datetime.utcnow().year
        result = await self.db.execute(
            select(func.count(Risk.id))
            .where(Risk.risk_id.like(f"RISK-{year}-%"))
        )
        count = result.scalar() or 0
        return f"RISK-{year}-{str(count + 1).zfill(4)}"

    async def generate_control_id(self) -> str:
        """Generate unique control ID."""
        result = await self.db.execute(select(func.count(RiskControl.id)))
        count = result.scalar() or 0
        return f"CTRL-{str(count + 1).zfill(4)}"

    # ==================== Risk Operations ====================

    async def create_risk(
        self,
        data: RiskCreate,
        user_id: Optional[str] = None
    ) -> Risk:
        """Create a new risk."""
        risk_id = await self.generate_risk_id()

        # Calculate inherent risk if provided
        inherent_score = None
        inherent_level = None
        if data.inherent_likelihood and data.inherent_impact:
            inherent_score = self.calculate_risk_score(
                data.inherent_likelihood, data.inherent_impact
            )
            inherent_level = self.determine_risk_level(inherent_score)

        risk = Risk(
            id=str(uuid4()),
            risk_id=risk_id,
            title=data.title,
            description=data.description,
            category=data.category,
            status=RiskStatus.IDENTIFIED,
            risk_source=data.risk_source,
            threat_scenario=data.threat_scenario,
            department=data.department,
            inherent_likelihood=data.inherent_likelihood,
            inherent_impact=data.inherent_impact,
            inherent_risk_score=inherent_score,
            inherent_risk_level=inherent_level,
            financial_impact=data.financial_impact,
            operational_impact=data.operational_impact,
            treatment_type=data.treatment_type,
            treatment_plan=data.treatment_plan,
            treatment_deadline=data.treatment_deadline,
            risk_owner=data.risk_owner,
            affected_assets=data.affected_assets,
            affected_processes=data.affected_processes,
            compliance_frameworks=data.compliance_frameworks,
            tags=data.tags,
            incident_id=data.incident_id,
            identified_date=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=90),
            created_by=user_id
        )

        self.db.add(risk)

        # If assessed, update status
        if inherent_score:
            risk.status = RiskStatus.ASSESSED

        await self.db.commit()
        await self.db.refresh(risk)

        logger.info(f"Created risk: {risk.risk_id} - {risk.title}")
        return risk

    async def get_risk(self, risk_id: str) -> Optional[Risk]:
        """Get a risk by ID."""
        result = await self.db.execute(
            select(Risk)
            .options(
                selectinload(Risk.controls),
                selectinload(Risk.treatment_actions),
                selectinload(Risk.assessments)
            )
            .where(or_(Risk.id == risk_id, Risk.risk_id == risk_id))
        )
        return result.scalar_one_or_none()

    async def list_risks(
        self,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List risks with filtering and pagination."""
        query = select(Risk).options(
            selectinload(Risk.controls),
            selectinload(Risk.treatment_actions)
        )
        count_query = select(func.count(Risk.id))

        conditions = []
        if filters:
            if filters.get("search"):
                search = filters["search"]
                search_filter = or_(
                    Risk.title.ilike(f"%{search}%"),
                    Risk.description.ilike(f"%{search}%"),
                    Risk.risk_id.ilike(f"%{search}%")
                )
                conditions.append(search_filter)
            if filters.get("category"):
                conditions.append(Risk.category == filters["category"])
            if filters.get("status"):
                conditions.append(Risk.status == filters["status"])
            if filters.get("risk_level"):
                conditions.append(or_(
                    Risk.inherent_risk_level == filters["risk_level"],
                    Risk.residual_risk_level == filters["risk_level"]
                ))
            if filters.get("risk_owner"):
                conditions.append(Risk.risk_owner == filters["risk_owner"])
            if filters.get("department"):
                conditions.append(Risk.department == filters["department"])

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(
            desc(Risk.inherent_risk_score),
            desc(Risk.created_at)
        ).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        risks = result.scalars().unique().all()

        return {
            "risks": list(risks),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_risk(
        self,
        risk_id: str,
        data: RiskUpdate,
        user_id: Optional[str] = None
    ) -> Optional[Risk]:
        """Update a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(risk, key, value)

        # Recalculate inherent risk if likelihood or impact changed
        if 'inherent_likelihood' in update_data or 'inherent_impact' in update_data:
            if risk.inherent_likelihood and risk.inherent_impact:
                risk.inherent_risk_score = self.calculate_risk_score(
                    risk.inherent_likelihood, risk.inherent_impact
                )
                risk.inherent_risk_level = self.determine_risk_level(risk.inherent_risk_score)

        # Recalculate residual risk if likelihood or impact changed
        if 'residual_likelihood' in update_data or 'residual_impact' in update_data:
            if risk.residual_likelihood and risk.residual_impact:
                risk.residual_risk_score = self.calculate_risk_score(
                    risk.residual_likelihood, risk.residual_impact
                )
                risk.residual_risk_level = self.determine_risk_level(risk.residual_risk_score)

        # Calculate target score
        if 'target_likelihood' in update_data or 'target_impact' in update_data:
            if risk.target_likelihood and risk.target_impact:
                risk.target_risk_score = self.calculate_risk_score(
                    risk.target_likelihood, risk.target_impact
                )

        await self.db.commit()
        await self.db.refresh(risk)
        return risk

    async def assess_risk(
        self,
        risk_id: str,
        data: RiskAssessmentCreate,
        user_id: Optional[str] = None
    ) -> Optional[RiskAssessment]:
        """Create a risk assessment and update risk scores."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return None

        # Calculate score
        score = self.calculate_risk_score(data.likelihood, data.impact)
        level = self.determine_risk_level(score)

        # Create assessment record
        assessment = RiskAssessment(
            id=str(uuid4()),
            risk_id=risk.id,
            assessment_type=data.assessment_type,
            likelihood=data.likelihood,
            impact=data.impact,
            risk_score=score,
            risk_level=level,
            assessment_notes=data.assessment_notes,
            assumptions=data.assumptions,
            assessed_by=user_id
        )
        self.db.add(assessment)

        # Update risk with inherent assessment
        risk.inherent_likelihood = data.likelihood
        risk.inherent_impact = data.impact
        risk.inherent_risk_score = score
        risk.inherent_risk_level = level
        risk.status = RiskStatus.ASSESSED
        risk.last_review_date = datetime.utcnow()
        risk.next_review_date = datetime.utcnow() + timedelta(days=risk.review_frequency_days)

        await self.db.commit()
        await self.db.refresh(assessment)

        logger.info(f"Assessed risk {risk.risk_id}: score={score}, level={level.value}")
        return assessment

    async def get_assessments(self, risk_id: str) -> List[RiskAssessment]:
        """Get assessment history for a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return []

        result = await self.db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.risk_id == risk.id)
            .order_by(desc(RiskAssessment.assessed_at))
        )
        return list(result.scalars().all())

    async def accept_risk(
        self,
        risk_id: str,
        acceptance_reason: str,
        acceptance_expiry: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Optional[Risk]:
        """Accept a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return None

        risk.status = RiskStatus.ACCEPTED
        risk.treatment_type = TreatmentType.ACCEPT
        risk.acceptance_reason = acceptance_reason
        risk.accepted_by = user_id
        risk.accepted_at = datetime.utcnow()
        risk.acceptance_expiry = acceptance_expiry

        await self.db.commit()
        await self.db.refresh(risk)

        logger.info(f"Accepted risk {risk.risk_id}")
        return risk

    async def close_risk(
        self,
        risk_id: str,
        closure_reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Risk]:
        """Close a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return None

        risk.status = RiskStatus.CLOSED
        risk.closed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(risk)

        logger.info(f"Closed risk {risk.risk_id}")
        return risk

    async def delete_risk(self, risk_id: str) -> bool:
        """Delete a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return False

        await self.db.delete(risk)
        await self.db.commit()
        return True

    # ==================== Control Operations ====================

    async def create_control(
        self,
        data: RiskControlCreate,
        user_id: Optional[str] = None
    ) -> RiskControl:
        """Create a new risk control."""
        control_id = await self.generate_control_id()

        control = RiskControl(
            id=str(uuid4()),
            control_id=control_id,
            name=data.name,
            description=data.description,
            control_type=data.control_type,
            status=ControlStatus.PLANNED,
            implementation_details=data.implementation_details,
            effectiveness_rating=data.effectiveness_rating,
            implementation_cost=data.implementation_cost,
            annual_cost=data.annual_cost,
            control_owner=data.control_owner,
            compliance_frameworks=data.compliance_frameworks,
            compliance_control_ids=data.compliance_control_ids
        )

        self.db.add(control)
        await self.db.commit()
        await self.db.refresh(control)

        logger.info(f"Created control: {control.control_id} - {control.name}")
        return control

    async def get_control(self, control_id: str) -> Optional[RiskControl]:
        """Get a control by ID."""
        result = await self.db.execute(
            select(RiskControl)
            .options(selectinload(RiskControl.risks))
            .where(or_(RiskControl.id == control_id, RiskControl.control_id == control_id))
        )
        return result.scalar_one_or_none()

    async def list_controls(
        self,
        page: int = 1,
        page_size: int = 50,
        control_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List controls with filtering and pagination."""
        query = select(RiskControl)
        count_query = select(func.count(RiskControl.id))

        conditions = []
        if control_type:
            conditions.append(RiskControl.control_type == control_type)
        if status:
            conditions.append(RiskControl.status == status)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(desc(RiskControl.created_at)).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        controls = result.scalars().all()

        return {
            "controls": list(controls),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_control(
        self,
        control_id: str,
        data: RiskControlUpdate
    ) -> Optional[RiskControl]:
        """Update a control."""
        control = await self.get_control(control_id)
        if not control:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(control, key, value)

        # If status changed to implemented, set implemented_date
        if data.status == ControlStatus.IMPLEMENTED and not control.implemented_date:
            control.implemented_date = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(control)
        return control

    async def delete_control(self, control_id: str) -> bool:
        """Delete a control."""
        control = await self.get_control(control_id)
        if not control:
            return False

        await self.db.delete(control)
        await self.db.commit()
        return True

    async def link_control_to_risk(
        self,
        risk_id: str,
        control_id: str
    ) -> Optional[Risk]:
        """Link a control to a risk."""
        risk = await self.get_risk(risk_id)
        control = await self.get_control(control_id)

        if not risk or not control:
            return None

        if control not in risk.controls:
            risk.controls.append(control)
            await self.db.commit()
            await self.db.refresh(risk)

        return risk

    async def unlink_control_from_risk(
        self,
        risk_id: str,
        control_id: str
    ) -> Optional[Risk]:
        """Unlink a control from a risk."""
        risk = await self.get_risk(risk_id)
        control = await self.get_control(control_id)

        if not risk or not control:
            return None

        if control in risk.controls:
            risk.controls.remove(control)
            await self.db.commit()
            await self.db.refresh(risk)

        return risk

    # ==================== Treatment Actions ====================

    async def create_treatment_action(
        self,
        risk_id: str,
        data: TreatmentActionCreate,
        user_id: Optional[str] = None
    ) -> Optional[TreatmentAction]:
        """Create a treatment action for a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return None

        action = TreatmentAction(
            id=str(uuid4()),
            risk_id=risk.id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            assigned_to=data.assigned_to,
            due_date=data.due_date,
            estimated_cost=data.estimated_cost,
            expected_risk_reduction=data.expected_risk_reduction
        )

        self.db.add(action)

        # Update risk status if first treatment action
        if risk.status == RiskStatus.ASSESSED:
            risk.status = RiskStatus.TREATMENT_PLANNED

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def get_treatment_actions(self, risk_id: str) -> List[TreatmentAction]:
        """Get treatment actions for a risk."""
        risk = await self.get_risk(risk_id)
        if not risk:
            return []

        result = await self.db.execute(
            select(TreatmentAction)
            .where(TreatmentAction.risk_id == risk.id)
            .order_by(desc(TreatmentAction.created_at))
        )
        return list(result.scalars().all())

    async def update_treatment_action(
        self,
        action_id: str,
        data: TreatmentActionUpdate
    ) -> Optional[TreatmentAction]:
        """Update a treatment action."""
        result = await self.db.execute(
            select(TreatmentAction).where(TreatmentAction.id == action_id)
        )
        action = result.scalar_one_or_none()
        if not action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(action, key, value)

        # Handle completion
        if data.status == "completed" and not action.completed_at:
            action.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def delete_treatment_action(self, action_id: str) -> bool:
        """Delete a treatment action."""
        result = await self.db.execute(
            select(TreatmentAction).where(TreatmentAction.id == action_id)
        )
        action = result.scalar_one_or_none()
        if not action:
            return False

        await self.db.delete(action)
        await self.db.commit()
        return True

    # ==================== Risk Appetite ====================

    async def set_risk_appetite(
        self,
        data: RiskAppetiteCreate,
        user_id: Optional[str] = None
    ) -> RiskAppetite:
        """Set or update risk appetite for a category."""
        # Check if appetite exists for category
        result = await self.db.execute(
            select(RiskAppetite).where(RiskAppetite.category == data.category)
        )
        appetite = result.scalar_one_or_none()

        if appetite:
            # Update existing
            appetite.appetite_level = data.appetite_level
            appetite.tolerance_threshold = data.tolerance_threshold
            appetite.description = data.description
            appetite.max_single_loss = data.max_single_loss
            appetite.max_annual_loss = data.max_annual_loss
            appetite.requires_board_approval = data.requires_board_approval
            appetite.requires_executive_approval = data.requires_executive_approval
            appetite.approved_by = user_id
        else:
            # Create new
            appetite = RiskAppetite(
                id=str(uuid4()),
                category=data.category,
                appetite_level=data.appetite_level,
                tolerance_threshold=data.tolerance_threshold,
                description=data.description,
                max_single_loss=data.max_single_loss,
                max_annual_loss=data.max_annual_loss,
                requires_board_approval=data.requires_board_approval,
                requires_executive_approval=data.requires_executive_approval,
                effective_date=datetime.utcnow(),
                approved_by=user_id
            )
            self.db.add(appetite)

        await self.db.commit()
        await self.db.refresh(appetite)
        return appetite

    async def get_risk_appetite(self) -> List[RiskAppetite]:
        """Get all risk appetite settings."""
        result = await self.db.execute(
            select(RiskAppetite).order_by(RiskAppetite.category)
        )
        return list(result.scalars().all())

    async def get_risk_appetite_by_category(
        self,
        category: RiskCategory
    ) -> Optional[RiskAppetite]:
        """Get risk appetite for a specific category."""
        result = await self.db.execute(
            select(RiskAppetite).where(RiskAppetite.category == category)
        )
        return result.scalar_one_or_none()

    # ==================== Risk Matrix ====================

    async def get_risk_matrix(self) -> List[RiskMatrixCell]:
        """Generate risk matrix with counts."""
        matrix = []

        for likelihood in LikelihoodLevel:
            for impact in ImpactLevel:
                score = self.calculate_risk_score(likelihood, impact)
                level = self.determine_risk_level(score)

                # Count risks at this position (using inherent values)
                result = await self.db.execute(
                    select(Risk)
                    .where(
                        and_(
                            Risk.inherent_likelihood == likelihood,
                            Risk.inherent_impact == impact,
                            Risk.status.notin_([RiskStatus.CLOSED])
                        )
                    )
                )
                risks = result.scalars().all()

                matrix.append(RiskMatrixCell(
                    likelihood=likelihood,
                    impact=impact,
                    risk_level=level,
                    risk_count=len(risks),
                    risks=[{"id": r.id, "risk_id": r.risk_id, "title": r.title} for r in risks]
                ))

        return matrix

    # ==================== Statistics ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get risk management statistics."""
        now = datetime.utcnow()

        # Total risks (excluding closed)
        total_result = await self.db.execute(
            select(func.count(Risk.id))
            .where(Risk.status != RiskStatus.CLOSED)
        )
        total_risks = total_result.scalar() or 0

        # Open risks (not mitigated, accepted, or closed)
        open_result = await self.db.execute(
            select(func.count(Risk.id))
            .where(Risk.status.in_([
                RiskStatus.IDENTIFIED, RiskStatus.ASSESSED,
                RiskStatus.TREATMENT_PLANNED, RiskStatus.TREATMENT_IN_PROGRESS
            ]))
        )
        open_risks = open_result.scalar() or 0

        # By category
        category_result = await self.db.execute(
            select(Risk.category, func.count(Risk.id))
            .where(Risk.status != RiskStatus.CLOSED)
            .group_by(Risk.category)
        )
        by_category = {str(row[0].value): row[1] for row in category_result.fetchall()}

        # By status
        status_result = await self.db.execute(
            select(Risk.status, func.count(Risk.id))
            .group_by(Risk.status)
        )
        by_status = {str(row[0].value): row[1] for row in status_result.fetchall()}

        # By risk level (inherent)
        level_result = await self.db.execute(
            select(Risk.inherent_risk_level, func.count(Risk.id))
            .where(
                and_(
                    Risk.inherent_risk_level.isnot(None),
                    Risk.status != RiskStatus.CLOSED
                )
            )
            .group_by(Risk.inherent_risk_level)
        )
        by_level = {str(row[0].value): row[1] for row in level_result.fetchall() if row[0]}

        # Critical and high risks
        critical_result = await self.db.execute(
            select(func.count(Risk.id))
            .where(
                and_(
                    Risk.inherent_risk_level == RiskLevel.CRITICAL,
                    Risk.status != RiskStatus.CLOSED
                )
            )
        )
        critical_risks = critical_result.scalar() or 0

        high_result = await self.db.execute(
            select(func.count(Risk.id))
            .where(
                and_(
                    Risk.inherent_risk_level == RiskLevel.HIGH,
                    Risk.status != RiskStatus.CLOSED
                )
            )
        )
        high_risks = high_result.scalar() or 0

        # Overdue treatment actions
        overdue_result = await self.db.execute(
            select(func.count(TreatmentAction.id))
            .where(
                and_(
                    TreatmentAction.due_date < now,
                    TreatmentAction.status.in_(["pending", "in_progress"])
                )
            )
        )
        overdue_treatments = overdue_result.scalar() or 0

        # Risks needing review
        review_result = await self.db.execute(
            select(func.count(Risk.id))
            .where(
                and_(
                    Risk.next_review_date <= now,
                    Risk.status != RiskStatus.CLOSED
                )
            )
        )
        risks_needing_review = review_result.scalar() or 0

        # Controls stats
        controls_result = await self.db.execute(select(func.count(RiskControl.id)))
        total_controls = controls_result.scalar() or 0

        effective_controls_result = await self.db.execute(
            select(func.count(RiskControl.id))
            .where(
                and_(
                    RiskControl.status == ControlStatus.IMPLEMENTED,
                    RiskControl.effectiveness_rating >= 70
                )
            )
        )
        effective_controls = effective_controls_result.scalar() or 0

        # Average risk score
        avg_result = await self.db.execute(
            select(func.avg(Risk.inherent_risk_score))
            .where(
                and_(
                    Risk.inherent_risk_score.isnot(None),
                    Risk.status != RiskStatus.CLOSED
                )
            )
        )
        avg_score = avg_result.scalar()
        avg_score = round(avg_score, 2) if avg_score else None

        # Total financial exposure
        exposure_result = await self.db.execute(
            select(func.sum(Risk.financial_impact))
            .where(
                and_(
                    Risk.financial_impact.isnot(None),
                    Risk.status.in_([
                        RiskStatus.IDENTIFIED, RiskStatus.ASSESSED,
                        RiskStatus.TREATMENT_PLANNED, RiskStatus.TREATMENT_IN_PROGRESS
                    ])
                )
            )
        )
        total_exposure = exposure_result.scalar()

        # Recent risks
        recent_result = await self.db.execute(
            select(Risk)
            .options(selectinload(Risk.controls))
            .order_by(desc(Risk.created_at))
            .limit(10)
        )
        recent_risks = recent_result.scalars().all()

        return {
            "total_risks": total_risks,
            "open_risks": open_risks,
            "risks_by_category": by_category,
            "risks_by_status": by_status,
            "risks_by_level": by_level,
            "critical_risks": critical_risks,
            "high_risks": high_risks,
            "overdue_treatments": overdue_treatments,
            "risks_needing_review": risks_needing_review,
            "total_controls": total_controls,
            "effective_controls": effective_controls,
            "average_risk_score": avg_score,
            "total_financial_exposure": total_exposure,
            "recent_risks": recent_risks
        }
