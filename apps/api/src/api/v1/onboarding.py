"""
Onboarding API Endpoints

API endpoints for the onboarding wizard.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_current_user, get_db
from src.models.user import User
from src.models.onboarding import (
    IndustrySector,
    CompanySize,
    CountryCode,
    REGULATION_RULES,
    get_industry_display_name,
    get_size_display_name,
)
from src.schemas.onboarding import (
    OrganizationProfileCreate,
    OrganizationProfileUpdate,
    OrganizationProfileResponse,
    SpecialStatusUpdate,
    RegulationDetectionResponse,
    RegulationConfirmation,
    BaselineRecommendationResponse,
    FrameworkSelection,
    CompliancePlanResponse,
    OnboardingComplete,
    OnboardingCompletionResponse,
    WizardState,
    IndustryInfo,
    RegulationInfo,
)
from src.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# =============================================================================
# REFERENCE DATA
# =============================================================================

@router.get("/industries", response_model=List[IndustryInfo])
async def list_industries():
    """List available industry sectors."""
    categories = {
        "financial": [
            IndustrySector.BANKING,
            IndustrySector.INSURANCE,
            IndustrySector.INVESTMENT,
            IndustrySector.PAYMENT_SERVICES,
            IndustrySector.CRYPTO_ASSETS,
        ],
        "critical_infrastructure": [
            IndustrySector.ENERGY,
            IndustrySector.WATER,
            IndustrySector.FOOD,
            IndustrySector.HEALTHCARE,
            IndustrySector.TRANSPORT,
            IndustrySector.DIGITAL_INFRASTRUCTURE,
            IndustrySector.ICT_SERVICES,
            IndustrySector.SPACE,
            IndustrySector.POSTAL,
            IndustrySector.WASTE_MANAGEMENT,
            IndustrySector.CHEMICALS,
            IndustrySector.MANUFACTURING,
        ],
        "automotive": [
            IndustrySector.AUTOMOTIVE,
            IndustrySector.AUTOMOTIVE_SUPPLIER,
        ],
        "general": [
            IndustrySector.PUBLIC_ADMINISTRATION,
            IndustrySector.RETAIL,
            IndustrySector.PROFESSIONAL_SERVICES,
            IndustrySector.TECHNOLOGY,
            IndustrySector.OTHER,
        ],
    }

    icons = {
        IndustrySector.BANKING: "Landmark",
        IndustrySector.INSURANCE: "Shield",
        IndustrySector.INVESTMENT: "TrendingUp",
        IndustrySector.PAYMENT_SERVICES: "CreditCard",
        IndustrySector.CRYPTO_ASSETS: "Bitcoin",
        IndustrySector.ENERGY: "Zap",
        IndustrySector.WATER: "Droplet",
        IndustrySector.FOOD: "Utensils",
        IndustrySector.HEALTHCARE: "Heart",
        IndustrySector.TRANSPORT: "Truck",
        IndustrySector.DIGITAL_INFRASTRUCTURE: "Server",
        IndustrySector.ICT_SERVICES: "Cloud",
        IndustrySector.SPACE: "Rocket",
        IndustrySector.POSTAL: "Mail",
        IndustrySector.WASTE_MANAGEMENT: "Trash",
        IndustrySector.CHEMICALS: "Flask",
        IndustrySector.MANUFACTURING: "Factory",
        IndustrySector.AUTOMOTIVE: "Car",
        IndustrySector.AUTOMOTIVE_SUPPLIER: "Cog",
        IndustrySector.PUBLIC_ADMINISTRATION: "Building2",
        IndustrySector.RETAIL: "ShoppingCart",
        IndustrySector.PROFESSIONAL_SERVICES: "Briefcase",
        IndustrySector.TECHNOLOGY: "Cpu",
        IndustrySector.OTHER: "MoreHorizontal",
    }

    industries = []
    for category, sectors in categories.items():
        for sector in sectors:
            industries.append(IndustryInfo(
                id=sector.value,
                name_en=get_industry_display_name(sector, "en"),
                name_de=get_industry_display_name(sector, "de"),
                category=category,
                icon=icons.get(sector, "Building"),
            ))

    return industries


@router.get("/regulations", response_model=List[RegulationInfo])
async def list_regulations():
    """List available regulations."""
    regulations = []
    for reg_id, reg_info in REGULATION_RULES.items():
        regulations.append(RegulationInfo(
            id=reg_id,
            name=reg_info["name"],
            name_de=reg_info["name_de"],
            description=reg_info["description"],
            deadline=reg_info.get("deadline"),
            authority=reg_info.get("authority", ""),
            penalties=reg_info.get("penalties", ""),
        ))
    return regulations


@router.get("/countries")
async def list_countries():
    """List available countries."""
    countries = []
    country_names = {
        CountryCode.DE: {"en": "Germany", "de": "Deutschland"},
        CountryCode.AT: {"en": "Austria", "de": "Österreich"},
        CountryCode.CH: {"en": "Switzerland", "de": "Schweiz"},
        CountryCode.FR: {"en": "France", "de": "Frankreich"},
        CountryCode.NL: {"en": "Netherlands", "de": "Niederlande"},
        CountryCode.BE: {"en": "Belgium", "de": "Belgien"},
        CountryCode.LU: {"en": "Luxembourg", "de": "Luxemburg"},
        CountryCode.IT: {"en": "Italy", "de": "Italien"},
        CountryCode.ES: {"en": "Spain", "de": "Spanien"},
        CountryCode.PL: {"en": "Poland", "de": "Polen"},
        CountryCode.OTHER_EU: {"en": "Other EU", "de": "Anderes EU-Land"},
        CountryCode.NON_EU: {"en": "Non-EU", "de": "Nicht-EU"},
    }
    for code in CountryCode:
        names = country_names.get(code, {"en": code.value, "de": code.value})
        countries.append({
            "code": code.value,
            "name_en": names["en"],
            "name_de": names["de"],
            "is_eu": code not in [CountryCode.CH, CountryCode.NON_EU],
        })
    return countries


@router.get("/company-sizes")
async def list_company_sizes():
    """List company size options."""
    return [
        {
            "id": size.value,
            "name_en": get_size_display_name(size, "en"),
            "name_de": get_size_display_name(size, "de"),
            "threshold": {
                CompanySize.MICRO: {"employees": "<10", "revenue": "<€2M"},
                CompanySize.SMALL: {"employees": "10-49", "revenue": "<€10M"},
                CompanySize.MEDIUM: {"employees": "50-249", "revenue": "<€50M"},
                CompanySize.LARGE: {"employees": "250+", "revenue": "€50M+"},
            }[size],
        }
        for size in CompanySize
    ]


# =============================================================================
# WIZARD STATE
# =============================================================================

@router.get("/wizard-state", response_model=WizardState)
async def get_wizard_state(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current wizard state."""
    service = OnboardingService(db)
    return await service.get_wizard_state(current_user.tenant_id)


# =============================================================================
# STEP 1: ORGANIZATION PROFILE
# =============================================================================

@router.post("/profile", response_model=OrganizationProfileResponse)
async def create_profile(
    data: OrganizationProfileCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Create organization profile (Step 1)."""
    service = OnboardingService(db)

    # Check if profile already exists
    existing = await service.get_profile(current_user.tenant_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization profile already exists. Use PUT to update.",
        )

    profile = await service.create_profile(
        data=data,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    return service._profile_to_response(profile)


@router.get("/profile", response_model=OrganizationProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get organization profile."""
    service = OnboardingService(db)
    profile = await service.get_profile(current_user.tenant_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization profile not found. Complete onboarding first.",
        )
    return service._profile_to_response(profile)


@router.put("/profile/{profile_id}", response_model=OrganizationProfileResponse)
async def update_profile(
    profile_id: str,
    data: OrganizationProfileUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update organization profile."""
    service = OnboardingService(db)
    try:
        profile = await service.update_profile(
            profile_id=profile_id,
            data=data,
            tenant_id=current_user.tenant_id,
        )
        return service._profile_to_response(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# STEP 2: SPECIAL STATUS & REGULATION DETECTION
# =============================================================================

@router.put("/profile/{profile_id}/special-status", response_model=OrganizationProfileResponse)
async def update_special_status(
    profile_id: str,
    data: SpecialStatusUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update special regulatory status (KRITIS, BaFin, etc.)."""
    service = OnboardingService(db)
    try:
        profile = await service.update_special_status(
            profile_id=profile_id,
            data=data,
            tenant_id=current_user.tenant_id,
        )
        return service._profile_to_response(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/profile/{profile_id}/detect-regulations", response_model=RegulationDetectionResponse)
async def detect_regulations(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Detect applicable regulations based on profile."""
    service = OnboardingService(db)
    try:
        profile = await service._get_profile_by_id(profile_id, current_user.tenant_id)
        return service.detect_applicable_regulations(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/profile/{profile_id}/confirm-regulations", response_model=OrganizationProfileResponse)
async def confirm_regulations(
    profile_id: str,
    data: RegulationConfirmation,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Confirm applicable regulations."""
    service = OnboardingService(db)
    try:
        profile = await service.confirm_regulations(
            profile_id=profile_id,
            confirmed_regulations=data.confirmed_regulations,
            tenant_id=current_user.tenant_id,
        )
        return service._profile_to_response(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# STEP 3: BASELINE FRAMEWORK SELECTION
# =============================================================================

@router.get("/profile/{profile_id}/recommend-frameworks", response_model=BaselineRecommendationResponse)
async def recommend_frameworks(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get framework recommendations based on profile."""
    service = OnboardingService(db)
    try:
        profile = await service._get_profile_by_id(profile_id, current_user.tenant_id)
        return service.get_baseline_recommendations(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/profile/{profile_id}/select-frameworks", response_model=OrganizationProfileResponse)
async def select_frameworks(
    profile_id: str,
    data: FrameworkSelection,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Select implementation frameworks."""
    service = OnboardingService(db)
    try:
        profile = await service.select_frameworks(
            profile_id=profile_id,
            selected_frameworks=data.selected_frameworks,
            tenant_id=current_user.tenant_id,
        )
        return service._profile_to_response(profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# STEP 4: COMPLIANCE PLAN
# =============================================================================

@router.post("/profile/{profile_id}/generate-plan", response_model=CompliancePlanResponse)
async def generate_compliance_plan(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Generate compliance plan based on profile."""
    service = OnboardingService(db)
    try:
        return await service.generate_compliance_plan(
            profile_id=profile_id,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/profile/{profile_id}/plan", response_model=CompliancePlanResponse)
async def get_compliance_plan(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get existing compliance plan."""
    service = OnboardingService(db)
    try:
        return await service.generate_compliance_plan(
            profile_id=profile_id,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# STEP 5: COMPLETE ONBOARDING
# =============================================================================

@router.post("/profile/{profile_id}/complete", response_model=OnboardingCompletionResponse)
async def complete_onboarding(
    profile_id: str,
    data: OnboardingComplete,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Complete onboarding and create initial assessments."""
    service = OnboardingService(db)
    try:
        result = await service.complete_onboarding(
            profile_id=profile_id,
            tenant_id=current_user.tenant_id,
            create_assessments=data.create_initial_assessments,
        )
        return OnboardingCompletionResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
