"""
Integrations Module - Compliance Hub for ISORA.

Provides integrations with regulatory frameworks and threat intelligence:
- BSI IT-Grundschutz (Germany)
- NIST CSF 2.0, SP 800-53, SP 800-61r3, NVD
- ISO 27001:2022, ISO 27035
- MITRE ATT&CK
- OWASP Top 10, Cheat Sheet Series
"""

from src.integrations.compliance_hub import ComplianceHub, ComplianceFramework
from src.integrations.models import (
    ComplianceCheck,
    ComplianceStatus,
    ComplianceReport,
    ThreatIntelligence,
    CVEInfo,
    ATTACKTechnique,
)
from src.integrations.bsi_integration import BSIIntegration
from src.integrations.nist_integration import NISTOSCALIntegration, NVDIntegration
from src.integrations.mitre_integration import MITREATTACKIntegration
from src.integrations.iso_mapper import ISOComplianceMapper
from src.integrations.owasp_integration import OWASPIntegration
from src.integrations.cross_framework_mapper import CrossFrameworkMapper, FrameworkType, UnifiedControl
from src.integrations.bsi_meldung import BSIMeldungGenerator, BSIMeldung
from src.integrations.ioc_enrichment import (
    IOCEnricher,
    IOCType,
    ThreatLevel,
    EnrichmentSource,
    EnrichmentResult,
)

__all__ = [
    "ComplianceHub",
    "ComplianceFramework",
    "ComplianceCheck",
    "ComplianceStatus",
    "ComplianceReport",
    "ThreatIntelligence",
    "CVEInfo",
    "ATTACKTechnique",
    "BSIIntegration",
    "NISTOSCALIntegration",
    "NVDIntegration",
    "MITREATTACKIntegration",
    "ISOComplianceMapper",
    "OWASPIntegration",
    "CrossFrameworkMapper",
    "FrameworkType",
    "UnifiedControl",
    "BSIMeldungGenerator",
    "BSIMeldung",
    "IOCEnricher",
    "IOCType",
    "ThreatLevel",
    "EnrichmentSource",
    "EnrichmentResult",
]
