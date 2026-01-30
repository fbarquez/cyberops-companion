"""
Compliance framework endpoints.

Provides API endpoints for:
- Listing available compliance frameworks
- Validating compliance against frameworks
- Cross-framework control mapping
- Compliance report generation
- NIS2 Directive notifications
- OWASP Top 10 risk analysis
- IOC enrichment
- BSI Meldung generation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.deps import DBSession, CurrentUser
from src.services.compliance_service import ComplianceService, get_compliance_service

# Import integrations
from src.integrations.ioc_enrichment import (
    get_ioc_enricher,
    IOCType,
    ThreatLevel,
)
from src.integrations.bsi_meldung import (
    get_bsi_meldung_generator,
    IncidentCategory,
    ImpactLevel,
    KRITISSector,
    NotificationType,
)
from src.integrations.nis2_directive import (
    get_nis2_manager,
    get_entity_type_for_sector,
)
from src.integrations.nis2_models import (
    NIS2EntityType,
    NIS2Sector,
    NIS2IncidentSeverity,
    EU_MEMBER_STATES,
)
from src.integrations.owasp_integration import get_owasp_integration


router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class FrameworkInfoResponse(BaseModel):
    """Framework information response."""
    id: str
    name: str
    description: str
    version: str
    controls_count: int
    organization: Optional[str] = None
    url: Optional[str] = None


class ComplianceValidationRequest(BaseModel):
    """Request to validate compliance."""
    incident_id: str
    phase: str
    frameworks: List[str]


class ValidationResultResponse(BaseModel):
    """Validation result for a single framework."""
    framework: str
    compliant: bool
    score: float
    total_controls: int
    compliant_count: int
    partial_count: int
    gap_count: int
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ComplianceValidationResponse(BaseModel):
    """Response for compliance validation."""
    incident_id: str
    phase: str
    frameworks: List[str]
    validation_results: Dict[str, ValidationResultResponse]
    overall_score: float
    validated_at: datetime


class CrossMappingControl(BaseModel):
    """Cross-framework mapping control."""
    unified_id: str
    name: str
    description: str
    category: str
    ir_phases: List[str]
    framework_controls: Dict[str, List[str]]
    evidence_requirements: List[str] = Field(default_factory=list)


class CrossMappingResponse(BaseModel):
    """Response for cross-framework mapping."""
    phase: Optional[str] = None
    controls: List[CrossMappingControl] = Field(default_factory=list)
    headers: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None


class ControlDetailsResponse(BaseModel):
    """Response for control details."""
    control_id: str
    framework: str
    unified_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    ir_phases: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    equivalent_controls: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)
    evidence_requirements: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ComplianceReportResponse(BaseModel):
    """Response for compliance report."""
    incident_id: str
    frameworks: List[str]
    generated_at: datetime
    generated_by: Optional[str] = None
    overall_compliance: float
    total_controls: int
    compliant_count: int
    partial_count: int
    gap_count: int
    framework_scores: Dict[str, float]
    gaps: List[Dict[str, Any]]
    recommendations: List[str]
    critical_gaps: List[Dict[str, Any]]


class IOCEnrichmentRequest(BaseModel):
    """Request for IOC enrichment."""
    ioc_type: str  # ip, domain, hash, file_path
    value: str
    sources: Optional[List[str]] = None


class IOCEnrichmentResponse(BaseModel):
    """Response for IOC enrichment."""
    ioc_type: str
    value: str
    threat_level: str
    sources_checked: List[str]
    enrichment_results: Dict[str, Any]
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/frameworks", response_model=List[FrameworkInfoResponse])
async def get_frameworks(
    current_user: CurrentUser,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get available compliance frameworks.

    Returns a list of all compliance frameworks supported by the system,
    including BSI IT-Grundschutz, NIST CSF, ISO 27001, and more.
    """
    frameworks = await service.get_frameworks()
    return [
        FrameworkInfoResponse(
            id=f.id,
            name=f.name,
            description=f.description,
            version=f.version,
            controls_count=f.controls_count,
            organization=f.organization,
            url=f.url,
        )
        for f in frameworks
    ]


@router.get("/frameworks/{framework_id}", response_model=FrameworkInfoResponse)
async def get_framework(
    framework_id: str,
    current_user: CurrentUser,
    service: ComplianceService = Depends(get_compliance_service),
):
    """Get details of a specific compliance framework."""
    framework = await service.get_framework(framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail=f"Framework {framework_id} not found")

    return FrameworkInfoResponse(
        id=framework.id,
        name=framework.name,
        description=framework.description,
        version=framework.version,
        controls_count=framework.controls_count,
        organization=framework.organization,
        url=framework.url,
    )


@router.post("/validate", response_model=ComplianceValidationResponse)
async def validate_compliance(
    data: ComplianceValidationRequest,
    db: DBSession,
    current_user: CurrentUser,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Validate incident compliance against frameworks.

    Validates the specified incident phase against the requested compliance
    frameworks and returns detailed results including compliance score,
    gaps, and recommendations.
    """
    # Map frontend framework IDs to backend IDs
    framework_mapping = {
        "bsi": "bsi_grundschutz",
        "nist": "nist_csf_2",
        "iso27001": "iso_27001",
        "iso27035": "iso_27035",
        "mitre": "mitre_attack",
        "nis2": "nis2",
        "owasp": "owasp_top_10",
    }

    # Convert framework IDs
    frameworks = [framework_mapping.get(f, f) for f in data.frameworks]

    # Perform validation
    results = await service.validate_phase_compliance(
        db=db,
        incident_id=data.incident_id,
        phase=data.phase,
        frameworks=frameworks,
        operator=current_user.username if hasattr(current_user, 'username') else str(current_user.id),
    )

    # Convert results to response format
    validation_results = {}
    total_score = 0.0

    for fw_id, result in results.items():
        # Map back to frontend ID
        frontend_id = next(
            (k for k, v in framework_mapping.items() if v == fw_id),
            fw_id
        )
        validation_results[frontend_id] = ValidationResultResponse(
            framework=frontend_id,
            compliant=result.compliant,
            score=result.score,
            total_controls=result.total_controls,
            compliant_count=result.compliant_count,
            partial_count=result.partial_count,
            gap_count=result.gap_count,
            gaps=result.gaps,
            recommendations=result.recommendations,
        )
        total_score += result.score

    # Calculate overall score
    overall_score = total_score / len(results) if results else 0.0

    return ComplianceValidationResponse(
        incident_id=data.incident_id,
        phase=data.phase,
        frameworks=data.frameworks,
        validation_results=validation_results,
        overall_score=round(overall_score, 1),
        validated_at=datetime.now(timezone.utc),
    )


class IncidentValidationRequest(BaseModel):
    """Request to validate all phases of an incident."""
    incident_id: str
    frameworks: List[str]


class PhaseValidationResult(BaseModel):
    """Validation result for a single phase and framework."""
    framework_id: str
    framework_name: str
    phase: str
    is_compliant: bool
    score: float
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    timestamp: str


@router.post("/validate/incident")
async def validate_incident_compliance(
    data: IncidentValidationRequest,
    db: DBSession,
    current_user: CurrentUser,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Validate compliance for all phases of an incident.

    Returns validation results grouped by phase and framework.
    """
    # Map frontend framework IDs to backend IDs
    framework_mapping = {
        "bsi": "bsi_grundschutz",
        "nist": "nist_csf_2",
        "iso27001": "iso_27001",
        "iso27035": "iso_27035",
        "mitre": "mitre_attack",
        "nis2": "nis2",
        "owasp": "owasp_top_10",
    }

    reverse_mapping = {v: k for k, v in framework_mapping.items()}
    backend_frameworks = [framework_mapping.get(f, f) for f in data.frameworks]
    operator = current_user.username if hasattr(current_user, 'username') else str(current_user.id)

    # Get validation results for all phases
    all_results = await service.validate_incident_compliance(
        db=db,
        incident_id=data.incident_id,
        frameworks=backend_frameworks,
        operator=operator,
    )

    # Convert to frontend format
    response: Dict[str, Dict[str, PhaseValidationResult]] = {}
    now = datetime.now(timezone.utc).isoformat()

    for phase, phase_results in all_results.items():
        response[phase] = {}
        for fw_id, result in phase_results.items():
            # Map back to frontend ID
            frontend_fw = reverse_mapping.get(fw_id, fw_id)

            # Get framework name
            framework_info = await service.get_framework(fw_id)
            fw_name = framework_info.name if framework_info else fw_id

            response[phase][frontend_fw] = PhaseValidationResult(
                framework_id=frontend_fw,
                framework_name=fw_name,
                phase=phase,
                is_compliant=result.compliant,
                score=result.score,
                checks=[
                    {
                        "control_id": c.get("control_id", ""),
                        "control_name": c.get("control_name", ""),
                        "status": c.get("status", "not_applicable"),
                        "evidence": c.get("evidence", []),
                        "notes": c.get("notes", ""),
                    }
                    for c in result.gaps  # gaps contains control check details
                ],
                gaps=[g.get("control_name", str(g)) if isinstance(g, dict) else str(g) for g in result.gaps],
                recommendations=result.recommendations,
                timestamp=now,
            ).model_dump()

    return response


class UnifiedControlResponse(BaseModel):
    """Unified control for frontend consumption."""
    id: str
    name: str
    description: str
    phase: str
    mappings: Dict[str, List[str]]


class CrossMappingUnifiedResponse(BaseModel):
    """Cross-framework mapping with unified controls."""
    unified_controls: List[UnifiedControlResponse]


@router.get("/cross-mapping")
async def get_cross_mapping(
    phase: Optional[str] = Query(None, description="Filter by IR phase"),
    current_user: CurrentUser = None,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get cross-framework control mapping.

    Returns a mapping of equivalent controls across different compliance
    frameworks (BSI, NIST, ISO, OWASP). Optionally filter by IR phase.
    """
    # Framework key mapping from backend to frontend
    framework_key_mapping = {
        "bsi_grundschutz": "bsi",
        "nist_csf_2": "nist",
        "nist_800_53": "nist",
        "iso_27001": "iso27001",
        "iso_27035": "iso27001",
        "owasp_top_10": "owasp",
    }

    if phase:
        mapping = await service.get_cross_framework_mapping(phase=phase)
        controls = mapping.get("controls", [])

        unified_controls = []
        for c in controls:
            # Convert framework_controls to mappings with frontend keys
            mappings = {}
            for fw_key, ctrl_list in c.get("framework_controls", {}).items():
                frontend_key = framework_key_mapping.get(fw_key, fw_key)
                if frontend_key not in mappings:
                    mappings[frontend_key] = []
                mappings[frontend_key].extend(ctrl_list)

            unified_controls.append(UnifiedControlResponse(
                id=c["unified_id"],
                name=c["name"],
                description=c["description"],
                phase=phase,
                mappings=mappings,
            ))

        return CrossMappingUnifiedResponse(unified_controls=unified_controls)
    else:
        # Get all controls from all phases
        all_phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
        unified_controls = []
        seen_ids = set()

        for p in all_phases:
            mapping = await service.get_cross_framework_mapping(phase=p)
            controls = mapping.get("controls", [])

            for c in controls:
                if c["unified_id"] in seen_ids:
                    continue
                seen_ids.add(c["unified_id"])

                # Convert framework_controls to mappings with frontend keys
                mappings = {}
                for fw_key, ctrl_list in c.get("framework_controls", {}).items():
                    frontend_key = framework_key_mapping.get(fw_key, fw_key)
                    if frontend_key not in mappings:
                        mappings[frontend_key] = []
                    mappings[frontend_key].extend(ctrl_list)

                unified_controls.append(UnifiedControlResponse(
                    id=c["unified_id"],
                    name=c["name"],
                    description=c["description"],
                    phase=p,
                    mappings=mappings,
                ))

        return CrossMappingUnifiedResponse(unified_controls=unified_controls)


@router.get("/cross-mapping/control/{control_id}", response_model=ControlDetailsResponse)
async def get_control_details(
    control_id: str,
    framework: str = Query(..., description="Framework of the control"),
    current_user: CurrentUser = None,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get detailed information about a control.

    Returns cross-framework references, evidence requirements, and
    equivalent controls in other frameworks.
    """
    # Map frontend framework IDs to backend IDs
    framework_mapping = {
        "bsi": "bsi_grundschutz",
        "nist": "nist_csf_2",
        "nist_csf": "nist_csf_2",
        "nist_800_53": "nist_800_53",
        "iso27001": "iso_27001",
        "iso_27001": "iso_27001",
        "iso27035": "iso_27035",
        "iso_27035": "iso_27035",
        "owasp": "owasp_top_10",
        "owasp_top_10": "owasp_top_10",
    }

    backend_fw = framework_mapping.get(framework, framework)
    details = await service.get_control_details(control_id, backend_fw)

    return ControlDetailsResponse(
        control_id=details.get("control_id", control_id),
        framework=framework,
        unified_id=details.get("unified_id"),
        name=details.get("name"),
        description=details.get("description"),
        ir_phases=details.get("ir_phases", []),
        keywords=details.get("keywords", []),
        equivalent_controls=details.get("equivalent_controls", {}),
        evidence_requirements=details.get("evidence_requirements", []),
        error=details.get("error"),
    )


@router.get("/cross-mapping/equivalent")
async def find_equivalent_controls(
    control_id: str = Query(..., description="Control ID to find equivalents for"),
    framework: str = Query(..., description="Framework of the source control"),
    current_user: CurrentUser = None,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Find equivalent controls in other frameworks.

    Given a control ID from one framework, returns the equivalent controls
    in all other supported frameworks.
    """
    # Map frontend framework IDs to backend IDs
    framework_mapping = {
        "bsi": "bsi_grundschutz",
        "nist": "nist_csf_2",
        "iso27001": "iso_27001",
        "owasp": "owasp_top_10",
    }

    backend_fw = framework_mapping.get(framework, framework)
    equivalents = await service.find_equivalent_controls(control_id, backend_fw)

    return {
        "control_id": control_id,
        "framework": framework,
        "equivalent_controls": equivalents,
    }


class ComplianceReportRequest(BaseModel):
    """Request for compliance report."""
    incident_id: str
    frameworks: List[str]


@router.post("/report", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    data: ComplianceReportRequest,
    db: DBSession,
    current_user: CurrentUser,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Get comprehensive compliance report for an incident.

    Generates a detailed compliance report covering all phases of the
    incident response, with scores and gaps for each selected framework.
    """
    # Map frontend framework IDs to backend IDs
    framework_mapping = {
        "bsi": "bsi_grundschutz",
        "nist": "nist_csf_2",
        "iso27001": "iso_27001",
        "iso27035": "iso_27035",
        "mitre": "mitre_attack",
        "nis2": "nis2",
        "owasp": "owasp_top_10",
    }

    backend_frameworks = [framework_mapping.get(f, f) for f in data.frameworks]
    operator = current_user.username if hasattr(current_user, 'username') else "system"

    report = await service.generate_compliance_report(
        db=db,
        incident_id=data.incident_id,
        frameworks=backend_frameworks,
        operator=operator,
    )

    # Calculate framework scores
    framework_scores = {}
    for fw_id in data.frameworks:
        backend_fw = framework_mapping.get(fw_id, fw_id)
        checks = report.results.get(backend_fw, [])
        if checks:
            compliant = sum(1 for c in checks if c.status.value == "compliant")
            total = len(checks)
            framework_scores[fw_id] = round((compliant / total * 100) if total > 0 else 0, 1)
        else:
            framework_scores[fw_id] = 0.0

    # Extract gaps and recommendations
    gaps = []
    recommendations = []
    critical_gaps = []

    for fw_checks in report.results.values():
        for check in fw_checks:
            if check.status.value == "gap":
                gap_info = {
                    "framework": check.framework.value,
                    "control_id": check.control_id,
                    "control_name": check.control_name,
                    "gap_description": check.gap_description,
                    "priority": check.remediation_priority,
                }
                gaps.append(gap_info)

                if check.remediation_priority == "high":
                    critical_gaps.append(gap_info)

                if check.recommendation:
                    recommendations.append(check.recommendation)

    return ComplianceReportResponse(
        incident_id=data.incident_id,
        frameworks=data.frameworks,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
        overall_compliance=report.compliance_score,
        total_controls=report.total_controls,
        compliant_count=report.compliant_count,
        partial_count=report.partial_count,
        gap_count=report.gap_count,
        framework_scores=framework_scores,
        gaps=gaps,
        recommendations=list(set(recommendations)),
        critical_gaps=critical_gaps,
    )


class ReportExportRequest(BaseModel):
    """Request to export compliance report."""
    incident_id: str
    frameworks: List[str]
    format: str = "markdown"


@router.post("/report/export")
async def export_compliance_report(
    data: ReportExportRequest,
    db: DBSession,
    current_user: CurrentUser,
    service: ComplianceService = Depends(get_compliance_service),
):
    """
    Export compliance report in specified format.

    Returns the compliance report as a formatted string (Markdown or JSON).
    """
    # Map frontend framework IDs to backend IDs
    framework_mapping = {
        "bsi": "bsi_grundschutz",
        "nist": "nist_csf_2",
        "iso27001": "iso_27001",
        "iso27035": "iso_27035",
        "mitre": "mitre_attack",
        "nis2": "nis2",
        "owasp": "owasp_top_10",
    }

    backend_frameworks = [framework_mapping.get(f, f) for f in data.frameworks]
    operator = current_user.username if hasattr(current_user, 'username') else "system"

    exported = await service.export_compliance_report(
        db=db,
        incident_id=data.incident_id,
        frameworks=backend_frameworks,
        format=data.format,
        operator=operator,
    )

    return {
        "incident_id": data.incident_id,
        "format": data.format,
        "content": exported,
    }


@router.post("/ioc/enrich", response_model=IOCEnrichmentResponse)
async def enrich_ioc(
    data: IOCEnrichmentRequest,
    current_user: CurrentUser,
):
    """
    Enrich an IOC with threat intelligence.

    Enriches the provided IOC (IP, domain, hash, URL, email) with threat
    intelligence from multiple sources including VirusTotal, AbuseIPDB,
    Shodan, GreyNoise, and AlienVault OTX.
    """
    enricher = get_ioc_enricher()

    # Enrich the IOC (synchronous call)
    result = enricher.enrich(data.value, data.ioc_type)

    # Map threat level to string
    threat_level_str = result.overall_threat_level.value if hasattr(result.overall_threat_level, 'value') else str(result.overall_threat_level)

    # Build source results list from dict
    source_results_list = []
    for source, sr in result.source_results.items():
        source_results_list.append({
            "source": source.value if hasattr(source, 'value') else str(source),
            "available": sr.available,
            "threat_level": sr.threat_level.value if hasattr(sr.threat_level, 'value') else str(sr.threat_level),
            "confidence": sr.confidence,
            "categories": sr.categories,
            "tags": sr.tags,
        })

    return IOCEnrichmentResponse(
        ioc_type=result.ioc_type.value if hasattr(result.ioc_type, 'value') else str(result.ioc_type),
        value=result.ioc_value,
        threat_level=threat_level_str,
        sources_checked=[s.value if hasattr(s, 'value') else str(s) for s in result.source_results.keys()],
        enrichment_results={
            "is_malicious": result.risk_score > 50,  # Derive from risk score
            "confidence": result.confidence,
            "mitre_techniques": [],  # Not available in EnrichmentResult
            "recommendations": result.recommended_actions,
            "source_results": source_results_list,
        },
        first_seen=result.first_seen_global,
        last_seen=result.last_seen_global,
        tags=result.tags,
    )


class IOCBatchEnrichmentRequest(BaseModel):
    """Request for batch IOC enrichment."""
    iocs: List[Dict[str, str]]  # List of {"type": "ip", "value": "1.2.3.4"}


@router.post("/ioc/enrich/batch")
async def enrich_iocs_batch(
    data: IOCBatchEnrichmentRequest,
    current_user: CurrentUser,
):
    """
    Enrich multiple IOCs in batch.

    Processes multiple IOCs and returns enrichment results for all.
    """
    enricher = get_ioc_enricher()

    # Convert to list of IOC values (enrich_batch expects list of strings)
    iocs = [item["value"] for item in data.iocs]

    # Enrich batch (synchronous call)
    results = enricher.enrich_batch(iocs)

    # Build results list with correct attributes
    results_list = []
    for r in results:
        results_list.append({
            "ioc_type": r.ioc_type.value if hasattr(r.ioc_type, 'value') else str(r.ioc_type),
            "value": r.ioc_value,
            "threat_level": r.overall_threat_level.value if hasattr(r.overall_threat_level, 'value') else str(r.overall_threat_level),
            "is_malicious": r.risk_score > 50,
            "confidence": r.confidence,
            "tags": r.tags,
            "recommendations": r.recommended_actions,
        })

    # Build summary
    summary = {
        "total_iocs": len(results),
        "high_threat": sum(1 for r in results if r.overall_threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]),
        "medium_threat": sum(1 for r in results if r.overall_threat_level == ThreatLevel.MEDIUM),
        "low_threat": sum(1 for r in results if r.overall_threat_level == ThreatLevel.LOW),
        "clean": sum(1 for r in results if r.overall_threat_level == ThreatLevel.CLEAN),
    }

    return {
        "total": len(results),
        "results": results_list,
        "summary": summary,
    }


@router.get("/ioc/types")
async def get_ioc_types(current_user: CurrentUser):
    """Get available IOC types."""
    return {
        "types": [
            {"id": "ip", "name": "IP Address", "description": "IPv4 or IPv6 address"},
            {"id": "domain", "name": "Domain", "description": "Domain name"},
            {"id": "url", "name": "URL", "description": "Full URL"},
            {"id": "hash_md5", "name": "MD5 Hash", "description": "MD5 file hash"},
            {"id": "hash_sha1", "name": "SHA1 Hash", "description": "SHA1 file hash"},
            {"id": "hash_sha256", "name": "SHA256 Hash", "description": "SHA256 file hash"},
            {"id": "email", "name": "Email", "description": "Email address"},
            {"id": "file_path", "name": "File Path", "description": "File system path"},
        ]
    }


@router.post("/ioc/export")
async def export_ioc_results(
    data: IOCBatchEnrichmentRequest,
    format: str = Query("json", description="Export format: json, csv, markdown, stix"),
    current_user: CurrentUser = None,
):
    """
    Export IOC enrichment results in specified format.

    Supports JSON, CSV, Markdown, and STIX 2.1 formats.
    """
    enricher = get_ioc_enricher()

    # Enrich IOCs
    iocs = [(item["value"], item.get("type")) for item in data.iocs]
    results = await enricher.enrich_batch(iocs)

    # Export in requested format
    exported = enricher.export_results(results, format)

    return {
        "format": format,
        "content": exported,
        "ioc_count": len(results),
    }


class BSIMeldungRequest(BaseModel):
    """Request to create BSI Meldung."""
    incident_id: str
    incident_title: str
    incident_description: str
    incident_type: str
    severity: str
    detected_at: datetime
    kritis_sector: Optional[str] = None
    affected_systems: List[Dict[str, Any]] = Field(default_factory=list)
    is_kritis: bool = False
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_organization: Optional[str] = None


@router.post("/bsi/generate")
async def generate_bsi_meldung(
    data: BSIMeldungRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Generate BSI Meldung (notification) report.

    Generates a report in the format required for BSI incident notification
    as per German regulations (BSI-Gesetz, BSIG).
    """
    from src.integrations.bsi_meldung import ContactPerson, AffectedSystem

    generator = get_bsi_meldung_generator()

    # Map incident type to category
    category_mapping = {
        "malware": IncidentCategory.MALWARE,
        "ransomware": IncidentCategory.RANSOMWARE,
        "phishing": IncidentCategory.PHISHING,
        "ddos": IncidentCategory.DOS_DDOS,
        "dos_ddos": IncidentCategory.DOS_DDOS,
        "data_breach": IncidentCategory.DATA_BREACH,
        "unauthorized_access": IncidentCategory.UNAUTHORIZED_ACCESS,
        "apt": IncidentCategory.APT,
        "insider_threat": IncidentCategory.INSIDER_THREAT,
        "supply_chain": IncidentCategory.SUPPLY_CHAIN,
        "vulnerability_exploitation": IncidentCategory.VULNERABILITY_EXPLOITATION,
        "other": IncidentCategory.OTHER,
    }

    # Map severity to impact level
    impact_mapping = {
        "critical": ImpactLevel.CRITICAL,
        "high": ImpactLevel.HIGH,
        "medium": ImpactLevel.MEDIUM,
        "low": ImpactLevel.LOW,
        "unknown": ImpactLevel.UNKNOWN,
    }

    # Map KRITIS sector
    sector_mapping = {
        "energy": KRITISSector.ENERGY,
        "water": KRITISSector.WATER,
        "food": KRITISSector.FOOD,
        "health": KRITISSector.HEALTH,
        "finance": KRITISSector.FINANCE,
        "transport": KRITISSector.TRANSPORT,
        "it": KRITISSector.IT_TELECOM,
        "it_telecom": KRITISSector.IT_TELECOM,
        "it_telekommunikation": KRITISSector.IT_TELECOM,
        "media": KRITISSector.MEDIA,
        "government": KRITISSector.GOVERNMENT,
        "not_kritis": KRITISSector.NOT_KRITIS,
    }

    # Create contact person if provided
    contact = None
    if data.contact_name:
        contact = ContactPerson(
            name=data.contact_name,
            email=data.contact_email or "",
            phone=data.contact_phone,
            organization=data.contact_organization,
        )

    # Create affected systems
    affected_systems = [
        AffectedSystem(
            name=sys.get("name", "Unknown"),
            system_type=sys.get("type", "server"),
            criticality=sys.get("criticality", "medium"),
            affected_services=sys.get("services", []),
            data_classification=sys.get("data_classification"),
            user_count=sys.get("user_count"),
        )
        for sys in data.affected_systems
    ]

    # Build incident data for the generator
    incident_data = {
        "id": data.incident_id,
        "title": data.incident_title,
        "description": data.incident_description,
        "severity": data.severity,
        "detected_at": data.detected_at.isoformat() if data.detected_at else None,
        "category": category_mapping.get(data.incident_type, IncidentCategory.OTHER).value,
        "impact_level": impact_mapping.get(data.severity.lower(), ImpactLevel.MEDIUM).value,
        "affected_systems": [
            {
                "name": sys.name,
                "type": sys.system_type,
                "criticality": sys.criticality,
                "services": sys.affected_services,
            }
            for sys in affected_systems
        ],
    }

    # Build organization data
    organization_data = {
        "name": data.organization_name if hasattr(data, 'organization_name') else "",
        "address": data.organization_address if hasattr(data, 'organization_address') else "",
        "sector": sector_mapping.get(data.kritis_sector, KRITISSector.NOT_KRITIS).value if data.kritis_sector else "nicht_kritis",
        "is_kritis": data.is_kritis,
    }

    # Build contact data
    contact_data = {
        "name": data.contact_name or "",
        "email": data.contact_email or "",
        "phone": data.contact_phone or "",
        "organization": data.contact_organization if hasattr(data, 'contact_organization') else "",
    }

    # Create BSI Meldung
    meldung = generator.create_from_incident(
        incident_id=data.incident_id,
        incident_data=incident_data,
        organization_data=organization_data,
        contact_data=contact_data,
    )

    # Generate export
    markdown_export = generator.export_markdown(meldung)
    json_export = generator.export_json(meldung)

    return {
        "meldung_id": meldung.meldung_id,
        "incident_id": meldung.incident_id,
        "notification_type": meldung.notification_type.value,
        "category": meldung.incident_category.value,
        "impact_level": meldung.impact_level.value,
        "is_kritis": meldung.is_kritis_operator,
        "kritis_sector": meldung.organization_sector.value,
        "created_at": meldung.created_at.isoformat(),
        "affected_systems_count": len(meldung.affected_systems),
        "markdown_content": markdown_export,
        "json_content": json_export,
    }


@router.get("/bsi/sectors")
async def get_kritis_sectors(current_user: CurrentUser):
    """Get available KRITIS sectors."""
    generator = get_bsi_meldung_generator()
    return generator.get_kritis_sectors()


@router.get("/bsi/categories")
async def get_incident_categories(current_user: CurrentUser):
    """Get available incident categories."""
    generator = get_bsi_meldung_generator()
    return generator.get_incident_categories()


@router.get("/bsi/deadlines")
async def calculate_bsi_deadlines(
    detected_at: datetime = Query(..., description="When the incident was detected"),
    is_kritis: bool = Query(False, description="Is this a KRITIS operator"),
    current_user: CurrentUser = None,
):
    """Calculate BSI notification deadlines."""
    generator = get_bsi_meldung_generator()
    deadlines = generator.calculate_deadlines(detected_at, is_kritis)
    return deadlines


# =============================================================================
# NIS2 Directive Endpoints
# =============================================================================

class NIS2NotificationRequest(BaseModel):
    """Request to create NIS2 notification."""
    incident_id: str
    incident_title: str
    incident_description: str
    severity: str  # significant, substantial, minor
    detected_at: datetime
    sector: str
    member_state: str  # DE, FR, etc.
    entity_name: str
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    contact_role: Optional[str] = None
    affected_services: List[str] = Field(default_factory=list)
    affected_users: Optional[int] = None
    affected_countries: List[str] = Field(default_factory=list)
    data_breach: bool = False
    financial_impact: Optional[float] = None


@router.post("/nis2/notifications")
async def create_nis2_notification(
    data: NIS2NotificationRequest,
    current_user: CurrentUser,
):
    """
    Create a new NIS2 notification.

    Creates a notification according to NIS2 Directive requirements,
    including deadlines for early warning (24h), incident notification (72h),
    and final report (30 days).
    """
    from src.integrations.nis2_models import (
        NIS2ContactPerson,
        NIS2IncidentImpact,
    )

    manager = get_nis2_manager()

    # Map severity
    severity_mapping = {
        "significant": NIS2IncidentSeverity.SIGNIFICANT,
        "substantial": NIS2IncidentSeverity.SUBSTANTIAL,
        "minor": NIS2IncidentSeverity.MINOR,
    }

    # Map sector
    sector_mapping = {
        "energy": NIS2Sector.ENERGY,
        "transport": NIS2Sector.TRANSPORT,
        "banking": NIS2Sector.BANKING,
        "financial_market": NIS2Sector.FINANCIAL_MARKET,
        "health": NIS2Sector.HEALTH,
        "drinking_water": NIS2Sector.DRINKING_WATER,
        "waste_water": NIS2Sector.WASTE_WATER,
        "digital_infrastructure": NIS2Sector.DIGITAL_INFRASTRUCTURE,
        "ict_service_management": NIS2Sector.ICT_SERVICE_MANAGEMENT,
        "public_administration": NIS2Sector.PUBLIC_ADMINISTRATION,
        "space": NIS2Sector.SPACE,
        "postal": NIS2Sector.POSTAL,
        "waste_management": NIS2Sector.WASTE_MANAGEMENT,
        "chemicals": NIS2Sector.CHEMICALS,
        "food": NIS2Sector.FOOD,
        "manufacturing": NIS2Sector.MANUFACTURING,
        "digital_providers": NIS2Sector.DIGITAL_PROVIDERS,
        "research": NIS2Sector.RESEARCH,
    }

    # Create contact
    contact = NIS2ContactPerson(
        name=data.contact_name,
        email=data.contact_email,
        phone=data.contact_phone,
        role=data.contact_role,
    )

    # Create impact assessment
    impact = NIS2IncidentImpact(
        affected_services=data.affected_services,
        affected_users=data.affected_users,
        affected_member_states=data.affected_countries,
        data_breach=data.data_breach,
        financial_impact=data.financial_impact,
    )

    # Get entity type based on sector
    sector_enum = sector_mapping.get(data.sector.lower(), NIS2Sector.DIGITAL_INFRASTRUCTURE)
    entity_type = get_entity_type_for_sector(sector_enum)

    # Create notification with correct parameters
    notification = manager.create_notification(
        incident_id=data.incident_id,
        entity_type=entity_type,
        sector=sector_enum,
        organization_name=data.entity_name,
        member_state=data.member_state,
        detection_time=data.detected_at,
        primary_contact=contact,
    )

    # Get stored notification data with notification_id
    stored_notification = manager._notifications.get(data.incident_id, {})
    notification_id = stored_notification.get("notification_id", data.incident_id)

    # Get deadlines using incident_id
    deadlines = manager.get_deadlines(data.incident_id)

    return {
        "notification_id": notification_id,
        "incident_id": notification.incident_id,
        "entity_name": notification.organization_name,
        "entity_type": notification.entity_type.value,
        "sector": notification.sector.value,
        "member_state": notification.member_state,
        "created_at": notification.created_at.isoformat(),
        "deadlines": deadlines,
    }


@router.post("/nis2/notifications/{notification_id}/early-warning")
async def submit_nis2_early_warning(
    notification_id: str,
    initial_assessment: str,
    suspected_cause: Optional[str] = None,
    cross_border: bool = False,
    current_user: CurrentUser = None,
):
    """
    Submit early warning for NIS2 notification (required within 24 hours).
    """
    manager = get_nis2_manager()

    early_warning = manager.submit_early_warning(
        notification_id=notification_id,
        initial_assessment=initial_assessment,
        suspected_cause=suspected_cause,
        cross_border=cross_border,
    )

    if not early_warning:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "notification_id": notification_id,
        "early_warning_submitted": True,
        "submitted_at": early_warning.submitted_at.isoformat() if early_warning.submitted_at else None,
        "initial_assessment": early_warning.initial_assessment,
        "cross_border": early_warning.cross_border_impact,
    }


@router.post("/nis2/notifications/{notification_id}/incident-notification")
async def submit_nis2_incident_notification(
    notification_id: str,
    severity_assessment: str,
    root_cause: Optional[str] = None,
    mitigation_measures: List[str] = None,
    current_user: CurrentUser = None,
):
    """
    Submit incident notification for NIS2 (required within 72 hours).
    """
    manager = get_nis2_manager()

    incident_notification = manager.submit_incident_notification(
        notification_id=notification_id,
        severity_assessment=severity_assessment,
        root_cause=root_cause,
        mitigation_measures=mitigation_measures or [],
    )

    if not incident_notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "notification_id": notification_id,
        "incident_notification_submitted": True,
        "submitted_at": incident_notification.submitted_at.isoformat() if incident_notification.submitted_at else None,
        "severity_assessment": incident_notification.severity_assessment,
    }


@router.post("/nis2/notifications/{notification_id}/final-report")
async def submit_nis2_final_report(
    notification_id: str,
    detailed_description: str,
    threat_type: str,
    root_cause_analysis: str,
    mitigation_applied: List[str],
    lessons_learned: List[str],
    current_user: CurrentUser = None,
):
    """
    Submit final report for NIS2 notification (required within 30 days).
    """
    manager = get_nis2_manager()

    final_report = manager.submit_final_report(
        notification_id=notification_id,
        detailed_description=detailed_description,
        threat_type=threat_type,
        root_cause_analysis=root_cause_analysis,
        mitigation_applied=mitigation_applied,
        lessons_learned=lessons_learned,
    )

    if not final_report:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "notification_id": notification_id,
        "final_report_submitted": True,
        "submitted_at": final_report.submitted_at.isoformat() if final_report.submitted_at else None,
        "threat_type": final_report.threat_type,
    }


@router.get("/nis2/notifications/{notification_id}")
async def get_nis2_notification(
    notification_id: str,
    current_user: CurrentUser,
):
    """Get NIS2 notification details."""
    manager = get_nis2_manager()
    notification = manager.notifications.get(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    deadlines = manager.get_deadlines(notification_id)

    return {
        "notification_id": notification.notification_id,
        "incident_id": notification.incident_id,
        "entity_name": notification.entity_name,
        "entity_type": notification.entity_type.value,
        "sector": notification.sector.value,
        "member_state": notification.member_state,
        "severity": notification.severity.value,
        "status": notification.status.value,
        "created_at": notification.created_at.isoformat(),
        "deadlines": deadlines,
        "early_warning": {
            "submitted": notification.early_warning is not None,
            "data": {
                "initial_assessment": notification.early_warning.initial_assessment,
                "cross_border": notification.early_warning.cross_border_impact,
            } if notification.early_warning else None,
        },
        "incident_notification": {
            "submitted": notification.incident_notification is not None,
            "data": {
                "severity_assessment": notification.incident_notification.severity_assessment,
            } if notification.incident_notification else None,
        },
        "final_report": {
            "submitted": notification.final_report is not None,
            "data": {
                "threat_type": notification.final_report.threat_type,
            } if notification.final_report else None,
        },
    }


@router.get("/nis2/notifications/{notification_id}/export")
async def export_nis2_notification(
    notification_id: str,
    format: str = Query("markdown", description="Export format: markdown or json"),
    current_user: CurrentUser = None,
):
    """Export NIS2 notification report."""
    manager = get_nis2_manager()
    exported = manager.export_notification_report(notification_id, format)

    if not exported:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "notification_id": notification_id,
        "format": format,
        "content": exported,
    }


@router.get("/nis2/sectors")
async def get_nis2_sectors(current_user: CurrentUser):
    """Get available NIS2 sectors with entity type classification."""
    from src.integrations.nis2_models import SECTOR_ENTITY_TYPE

    sectors = []
    for sector in NIS2Sector:
        entity_type = SECTOR_ENTITY_TYPE.get(sector, NIS2EntityType.IMPORTANT)
        sectors.append({
            "id": sector.value,
            "name": sector.value.replace("_", " ").title(),
            "entity_type": entity_type.value,
            "is_essential": entity_type == NIS2EntityType.ESSENTIAL,
        })

    return {"sectors": sectors}


@router.get("/nis2/member-states")
async def get_nis2_member_states(current_user: CurrentUser):
    """Get EU member states with CSIRT contacts."""
    return {"member_states": EU_MEMBER_STATES}


@router.get("/nis2/deadlines")
async def calculate_nis2_deadlines(
    detected_at: datetime = Query(..., description="When the incident was detected"),
    current_user: CurrentUser = None,
):
    """Calculate NIS2 notification deadlines."""
    manager = get_nis2_manager()
    deadlines = manager.calculate_deadlines(detected_at)
    return deadlines


# =============================================================================
# OWASP Top 10 Endpoints
# =============================================================================

@router.get("/owasp/risks")
async def get_owasp_risks(current_user: CurrentUser):
    """
    Get all OWASP Top 10 2021 risks.

    Returns comprehensive information about each risk including
    attack vectors, CWE mappings, and prevention strategies.
    """
    owasp = get_owasp_integration()
    risks = owasp.get_all_risks()

    return {
        "version": "2021",
        "risks": [
            {
                "id": risk.id,
                "name": risk.name,
                "description": risk.description,
                "cwe_mapped": risk.cwe_mapped,
                "attack_vectors": risk.attack_vectors,
                "impact": risk.impact,
                "prevention": risk.prevention,
                "ir_phase_relevance": risk.ir_phase_relevance,
            }
            for risk in risks
        ],
    }


@router.get("/owasp/risks/{risk_id}")
async def get_owasp_risk(
    risk_id: str,
    current_user: CurrentUser,
):
    """
    Get detailed information about a specific OWASP risk.

    Includes attack vectors, CWE mappings, prevention strategies,
    and relevant IR phases.
    """
    owasp = get_owasp_integration()
    risk = owasp.get_risk(risk_id.upper())

    if not risk:
        raise HTTPException(status_code=404, detail=f"OWASP risk {risk_id} not found")

    # Get cheat sheets for this risk
    cheat_sheets = []
    for cwe in risk.cwe_mapped[:3]:  # Limit to avoid too many lookups
        sheet = owasp.get_cheat_sheet(f"CWE-{cwe}")
        if sheet:
            cheat_sheets.append({
                "name": sheet.name,
                "url": sheet.url,
                "key_points": sheet.key_points,
            })

    return {
        "id": risk.id,
        "name": risk.name,
        "description": risk.description,
        "cwe_mapped": risk.cwe_mapped,
        "attack_vectors": risk.attack_vectors,
        "impact": risk.impact,
        "prevention": risk.prevention,
        "ir_phase_relevance": risk.ir_phase_relevance,
        "cheat_sheets": cheat_sheets,
    }


@router.get("/owasp/phase/{phase}")
async def get_owasp_phase_recommendations(
    phase: str,
    current_user: CurrentUser,
):
    """
    Get OWASP recommendations for a specific IR phase.

    Returns risks and recommendations relevant to the specified
    incident response phase.
    """
    owasp = get_owasp_integration()
    recommendations = owasp.get_phase_recommendations(phase)

    return {
        "phase": phase,
        "recommendations": recommendations,
    }


class OWASPIndicatorsRequest(BaseModel):
    """Request to identify OWASP risks from indicators."""
    indicators: List[str]


@router.post("/owasp/identify")
async def identify_owasp_risks(
    data: OWASPIndicatorsRequest,
    current_user: CurrentUser,
):
    """
    Identify potential OWASP risks from incident indicators.

    Analyzes the provided indicators (e.g., "SQL error", "XSS",
    "authentication bypass") and identifies matching OWASP risks.
    """
    owasp = get_owasp_integration()
    identified = owasp.identify_risks_from_indicators(data.indicators)

    return {
        "indicators_analyzed": len(data.indicators),
        "risks_identified": len(identified),
        "risks": [
            {
                "id": risk.get("id"),
                "name": risk.get("name"),
                "description": risk.get("description"),
                "prevention": risk.get("prevention", [])[:3],  # Top 3 prevention measures
            }
            for risk in identified
        ],
    }


class OWASPRemediationRequest(BaseModel):
    """Request for remediation guidance."""
    risk_id: str
    context: Optional[str] = None


@router.post("/owasp/remediation")
async def get_owasp_remediation(
    data: OWASPRemediationRequest,
    current_user: CurrentUser,
):
    """
    Get detailed remediation guidance for an OWASP risk.

    Returns actionable remediation steps, cheat sheets,
    and prevention measures for the specified risk.
    """
    owasp = get_owasp_integration()
    guidance = owasp.get_remediation_guidance(data.risk_id.upper())

    if not guidance:
        raise HTTPException(status_code=404, detail=f"OWASP risk {data.risk_id} not found")

    return guidance


@router.post("/owasp/validate/{phase}")
async def validate_owasp_compliance(
    phase: str,
    incident_data: Dict[str, Any],
    current_user: CurrentUser,
):
    """
    Validate OWASP compliance for an incident phase.

    Checks if the incident handling for the specified phase
    follows OWASP security recommendations.
    """
    owasp = get_owasp_integration()
    result = owasp.validate_phase_compliance(phase, incident_data)

    return {
        "phase": phase,
        "compliant": result.get("compliant", False),
        "score": result.get("score", 0.0),
        "checks": result.get("checks", []),
        "recommendations": result.get("recommendations", []),
    }
