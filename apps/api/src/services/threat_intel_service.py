"""
Threat Intelligence Service.

Manages IOCs, Threat Actors, and Campaigns with enrichment capabilities.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.threat_intel import (
    IOC, ThreatActor, Campaign, ThreatFeed,
    ThreatLevel, IOCType, IOCStatus,
    ActorMotivation, ActorSophistication
)
from src.schemas.threat_intel import (
    IOCCreate, IOCUpdate, IOCBulkCreate,
    ThreatActorCreate, ThreatActorUpdate,
    CampaignCreate, CampaignUpdate,
    ThreatFeedCreate, EnrichmentResponse, ThreatIntelStats
)
from src.integrations.ioc_enrichment import (
    IOCEnricher, get_ioc_enricher, EnrichmentResult,
    IOCType as EnricherIOCType, ThreatLevel as EnricherThreatLevel
)


class ThreatIntelService:
    """Service for managing Threat Intelligence data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.enricher = get_ioc_enricher(offline_mode=True)

    # ============== IOC Methods ==============

    async def create_ioc(
        self,
        data: IOCCreate,
        user_id: Optional[str] = None,
        auto_enrich: bool = True
    ) -> IOC:
        """Create a new IOC, optionally enriching it."""
        # Auto-detect type if not provided
        ioc_type = data.type
        if ioc_type is None:
            detected = self.enricher.detect_ioc_type(data.value)
            ioc_type = IOCType(detected.value)

        ioc = IOC(
            value=data.value.lower().strip(),
            type=ioc_type,
            status=IOCStatus.ACTIVE,
            description=data.description,
            tags=data.tags or [],
            source=data.source,
            expires_at=data.expires_at,
            created_by=user_id,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            incident_id=data.incident_id,
        )

        # Auto-enrich if requested
        if auto_enrich:
            enrichment = self.enricher.enrich(data.value)
            self._apply_enrichment(ioc, enrichment)

        self.db.add(ioc)
        await self.db.commit()
        await self.db.refresh(ioc)
        return ioc

    async def bulk_create_iocs(
        self,
        data: IOCBulkCreate,
        user_id: Optional[str] = None,
        auto_enrich: bool = True
    ) -> List[IOC]:
        """Create multiple IOCs at once."""
        created_iocs = []

        for ioc_data in data.iocs:
            # Check if IOC already exists
            existing = await self.get_ioc_by_value(ioc_data.value)
            if existing:
                # Update last_seen
                existing.last_seen = datetime.utcnow()
                created_iocs.append(existing)
                continue

            ioc = await self.create_ioc(ioc_data, user_id, auto_enrich)
            created_iocs.append(ioc)

        await self.db.commit()
        return created_iocs

    async def get_ioc(self, ioc_id: str) -> Optional[IOC]:
        """Get IOC by ID."""
        result = await self.db.execute(
            select(IOC)
            .options(selectinload(IOC.threat_actors), selectinload(IOC.campaigns))
            .where(IOC.id == ioc_id)
        )
        return result.scalar_one_or_none()

    async def get_ioc_by_value(self, value: str) -> Optional[IOC]:
        """Get IOC by value."""
        result = await self.db.execute(
            select(IOC).where(IOC.value == value.lower().strip())
        )
        return result.scalar_one_or_none()

    async def list_iocs(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[IOCStatus] = None,
        ioc_type: Optional[IOCType] = None,
        threat_level: Optional[ThreatLevel] = None,
        search: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> tuple[List[IOC], int]:
        """List IOCs with filtering and pagination."""
        query = select(IOC)

        # Apply filters
        conditions = []
        if status:
            conditions.append(IOC.status == status)
        if ioc_type:
            conditions.append(IOC.type == ioc_type)
        if threat_level:
            conditions.append(IOC.threat_level == threat_level)
        if search:
            conditions.append(IOC.value.ilike(f"%{search}%"))
        if incident_id:
            conditions.append(IOC.incident_id == incident_id)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(IOC.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        iocs = result.scalars().all()

        return list(iocs), total

    async def update_ioc(self, ioc_id: str, data: IOCUpdate) -> Optional[IOC]:
        """Update an IOC."""
        ioc = await self.get_ioc(ioc_id)
        if not ioc:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ioc, field, value)

        ioc.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(ioc)
        return ioc

    async def delete_ioc(self, ioc_id: str) -> bool:
        """Delete an IOC."""
        ioc = await self.get_ioc(ioc_id)
        if not ioc:
            return False

        await self.db.delete(ioc)
        await self.db.commit()
        return True

    async def enrich_ioc(
        self,
        value: str,
        ioc_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
        save: bool = False,
        user_id: Optional[str] = None
    ) -> EnrichmentResponse:
        """Enrich an IOC with threat intelligence."""
        # Convert type if provided
        enricher_type = None
        if ioc_type:
            enricher_type = EnricherIOCType(ioc_type)

        # Perform enrichment
        result = self.enricher.enrich(value, enricher_type)

        # Optionally save to database
        if save:
            existing = await self.get_ioc_by_value(value)
            if existing:
                self._apply_enrichment(existing, result)
                existing.last_enriched = datetime.utcnow()
                await self.db.commit()
            else:
                ioc_data = IOCCreate(value=value)
                await self.create_ioc(ioc_data, user_id, auto_enrich=False)
                new_ioc = await self.get_ioc_by_value(value)
                if new_ioc:
                    self._apply_enrichment(new_ioc, result)
                    new_ioc.last_enriched = datetime.utcnow()
                    await self.db.commit()

        # Convert to response schema
        return self._enrichment_to_response(result)

    async def enrich_batch(
        self,
        values: List[str],
        save: bool = False,
        user_id: Optional[str] = None
    ) -> List[EnrichmentResponse]:
        """Enrich multiple IOCs."""
        responses = []
        for value in values:
            response = await self.enrich_ioc(value, save=save, user_id=user_id)
            responses.append(response)
        return responses

    def _apply_enrichment(self, ioc: IOC, enrichment: EnrichmentResult) -> None:
        """Apply enrichment results to an IOC model."""
        ioc.threat_level = ThreatLevel(enrichment.overall_threat_level.value)
        ioc.risk_score = enrichment.risk_score
        ioc.confidence = enrichment.confidence
        ioc.categories = enrichment.categories
        ioc.tags = list(set(ioc.tags or []) | set(enrichment.tags))
        ioc.mitre_techniques = enrichment.mitre_techniques
        ioc.country = enrichment.geographic_info.get("country")
        ioc.asn = enrichment.geographic_info.get("asn")
        ioc.enrichment_data = {
            "sources": {
                src.value: {
                    "available": sr.available,
                    "threat_level": sr.threat_level.value,
                    "detections": sr.detections,
                    "total_engines": sr.total_engines,
                }
                for src, sr in enrichment.source_results.items()
            },
            "recommended_actions": enrichment.recommended_actions,
            "related_iocs": enrichment.related_iocs,
        }
        ioc.last_enriched = datetime.utcnow()

    def _enrichment_to_response(self, result: EnrichmentResult) -> EnrichmentResponse:
        """Convert enrichment result to response schema."""
        from src.schemas.threat_intel import (
            ThreatLevelEnum, SourceResultResponse
        )

        sources = {}
        for src, sr in result.source_results.items():
            sources[src.value] = SourceResultResponse(
                source=src.value,
                available=sr.available,
                threat_level=ThreatLevelEnum(sr.threat_level.value),
                confidence=sr.confidence,
                detections=sr.detections,
                total_engines=sr.total_engines,
                categories=sr.categories,
                tags=sr.tags,
                country=sr.country,
                error=sr.error,
            )

        return EnrichmentResponse(
            ioc=result.ioc_value,
            type=result.ioc_type.value,
            threat_level=ThreatLevelEnum(result.overall_threat_level.value),
            risk_score=result.risk_score,
            confidence=result.confidence,
            categories=result.categories,
            tags=result.tags,
            geographic_info=result.geographic_info,
            recommended_actions=result.recommended_actions,
            mitre_techniques=result.mitre_techniques,
            related_iocs=result.related_iocs,
            sources=sources,
            enrichment_time=result.enrichment_time,
            is_cached=result.is_cached,
        )

    # ============== Threat Actor Methods ==============

    async def create_actor(self, data: ThreatActorCreate) -> ThreatActor:
        """Create a new threat actor."""
        actor = ThreatActor(
            name=data.name,
            aliases=data.aliases or [],
            motivation=ActorMotivation(data.motivation.value) if data.motivation else ActorMotivation.UNKNOWN,
            sophistication=ActorSophistication(data.sophistication.value) if data.sophistication else ActorSophistication.UNKNOWN,
            description=data.description,
            country_of_origin=data.country_of_origin,
            target_sectors=data.target_sectors or [],
            target_countries=data.target_countries or [],
            mitre_techniques=data.mitre_techniques or [],
            tools_used=data.tools_used or [],
            first_seen=datetime.utcnow(),
        )

        self.db.add(actor)
        await self.db.commit()
        await self.db.refresh(actor)
        return actor

    async def get_actor(self, actor_id: str) -> Optional[ThreatActor]:
        """Get threat actor by ID."""
        result = await self.db.execute(
            select(ThreatActor)
            .options(selectinload(ThreatActor.iocs), selectinload(ThreatActor.campaigns))
            .where(ThreatActor.id == actor_id)
        )
        return result.scalar_one_or_none()

    async def get_actor_by_name(self, name: str) -> Optional[ThreatActor]:
        """Get threat actor by name or alias."""
        result = await self.db.execute(
            select(ThreatActor).where(
                or_(
                    ThreatActor.name.ilike(name),
                    ThreatActor.aliases.any(name)
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_actors(
        self,
        is_active: Optional[bool] = None,
        motivation: Optional[ActorMotivation] = None,
        sophistication: Optional[ActorSophistication] = None,
        search: Optional[str] = None,
    ) -> tuple[List[ThreatActor], int]:
        """List threat actors with filtering."""
        query = select(ThreatActor)

        conditions = []
        if is_active is not None:
            conditions.append(ThreatActor.is_active == is_active)
        if motivation:
            conditions.append(ThreatActor.motivation == motivation)
        if sophistication:
            conditions.append(ThreatActor.sophistication == sophistication)
        if search:
            conditions.append(
                or_(
                    ThreatActor.name.ilike(f"%{search}%"),
                    ThreatActor.description.ilike(f"%{search}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(ThreatActor.name)
        result = await self.db.execute(query)
        actors = result.scalars().all()

        return list(actors), total

    async def update_actor(self, actor_id: str, data: ThreatActorUpdate) -> Optional[ThreatActor]:
        """Update a threat actor."""
        actor = await self.get_actor(actor_id)
        if not actor:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "motivation" and value:
                value = ActorMotivation(value.value)
            elif field == "sophistication" and value:
                value = ActorSophistication(value.value)
            elif field == "threat_level" and value:
                value = ThreatLevel(value.value)
            setattr(actor, field, value)

        actor.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(actor)
        return actor

    async def link_ioc_to_actor(self, ioc_id: str, actor_id: str) -> bool:
        """Link an IOC to a threat actor."""
        ioc = await self.get_ioc(ioc_id)
        actor = await self.get_actor(actor_id)

        if not ioc or not actor:
            return False

        if actor not in ioc.threat_actors:
            ioc.threat_actors.append(actor)
            await self.db.commit()

        return True

    # ============== Campaign Methods ==============

    async def create_campaign(self, data: CampaignCreate) -> Campaign:
        """Create a new campaign."""
        campaign = Campaign(
            name=data.name,
            campaign_type=data.campaign_type,
            description=data.description,
            objectives=data.objectives,
            target_sectors=data.target_sectors or [],
            target_countries=data.target_countries or [],
            mitre_techniques=data.mitre_techniques or [],
            attack_vectors=data.attack_vectors or [],
            malware_used=data.malware_used or [],
            start_date=data.start_date,
            end_date=data.end_date,
        )

        # Link actors if provided
        if data.actor_ids:
            for actor_id in data.actor_ids:
                actor = await self.get_actor(actor_id)
                if actor:
                    campaign.threat_actors.append(actor)

        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        result = await self.db.execute(
            select(Campaign)
            .options(selectinload(Campaign.iocs), selectinload(Campaign.threat_actors))
            .where(Campaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        is_active: Optional[bool] = None,
        campaign_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Campaign], int]:
        """List campaigns with filtering."""
        query = select(Campaign)

        conditions = []
        if is_active is not None:
            conditions.append(Campaign.is_active == is_active)
        if campaign_type:
            conditions.append(Campaign.campaign_type == campaign_type)
        if search:
            conditions.append(
                or_(
                    Campaign.name.ilike(f"%{search}%"),
                    Campaign.description.ilike(f"%{search}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(Campaign.created_at.desc())
        result = await self.db.execute(query)
        campaigns = result.scalars().all()

        return list(campaigns), total

    async def update_campaign(self, campaign_id: str, data: CampaignUpdate) -> Optional[Campaign]:
        """Update a campaign."""
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "threat_level" and value:
                value = ThreatLevel(value.value)
            setattr(campaign, field, value)

        campaign.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def link_ioc_to_campaign(self, ioc_id: str, campaign_id: str) -> bool:
        """Link an IOC to a campaign."""
        ioc = await self.get_ioc(ioc_id)
        campaign = await self.get_campaign(campaign_id)

        if not ioc or not campaign:
            return False

        if campaign not in ioc.campaigns:
            ioc.campaigns.append(campaign)
            await self.db.commit()

        return True

    # ============== Statistics ==============

    async def get_stats(self) -> ThreatIntelStats:
        """Get threat intelligence statistics."""
        # Total IOCs
        total_iocs_result = await self.db.execute(select(func.count(IOC.id)))
        total_iocs = total_iocs_result.scalar() or 0

        # Active IOCs
        active_iocs_result = await self.db.execute(
            select(func.count(IOC.id)).where(IOC.status == IOCStatus.ACTIVE)
        )
        active_iocs = active_iocs_result.scalar() or 0

        # IOCs by type
        iocs_by_type_result = await self.db.execute(
            select(IOC.type, func.count(IOC.id)).group_by(IOC.type)
        )
        iocs_by_type = {row[0].value: row[1] for row in iocs_by_type_result.all()}

        # IOCs by threat level
        iocs_by_level_result = await self.db.execute(
            select(IOC.threat_level, func.count(IOC.id)).group_by(IOC.threat_level)
        )
        iocs_by_threat_level = {row[0].value: row[1] for row in iocs_by_level_result.all()}

        # Total actors
        total_actors_result = await self.db.execute(select(func.count(ThreatActor.id)))
        total_actors = total_actors_result.scalar() or 0

        # Active actors
        active_actors_result = await self.db.execute(
            select(func.count(ThreatActor.id)).where(ThreatActor.is_active == True)
        )
        active_actors = active_actors_result.scalar() or 0

        # Total campaigns
        total_campaigns_result = await self.db.execute(select(func.count(Campaign.id)))
        total_campaigns = total_campaigns_result.scalar() or 0

        # Active campaigns
        active_campaigns_result = await self.db.execute(
            select(func.count(Campaign.id)).where(Campaign.is_active == True)
        )
        active_campaigns = active_campaigns_result.scalar() or 0

        # Recent IOCs
        recent_result = await self.db.execute(
            select(IOC).order_by(IOC.created_at.desc()).limit(5)
        )
        recent_iocs_models = recent_result.scalars().all()

        # Convert to response format
        from src.schemas.threat_intel import IOCResponse, IOCTypeEnum, IOCStatusEnum, ThreatLevelEnum

        recent_iocs = [
            IOCResponse(
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
            for ioc in recent_iocs_models
        ]

        return ThreatIntelStats(
            total_iocs=total_iocs,
            active_iocs=active_iocs,
            iocs_by_type=iocs_by_type,
            iocs_by_threat_level=iocs_by_threat_level,
            total_actors=total_actors,
            active_actors=active_actors,
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            recent_iocs=recent_iocs,
        )
