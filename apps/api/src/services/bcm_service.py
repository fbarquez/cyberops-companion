"""
Business Continuity Management (BCM) Service.

Business logic for BCM based on BSI Standard 200-4 and ISO 22301.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.bcm import (
    BCMProcess, BCMBIA, BCMRiskScenario, BCMStrategy,
    BCMEmergencyPlan, BCMContact, BCMExercise, BCMAssessment,
    BCMProcessCriticality, BCMProcessStatus, BCMImpactLevel, BCMBIAStatus,
    BCMScenarioCategory, BCMLikelihood, BCMImpact, BCMScenarioStatus,
    BCMStrategyType, BCMStrategyStatus, BCMPlanType, BCMPlanStatus,
    BCMContactType, BCMContactAvailability, BCMExerciseType, BCMExerciseStatus,
    BCMAssessmentStatus, BCMControlEffectiveness
)
from src.schemas.bcm import (
    ProcessCreate, ProcessUpdate, BIACreate,
    ScenarioCreate, ScenarioUpdate,
    StrategyCreate, StrategyUpdate,
    PlanCreate, PlanUpdate,
    ContactCreate, ContactUpdate,
    ExerciseCreate, ExerciseUpdate, ExerciseCompleteRequest,
    AssessmentCreate
)


# Likelihood/Impact to numeric mapping for risk score calculation
LIKELIHOOD_VALUES = {
    BCMLikelihood.RARE: 1,
    BCMLikelihood.UNLIKELY: 2,
    BCMLikelihood.POSSIBLE: 3,
    BCMLikelihood.LIKELY: 4,
    BCMLikelihood.ALMOST_CERTAIN: 5,
}

IMPACT_VALUES = {
    BCMImpact.NEGLIGIBLE: 1,
    BCMImpact.MINOR: 2,
    BCMImpact.MODERATE: 3,
    BCMImpact.MAJOR: 4,
    BCMImpact.CATASTROPHIC: 5,
}


class BCMService:
    """Service for Business Continuity Management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Dashboard Methods ==========

    async def get_dashboard_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get BCM dashboard statistics."""
        # Process stats
        processes = await self.list_processes(tenant_id)
        total_processes = len(processes)
        critical_processes = sum(1 for p in processes if p.criticality == BCMProcessCriticality.CRITICAL)

        processes_by_criticality = {}
        for p in processes:
            key = p.criticality.value
            processes_by_criticality[key] = processes_by_criticality.get(key, 0) + 1

        # BIA stats
        processes_with_bia = 0
        total_rto = 0
        bia_count = 0
        for p in processes:
            bia = await self.get_bia(p.id, tenant_id)
            if bia:
                processes_with_bia += 1
                total_rto += bia.rto_hours
                bia_count += 1

        bia_completion = (processes_with_bia / total_processes * 100) if total_processes > 0 else 0.0
        average_rto = (total_rto / bia_count) if bia_count > 0 else None

        # Scenario stats
        scenarios_result = await self.db.execute(
            select(BCMRiskScenario).where(BCMRiskScenario.tenant_id == tenant_id)
        )
        scenarios = scenarios_result.scalars().all()
        total_scenarios = len(scenarios)

        scenarios_by_category = {}
        high_risk_scenarios = 0
        for s in scenarios:
            key = s.category.value
            scenarios_by_category[key] = scenarios_by_category.get(key, 0) + 1
            if s.risk_score >= 15:  # High risk threshold
                high_risk_scenarios += 1

        # Plan stats
        plans_result = await self.db.execute(
            select(BCMEmergencyPlan).where(BCMEmergencyPlan.tenant_id == tenant_id)
        )
        plans = plans_result.scalars().all()
        total_plans = len(plans)
        active_plans = sum(1 for p in plans if p.status == BCMPlanStatus.ACTIVE)

        plans_by_type = {}
        for p in plans:
            key = p.plan_type.value
            plans_by_type[key] = plans_by_type.get(key, 0) + 1

        # Exercise stats
        current_year = date.today().year
        exercises_result = await self.db.execute(
            select(BCMExercise).where(
                and_(
                    BCMExercise.tenant_id == tenant_id,
                    func.extract('year', BCMExercise.planned_date) == current_year
                )
            ).order_by(BCMExercise.planned_date)
        )
        exercises = exercises_result.scalars().all()
        exercises_this_year = len(exercises)
        completed_exercises = sum(1 for e in exercises if e.status == BCMExerciseStatus.COMPLETED)

        # Upcoming exercises
        upcoming_exercises = []
        for e in exercises:
            if e.status == BCMExerciseStatus.PLANNED and e.planned_date >= date.today():
                upcoming_exercises.append({
                    "id": e.id,
                    "name": e.name,
                    "planned_date": e.planned_date.isoformat(),
                    "exercise_type": e.exercise_type.value,
                })
        upcoming_exercises = upcoming_exercises[:5]  # Limit to 5

        # Assessment stats
        assessments_result = await self.db.execute(
            select(BCMAssessment)
            .where(BCMAssessment.tenant_id == tenant_id)
            .order_by(BCMAssessment.created_at.desc())
        )
        assessments = assessments_result.scalars().all()
        total_assessments = len(assessments)
        latest_score = assessments[0].overall_score if assessments and assessments[0].overall_score else None

        # Recent activity (combine recent items)
        recent_activity = []

        # Add recent processes
        for p in processes[:3]:
            recent_activity.append({
                "type": "process",
                "action": "created",
                "name": p.name,
                "date": p.created_at.isoformat(),
            })

        # Add recent exercises
        for e in exercises[:3]:
            recent_activity.append({
                "type": "exercise",
                "action": "completed" if e.status == BCMExerciseStatus.COMPLETED else "planned",
                "name": e.name,
                "date": e.created_at.isoformat(),
            })

        # Sort by date and limit
        recent_activity.sort(key=lambda x: x["date"], reverse=True)
        recent_activity = recent_activity[:10]

        return {
            "total_processes": total_processes,
            "critical_processes": critical_processes,
            "processes_by_criticality": processes_by_criticality,
            "bia_completion_percentage": bia_completion,
            "processes_with_bia": processes_with_bia,
            "average_rto_hours": average_rto,
            "total_scenarios": total_scenarios,
            "scenarios_by_category": scenarios_by_category,
            "high_risk_scenarios": high_risk_scenarios,
            "total_plans": total_plans,
            "active_plans": active_plans,
            "plans_by_type": plans_by_type,
            "exercises_this_year": exercises_this_year,
            "completed_exercises": completed_exercises,
            "upcoming_exercises": upcoming_exercises,
            "total_assessments": total_assessments,
            "latest_assessment_score": latest_score,
            "recent_activity": recent_activity,
        }

    # ========== Process Methods ==========

    async def create_process(
        self,
        tenant_id: str,
        data: ProcessCreate,
        created_by: str
    ) -> BCMProcess:
        """Create a new business process."""
        process = BCMProcess(
            id=str(uuid4()),
            tenant_id=tenant_id,
            process_id=data.process_id,
            name=data.name,
            description=data.description,
            owner=data.owner,
            department=data.department,
            criticality=data.criticality,
            internal_dependencies=data.internal_dependencies,
            external_dependencies=data.external_dependencies,
            it_systems=data.it_systems,
            key_personnel=data.key_personnel,
            status=data.status,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        self.db.add(process)
        await self.db.flush()
        return process

    async def get_process(self, process_id: str, tenant_id: str) -> Optional[BCMProcess]:
        """Get a process by ID."""
        result = await self.db.execute(
            select(BCMProcess).where(
                and_(
                    BCMProcess.id == process_id,
                    BCMProcess.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_processes(
        self,
        tenant_id: str,
        criticality: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> List[BCMProcess]:
        """List processes for a tenant."""
        query = select(BCMProcess).where(BCMProcess.tenant_id == tenant_id)

        if criticality:
            try:
                crit_enum = BCMProcessCriticality(criticality)
                query = query.where(BCMProcess.criticality == crit_enum)
            except ValueError:
                pass

        if status:
            try:
                status_enum = BCMProcessStatus(status)
                query = query.where(BCMProcess.status == status_enum)
            except ValueError:
                pass

        query = query.order_by(BCMProcess.criticality, BCMProcess.name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_process(
        self,
        process_id: str,
        tenant_id: str,
        data: ProcessUpdate
    ) -> Optional[BCMProcess]:
        """Update a process."""
        process = await self.get_process(process_id, tenant_id)
        if not process:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(process, field, value)

        process.updated_at = datetime.utcnow()
        return process

    async def delete_process(self, process_id: str, tenant_id: str) -> bool:
        """Delete a process."""
        process = await self.get_process(process_id, tenant_id)
        if not process:
            return False

        await self.db.delete(process)
        return True

    # ========== BIA Methods ==========

    async def create_or_update_bia(
        self,
        process_id: str,
        tenant_id: str,
        data: BIACreate
    ) -> Optional[BCMBIA]:
        """Create or update BIA for a process."""
        # Verify process exists
        process = await self.get_process(process_id, tenant_id)
        if not process:
            return None

        # Check if BIA exists
        result = await self.db.execute(
            select(BCMBIA).where(BCMBIA.process_id == process_id)
        )
        bia = result.scalar_one_or_none()

        if bia:
            # Update existing
            update_data = data.model_dump()
            for field, value in update_data.items():
                setattr(bia, field, value)
            bia.updated_at = datetime.utcnow()
        else:
            # Create new
            bia = BCMBIA(
                id=str(uuid4()),
                tenant_id=tenant_id,
                process_id=process_id,
                analysis_date=datetime.utcnow(),
                created_at=datetime.utcnow(),
                **data.model_dump()
            )
            self.db.add(bia)

        await self.db.flush()
        return bia

    async def get_bia(self, process_id: str, tenant_id: str) -> Optional[BCMBIA]:
        """Get BIA for a process."""
        result = await self.db.execute(
            select(BCMBIA).where(
                and_(
                    BCMBIA.process_id == process_id,
                    BCMBIA.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_bia_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get BIA summary across all processes."""
        processes = await self.list_processes(tenant_id)
        total = len(processes)

        with_bia = 0
        by_status: Dict[str, int] = {}
        by_criticality: Dict[str, int] = {}
        total_rto = 0
        total_rpo = 0
        bia_count = 0

        for p in processes:
            bia = await self.get_bia(p.id, tenant_id)
            if bia:
                with_bia += 1
                status_key = bia.status.value
                by_status[status_key] = by_status.get(status_key, 0) + 1
                crit_key = p.criticality.value
                by_criticality[crit_key] = by_criticality.get(crit_key, 0) + 1
                total_rto += bia.rto_hours
                total_rpo += bia.rpo_hours
                bia_count += 1

        return {
            "total_processes": total,
            "processes_with_bia": with_bia,
            "bia_completion_percentage": (with_bia / total * 100) if total > 0 else 0.0,
            "by_status": by_status,
            "by_criticality": by_criticality,
            "average_rto_hours": (total_rto / bia_count) if bia_count > 0 else None,
            "average_rpo_hours": (total_rpo / bia_count) if bia_count > 0 else None,
        }

    # ========== Risk Scenario Methods ==========

    async def create_scenario(
        self,
        tenant_id: str,
        data: ScenarioCreate,
        created_by: str
    ) -> BCMRiskScenario:
        """Create a risk scenario."""
        # Calculate risk score
        likelihood_val = LIKELIHOOD_VALUES.get(data.likelihood, 3)
        impact_val = IMPACT_VALUES.get(data.impact, 3)
        risk_score = likelihood_val * impact_val

        scenario = BCMRiskScenario(
            id=str(uuid4()),
            tenant_id=tenant_id,
            scenario_id=data.scenario_id,
            name=data.name,
            description=data.description,
            category=data.category,
            likelihood=data.likelihood,
            impact=data.impact,
            risk_score=risk_score,
            affected_processes=data.affected_processes,
            single_points_of_failure=data.single_points_of_failure,
            existing_controls=data.existing_controls,
            control_effectiveness=data.control_effectiveness,
            status=data.status,
            created_at=datetime.utcnow(),
        )
        self.db.add(scenario)
        await self.db.flush()
        return scenario

    async def get_scenario(self, scenario_id: str, tenant_id: str) -> Optional[BCMRiskScenario]:
        """Get a scenario by ID."""
        result = await self.db.execute(
            select(BCMRiskScenario).where(
                and_(
                    BCMRiskScenario.id == scenario_id,
                    BCMRiskScenario.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_scenarios(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[BCMRiskScenario], int]:
        """List risk scenarios."""
        query = select(BCMRiskScenario).where(BCMRiskScenario.tenant_id == tenant_id)

        if category:
            try:
                cat_enum = BCMScenarioCategory(category)
                query = query.where(BCMRiskScenario.category == cat_enum)
            except ValueError:
                pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(BCMRiskScenario.risk_score.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        scenarios = list(result.scalars().all())

        return scenarios, total

    async def update_scenario(
        self,
        scenario_id: str,
        tenant_id: str,
        data: ScenarioUpdate,
        assessed_by: str
    ) -> Optional[BCMRiskScenario]:
        """Update a scenario."""
        scenario = await self.get_scenario(scenario_id, tenant_id)
        if not scenario:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Recalculate risk score if likelihood or impact changed
        if 'likelihood' in update_data or 'impact' in update_data:
            likelihood = update_data.get('likelihood', scenario.likelihood)
            impact = update_data.get('impact', scenario.impact)
            if isinstance(likelihood, str):
                likelihood = BCMLikelihood(likelihood)
            if isinstance(impact, str):
                impact = BCMImpact(impact)
            likelihood_val = LIKELIHOOD_VALUES.get(likelihood, 3)
            impact_val = IMPACT_VALUES.get(impact, 3)
            update_data['risk_score'] = likelihood_val * impact_val

        for field, value in update_data.items():
            setattr(scenario, field, value)

        scenario.assessed_by = assessed_by
        scenario.assessed_at = datetime.utcnow()
        scenario.updated_at = datetime.utcnow()

        return scenario

    async def delete_scenario(self, scenario_id: str, tenant_id: str) -> bool:
        """Delete a scenario."""
        scenario = await self.get_scenario(scenario_id, tenant_id)
        if not scenario:
            return False

        await self.db.delete(scenario)
        return True

    async def get_risk_matrix(self, tenant_id: str) -> Dict[str, Any]:
        """Get risk matrix data for visualization."""
        scenarios, _ = await self.list_scenarios(tenant_id, page_size=1000)

        # Initialize matrix
        matrix: Dict[str, Dict[str, int]] = {}
        scenarios_by_cell: Dict[str, List[Dict[str, Any]]] = {}

        for likelihood in BCMLikelihood:
            matrix[likelihood.value] = {}
            for impact in BCMImpact:
                matrix[likelihood.value][impact.value] = 0
                cell_key = f"{likelihood.value}-{impact.value}"
                scenarios_by_cell[cell_key] = []

        # Populate matrix
        for s in scenarios:
            matrix[s.likelihood.value][s.impact.value] += 1
            cell_key = f"{s.likelihood.value}-{s.impact.value}"
            scenarios_by_cell[cell_key].append({
                "id": s.id,
                "name": s.name,
                "risk_score": s.risk_score,
            })

        return {
            "matrix": matrix,
            "scenarios_by_cell": scenarios_by_cell,
        }

    # ========== Strategy Methods ==========

    async def create_strategy(
        self,
        process_id: str,
        tenant_id: str,
        data: StrategyCreate
    ) -> Optional[BCMStrategy]:
        """Create a continuity strategy for a process."""
        # Verify process exists
        process = await self.get_process(process_id, tenant_id)
        if not process:
            return None

        strategy = BCMStrategy(
            id=str(uuid4()),
            tenant_id=tenant_id,
            process_id=process_id,
            created_at=datetime.utcnow(),
            **data.model_dump()
        )
        self.db.add(strategy)
        await self.db.flush()
        return strategy

    async def get_strategy(self, strategy_id: str, tenant_id: str) -> Optional[BCMStrategy]:
        """Get a strategy by ID."""
        result = await self.db.execute(
            select(BCMStrategy).where(
                and_(
                    BCMStrategy.id == strategy_id,
                    BCMStrategy.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_strategies_for_process(
        self,
        process_id: str,
        tenant_id: str
    ) -> List[BCMStrategy]:
        """List strategies for a process."""
        result = await self.db.execute(
            select(BCMStrategy).where(
                and_(
                    BCMStrategy.process_id == process_id,
                    BCMStrategy.tenant_id == tenant_id
                )
            ).order_by(BCMStrategy.created_at)
        )
        return list(result.scalars().all())

    async def update_strategy(
        self,
        strategy_id: str,
        tenant_id: str,
        data: StrategyUpdate
    ) -> Optional[BCMStrategy]:
        """Update a strategy."""
        strategy = await self.get_strategy(strategy_id, tenant_id)
        if not strategy:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)

        strategy.updated_at = datetime.utcnow()
        return strategy

    async def delete_strategy(self, strategy_id: str, tenant_id: str) -> bool:
        """Delete a strategy."""
        strategy = await self.get_strategy(strategy_id, tenant_id)
        if not strategy:
            return False

        await self.db.delete(strategy)
        return True

    # ========== Emergency Plan Methods ==========

    async def create_plan(
        self,
        tenant_id: str,
        data: PlanCreate,
        created_by: str
    ) -> BCMEmergencyPlan:
        """Create an emergency plan."""
        plan = BCMEmergencyPlan(
            id=str(uuid4()),
            tenant_id=tenant_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            **data.model_dump()
        )
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def get_plan(self, plan_id: str, tenant_id: str) -> Optional[BCMEmergencyPlan]:
        """Get a plan by ID."""
        result = await self.db.execute(
            select(BCMEmergencyPlan).where(
                and_(
                    BCMEmergencyPlan.id == plan_id,
                    BCMEmergencyPlan.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_plans(
        self,
        tenant_id: str,
        plan_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BCMEmergencyPlan], int]:
        """List emergency plans."""
        query = select(BCMEmergencyPlan).where(BCMEmergencyPlan.tenant_id == tenant_id)

        if plan_type:
            try:
                type_enum = BCMPlanType(plan_type)
                query = query.where(BCMEmergencyPlan.plan_type == type_enum)
            except ValueError:
                pass

        if status:
            try:
                status_enum = BCMPlanStatus(status)
                query = query.where(BCMEmergencyPlan.status == status_enum)
            except ValueError:
                pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(BCMEmergencyPlan.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        plans = list(result.scalars().all())

        return plans, total

    async def update_plan(
        self,
        plan_id: str,
        tenant_id: str,
        data: PlanUpdate
    ) -> Optional[BCMEmergencyPlan]:
        """Update a plan."""
        plan = await self.get_plan(plan_id, tenant_id)
        if not plan:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        plan.updated_at = datetime.utcnow()
        return plan

    async def delete_plan(self, plan_id: str, tenant_id: str) -> bool:
        """Delete a plan."""
        plan = await self.get_plan(plan_id, tenant_id)
        if not plan:
            return False

        await self.db.delete(plan)
        return True

    async def approve_plan(
        self,
        plan_id: str,
        tenant_id: str,
        approved_by: str
    ) -> Optional[BCMEmergencyPlan]:
        """Approve a plan."""
        plan = await self.get_plan(plan_id, tenant_id)
        if not plan:
            return None

        plan.status = BCMPlanStatus.APPROVED
        plan.approved_by = approved_by
        plan.approved_at = datetime.utcnow()
        plan.updated_at = datetime.utcnow()

        return plan

    # ========== Contact Methods ==========

    async def create_contact(
        self,
        tenant_id: str,
        data: ContactCreate
    ) -> BCMContact:
        """Create an emergency contact."""
        contact = BCMContact(
            id=str(uuid4()),
            tenant_id=tenant_id,
            created_at=datetime.utcnow(),
            **data.model_dump()
        )
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def get_contact(self, contact_id: str, tenant_id: str) -> Optional[BCMContact]:
        """Get a contact by ID."""
        result = await self.db.execute(
            select(BCMContact).where(
                and_(
                    BCMContact.id == contact_id,
                    BCMContact.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_contacts(self, tenant_id: str) -> List[BCMContact]:
        """List all contacts ordered by priority."""
        result = await self.db.execute(
            select(BCMContact)
            .where(BCMContact.tenant_id == tenant_id)
            .order_by(BCMContact.priority, BCMContact.name)
        )
        return list(result.scalars().all())

    async def update_contact(
        self,
        contact_id: str,
        tenant_id: str,
        data: ContactUpdate
    ) -> Optional[BCMContact]:
        """Update a contact."""
        contact = await self.get_contact(contact_id, tenant_id)
        if not contact:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)

        contact.updated_at = datetime.utcnow()
        return contact

    async def delete_contact(self, contact_id: str, tenant_id: str) -> bool:
        """Delete a contact."""
        contact = await self.get_contact(contact_id, tenant_id)
        if not contact:
            return False

        await self.db.delete(contact)
        return True

    # ========== Exercise Methods ==========

    async def create_exercise(
        self,
        tenant_id: str,
        data: ExerciseCreate,
        created_by: str
    ) -> BCMExercise:
        """Create a BC exercise."""
        exercise = BCMExercise(
            id=str(uuid4()),
            tenant_id=tenant_id,
            conducted_by=created_by,
            created_at=datetime.utcnow(),
            **data.model_dump()
        )
        self.db.add(exercise)
        await self.db.flush()
        return exercise

    async def get_exercise(self, exercise_id: str, tenant_id: str) -> Optional[BCMExercise]:
        """Get an exercise by ID."""
        result = await self.db.execute(
            select(BCMExercise).where(
                and_(
                    BCMExercise.id == exercise_id,
                    BCMExercise.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_exercises(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BCMExercise], int]:
        """List exercises."""
        query = select(BCMExercise).where(BCMExercise.tenant_id == tenant_id)

        if status:
            try:
                status_enum = BCMExerciseStatus(status)
                query = query.where(BCMExercise.status == status_enum)
            except ValueError:
                pass

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(BCMExercise.planned_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        exercises = list(result.scalars().all())

        return exercises, total

    async def update_exercise(
        self,
        exercise_id: str,
        tenant_id: str,
        data: ExerciseUpdate
    ) -> Optional[BCMExercise]:
        """Update an exercise."""
        exercise = await self.get_exercise(exercise_id, tenant_id)
        if not exercise:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(exercise, field, value)

        exercise.updated_at = datetime.utcnow()
        return exercise

    async def delete_exercise(self, exercise_id: str, tenant_id: str) -> bool:
        """Delete an exercise."""
        exercise = await self.get_exercise(exercise_id, tenant_id)
        if not exercise:
            return False

        await self.db.delete(exercise)
        return True

    async def complete_exercise(
        self,
        exercise_id: str,
        tenant_id: str,
        data: ExerciseCompleteRequest,
        conducted_by: str
    ) -> Optional[BCMExercise]:
        """Complete an exercise with results."""
        exercise = await self.get_exercise(exercise_id, tenant_id)
        if not exercise:
            return None

        exercise.status = BCMExerciseStatus.COMPLETED
        exercise.actual_date = data.actual_date
        exercise.actual_duration_hours = data.actual_duration_hours
        exercise.results_summary = data.results_summary
        exercise.objectives_met = data.objectives_met
        exercise.issues_identified = data.issues_identified
        exercise.lessons_learned = data.lessons_learned
        exercise.action_items = data.action_items
        exercise.conducted_by = conducted_by
        exercise.updated_at = datetime.utcnow()

        return exercise

    # ========== Assessment Methods ==========

    async def create_assessment(
        self,
        tenant_id: str,
        data: AssessmentCreate,
        created_by: str
    ) -> BCMAssessment:
        """Create a BCM assessment."""
        assessment = BCMAssessment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            status=BCMAssessmentStatus.DRAFT,
            assessment_date=date.today(),
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        self.db.add(assessment)
        await self.db.flush()
        return assessment

    async def get_assessment(self, assessment_id: str, tenant_id: str) -> Optional[BCMAssessment]:
        """Get an assessment by ID."""
        result = await self.db.execute(
            select(BCMAssessment).where(
                and_(
                    BCMAssessment.id == assessment_id,
                    BCMAssessment.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[BCMAssessment], int]:
        """List BCM assessments."""
        query = select(BCMAssessment).where(BCMAssessment.tenant_id == tenant_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(BCMAssessment.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        assessments = list(result.scalars().all())

        return assessments, total

    async def delete_assessment(self, assessment_id: str, tenant_id: str) -> bool:
        """Delete an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return False

        await self.db.delete(assessment)
        return True

    async def recalculate_assessment_scores(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[BCMAssessment]:
        """Recalculate all scores for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Get all data
        processes = await self.list_processes(tenant_id)
        total_processes = len(processes)
        critical_processes = sum(1 for p in processes if p.criticality == BCMProcessCriticality.CRITICAL)

        # Count processes with BIA
        processes_with_bia = 0
        processes_with_strategy = 0
        for p in processes:
            bia = await self.get_bia(p.id, tenant_id)
            if bia and bia.status in [BCMBIAStatus.COMPLETED, BCMBIAStatus.APPROVED]:
                processes_with_bia += 1

            strategies = await self.list_strategies_for_process(p.id, tenant_id)
            if strategies:
                processes_with_strategy += 1

        # Get plans and exercises
        plans, _ = await self.list_plans(tenant_id, status="active")
        processes_with_plan = 0
        for plan in plans:
            processes_with_plan += len(plan.affected_processes or [])

        # Count plans tested this year
        current_year = date.today().year
        exercises, _ = await self.list_exercises(tenant_id, status="completed")
        plans_tested = set()
        for ex in exercises:
            if ex.actual_date and ex.actual_date.year == current_year and ex.plan_id:
                plans_tested.add(ex.plan_id)

        # Update counts
        assessment.total_processes = total_processes
        assessment.critical_processes = critical_processes
        assessment.processes_with_bia = processes_with_bia
        assessment.processes_with_strategy = processes_with_strategy
        assessment.processes_with_plan = min(processes_with_plan, total_processes)
        assessment.plans_tested_this_year = len(plans_tested)

        # Calculate scores (0-100)
        if total_processes > 0:
            assessment.process_coverage_score = 100.0  # We have documented processes
            assessment.bia_completion_score = (processes_with_bia / total_processes) * 100
            assessment.strategy_coverage_score = (processes_with_strategy / total_processes) * 100
        else:
            assessment.process_coverage_score = 0.0
            assessment.bia_completion_score = 0.0
            assessment.strategy_coverage_score = 0.0

        if critical_processes > 0:
            assessment.plan_coverage_score = min((processes_with_plan / critical_processes) * 100, 100)
        else:
            assessment.plan_coverage_score = 100.0 if len(plans) > 0 else 0.0

        total_active_plans = len(plans)
        if total_active_plans > 0:
            assessment.test_coverage_score = (len(plans_tested) / total_active_plans) * 100
        else:
            assessment.test_coverage_score = 0.0

        # Calculate overall score using weighted formula
        assessment.overall_score = (
            (assessment.process_coverage_score or 0) * 0.15 +
            (assessment.bia_completion_score or 0) * 0.25 +
            (assessment.strategy_coverage_score or 0) * 0.20 +
            (assessment.plan_coverage_score or 0) * 0.25 +
            (assessment.test_coverage_score or 0) * 0.15
        )

        assessment.updated_at = datetime.utcnow()
        return assessment

    async def get_wizard_state(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current wizard state for an assessment."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Define steps
        steps = [
            {"step": 1, "name": "Process Inventory", "status": "pending"},
            {"step": 2, "name": "Business Impact Analysis", "status": "pending"},
            {"step": 3, "name": "Risk Assessment", "status": "pending"},
            {"step": 4, "name": "Strategy Planning", "status": "pending"},
            {"step": 5, "name": "Plan Development", "status": "pending"},
            {"step": 6, "name": "Testing", "status": "pending"},
            {"step": 7, "name": "Complete", "status": "pending"},
        ]

        # Determine current step based on status
        status_to_step = {
            BCMAssessmentStatus.DRAFT: 1,
            BCMAssessmentStatus.PROCESS_INVENTORY: 1,
            BCMAssessmentStatus.BIA_ANALYSIS: 2,
            BCMAssessmentStatus.RISK_ASSESSMENT: 3,
            BCMAssessmentStatus.STRATEGY_PLANNING: 4,
            BCMAssessmentStatus.PLAN_DEVELOPMENT: 5,
            BCMAssessmentStatus.TESTING: 6,
            BCMAssessmentStatus.COMPLETED: 7,
        }

        current_step = status_to_step.get(assessment.status, 1)

        # Update step statuses
        for step in steps:
            if step["step"] < current_step:
                step["status"] = "completed"
            elif step["step"] == current_step:
                step["status"] = "current"

        # Validation
        validation_errors = []
        can_proceed = True

        # Check if current step requirements are met
        if current_step == 1:
            processes = await self.list_processes(tenant_id)
            if len(processes) == 0:
                validation_errors.append("Please document at least one business process")
                can_proceed = False

        return {
            "assessment_id": assessment_id,
            "current_step": current_step,
            "step_name": steps[current_step - 1]["name"],
            "steps": steps,
            "is_complete": assessment.status == BCMAssessmentStatus.COMPLETED,
            "can_proceed": can_proceed,
            "validation_errors": validation_errors,
        }

    async def complete_assessment(
        self,
        assessment_id: str,
        tenant_id: str
    ) -> Optional[BCMAssessment]:
        """Mark an assessment as complete."""
        assessment = await self.get_assessment(assessment_id, tenant_id)
        if not assessment:
            return None

        # Recalculate scores before completing
        await self.recalculate_assessment_scores(assessment_id, tenant_id)

        assessment.status = BCMAssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()
        assessment.updated_at = datetime.utcnow()

        return assessment
