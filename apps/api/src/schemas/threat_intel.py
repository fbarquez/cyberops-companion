"""
Pydantic schemas for Threat Intelligence.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class ThreatLevelEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class IOCTypeEnum(str, Enum):
    IP_ADDRESS = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH_MD5 = "md5"
    FILE_HASH_SHA1 = "sha1"
    FILE_HASH_SHA256 = "sha256"
    EMAIL = "email"
    CVE = "cve"
    REGISTRY_KEY = "registry"
    FILE_PATH = "file_path"
    PROCESS_NAME = "process"


class IOCStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FALSE_POSITIVE = "false_positive"
    UNDER_REVIEW = "under_review"


class ActorMotivationEnum(str, Enum):
    FINANCIAL = "financial"
    ESPIONAGE = "espionage"
    HACKTIVISM = "hacktivism"
    DESTRUCTION = "destruction"
    UNKNOWN = "unknown"


class ActorSophisticationEnum(str, Enum):
    APT = "apt"
    ORGANIZED_CRIME = "organized_crime"
    SCRIPT_KIDDIE = "script_kiddie"
    INSIDER = "insider"
    UNKNOWN = "unknown"


# IOC Schemas
class IOCBase(BaseModel):
    value: str = Field(..., description="The IOC value (IP, domain, hash, etc.)")
    type: Optional[IOCTypeEnum] = Field(None, description="Type of IOC (auto-detected if not provided)")
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    expires_at: Optional[datetime] = None


class IOCCreate(IOCBase):
    incident_id: Optional[str] = None


class IOCBulkCreate(BaseModel):
    iocs: List[IOCCreate] = Field(..., description="List of IOCs to create")


class IOCUpdate(BaseModel):
    status: Optional[IOCStatusEnum] = None
    threat_level: Optional[ThreatLevelEnum] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class IOCResponse(BaseModel):
    id: str
    value: str
    type: IOCTypeEnum
    status: IOCStatusEnum
    threat_level: ThreatLevelEnum
    risk_score: float
    confidence: float
    description: Optional[str] = None
    tags: List[str] = []
    categories: List[str] = []
    source: Optional[str] = None
    country: Optional[str] = None
    asn: Optional[str] = None
    mitre_techniques: List[str] = []
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    last_enriched: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IOCListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    iocs: List[IOCResponse]


# Enrichment Schemas
class EnrichIOCRequest(BaseModel):
    value: str = Field(..., description="IOC value to enrich")
    type: Optional[IOCTypeEnum] = Field(None, description="IOC type (auto-detected if not provided)")
    sources: Optional[List[str]] = Field(None, description="Specific sources to query")
    save: bool = Field(False, description="Save enriched IOC to database")


class EnrichBatchRequest(BaseModel):
    iocs: List[str] = Field(..., description="List of IOC values to enrich")
    save: bool = Field(False, description="Save enriched IOCs to database")


class SourceResultResponse(BaseModel):
    source: str
    available: bool
    threat_level: ThreatLevelEnum
    confidence: float
    detections: int = 0
    total_engines: int = 0
    categories: List[str] = []
    tags: List[str] = []
    country: Optional[str] = None
    error: Optional[str] = None


class EnrichmentResponse(BaseModel):
    ioc: str
    type: str
    threat_level: ThreatLevelEnum
    risk_score: float
    confidence: float
    categories: List[str] = []
    tags: List[str] = []
    geographic_info: Dict[str, str] = {}
    recommended_actions: List[str] = []
    mitre_techniques: List[str] = []
    related_iocs: List[str] = []
    sources: Dict[str, SourceResultResponse] = {}
    enrichment_time: datetime
    is_cached: bool = False


# Threat Actor Schemas
class ThreatActorBase(BaseModel):
    name: str = Field(..., description="Primary name of the threat actor")
    aliases: List[str] = Field(default_factory=list)
    motivation: Optional[ActorMotivationEnum] = ActorMotivationEnum.UNKNOWN
    sophistication: Optional[ActorSophisticationEnum] = ActorSophisticationEnum.UNKNOWN
    description: Optional[str] = None
    country_of_origin: Optional[str] = None
    target_sectors: List[str] = Field(default_factory=list)
    target_countries: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)


class ThreatActorCreate(ThreatActorBase):
    pass


class ThreatActorUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[List[str]] = None
    motivation: Optional[ActorMotivationEnum] = None
    sophistication: Optional[ActorSophisticationEnum] = None
    threat_level: Optional[ThreatLevelEnum] = None
    description: Optional[str] = None
    target_sectors: Optional[List[str]] = None
    mitre_techniques: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ThreatActorResponse(BaseModel):
    id: str
    name: str
    aliases: List[str] = []
    motivation: ActorMotivationEnum
    sophistication: ActorSophisticationEnum
    threat_level: ThreatLevelEnum
    description: Optional[str] = None
    country_of_origin: Optional[str] = None
    target_sectors: List[str] = []
    target_countries: List[str] = []
    mitre_techniques: List[str] = []
    tools_used: List[str] = []
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True
    ioc_count: int = 0
    campaign_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ThreatActorListResponse(BaseModel):
    total: int
    actors: List[ThreatActorResponse]


# Campaign Schemas
class CampaignBase(BaseModel):
    name: str = Field(..., description="Campaign name")
    campaign_type: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    target_sectors: List[str] = Field(default_factory=list)
    target_countries: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    attack_vectors: List[str] = Field(default_factory=list)
    malware_used: List[str] = Field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignCreate(CampaignBase):
    actor_ids: List[str] = Field(default_factory=list, description="Associated threat actor IDs")


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    campaign_type: Optional[str] = None
    threat_level: Optional[ThreatLevelEnum] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    campaign_type: Optional[str] = None
    threat_level: ThreatLevelEnum
    description: Optional[str] = None
    objectives: Optional[str] = None
    target_sectors: List[str] = []
    target_countries: List[str] = []
    mitre_techniques: List[str] = []
    attack_vectors: List[str] = []
    malware_used: List[str] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    ioc_count: int = 0
    actor_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    total: int
    campaigns: List[CampaignResponse]


# Feed Schemas
class ThreatFeedBase(BaseModel):
    name: str
    feed_type: str = Field(..., description="Feed type: misp, otx, virustotal, opencti, taxii")
    url: Optional[str] = None
    api_key: Optional[str] = None
    sync_interval_minutes: int = 60
    ioc_types: List[str] = Field(default_factory=list)
    min_confidence: float = 0.0


class ThreatFeedCreate(ThreatFeedBase):
    auth_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ThreatFeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None
    ioc_types: Optional[List[str]] = None
    min_confidence: Optional[float] = None
    auth_config: Optional[Dict[str, Any]] = None


class ThreatFeedResponse(BaseModel):
    id: str
    name: str
    feed_type: str
    url: Optional[str] = None
    is_enabled: bool
    sync_interval_minutes: int
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_count: int = 0
    ioc_types: List[str] = []
    min_confidence: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ThreatFeedListResponse(BaseModel):
    total: int
    feeds: List[ThreatFeedResponse]


class FeedSyncResponse(BaseModel):
    feed_id: str
    feed_type: str
    success: bool
    iocs_fetched: int = 0
    iocs_new: int = 0
    iocs_updated: int = 0
    iocs_skipped: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    duration_seconds: float = 0.0
    sync_started_at: Optional[datetime] = None
    sync_completed_at: Optional[datetime] = None


class FeedTestResponse(BaseModel):
    success: bool
    message: str
    feed_type: str
    feed_id: Optional[str] = None


class FeedSyncHistoryResponse(BaseModel):
    id: str
    feed_id: str
    sync_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None


# Statistics
class ThreatIntelStats(BaseModel):
    total_iocs: int
    active_iocs: int
    iocs_by_type: Dict[str, int]
    iocs_by_threat_level: Dict[str, int]
    total_actors: int
    active_actors: int
    total_campaigns: int
    active_campaigns: int
    recent_iocs: List[IOCResponse] = []
