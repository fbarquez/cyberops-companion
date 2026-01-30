"""
Compliance and threat intelligence integrations.

This package provides integrations with:
- BSI IT-Grundschutz (Germany)
- BSI Meldepflicht (Incident Notification)
- ISO 27001:2022 / ISO 27035
- NIST CSF 2.0, SP 800-53, SP 800-61r3
- NIS2 Directive (EU)
- MITRE ATT&CK
- OWASP Top 10
- IOC Enrichment
- Cross-framework control mapping
"""

from src.integrations.models import (
    ComplianceStatus,
    ComplianceFramework,
    ComplianceControl,
    ComplianceCheck,
    ComplianceReport,
    PhaseComplianceMapping,
    CVSSScore,
    CVEInfo,
    ATTACKTechnique,
    ThreatIntelligence,
)

from src.integrations.bsi_integration import BSIIntegration
from src.integrations.iso_mapper import ISOComplianceMapper
from src.integrations.cross_framework_mapper import CrossFrameworkMapper, FrameworkType
from src.integrations.mitre_integration import (
    MITREIntegration,
    get_mitre_integration,
    ATTACKTechnique as MITRETechnique,
)
from src.integrations.nis2_directive import (
    NIS2DirectiveManager,
    get_nis2_manager,
    get_entity_type_for_sector,
    get_csirt_for_member_state,
)
from src.integrations.nis2_models import (
    NIS2EntityType,
    NIS2Sector,
    NIS2IncidentSeverity,
    NIS2NotificationStatus,
    NIS2ContactPerson,
    NIS2IncidentImpact,
    NIS2Notification,
    NIS2EarlyWarning,
    NIS2IncidentNotification,
    NIS2FinalReport,
    EU_MEMBER_STATES,
    SECTOR_ENTITY_TYPE,
)
from src.integrations.owasp_integration import (
    OWASPIntegration,
    get_owasp_integration,
    OWASPCategory,
)
from src.integrations.ioc_enrichment import (
    IOCEnricher,
    get_ioc_enricher,
    IOCType,
    ThreatLevel,
    EnrichmentSource,
    EnrichmentResult,
)
from src.integrations.bsi_meldung import (
    BSIMeldungGenerator,
    get_bsi_meldung_generator,
    BSIMeldung,
    IncidentCategory,
    ImpactLevel,
    KRITISSector,
    NotificationType,
)

__all__ = [
    # Models
    "ComplianceStatus",
    "ComplianceFramework",
    "ComplianceControl",
    "ComplianceCheck",
    "ComplianceReport",
    "PhaseComplianceMapping",
    "CVSSScore",
    "CVEInfo",
    "ATTACKTechnique",
    "ThreatIntelligence",
    # BSI Integration
    "BSIIntegration",
    "BSIMeldungGenerator",
    "get_bsi_meldung_generator",
    "BSIMeldung",
    "IncidentCategory",
    "ImpactLevel",
    "KRITISSector",
    "NotificationType",
    # ISO Integration
    "ISOComplianceMapper",
    # Cross-framework Mapping
    "CrossFrameworkMapper",
    "FrameworkType",
    # MITRE Integration
    "MITREIntegration",
    "get_mitre_integration",
    "MITRETechnique",
    # NIS2 Integration
    "NIS2DirectiveManager",
    "get_nis2_manager",
    "get_entity_type_for_sector",
    "get_csirt_for_member_state",
    "NIS2EntityType",
    "NIS2Sector",
    "NIS2IncidentSeverity",
    "NIS2NotificationStatus",
    "NIS2ContactPerson",
    "NIS2IncidentImpact",
    "NIS2Notification",
    "NIS2EarlyWarning",
    "NIS2IncidentNotification",
    "NIS2FinalReport",
    "EU_MEMBER_STATES",
    "SECTOR_ENTITY_TYPE",
    # OWASP Integration
    "OWASPIntegration",
    "get_owasp_integration",
    "OWASPCategory",
    # IOC Enrichment
    "IOCEnricher",
    "get_ioc_enricher",
    "IOCType",
    "ThreatLevel",
    "EnrichmentSource",
    "EnrichmentResult",
]
