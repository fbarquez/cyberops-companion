"""
Threat Intelligence Models.

Database models for IOCs, Threat Actors, and Campaigns.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Float, Boolean,
    ForeignKey, Table, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base


class ThreatLevel(str, enum.Enum):
    """Threat level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class IOCType(str, enum.Enum):
    """Types of Indicators of Compromise."""
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


class IOCStatus(str, enum.Enum):
    """IOC lifecycle status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    FALSE_POSITIVE = "false_positive"
    UNDER_REVIEW = "under_review"


class ActorMotivation(str, enum.Enum):
    """Threat actor motivation."""
    FINANCIAL = "financial"
    ESPIONAGE = "espionage"
    HACKTIVISM = "hacktivism"
    DESTRUCTION = "destruction"
    UNKNOWN = "unknown"


class ActorSophistication(str, enum.Enum):
    """Threat actor sophistication level."""
    APT = "apt"
    ORGANIZED_CRIME = "organized_crime"
    SCRIPT_KIDDIE = "script_kiddie"
    INSIDER = "insider"
    UNKNOWN = "unknown"


# Association tables
ioc_actor_association = Table(
    'ioc_actor_association',
    Base.metadata,
    Column('ioc_id', String(36), ForeignKey('iocs.id'), primary_key=True),
    Column('actor_id', String(36), ForeignKey('threat_actors.id'), primary_key=True)
)

ioc_campaign_association = Table(
    'ioc_campaign_association',
    Base.metadata,
    Column('ioc_id', String(36), ForeignKey('iocs.id'), primary_key=True),
    Column('campaign_id', String(36), ForeignKey('campaigns.id'), primary_key=True)
)

actor_campaign_association = Table(
    'actor_campaign_association',
    Base.metadata,
    Column('actor_id', String(36), ForeignKey('threat_actors.id'), primary_key=True),
    Column('campaign_id', String(36), ForeignKey('campaigns.id'), primary_key=True)
)


class IOC(Base):
    """Indicator of Compromise model."""
    __tablename__ = "iocs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    type = mapped_column(SQLEnum(IOCType), nullable=False, index=True)
    status = mapped_column(SQLEnum(IOCStatus), default=IOCStatus.ACTIVE, index=True)

    # Threat assessment
    threat_level = mapped_column(SQLEnum(ThreatLevel), default=ThreatLevel.UNKNOWN)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags = mapped_column(JSON, default=[])
    categories = mapped_column(JSON, default=[])

    # Source information
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Enrichment data
    enrichment_data = mapped_column(JSON, default={})
    last_enriched: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Geographic information
    country: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    asn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # MITRE ATT&CK mapping
    mitre_techniques = mapped_column(JSON, default=[])

    # Timestamps
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # User tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    threat_actors = relationship(
        "ThreatActor",
        secondary=ioc_actor_association,
        back_populates="iocs"
    )
    campaigns = relationship(
        "Campaign",
        secondary=ioc_campaign_association,
        back_populates="iocs"
    )

    # Related incidents
    incident_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=True)
    incident = relationship("Incident", back_populates="iocs")


class ThreatActor(Base):
    """Threat Actor model."""
    __tablename__ = "threat_actors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    aliases = mapped_column(JSON, default=[])

    # Classification
    motivation = mapped_column(SQLEnum(ActorMotivation), default=ActorMotivation.UNKNOWN)
    sophistication = mapped_column(SQLEnum(ActorSophistication), default=ActorSophistication.UNKNOWN)
    threat_level = mapped_column(SQLEnum(ThreatLevel), default=ThreatLevel.UNKNOWN)

    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    target_sectors = mapped_column(JSON, default=[])
    target_countries = mapped_column(JSON, default=[])

    # TTPs (Tactics, Techniques, and Procedures)
    mitre_techniques = mapped_column(JSON, default=[])
    tools_used = mapped_column(JSON, default=[])

    # Activity tracking
    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # External references
    external_refs = mapped_column(JSON, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    iocs = relationship(
        "IOC",
        secondary=ioc_actor_association,
        back_populates="threat_actors"
    )
    campaigns = relationship(
        "Campaign",
        secondary=actor_campaign_association,
        back_populates="threat_actors"
    )


class Campaign(Base):
    """Threat Campaign model."""
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Classification
    campaign_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    threat_level = mapped_column(SQLEnum(ThreatLevel), default=ThreatLevel.UNKNOWN)

    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Targets
    target_sectors = mapped_column(JSON, default=[])
    target_countries = mapped_column(JSON, default=[])

    # Timeline
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # TTPs
    mitre_techniques = mapped_column(JSON, default=[])
    attack_vectors = mapped_column(JSON, default=[])
    malware_used = mapped_column(JSON, default=[])

    # Impact assessment
    estimated_victims: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_damage_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # External references
    external_refs = mapped_column(JSON, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    iocs = relationship(
        "IOC",
        secondary=ioc_campaign_association,
        back_populates="campaigns"
    )
    threat_actors = relationship(
        "ThreatActor",
        secondary=actor_campaign_association,
        back_populates="campaigns"
    )


class ThreatFeed(Base):
    """Threat Intelligence Feed configuration."""
    __tablename__ = "threat_feeds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Authentication
    api_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    auth_config = mapped_column(JSON, default={})

    # Sync settings
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_sync_count: Mapped[int] = mapped_column(Integer, default=0)

    # Filtering
    ioc_types = mapped_column(JSON, default=[])
    min_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
