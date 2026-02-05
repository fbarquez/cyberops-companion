"""
BCM Seeder Script.

Seeds the database with BCM template data for demonstration and testing.
This script should be run after the database migrations.

Usage:
    python -m src.db.seed_bcm
"""
import asyncio
import json
import os
from datetime import datetime, date, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session
from src.models.bcm import (
    BCMProcess, BCMBIA, BCMRiskScenario, BCMStrategy,
    BCMEmergencyPlan, BCMContact, BCMExercise, BCMAssessment,
    BCMProcessCriticality, BCMProcessStatus, BCMBIAStatus,
    BCMScenarioCategory, BCMLikelihood, BCMImpact, BCMScenarioStatus,
    BCMStrategyType, BCMStrategyStatus, BCMPlanType, BCMPlanStatus,
    BCMContactType, BCMContactAvailability, BCMExerciseType, BCMExerciseStatus,
    BCMAssessmentStatus, BCMControlEffectiveness
)
from src.models.organization import Organization


# Likelihood/Impact mappings
LIKELIHOOD_MAP = {
    "rare": BCMLikelihood.RARE,
    "unlikely": BCMLikelihood.UNLIKELY,
    "possible": BCMLikelihood.POSSIBLE,
    "likely": BCMLikelihood.LIKELY,
    "almost_certain": BCMLikelihood.ALMOST_CERTAIN,
}

IMPACT_MAP = {
    "negligible": BCMImpact.NEGLIGIBLE,
    "minor": BCMImpact.MINOR,
    "moderate": BCMImpact.MODERATE,
    "major": BCMImpact.MAJOR,
    "catastrophic": BCMImpact.CATASTROPHIC,
}

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


async def get_first_tenant(db: AsyncSession) -> str | None:
    """Get the first available tenant ID for demo data."""
    result = await db.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    return org.id if org else None


async def seed_demo_processes(db: AsyncSession, tenant_id: str) -> list[BCMProcess]:
    """Seed demo business processes."""
    demo_processes = [
        {
            "process_id": "PROC-001",
            "name": "Payment Processing",
            "description": "Core payment processing system handling all customer transactions",
            "owner": "Finance Director",
            "department": "Finance",
            "criticality": BCMProcessCriticality.CRITICAL,
            "internal_dependencies": [],
            "external_dependencies": ["Payment Gateway Provider", "Bank API"],
            "it_systems": ["payment-server-01", "payment-db-01"],
            "key_personnel": ["John Smith", "Jane Doe"],
        },
        {
            "process_id": "PROC-002",
            "name": "Customer Service Portal",
            "description": "Customer-facing portal for account management and support",
            "owner": "Customer Service Manager",
            "department": "Customer Service",
            "criticality": BCMProcessCriticality.HIGH,
            "internal_dependencies": ["PROC-001"],
            "external_dependencies": ["CDN Provider"],
            "it_systems": ["web-server-01", "web-server-02"],
            "key_personnel": ["Alice Johnson"],
        },
        {
            "process_id": "PROC-003",
            "name": "Email System",
            "description": "Corporate email and calendar system",
            "owner": "IT Manager",
            "department": "IT",
            "criticality": BCMProcessCriticality.HIGH,
            "internal_dependencies": [],
            "external_dependencies": ["Microsoft 365"],
            "it_systems": [],
            "key_personnel": ["Bob Wilson"],
        },
        {
            "process_id": "PROC-004",
            "name": "HR Management System",
            "description": "Employee management, payroll, and benefits administration",
            "owner": "HR Director",
            "department": "Human Resources",
            "criticality": BCMProcessCriticality.MEDIUM,
            "internal_dependencies": [],
            "external_dependencies": ["Payroll Provider"],
            "it_systems": ["hr-server-01"],
            "key_personnel": ["Carol White"],
        },
        {
            "process_id": "PROC-005",
            "name": "Inventory Management",
            "description": "Warehouse and inventory tracking system",
            "owner": "Operations Manager",
            "department": "Operations",
            "criticality": BCMProcessCriticality.MEDIUM,
            "internal_dependencies": ["PROC-001"],
            "external_dependencies": ["Logistics Partners"],
            "it_systems": ["inventory-db-01"],
            "key_personnel": ["David Brown"],
        },
    ]

    processes = []
    for p_data in demo_processes:
        process = BCMProcess(
            id=str(uuid4()),
            tenant_id=tenant_id,
            status=BCMProcessStatus.ACTIVE,
            created_at=datetime.utcnow(),
            **p_data
        )
        db.add(process)
        processes.append(process)

    await db.flush()
    print(f"  Created {len(processes)} demo business processes")
    return processes


async def seed_demo_bia(db: AsyncSession, tenant_id: str, processes: list[BCMProcess]) -> list[BCMBIA]:
    """Seed demo BIA data for processes."""
    bia_templates = {
        "PROC-001": {  # Payment Processing - Critical
            "rto_hours": 4,
            "rpo_hours": 1,
            "mtpd_hours": 24,
            "financial_impact": 5,
            "operational_impact": 5,
            "reputational_impact": 5,
            "legal_impact": 4,
            "safety_impact": 1,
            "financial_justification": "Direct revenue loss estimated at $50,000 per hour of downtime",
            "minimum_staff": 5,
            "critical_equipment": ["Payment terminals", "Secure servers"],
            "critical_data": ["Transaction logs", "Customer payment data"],
            "status": BCMBIAStatus.APPROVED,
        },
        "PROC-002": {  # Customer Portal - High
            "rto_hours": 8,
            "rpo_hours": 4,
            "mtpd_hours": 48,
            "financial_impact": 3,
            "operational_impact": 4,
            "reputational_impact": 4,
            "legal_impact": 2,
            "safety_impact": 1,
            "minimum_staff": 3,
            "critical_equipment": ["Web servers"],
            "critical_data": ["Customer accounts"],
            "status": BCMBIAStatus.COMPLETED,
        },
        "PROC-003": {  # Email - High
            "rto_hours": 8,
            "rpo_hours": 2,
            "mtpd_hours": 48,
            "financial_impact": 2,
            "operational_impact": 4,
            "reputational_impact": 2,
            "legal_impact": 2,
            "safety_impact": 1,
            "minimum_staff": 2,
            "critical_equipment": [],
            "critical_data": ["Email archives"],
            "status": BCMBIAStatus.COMPLETED,
        },
    }

    bias = []
    for process in processes:
        if process.process_id in bia_templates:
            template = bia_templates[process.process_id]
            bia = BCMBIA(
                id=str(uuid4()),
                tenant_id=tenant_id,
                process_id=process.id,
                analysis_date=datetime.utcnow(),
                analyst="BCM Coordinator",
                next_review_date=date.today() + timedelta(days=365),
                created_at=datetime.utcnow(),
                **template
            )
            db.add(bia)
            bias.append(bia)

    await db.flush()
    print(f"  Created {len(bias)} demo BIA records")
    return bias


async def seed_scenarios_from_templates(db: AsyncSession, tenant_id: str, templates_file: str) -> list[BCMRiskScenario]:
    """Seed risk scenarios from template file."""
    with open(templates_file, 'r') as f:
        data = json.load(f)

    category_map = {
        "cyber_attack": BCMScenarioCategory.CYBER_ATTACK,
        "technical_failure": BCMScenarioCategory.TECHNICAL_FAILURE,
        "human_error": BCMScenarioCategory.HUMAN_ERROR,
        "supply_chain": BCMScenarioCategory.SUPPLY_CHAIN,
        "infrastructure": BCMScenarioCategory.INFRASTRUCTURE,
        "pandemic": BCMScenarioCategory.PANDEMIC,
        "natural_disaster": BCMScenarioCategory.NATURAL_DISASTER,
        "other": BCMScenarioCategory.OTHER,
    }

    scenarios = []
    for i, template in enumerate(data.get("scenario_templates", []), 1):
        likelihood = LIKELIHOOD_MAP.get(template.get("typical_likelihood", "possible"), BCMLikelihood.POSSIBLE)
        impact = IMPACT_MAP.get(template.get("typical_impact", "moderate"), BCMImpact.MODERATE)
        risk_score = LIKELIHOOD_VALUES[likelihood] * IMPACT_VALUES[impact]

        scenario = BCMRiskScenario(
            id=str(uuid4()),
            tenant_id=tenant_id,
            scenario_id=f"SCEN-{i:03d}",
            name=template["name"],
            description=template["description"],
            category=category_map.get(template["category"], BCMScenarioCategory.OTHER),
            likelihood=likelihood,
            impact=impact,
            risk_score=risk_score,
            existing_controls=template.get("suggested_controls"),
            control_effectiveness=BCMControlEffectiveness.MEDIUM,
            status=BCMScenarioStatus.ASSESSED,
            created_at=datetime.utcnow(),
            assessed_at=datetime.utcnow(),
        )
        db.add(scenario)
        scenarios.append(scenario)

    await db.flush()
    print(f"  Created {len(scenarios)} risk scenarios from templates")
    return scenarios


async def seed_plans_from_templates(db: AsyncSession, tenant_id: str, templates_file: str) -> list[BCMEmergencyPlan]:
    """Seed emergency plans from template file."""
    with open(templates_file, 'r') as f:
        data = json.load(f)

    plan_type_map = {
        "it_disaster_recovery": BCMPlanType.IT_DISASTER_RECOVERY,
        "communication": BCMPlanType.COMMUNICATION,
        "business_recovery": BCMPlanType.BUSINESS_RECOVERY,
        "crisis_management": BCMPlanType.CRISIS_MANAGEMENT,
        "emergency_response": BCMPlanType.EMERGENCY_RESPONSE,
        "evacuation": BCMPlanType.EVACUATION,
    }

    plans = []
    for i, template in enumerate(data.get("plan_templates", []), 1):
        plan = BCMEmergencyPlan(
            id=str(uuid4()),
            tenant_id=tenant_id,
            plan_id=f"PLAN-{i:03d}",
            name=template["name"],
            plan_type=plan_type_map.get(template["plan_type"], BCMPlanType.BUSINESS_RECOVERY),
            scope_description=template["scope_description"],
            response_phases=template.get("response_phases", []),
            activation_checklist=template.get("activation_checklist", []),
            recovery_checklist=template.get("recovery_checklist", []),
            roles_responsibilities=template.get("roles_responsibilities", []),
            version="1.0",
            effective_date=date.today(),
            review_date=date.today() + timedelta(days=365),
            status=BCMPlanStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )
        db.add(plan)
        plans.append(plan)

    await db.flush()
    print(f"  Created {len(plans)} emergency plans from templates")
    return plans


async def seed_demo_contacts(db: AsyncSession, tenant_id: str) -> list[BCMContact]:
    """Seed demo emergency contacts."""
    contacts_data = [
        {
            "name": "Crisis Manager",
            "role": "Crisis Management Lead",
            "department": "Executive",
            "phone_primary": "+1-555-0100",
            "phone_secondary": "+1-555-0101",
            "email": "crisis.manager@example.com",
            "availability": BCMContactAvailability.TWENTY_FOUR_SEVEN,
            "contact_type": BCMContactType.INTERNAL,
            "priority": 1,
        },
        {
            "name": "IT Director",
            "role": "IT Recovery Lead",
            "department": "IT",
            "phone_primary": "+1-555-0110",
            "email": "it.director@example.com",
            "availability": BCMContactAvailability.TWENTY_FOUR_SEVEN,
            "contact_type": BCMContactType.INTERNAL,
            "priority": 2,
        },
        {
            "name": "Security Operations Center",
            "role": "24/7 Monitoring",
            "department": "Security",
            "phone_primary": "+1-555-0120",
            "email": "soc@example.com",
            "availability": BCMContactAvailability.TWENTY_FOUR_SEVEN,
            "contact_type": BCMContactType.INTERNAL,
            "priority": 3,
        },
        {
            "name": "External IT Support",
            "role": "Managed Services Provider",
            "phone_primary": "+1-555-0200",
            "email": "support@msp-example.com",
            "availability": BCMContactAvailability.TWENTY_FOUR_SEVEN,
            "contact_type": BCMContactType.VENDOR,
            "priority": 5,
        },
        {
            "name": "Insurance Provider",
            "role": "Business Insurance",
            "phone_primary": "+1-555-0300",
            "email": "claims@insurance-example.com",
            "availability": BCMContactAvailability.BUSINESS_HOURS,
            "contact_type": BCMContactType.EXTERNAL,
            "priority": 10,
        },
    ]

    contacts = []
    for c_data in contacts_data:
        contact = BCMContact(
            id=str(uuid4()),
            tenant_id=tenant_id,
            created_at=datetime.utcnow(),
            **c_data
        )
        db.add(contact)
        contacts.append(contact)

    await db.flush()
    print(f"  Created {len(contacts)} demo emergency contacts")
    return contacts


async def seed_demo_exercises(db: AsyncSession, tenant_id: str, scenarios: list, plans: list) -> list[BCMExercise]:
    """Seed demo exercises."""
    exercises_data = [
        {
            "exercise_id": "EX-2024-001",
            "name": "Annual DR Failover Test",
            "description": "Full technical test of disaster recovery site activation",
            "exercise_type": BCMExerciseType.PARALLEL_TEST,
            "objectives": [
                "Verify DR site readiness",
                "Test backup restoration",
                "Measure actual recovery times"
            ],
            "scope": "All critical IT systems and data",
            "participants": ["IT Team", "Infrastructure Team", "Database Team"],
            "planned_date": date.today() - timedelta(days=30),
            "planned_duration_hours": 8,
            "actual_date": date.today() - timedelta(days=30),
            "actual_duration_hours": 10,
            "status": BCMExerciseStatus.COMPLETED,
            "results_summary": "DR failover successful with RTO of 6 hours achieved. Minor issues with network configuration resolved during test.",
            "objectives_met": {"Verify DR site readiness": True, "Test backup restoration": True, "Measure actual recovery times": True},
            "issues_identified": ["Network configuration scripts need updating", "Documentation gap for database recovery"],
            "lessons_learned": "Need to conduct quarterly mini-tests of network failover",
        },
        {
            "exercise_id": "EX-2024-002",
            "name": "Ransomware Response Tabletop",
            "description": "Discussion-based exercise for ransomware incident response",
            "exercise_type": BCMExerciseType.TABLETOP,
            "objectives": [
                "Validate response procedures",
                "Test communication protocols",
                "Practice decision-making"
            ],
            "scope": "Cyber incident response team and key stakeholders",
            "participants": ["Security Team", "IT Team", "Legal", "Communications"],
            "planned_date": date.today() - timedelta(days=60),
            "planned_duration_hours": 3,
            "actual_date": date.today() - timedelta(days=60),
            "actual_duration_hours": 4,
            "status": BCMExerciseStatus.COMPLETED,
            "results_summary": "Team demonstrated good understanding of procedures. Identified need for clearer escalation criteria.",
            "objectives_met": {"Validate response procedures": True, "Test communication protocols": True, "Practice decision-making": True},
            "issues_identified": ["Escalation criteria need clarification", "Legal contact information outdated"],
        },
        {
            "exercise_id": "EX-2024-003",
            "name": "Q2 Business Continuity Walkthrough",
            "description": "Step-by-step review of business recovery procedures",
            "exercise_type": BCMExerciseType.WALKTHROUGH,
            "objectives": [
                "Review updated procedures",
                "Validate contact lists",
                "Identify training needs"
            ],
            "scope": "All business departments",
            "participants": ["Department Managers", "BC Coordinators"],
            "planned_date": date.today() + timedelta(days=30),
            "planned_duration_hours": 4,
            "status": BCMExerciseStatus.PLANNED,
        },
    ]

    exercises = []
    for i, ex_data in enumerate(exercises_data):
        # Link to scenario/plan if available
        scenario_id = scenarios[i % len(scenarios)].id if scenarios else None
        plan_id = plans[i % len(plans)].id if plans else None

        exercise = BCMExercise(
            id=str(uuid4()),
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            plan_id=plan_id,
            created_at=datetime.utcnow(),
            **ex_data
        )
        db.add(exercise)
        exercises.append(exercise)

    await db.flush()
    print(f"  Created {len(exercises)} demo exercises")
    return exercises


async def seed_bcm(db: AsyncSession, tenant_id: str = None):
    """Main seeding function for BCM data."""
    print("Starting BCM data seeding...")

    # Get tenant
    if not tenant_id:
        tenant_id = await get_first_tenant(db)
        if not tenant_id:
            print("Error: No tenant found. Please create an organization first.")
            return

    print(f"  Using tenant: {tenant_id}")

    # Get templates file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_file = os.path.join(script_dir, "data", "bcm_templates.json")

    if not os.path.exists(templates_file):
        print(f"Warning: Templates file not found at {templates_file}")
        print("  Skipping template-based seeding")
        templates_file = None

    # Seed data
    processes = await seed_demo_processes(db, tenant_id)
    await seed_demo_bia(db, tenant_id, processes)

    scenarios = []
    plans = []
    if templates_file:
        scenarios = await seed_scenarios_from_templates(db, tenant_id, templates_file)
        plans = await seed_plans_from_templates(db, tenant_id, templates_file)

    await seed_demo_contacts(db, tenant_id)
    await seed_demo_exercises(db, tenant_id, scenarios, plans)

    await db.commit()
    print("BCM data seeding completed successfully!")


async def main():
    """Run the seeder."""
    async with async_session() as db:
        await seed_bcm(db)


if __name__ == "__main__":
    asyncio.run(main())
