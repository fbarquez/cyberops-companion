"""
Threat Intelligence API endpoints.

Endpoints for managing IOCs, Threat Actors, and Campaigns.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.threat_intel import IOCStatus, IOCType, ThreatLevel, ActorMotivation, ActorSophistication
from src.schemas.threat_intel import (
    IOCCreate, IOCUpdate, IOCResponse, IOCListResponse, IOCBulkCreate,
    EnrichIOCRequest, EnrichBatchRequest, EnrichmentResponse,
    ThreatActorCreate, ThreatActorUpdate, ThreatActorResponse, ThreatActorListResponse,
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignListResponse,
    ThreatIntelStats, IOCTypeEnum, IOCStatusEnum, ThreatLevelEnum
)
from src.services.threat_intel_service import ThreatIntelService

router = APIRouter()


# ============== IOC Endpoints ==============

@router.get("/iocs", response_model=IOCListResponse, summary="List IOCs")
async def list_iocs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by IOC type"),
    threat_level: Optional[str] = Query(None, description="Filter by threat level"),
    search: Optional[str] = Query(None, description="Search in IOC values"),
    incident_id: Optional[str] = Query(None, description="Filter by incident"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all IOCs with filtering and pagination.
    """
    service = ThreatIntelService(db)

    # Convert string params to enums
    status_enum = IOCStatus(status) if status else None
    type_enum = IOCType(type) if type else None
    threat_enum = ThreatLevel(threat_level) if threat_level else None

    iocs, total = await service.list_iocs(
        page=page,
        page_size=page_size,
        status=status_enum,
        ioc_type=type_enum,
        threat_level=threat_enum,
        search=search,
        incident_id=incident_id,
    )

    return IOCListResponse(
        total=total,
        page=page,
        page_size=page_size,
        iocs=[_ioc_to_response(ioc) for ioc in iocs]
    )


@router.post("/iocs", response_model=IOCResponse, status_code=status.HTTP_201_CREATED, summary="Create IOC")
async def create_ioc(
    data: IOCCreate,
    auto_enrich: bool = Query(True, description="Auto-enrich the IOC"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new IOC. Automatically enriches with threat intelligence by default.
    """
    service = ThreatIntelService(db)

    # Check if already exists
    existing = await service.get_ioc_by_value(data.value)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"IOC already exists with ID: {existing.id}"
        )

    ioc = await service.create_ioc(data, str(current_user.id), auto_enrich)
    return _ioc_to_response(ioc)


@router.post("/iocs/bulk", response_model=List[IOCResponse], status_code=status.HTTP_201_CREATED, summary="Bulk create IOCs")
async def bulk_create_iocs(
    data: IOCBulkCreate,
    auto_enrich: bool = Query(True, description="Auto-enrich IOCs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create multiple IOCs at once. Updates last_seen for existing IOCs.
    """
    service = ThreatIntelService(db)
    iocs = await service.bulk_create_iocs(data, str(current_user.id), auto_enrich)
    return [_ioc_to_response(ioc) for ioc in iocs]


@router.get("/iocs/{ioc_id}", response_model=IOCResponse, summary="Get IOC")
async def get_ioc(
    ioc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific IOC by ID.
    """
    service = ThreatIntelService(db)
    ioc = await service.get_ioc(ioc_id)

    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")

    return _ioc_to_response(ioc)


@router.patch("/iocs/{ioc_id}", response_model=IOCResponse, summary="Update IOC")
async def update_ioc(
    ioc_id: str,
    data: IOCUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an IOC's status, threat level, or other properties.
    """
    service = ThreatIntelService(db)
    ioc = await service.update_ioc(ioc_id, data)

    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")

    return _ioc_to_response(ioc)


@router.delete("/iocs/{ioc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete IOC")
async def delete_ioc(
    ioc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an IOC.
    """
    service = ThreatIntelService(db)
    deleted = await service.delete_ioc(ioc_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="IOC not found")


# ============== Enrichment Endpoints ==============

@router.post("/iocs/enrich", response_model=EnrichmentResponse, summary="Enrich IOC")
async def enrich_ioc(
    data: EnrichIOCRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enrich an IOC with threat intelligence from multiple sources.

    Sources include: VirusTotal, AbuseIPDB, Shodan, OTX, GreyNoise (when API keys configured).
    In offline mode, uses simulated data for training purposes.
    """
    service = ThreatIntelService(db)

    ioc_type = data.type.value if data.type else None
    response = await service.enrich_ioc(
        value=data.value,
        ioc_type=ioc_type,
        sources=data.sources,
        save=data.save,
        user_id=str(current_user.id) if data.save else None
    )

    return response


@router.post("/iocs/enrich/batch", response_model=List[EnrichmentResponse], summary="Batch enrich IOCs")
async def batch_enrich_iocs(
    data: EnrichBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enrich multiple IOCs at once.
    """
    service = ThreatIntelService(db)
    responses = await service.enrich_batch(
        values=data.iocs,
        save=data.save,
        user_id=str(current_user.id) if data.save else None
    )
    return responses


@router.post("/iocs/{ioc_id}/re-enrich", response_model=IOCResponse, summary="Re-enrich IOC")
async def re_enrich_ioc(
    ioc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Re-enrich an existing IOC with fresh threat intelligence.
    """
    service = ThreatIntelService(db)
    ioc = await service.get_ioc(ioc_id)

    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")

    await service.enrich_ioc(
        value=ioc.value,
        ioc_type=ioc.type.value,
        save=True,
        user_id=str(current_user.id)
    )

    # Refresh IOC
    ioc = await service.get_ioc(ioc_id)
    return _ioc_to_response(ioc)


# ============== Threat Actor Endpoints ==============

@router.get("/actors", response_model=ThreatActorListResponse, summary="List threat actors")
async def list_actors(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    motivation: Optional[str] = Query(None, description="Filter by motivation"),
    sophistication: Optional[str] = Query(None, description="Filter by sophistication"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all threat actors.
    """
    service = ThreatIntelService(db)

    motivation_enum = ActorMotivation(motivation) if motivation else None
    sophistication_enum = ActorSophistication(sophistication) if sophistication else None

    actors, total = await service.list_actors(
        is_active=is_active,
        motivation=motivation_enum,
        sophistication=sophistication_enum,
        search=search,
    )

    return ThreatActorListResponse(
        total=total,
        actors=[_actor_to_response(a) for a in actors]
    )


@router.post("/actors", response_model=ThreatActorResponse, status_code=status.HTTP_201_CREATED, summary="Create threat actor")
async def create_actor(
    data: ThreatActorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new threat actor profile.
    """
    service = ThreatIntelService(db)

    # Check if already exists
    existing = await service.get_actor_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Threat actor already exists with ID: {existing.id}"
        )

    actor = await service.create_actor(data)
    return _actor_to_response(actor)


@router.get("/actors/{actor_id}", response_model=ThreatActorResponse, summary="Get threat actor")
async def get_actor(
    actor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific threat actor by ID.
    """
    service = ThreatIntelService(db)
    actor = await service.get_actor(actor_id)

    if not actor:
        raise HTTPException(status_code=404, detail="Threat actor not found")

    return _actor_to_response(actor)


@router.patch("/actors/{actor_id}", response_model=ThreatActorResponse, summary="Update threat actor")
async def update_actor(
    actor_id: str,
    data: ThreatActorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a threat actor profile.
    """
    service = ThreatIntelService(db)
    actor = await service.update_actor(actor_id, data)

    if not actor:
        raise HTTPException(status_code=404, detail="Threat actor not found")

    return _actor_to_response(actor)


@router.post("/actors/{actor_id}/iocs/{ioc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Link IOC to actor")
async def link_ioc_to_actor(
    actor_id: str,
    ioc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Link an IOC to a threat actor.
    """
    service = ThreatIntelService(db)
    success = await service.link_ioc_to_actor(ioc_id, actor_id)

    if not success:
        raise HTTPException(status_code=404, detail="IOC or actor not found")


# ============== Campaign Endpoints ==============

@router.get("/campaigns", response_model=CampaignListResponse, summary="List campaigns")
async def list_campaigns(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    campaign_type: Optional[str] = Query(None, description="Filter by campaign type"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all threat campaigns.
    """
    service = ThreatIntelService(db)

    campaigns, total = await service.list_campaigns(
        is_active=is_active,
        campaign_type=campaign_type,
        search=search,
    )

    return CampaignListResponse(
        total=total,
        campaigns=[_campaign_to_response(c) for c in campaigns]
    )


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED, summary="Create campaign")
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new threat campaign.
    """
    service = ThreatIntelService(db)
    campaign = await service.create_campaign(data)
    return _campaign_to_response(campaign)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse, summary="Get campaign")
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific campaign by ID.
    """
    service = ThreatIntelService(db)
    campaign = await service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return _campaign_to_response(campaign)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse, summary="Update campaign")
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a campaign.
    """
    service = ThreatIntelService(db)
    campaign = await service.update_campaign(campaign_id, data)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return _campaign_to_response(campaign)


@router.post("/campaigns/{campaign_id}/iocs/{ioc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Link IOC to campaign")
async def link_ioc_to_campaign(
    campaign_id: str,
    ioc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Link an IOC to a campaign.
    """
    service = ThreatIntelService(db)
    success = await service.link_ioc_to_campaign(ioc_id, campaign_id)

    if not success:
        raise HTTPException(status_code=404, detail="IOC or campaign not found")


# ============== Statistics ==============

@router.get("/stats", response_model=ThreatIntelStats, summary="Get threat intel statistics")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get threat intelligence statistics and recent IOCs.
    """
    service = ThreatIntelService(db)
    return await service.get_stats()


# ============== Helper Functions ==============

def _ioc_to_response(ioc) -> IOCResponse:
    """Convert IOC model to response schema."""
    return IOCResponse(
        id=str(ioc.id),
        value=ioc.value,
        type=IOCTypeEnum(ioc.type.value),
        status=IOCStatusEnum(ioc.status.value),
        threat_level=ThreatLevelEnum(ioc.threat_level.value),
        risk_score=ioc.risk_score,
        confidence=ioc.confidence,
        description=ioc.description,
        tags=ioc.tags or [],
        categories=ioc.categories or [],
        source=ioc.source,
        country=ioc.country,
        asn=ioc.asn,
        mitre_techniques=ioc.mitre_techniques or [],
        first_seen=ioc.first_seen,
        last_seen=ioc.last_seen,
        last_enriched=ioc.last_enriched,
        created_at=ioc.created_at,
        updated_at=ioc.updated_at,
    )


def _actor_to_response(actor) -> ThreatActorResponse:
    """Convert ThreatActor model to response schema."""
    from src.schemas.threat_intel import ActorMotivationEnum, ActorSophisticationEnum

    return ThreatActorResponse(
        id=str(actor.id),
        name=actor.name,
        aliases=actor.aliases or [],
        motivation=ActorMotivationEnum(actor.motivation.value),
        sophistication=ActorSophisticationEnum(actor.sophistication.value),
        threat_level=ThreatLevelEnum(actor.threat_level.value),
        description=actor.description,
        country_of_origin=actor.country_of_origin,
        target_sectors=actor.target_sectors or [],
        target_countries=actor.target_countries or [],
        mitre_techniques=actor.mitre_techniques or [],
        tools_used=actor.tools_used or [],
        first_seen=actor.first_seen,
        last_seen=actor.last_seen,
        is_active=actor.is_active,
        ioc_count=len(actor.iocs) if hasattr(actor, 'iocs') and actor.iocs else 0,
        campaign_count=len(actor.campaigns) if hasattr(actor, 'campaigns') and actor.campaigns else 0,
        created_at=actor.created_at,
    )


def _campaign_to_response(campaign) -> CampaignResponse:
    """Convert Campaign model to response schema."""
    return CampaignResponse(
        id=str(campaign.id),
        name=campaign.name,
        campaign_type=campaign.campaign_type,
        threat_level=ThreatLevelEnum(campaign.threat_level.value),
        description=campaign.description,
        objectives=campaign.objectives,
        target_sectors=campaign.target_sectors or [],
        target_countries=campaign.target_countries or [],
        mitre_techniques=campaign.mitre_techniques or [],
        attack_vectors=campaign.attack_vectors or [],
        malware_used=campaign.malware_used or [],
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        is_active=campaign.is_active,
        ioc_count=len(campaign.iocs) if hasattr(campaign, 'iocs') and campaign.iocs else 0,
        actor_count=len(campaign.threat_actors) if hasattr(campaign, 'threat_actors') and campaign.threat_actors else 0,
        created_at=campaign.created_at,
    )
