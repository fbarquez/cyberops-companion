"""
Onboarding Service

Business logic for the onboarding wizard including regulation detection,
baseline recommendations, and compliance plan generation.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from src.models.onboarding import (
    OrganizationProfile,
    CompliancePlanItem,
    IndustrySector,
    CompanySize,
    CountryCode,
    OnboardingStatus,
    REGULATION_RULES,
    BASELINE_RECOMMENDATIONS,
    get_industry_display_name,
    get_size_display_name,
)
from src.schemas.onboarding import (
    OrganizationProfileCreate,
    OrganizationProfileUpdate,
    SpecialStatusUpdate,
    RegulationApplicability,
    RegulationDetectionResponse,
    FrameworkRecommendation,
    BaselineRecommendationResponse,
    PlanItem,
    CompliancePlanResponse,
    OrganizationProfileResponse,
    WizardState,
)


class OnboardingService:
    """Service for onboarding wizard operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # PROFILE MANAGEMENT
    # =========================================================================

    async def create_profile(
        self,
        data: OrganizationProfileCreate,
        user_id: str,
        tenant_id: str,
    ) -> OrganizationProfile:
        """Create organization profile (Step 1)."""
        profile = OrganizationProfile(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            organization_name=data.organization_name,
            industry_sector=data.industry_sector,
            company_size=data.company_size,
            employee_count=data.employee_count,
            annual_revenue_eur=data.annual_revenue_eur,
            headquarters_country=data.headquarters_country,
            operates_in_eu=data.operates_in_eu,
            eu_member_states=[c.value for c in (data.eu_member_states or [])],
            onboarding_status=OnboardingStatus.IN_PROGRESS,
            current_step=1,
            created_by=user_id,
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_profile(self, tenant_id: str) -> Optional[OrganizationProfile]:
        """Get organization profile for tenant."""
        result = await self.db.execute(
            select(OrganizationProfile).where(
                OrganizationProfile.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        profile_id: str,
        data: OrganizationProfileUpdate,
        tenant_id: str,
    ) -> OrganizationProfile:
        """Update organization profile."""
        profile = await self._get_profile_by_id(profile_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)
        if "eu_member_states" in update_data and update_data["eu_member_states"]:
            update_data["eu_member_states"] = [c.value for c in update_data["eu_member_states"]]

        for key, value in update_data.items():
            setattr(profile, key, value)

        profile.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_special_status(
        self,
        profile_id: str,
        data: SpecialStatusUpdate,
        tenant_id: str,
    ) -> OrganizationProfile:
        """Update special regulatory status (Step 2)."""
        profile = await self._get_profile_by_id(profile_id, tenant_id)

        profile.is_kritis_operator = data.is_kritis_operator
        profile.kritis_sector = data.kritis_sector
        profile.is_bafin_regulated = data.is_bafin_regulated
        profile.is_essential_service = data.is_essential_service
        profile.is_important_entity = data.is_important_entity
        profile.supplies_to_oem = data.supplies_to_oem
        profile.current_step = max(profile.current_step, 2)
        profile.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def _get_profile_by_id(
        self,
        profile_id: str,
        tenant_id: str,
    ) -> OrganizationProfile:
        """Get profile by ID with tenant check."""
        result = await self.db.execute(
            select(OrganizationProfile).where(
                OrganizationProfile.id == profile_id,
                OrganizationProfile.tenant_id == tenant_id,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError("Profile not found")
        return profile

    # =========================================================================
    # REGULATION DETECTION
    # =========================================================================

    def detect_applicable_regulations(
        self,
        profile: OrganizationProfile,
    ) -> RegulationDetectionResponse:
        """Detect applicable regulations based on profile."""
        regulations = []

        for reg_id, reg_info in REGULATION_RULES.items():
            applies, reason, mandatory = self._check_regulation_applies(
                reg_id, reg_info, profile
            )

            regulations.append(RegulationApplicability(
                regulation_id=reg_id,
                name=reg_info["name"],
                name_de=reg_info["name_de"],
                applies=applies,
                reason=reason,
                mandatory=mandatory,
                deadline=reg_info.get("deadline"),
                authority=reg_info.get("authority", ""),
                user_confirmed=reg_id in (profile.applicable_regulations or []),
            ))

        # Sort by applies (True first) then by name
        regulations.sort(key=lambda r: (not r.applies, r.name))

        summary = {
            "mandatory": sum(1 for r in regulations if r.applies and r.mandatory),
            "recommended": sum(1 for r in regulations if r.applies and not r.mandatory),
            "not_applicable": sum(1 for r in regulations if not r.applies),
        }

        return RegulationDetectionResponse(regulations=regulations, summary=summary)

    def _check_regulation_applies(
        self,
        reg_id: str,
        reg_info: Dict[str, Any],
        profile: OrganizationProfile,
    ) -> Tuple[bool, str, bool]:
        """Check if a regulation applies to the profile.

        Returns: (applies, reason, mandatory)
        """
        applies = False
        reasons = []
        mandatory = False

        # Check sector applicability
        applies_to_sectors = reg_info.get("applies_to_sectors", [])
        if applies_to_sectors == "all":
            applies = True
            reasons.append("Applies to all sectors")
        elif profile.industry_sector in applies_to_sectors:
            applies = True
            reasons.append(f"Applies to {get_industry_display_name(profile.industry_sector)}")

        # Check country requirement
        requires_country = reg_info.get("requires_country", [])
        if requires_country:
            if profile.headquarters_country in requires_country:
                reasons.append(f"Headquartered in {profile.headquarters_country.value}")
            else:
                applies = False
                reasons = [f"Only applies to entities in {', '.join(c.value for c in requires_country)}"]

        # Check EU requirement
        if reg_info.get("requires_eu") and not profile.operates_in_eu:
            applies = False
            reasons = ["Only applies to EU entities"]

        # Check size requirement
        min_size = reg_info.get("min_size")
        if min_size and applies:
            size_order = [CompanySize.MICRO, CompanySize.SMALL, CompanySize.MEDIUM, CompanySize.LARGE]
            profile_size_idx = size_order.index(profile.company_size)
            min_size_idx = size_order.index(min_size)
            if profile_size_idx < min_size_idx:
                applies = False
                reasons = [f"Generally applies to {get_size_display_name(min_size)} and larger"]

        # Check special conditions
        special_conditions = reg_info.get("special_conditions", [])
        for condition in special_conditions:
            if condition == "is_kritis_operator" and profile.is_kritis_operator:
                applies = True
                mandatory = True
                reasons.append("KRITIS operator status")
            elif condition == "is_bafin_regulated" and profile.is_bafin_regulated:
                applies = True
                mandatory = True
                reasons.append("BaFin regulated entity")
            elif condition == "is_essential_service" and profile.is_essential_service:
                applies = True
                mandatory = True
                reasons.append("Essential service provider (NIS2)")
            elif condition == "is_important_entity" and profile.is_important_entity:
                applies = True
                reasons.append("Important entity (NIS2)")
            elif condition == "supplies_to_oem" and profile.supplies_to_oem:
                applies = True
                reasons.append("Supplies to automotive OEMs")
            elif condition == "is_financial_entity":
                if profile.industry_sector in [
                    IndustrySector.BANKING,
                    IndustrySector.INSURANCE,
                    IndustrySector.INVESTMENT,
                    IndustrySector.PAYMENT_SERVICES,
                    IndustrySector.CRYPTO_ASSETS,
                ]:
                    mandatory = True

        reason = "; ".join(reasons) if reasons else "Does not apply to your profile"
        return applies, reason, mandatory

    async def confirm_regulations(
        self,
        profile_id: str,
        confirmed_regulations: List[str],
        tenant_id: str,
    ) -> OrganizationProfile:
        """Confirm applicable regulations (Step 2)."""
        profile = await self._get_profile_by_id(profile_id, tenant_id)
        profile.applicable_regulations = confirmed_regulations
        profile.current_step = max(profile.current_step, 2)
        profile.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    # =========================================================================
    # BASELINE RECOMMENDATIONS
    # =========================================================================

    def get_baseline_recommendations(
        self,
        profile: OrganizationProfile,
    ) -> BaselineRecommendationResponse:
        """Get framework recommendations based on profile."""
        recommendations = []
        controls_focus = []

        # Find matching baseline category
        baseline_key = self._get_baseline_category(profile)
        baseline = BASELINE_RECOMMENDATIONS.get(baseline_key, BASELINE_RECOMMENDATIONS["general"])

        controls_focus = baseline["controls_focus"]

        # Build framework recommendations
        for fw in baseline["frameworks"]:
            fw_details = self._get_framework_details(fw["id"], profile)
            recommendations.append(FrameworkRecommendation(
                id=fw["id"],
                name=fw["name"],
                description=fw_details["description"],
                priority=fw["priority"],
                reason=fw["reason"],
                controls_count=fw_details["controls_count"],
                maps_to_regulations=fw_details["maps_to"],
                estimated_effort_days=fw_details["effort_days"],
                recommended=True,
            ))

        # Calculate totals
        total_controls = sum(r.controls_count for r in recommendations)
        total_effort = sum(r.estimated_effort_days for r in recommendations)
        effort_months = max(1, total_effort // 20)  # ~20 working days per month

        return BaselineRecommendationResponse(
            recommendations=recommendations,
            controls_focus=controls_focus,
            total_controls=total_controls,
            estimated_effort_months=effort_months,
        )

    def _get_baseline_category(self, profile: OrganizationProfile) -> str:
        """Determine baseline category based on profile."""
        financial_sectors = [
            IndustrySector.BANKING,
            IndustrySector.INSURANCE,
            IndustrySector.INVESTMENT,
            IndustrySector.PAYMENT_SERVICES,
            IndustrySector.CRYPTO_ASSETS,
        ]
        critical_sectors = [
            IndustrySector.ENERGY,
            IndustrySector.WATER,
            IndustrySector.HEALTHCARE,
            IndustrySector.TRANSPORT,
            IndustrySector.DIGITAL_INFRASTRUCTURE,
        ]
        automotive_sectors = [
            IndustrySector.AUTOMOTIVE,
            IndustrySector.AUTOMOTIVE_SUPPLIER,
        ]

        if profile.industry_sector in financial_sectors:
            return "financial"
        elif profile.industry_sector in critical_sectors or profile.is_kritis_operator:
            return "critical_infrastructure"
        elif profile.industry_sector in automotive_sectors or profile.supplies_to_oem:
            return "automotive"
        else:
            return "general"

    def _get_framework_details(
        self,
        framework_id: str,
        profile: OrganizationProfile,
    ) -> Dict[str, Any]:
        """Get framework details."""
        frameworks = {
            "iso27001": {
                "description": "International standard for information security management systems (ISMS)",
                "controls_count": 93,
                "maps_to": ["nis2", "dora", "tisax", "gdpr"],
                "effort_days": 60,
            },
            "bsi": {
                "description": "German BSI IT-Grundschutz methodology with comprehensive building blocks",
                "controls_count": 200,  # Approximate
                "maps_to": ["kritis", "nis2"],
                "effort_days": 90,
            },
            "dora": {
                "description": "DORA 5-pillar framework for digital operational resilience",
                "controls_count": 28,
                "maps_to": ["dora"],
                "effort_days": 45,
            },
            "tisax": {
                "description": "VDA ISA catalog for automotive information security",
                "controls_count": 70,  # Approximate
                "maps_to": ["tisax"],
                "effort_days": 40,
            },
            "nist": {
                "description": "NIST Cybersecurity Framework 2.0",
                "controls_count": 106,
                "maps_to": ["nis2"],
                "effort_days": 50,
            },
        }
        return frameworks.get(framework_id, {
            "description": "Security framework",
            "controls_count": 50,
            "maps_to": [],
            "effort_days": 30,
        })

    async def select_frameworks(
        self,
        profile_id: str,
        selected_frameworks: List[str],
        tenant_id: str,
    ) -> OrganizationProfile:
        """Save selected frameworks (Step 3)."""
        profile = await self._get_profile_by_id(profile_id, tenant_id)
        profile.selected_frameworks = selected_frameworks
        profile.current_step = max(profile.current_step, 3)
        profile.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    # =========================================================================
    # COMPLIANCE PLAN GENERATION
    # =========================================================================

    async def generate_compliance_plan(
        self,
        profile_id: str,
        tenant_id: str,
    ) -> CompliancePlanResponse:
        """Generate compliance plan based on profile (Step 4)."""
        profile = await self._get_profile_by_id(profile_id, tenant_id)

        # Delete existing plan items
        await self.db.execute(
            delete(CompliancePlanItem).where(
                CompliancePlanItem.profile_id == profile_id
            )
        )

        # Generate plan items
        plan_items = self._generate_plan_items(profile)

        # Save to database
        for item_data in plan_items:
            item = CompliancePlanItem(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                tenant_id=tenant_id,
                **item_data
            )
            self.db.add(item)

        profile.current_step = max(profile.current_step, 4)
        await self.db.commit()

        # Fetch saved items
        result = await self.db.execute(
            select(CompliancePlanItem).where(
                CompliancePlanItem.profile_id == profile_id
            ).order_by(CompliancePlanItem.priority, CompliancePlanItem.category)
        )
        items = result.scalars().all()

        # Group by category
        items_by_category = {}
        for item in items:
            cat = item.category
            if cat not in items_by_category:
                items_by_category[cat] = []
            items_by_category[cat].append(self._item_to_schema(item))

        # Calculate summary
        summary = {
            "total_items": len(items),
            "by_priority": {
                "critical": sum(1 for i in items if i.priority == 1),
                "high": sum(1 for i in items if i.priority == 2),
                "medium": sum(1 for i in items if i.priority == 3),
                "low": sum(1 for i in items if i.priority == 4),
            },
            "estimated_effort_days": sum(i.estimated_effort_days or 0 for i in items),
        }

        # Calculate timeline milestones
        timeline = self._generate_timeline(items, profile)

        return CompliancePlanResponse(
            profile_id=profile_id,
            organization_name=profile.organization_name,
            generated_at=datetime.utcnow(),
            regulations=profile.applicable_regulations or [],
            frameworks=profile.selected_frameworks or [],
            items_by_category=items_by_category,
            summary=summary,
            timeline=timeline,
        )

    def _generate_plan_items(self, profile: OrganizationProfile) -> List[Dict[str, Any]]:
        """Generate plan items based on profile."""
        items = []
        base_date = datetime.utcnow()

        # Phase 1: Foundation (Month 1-2)
        foundation_items = [
            {
                "category": "Governance",
                "title": "Establish Information Security Policy",
                "description": "Create and approve the overarching information security policy",
                "framework_id": "iso27001",
                "control_ref": "A.5.1",
                "owner_role": "CISO",
                "priority": 1,
                "due_date": base_date + timedelta(days=30),
                "estimated_effort_days": 5,
                "evidence_required": True,
                "evidence_type": "Policy Document",
            },
            {
                "category": "Governance",
                "title": "Define Roles and Responsibilities",
                "description": "Document security roles, responsibilities, and reporting lines",
                "framework_id": "iso27001",
                "control_ref": "A.5.2",
                "owner_role": "CISO",
                "priority": 1,
                "due_date": base_date + timedelta(days=30),
                "estimated_effort_days": 3,
                "evidence_required": True,
                "evidence_type": "RACI Matrix",
            },
            {
                "category": "Risk Management",
                "title": "Conduct Initial Risk Assessment",
                "description": "Identify and assess information security risks",
                "framework_id": "iso27001",
                "control_ref": "A.5.7",
                "owner_role": "Risk Manager",
                "priority": 1,
                "due_date": base_date + timedelta(days=45),
                "estimated_effort_days": 10,
                "evidence_required": True,
                "evidence_type": "Risk Register",
            },
            {
                "category": "Asset Management",
                "title": "Create Asset Inventory",
                "description": "Inventory all information assets and assign owners",
                "framework_id": "iso27001",
                "control_ref": "A.5.9",
                "owner_role": "IT Manager",
                "priority": 1,
                "due_date": base_date + timedelta(days=45),
                "estimated_effort_days": 8,
                "evidence_required": True,
                "evidence_type": "Asset Register",
            },
        ]
        items.extend(foundation_items)

        # Phase 2: Core Controls (Month 2-4)
        core_items = [
            {
                "category": "Access Control",
                "title": "Implement Access Control Policy",
                "description": "Define and implement access control rules and procedures",
                "framework_id": "iso27001",
                "control_ref": "A.5.15",
                "owner_role": "IT Manager",
                "priority": 2,
                "due_date": base_date + timedelta(days=60),
                "estimated_effort_days": 5,
                "evidence_required": True,
                "evidence_type": "Access Control Policy",
            },
            {
                "category": "Access Control",
                "title": "Implement Multi-Factor Authentication",
                "description": "Deploy MFA for privileged and remote access",
                "framework_id": "iso27001",
                "control_ref": "A.5.17",
                "owner_role": "IT Manager",
                "priority": 2,
                "due_date": base_date + timedelta(days=75),
                "estimated_effort_days": 10,
                "evidence_required": True,
                "evidence_type": "MFA Configuration",
            },
            {
                "category": "Incident Management",
                "title": "Establish Incident Response Process",
                "description": "Define incident classification, response procedures, and escalation",
                "framework_id": "iso27001",
                "control_ref": "A.5.24",
                "owner_role": "CISO",
                "priority": 2,
                "due_date": base_date + timedelta(days=60),
                "estimated_effort_days": 5,
                "evidence_required": True,
                "evidence_type": "Incident Response Plan",
            },
            {
                "category": "Business Continuity",
                "title": "Conduct Business Impact Analysis",
                "description": "Identify critical processes and their recovery requirements",
                "framework_id": "iso27001",
                "control_ref": "A.5.29",
                "owner_role": "BCM Manager",
                "priority": 2,
                "due_date": base_date + timedelta(days=75),
                "estimated_effort_days": 8,
                "evidence_required": True,
                "evidence_type": "BIA Report",
            },
        ]
        items.extend(core_items)

        # Add regulation-specific items
        if "dora" in (profile.applicable_regulations or []):
            dora_items = [
                {
                    "category": "ICT Risk Management",
                    "title": "Establish ICT Risk Management Framework",
                    "description": "DORA Art. 5-6: Management body oversight of ICT risks",
                    "regulation_id": "dora",
                    "control_ref": "DORA Art.5",
                    "owner_role": "CISO",
                    "priority": 1,
                    "due_date": base_date + timedelta(days=45),
                    "estimated_effort_days": 8,
                    "evidence_required": True,
                    "evidence_type": "ICT Risk Framework",
                },
                {
                    "category": "Third-Party Risk",
                    "title": "Create ICT Third-Party Register",
                    "description": "DORA Art. 28-29: Register of all ICT service providers",
                    "regulation_id": "dora",
                    "control_ref": "DORA Art.28",
                    "owner_role": "Vendor Manager",
                    "priority": 1,
                    "due_date": base_date + timedelta(days=60),
                    "estimated_effort_days": 10,
                    "evidence_required": True,
                    "evidence_type": "ICT Provider Register",
                },
                {
                    "category": "Incident Reporting",
                    "title": "Implement Major Incident Reporting Process",
                    "description": "DORA Art. 19: Process to report major ICT incidents to authorities",
                    "regulation_id": "dora",
                    "control_ref": "DORA Art.19",
                    "owner_role": "CISO",
                    "priority": 1,
                    "due_date": base_date + timedelta(days=45),
                    "estimated_effort_days": 5,
                    "evidence_required": True,
                    "evidence_type": "Incident Reporting Procedure",
                },
            ]
            items.extend(dora_items)

        if "nis2" in (profile.applicable_regulations or []):
            nis2_items = [
                {
                    "category": "Governance",
                    "title": "Ensure Management Body Accountability",
                    "description": "NIS2 Art. 20: Management body training and oversight",
                    "regulation_id": "nis2",
                    "control_ref": "NIS2 Art.20",
                    "owner_role": "CISO",
                    "priority": 1,
                    "due_date": base_date + timedelta(days=30),
                    "estimated_effort_days": 3,
                    "evidence_required": True,
                    "evidence_type": "Management Training Records",
                },
                {
                    "category": "Supply Chain",
                    "title": "Implement Supply Chain Security Measures",
                    "description": "NIS2 Art. 21: Security in supplier relationships",
                    "regulation_id": "nis2",
                    "control_ref": "NIS2 Art.21",
                    "owner_role": "Procurement",
                    "priority": 2,
                    "due_date": base_date + timedelta(days=90),
                    "estimated_effort_days": 15,
                    "evidence_required": True,
                    "evidence_type": "Supplier Security Requirements",
                },
            ]
            items.extend(nis2_items)

        if "kritis" in (profile.applicable_regulations or []) or profile.is_kritis_operator:
            kritis_items = [
                {
                    "category": "KRITIS Compliance",
                    "title": "Register with BSI as KRITIS Operator",
                    "description": "Complete BSI registration and designate contact person",
                    "regulation_id": "kritis",
                    "control_ref": "§8b BSIG",
                    "owner_role": "CISO",
                    "priority": 1,
                    "due_date": base_date + timedelta(days=14),
                    "estimated_effort_days": 2,
                    "evidence_required": True,
                    "evidence_type": "BSI Registration",
                },
                {
                    "category": "KRITIS Compliance",
                    "title": "Prepare for KRITIS Audit (§8a)",
                    "description": "Prepare documentation for biennial KRITIS audit",
                    "regulation_id": "kritis",
                    "control_ref": "§8a BSIG",
                    "owner_role": "CISO",
                    "priority": 2,
                    "due_date": base_date + timedelta(days=180),
                    "estimated_effort_days": 30,
                    "evidence_required": True,
                    "evidence_type": "Audit Documentation",
                },
            ]
            items.extend(kritis_items)

        return items

    def _item_to_schema(self, item: CompliancePlanItem) -> PlanItem:
        """Convert database model to schema."""
        priority_labels = {1: "Critical", 2: "High", 3: "Medium", 4: "Low"}
        return PlanItem(
            id=item.id,
            category=item.category,
            title=item.title,
            description=item.description,
            regulation_id=item.regulation_id,
            regulation_name=REGULATION_RULES.get(item.regulation_id, {}).get("name") if item.regulation_id else None,
            framework_id=item.framework_id,
            framework_name=self._get_framework_name(item.framework_id) if item.framework_id else None,
            control_ref=item.control_ref,
            owner_role=item.owner_role,
            owner_id=item.owner_id,
            owner_name=None,  # Would need user lookup
            priority=item.priority,
            priority_label=priority_labels.get(item.priority, "Medium"),
            due_date=item.due_date,
            estimated_effort_days=item.estimated_effort_days,
            status=item.status,
            evidence_required=item.evidence_required,
            evidence_type=item.evidence_type,
        )

    def _get_framework_name(self, framework_id: str) -> str:
        """Get framework display name."""
        names = {
            "iso27001": "ISO 27001:2022",
            "bsi": "BSI IT-Grundschutz",
            "dora": "DORA",
            "tisax": "TISAX",
            "nist": "NIST CSF",
        }
        return names.get(framework_id, framework_id)

    def _generate_timeline(
        self,
        items: List[CompliancePlanItem],
        profile: OrganizationProfile,
    ) -> Dict[str, Any]:
        """Generate timeline milestones."""
        base_date = datetime.utcnow()
        milestones = []

        # Phase milestones
        milestones.append({
            "name": "Phase 1: Foundation",
            "date": (base_date + timedelta(days=45)).isoformat(),
            "items_count": sum(1 for i in items if i.priority == 1),
        })
        milestones.append({
            "name": "Phase 2: Core Controls",
            "date": (base_date + timedelta(days=90)).isoformat(),
            "items_count": sum(1 for i in items if i.priority == 2),
        })
        milestones.append({
            "name": "Phase 3: Full Implementation",
            "date": (base_date + timedelta(days=180)).isoformat(),
            "items_count": sum(1 for i in items if i.priority >= 3),
        })

        # Regulatory deadlines
        for reg_id in (profile.applicable_regulations or []):
            reg_info = REGULATION_RULES.get(reg_id, {})
            if reg_info.get("deadline"):
                milestones.append({
                    "name": f"{reg_info['name']} Deadline",
                    "date": reg_info["deadline"],
                    "type": "regulatory",
                })

        return {
            "start_date": base_date.isoformat(),
            "milestones": milestones,
        }

    # =========================================================================
    # COMPLETE ONBOARDING
    # =========================================================================

    async def complete_onboarding(
        self,
        profile_id: str,
        tenant_id: str,
        create_assessments: bool = True,
    ) -> Dict[str, Any]:
        """Complete onboarding and optionally create initial assessments."""
        profile = await self._get_profile_by_id(profile_id, tenant_id)

        profile.onboarding_status = OnboardingStatus.COMPLETED
        profile.onboarding_completed_at = datetime.utcnow()
        profile.current_step = 5

        created_assessments = []

        # TODO: Create initial assessments for selected frameworks
        # This would integrate with ISO27001, NIS2, DORA services

        await self.db.commit()

        next_steps = [
            "Review and customize your compliance plan",
            "Assign owners to plan items",
            "Begin implementing Phase 1 (Foundation) controls",
            "Schedule initial risk assessment workshop",
        ]

        if "dora" in (profile.applicable_regulations or []):
            next_steps.append("Start DORA assessment wizard")
        if "nis2" in (profile.applicable_regulations or []):
            next_steps.append("Complete NIS2 scope assessment")

        return {
            "profile_id": profile_id,
            "organization_name": profile.organization_name,
            "applicable_regulations": profile.applicable_regulations or [],
            "selected_frameworks": profile.selected_frameworks or [],
            "plan_items_count": await self._count_plan_items(profile_id),
            "created_assessments": created_assessments,
            "next_steps": next_steps,
            "dashboard_url": "/compliance",
        }

    async def _count_plan_items(self, profile_id: str) -> int:
        """Count plan items for profile."""
        result = await self.db.execute(
            select(CompliancePlanItem).where(
                CompliancePlanItem.profile_id == profile_id
            )
        )
        return len(result.scalars().all())

    # =========================================================================
    # WIZARD STATE
    # =========================================================================

    async def get_wizard_state(self, tenant_id: str) -> WizardState:
        """Get current wizard state."""
        profile = await self.get_profile(tenant_id)

        steps = [
            {"id": 1, "name": "Organization Profile", "status": "pending"},
            {"id": 2, "name": "Regulations", "status": "pending"},
            {"id": 3, "name": "Frameworks", "status": "pending"},
            {"id": 4, "name": "Compliance Plan", "status": "pending"},
            {"id": 5, "name": "Complete", "status": "pending"},
        ]

        current_step = 1
        can_proceed = False

        if profile:
            current_step = profile.current_step
            for i, step in enumerate(steps):
                if i + 1 < current_step:
                    step["status"] = "completed"
                elif i + 1 == current_step:
                    step["status"] = "current"
            can_proceed = current_step < 5

        return WizardState(
            current_step=current_step,
            total_steps=5,
            steps=steps,
            can_proceed=can_proceed,
            profile=self._profile_to_response(profile) if profile else None,
        )

    def _profile_to_response(self, profile: OrganizationProfile) -> OrganizationProfileResponse:
        """Convert profile to response schema."""
        country_names = {
            CountryCode.DE: "Germany",
            CountryCode.AT: "Austria",
            CountryCode.CH: "Switzerland",
            # Add more as needed
        }

        return OrganizationProfileResponse(
            id=profile.id,
            tenant_id=profile.tenant_id,
            organization_name=profile.organization_name,
            industry_sector=profile.industry_sector,
            industry_sector_name=get_industry_display_name(profile.industry_sector),
            company_size=profile.company_size,
            company_size_name=get_size_display_name(profile.company_size),
            employee_count=profile.employee_count,
            annual_revenue_eur=profile.annual_revenue_eur,
            headquarters_country=profile.headquarters_country,
            headquarters_country_name=country_names.get(profile.headquarters_country, profile.headquarters_country.value),
            operates_in_eu=profile.operates_in_eu,
            eu_member_states=profile.eu_member_states or [],
            is_kritis_operator=profile.is_kritis_operator,
            kritis_sector=profile.kritis_sector,
            is_bafin_regulated=profile.is_bafin_regulated,
            is_essential_service=profile.is_essential_service,
            is_important_entity=profile.is_important_entity,
            supplies_to_oem=profile.supplies_to_oem,
            applicable_regulations=profile.applicable_regulations or [],
            selected_frameworks=profile.selected_frameworks or [],
            onboarding_status=profile.onboarding_status,
            onboarding_completed_at=profile.onboarding_completed_at,
            current_step=profile.current_step,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
