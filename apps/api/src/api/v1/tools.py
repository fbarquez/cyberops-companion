"""
Tools endpoints (Playbook, Templates, Lessons, MITRE Navigator, Simulations).

Provides:
- Playbook generation and templates
- Communication templates
- Lessons learned management
- MITRE ATT&CK Navigator integration
- Training simulations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from src.api.deps import DBSession, CurrentUser
from src.services.playbook_service import PlaybookService, get_playbook_service
from src.services.simulation_service import SimulationService, get_simulation_service
from src.integrations.mitre_integration import (
    MITREIntegration,
    get_mitre_integration,
    ATTACKTechnique,
)


router = APIRouter()


# ============ Playbook Generator ============

class PlaybookGenerateRequest(BaseModel):
    """Request to generate a playbook."""
    incident_type: str
    severity: str
    affected_systems: List[str] = Field(default_factory=list)
    compliance_frameworks: Optional[List[str]] = None


class PlaybookTypeResponse(BaseModel):
    """Playbook type response."""
    id: str
    name: str
    description: str
    available: bool = True


@router.get("/playbook/types", response_model=List[PlaybookTypeResponse])
async def get_playbook_types(
    current_user: CurrentUser,
    service: PlaybookService = Depends(get_playbook_service),
):
    """Get available playbook types."""
    types = service.get_playbook_types()
    return [
        PlaybookTypeResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            available=t.available,
        )
        for t in types
    ]


@router.get("/playbook/{playbook_id}")
async def get_playbook(
    playbook_id: str,
    current_user: CurrentUser,
    service: PlaybookService = Depends(get_playbook_service),
):
    """Get a specific playbook by ID."""
    playbook = service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {playbook_id}")
    return playbook.model_dump()


@router.post("/playbook/generate")
async def generate_playbook(
    data: PlaybookGenerateRequest,
    current_user: CurrentUser,
    service: PlaybookService = Depends(get_playbook_service),
):
    """Generate a customized incident response playbook."""
    return service.generate_playbook(
        incident_type=data.incident_type,
        severity=data.severity,
        affected_systems=data.affected_systems,
        compliance_frameworks=data.compliance_frameworks,
    )


@router.get("/playbook/{playbook_id}/export")
async def export_playbook(
    playbook_id: str,
    format: str = Query("markdown", pattern="^(markdown|json)$"),
    current_user: CurrentUser = None,
    service: PlaybookService = Depends(get_playbook_service),
):
    """Export a playbook in the specified format."""
    content = service.export_playbook(playbook_id, format)
    if not content:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {playbook_id}")
    return {"playbook_id": playbook_id, "format": format, "content": content}


# ============ Communication Templates ============

class TemplateInfo(BaseModel):
    """Template information."""
    id: str
    name: str
    category: str
    description: str
    language: str


TEMPLATES = [
    {
        "id": "exec_summary",
        "name": {"en": "Executive Summary", "de": "Zusammenfassung für die Geschäftsleitung"},
        "category": "reporting",
        "description": {
            "en": "High-level incident summary for executives",
            "de": "Übersicht über den Vorfall für die Geschäftsleitung",
        },
    },
    {
        "id": "tech_report",
        "name": {"en": "Technical Report", "de": "Technischer Bericht"},
        "category": "reporting",
        "description": {
            "en": "Detailed technical incident report",
            "de": "Detaillierter technischer Vorfallbericht",
        },
    },
    {
        "id": "stakeholder_notification",
        "name": {"en": "Stakeholder Notification", "de": "Stakeholder-Benachrichtigung"},
        "category": "communication",
        "description": {
            "en": "Notification template for stakeholders",
            "de": "Benachrichtigungsvorlage für Stakeholder",
        },
    },
    {
        "id": "customer_notification",
        "name": {"en": "Customer Notification", "de": "Kundenbenachrichtigung"},
        "category": "communication",
        "description": {
            "en": "Notification template for affected customers",
            "de": "Benachrichtigungsvorlage für betroffene Kunden",
        },
    },
    {
        "id": "regulatory_notification",
        "name": {"en": "Regulatory Notification", "de": "Behördliche Meldung"},
        "category": "compliance",
        "description": {
            "en": "Template for regulatory body notification (BSI, GDPR)",
            "de": "Vorlage für Meldung an Aufsichtsbehörden (BSI, DSGVO)",
        },
    },
    {
        "id": "press_release",
        "name": {"en": "Press Release", "de": "Pressemitteilung"},
        "category": "communication",
        "description": {
            "en": "Public communication template for media",
            "de": "Vorlage für öffentliche Kommunikation an Medien",
        },
    },
]


@router.get("/templates", response_model=List[TemplateInfo])
async def get_templates(
    category: Optional[str] = None,
    lang: str = Query("en", pattern="^(en|de)$"),
    current_user: CurrentUser = None,
):
    """Get available communication templates."""
    templates = []
    for t in TEMPLATES:
        if category and t["category"] != category:
            continue
        templates.append(TemplateInfo(
            id=t["id"],
            name=t["name"].get(lang, t["name"]["en"]),
            category=t["category"],
            description=t["description"].get(lang, t["description"]["en"]),
            language=lang,
        ))
    return templates


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    incident_id: Optional[str] = None,
    lang: str = Query("en", pattern="^(en|de)$"),
    current_user: CurrentUser = None,
):
    """Get a specific template, optionally populated with incident data."""
    template_data = next((t for t in TEMPLATES if t["id"] == template_id), None)
    if not template_data:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    # Generate template content
    content = _generate_template_content(template_id, lang)

    return {
        "id": template_id,
        "name": template_data["name"].get(lang, template_data["name"]["en"]),
        "category": template_data["category"],
        "content": content,
        "placeholders": ["incident_id", "incident_title", "severity", "date", "affected_systems"],
        "populated": incident_id is not None,
    }


def _generate_template_content(template_id: str, lang: str) -> str:
    """Generate template content based on ID and language."""
    templates_content = {
        "exec_summary": {
            "en": """# Executive Incident Summary

**Incident ID:** {{incident_id}}
**Date:** {{date}}
**Severity:** {{severity}}

## Summary
Brief description of the incident and its business impact.

## Current Status
- Phase: [Detection/Analysis/Containment/Eradication/Recovery]
- Status: [Active/Contained/Resolved]

## Business Impact
- Affected Systems: {{affected_systems}}
- Data Impact: [To be determined]
- Operational Impact: [Description]

## Actions Taken
1. [Action 1]
2. [Action 2]

## Next Steps
- [Next step 1]
- [Next step 2]

## Recommendations
[Management recommendations]
""",
            "de": """# Zusammenfassung für die Geschäftsleitung

**Vorfall-ID:** {{incident_id}}
**Datum:** {{date}}
**Schweregrad:** {{severity}}

## Zusammenfassung
Kurze Beschreibung des Vorfalls und seiner geschäftlichen Auswirkungen.

## Aktueller Status
- Phase: [Erkennung/Analyse/Eindämmung/Beseitigung/Wiederherstellung]
- Status: [Aktiv/Eingedämmt/Behoben]

## Geschäftliche Auswirkungen
- Betroffene Systeme: {{affected_systems}}
- Datenauswirkung: [Zu ermitteln]
- Betriebliche Auswirkung: [Beschreibung]

## Durchgeführte Maßnahmen
1. [Maßnahme 1]
2. [Maßnahme 2]

## Nächste Schritte
- [Nächster Schritt 1]
- [Nächster Schritt 2]

## Empfehlungen
[Empfehlungen für das Management]
""",
        },
        "regulatory_notification": {
            "en": """# Regulatory Incident Notification

**To:** [Regulatory Authority]
**From:** [Organization Name]
**Date:** {{date}}
**Reference:** {{incident_id}}

## Incident Details
- Detection Date: {{date}}
- Incident Type: [Type]
- Severity: {{severity}}

## Description
[Detailed description of the incident]

## Affected Data
- Personal Data: [Yes/No]
- Categories of Data: [Description]
- Number of Affected Individuals: [Number]

## Measures Taken
[Description of containment and remediation measures]

## Contact Information
[Contact details for follow-up]
""",
            "de": """# Meldung an Aufsichtsbehörde

**An:** [Aufsichtsbehörde]
**Von:** [Organisationsname]
**Datum:** {{date}}
**Referenz:** {{incident_id}}

## Vorfalldetails
- Erkennungsdatum: {{date}}
- Vorfalltyp: [Typ]
- Schweregrad: {{severity}}

## Beschreibung
[Detaillierte Beschreibung des Vorfalls]

## Betroffene Daten
- Personenbezogene Daten: [Ja/Nein]
- Datenkategorien: [Beschreibung]
- Anzahl betroffener Personen: [Anzahl]

## Ergriffene Maßnahmen
[Beschreibung der Eindämmungs- und Behebungsmaßnahmen]

## Kontaktinformationen
[Kontaktdaten für Rückfragen]
""",
        },
    }

    content = templates_content.get(template_id, {}).get(lang)
    if not content:
        content = f"# {template_id}\n\nTemplate content placeholder for {{{{incident_id}}}}"
    return content


# ============ Lessons Learned ============

class LessonCreate(BaseModel):
    """Create a lesson learned."""
    incident_id: str
    title: str
    category: str
    description: str
    recommendations: List[str]
    tags: Optional[List[str]] = None


class LessonUpdate(BaseModel):
    """Update a lesson learned."""
    title: Optional[str] = None
    description: Optional[str] = None
    recommendations: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# In-memory lessons storage (would be database in production)
_lessons: Dict[str, Dict] = {}


@router.get("/lessons")
async def get_lessons(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: CurrentUser = None,
):
    """Get lessons learned."""
    lessons = list(_lessons.values())

    if category:
        lessons = [l for l in lessons if l.get("category") == category]
    if tag:
        lessons = [l for l in lessons if tag in l.get("tags", [])]

    return {
        "lessons": lessons,
        "total": len(lessons),
        "categories": ["detection", "response", "prevention", "communication", "process"],
    }


@router.post("/lessons")
async def create_lesson(
    data: LessonCreate,
    current_user: CurrentUser,
):
    """Create a new lesson learned."""
    lesson_id = f"lesson-{len(_lessons) + 1}"
    lesson = {
        "id": lesson_id,
        "incident_id": data.incident_id,
        "title": data.title,
        "category": data.category,
        "description": data.description,
        "recommendations": data.recommendations,
        "tags": data.tags or [],
        "created_by": str(current_user.id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _lessons[lesson_id] = lesson
    return lesson


@router.patch("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: str,
    data: LessonUpdate,
    current_user: CurrentUser,
):
    """Update a lesson learned."""
    if lesson_id not in _lessons:
        raise HTTPException(status_code=404, detail=f"Lesson not found: {lesson_id}")

    lesson = _lessons[lesson_id]
    if data.title is not None:
        lesson["title"] = data.title
    if data.description is not None:
        lesson["description"] = data.description
    if data.recommendations is not None:
        lesson["recommendations"] = data.recommendations
    if data.tags is not None:
        lesson["tags"] = data.tags

    lesson["updated_at"] = datetime.now(timezone.utc).isoformat()
    lesson["updated_by"] = str(current_user.id)

    return lesson


# ============ MITRE Navigator ============

class TechniqueResponse(BaseModel):
    """MITRE ATT&CK technique response."""
    technique_id: str
    name: str
    description: str
    tactics: List[str]
    is_subtechnique: bool
    parent_technique: Optional[str]
    platforms: List[str]
    url: str
    mitigations: List[Dict[str, str]]


class MITREMapRequest(BaseModel):
    """Request to map incident to MITRE."""
    incident_id: str
    techniques: List[str]
    notes: Optional[str] = None


@router.get("/mitre/techniques")
async def get_mitre_techniques(
    tactic: Optional[str] = None,
    phase: Optional[str] = None,
    current_user: CurrentUser = None,
    mitre: MITREIntegration = Depends(get_mitre_integration),
):
    """Get MITRE ATT&CK techniques."""
    if phase:
        techniques = mitre.get_techniques_for_phase(phase)
    elif tactic:
        techniques = mitre.get_techniques_for_tactic(tactic)
    else:
        techniques = mitre.get_all_techniques()

    return {
        "version": "v14",
        "tactics": [t["short_name"] for t in mitre.get_all_tactics()],
        "techniques": [
            TechniqueResponse(
                technique_id=t.technique_id,
                name=t.name,
                description=t.description,
                tactics=t.tactics,
                is_subtechnique=t.is_subtechnique,
                parent_technique=t.parent_technique,
                platforms=t.platforms,
                url=t.url,
                mitigations=t.mitigations,
            ).model_dump()
            for t in techniques
        ],
        "total": len(techniques),
    }


@router.get("/mitre/tactics")
async def get_mitre_tactics(
    current_user: CurrentUser = None,
    mitre: MITREIntegration = Depends(get_mitre_integration),
):
    """Get all MITRE ATT&CK tactics."""
    return {
        "tactics": mitre.get_all_tactics(),
        "total": len(mitre.get_all_tactics()),
    }


@router.get("/mitre/techniques/{technique_id}")
async def get_mitre_technique(
    technique_id: str,
    current_user: CurrentUser = None,
    mitre: MITREIntegration = Depends(get_mitre_integration),
):
    """Get a specific MITRE ATT&CK technique."""
    technique = mitre.get_technique_by_id(technique_id)
    if not technique:
        raise HTTPException(status_code=404, detail=f"Technique not found: {technique_id}")

    return TechniqueResponse(
        technique_id=technique.technique_id,
        name=technique.name,
        description=technique.description,
        tactics=technique.tactics,
        is_subtechnique=technique.is_subtechnique,
        parent_technique=technique.parent_technique,
        platforms=technique.platforms,
        url=technique.url,
        mitigations=technique.mitigations,
    ).model_dump()


@router.post("/mitre/map")
async def map_to_mitre(
    data: MITREMapRequest,
    db: DBSession,
    current_user: CurrentUser,
    mitre: MITREIntegration = Depends(get_mitre_integration),
):
    """Map incident techniques to MITRE ATT&CK and generate Navigator layer."""
    # Generate Navigator layer
    layer = mitre.generate_navigator_layer(
        techniques=data.techniques,
        layer_name=f"Incident {data.incident_id}",
        description=data.notes or f"Techniques mapped for incident {data.incident_id}",
    )

    return {
        "incident_id": data.incident_id,
        "mapped_techniques": data.techniques,
        "navigator_layer": layer,
        "mapped_at": datetime.now(timezone.utc).isoformat(),
        "download_url": f"/api/v1/tools/mitre/layer/{data.incident_id}",
    }


@router.get("/mitre/ransomware-techniques")
async def get_ransomware_techniques(
    current_user: CurrentUser = None,
    mitre: MITREIntegration = Depends(get_mitre_integration),
):
    """Get MITRE ATT&CK techniques commonly used by ransomware."""
    techniques = mitre.get_ransomware_techniques()
    return {
        "techniques": [
            TechniqueResponse(
                technique_id=t.technique_id,
                name=t.name,
                description=t.description,
                tactics=t.tactics,
                is_subtechnique=t.is_subtechnique,
                parent_technique=t.parent_technique,
                platforms=t.platforms,
                url=t.url,
                mitigations=t.mitigations,
            ).model_dump()
            for t in techniques
        ],
        "total": len(techniques),
    }


# ============ Simulations ============

class ScenarioResponse(BaseModel):
    """Simulation scenario response."""
    id: str
    name: str
    description: str
    difficulty: str
    estimated_duration: str
    objectives: List[str]


@router.get("/simulations/scenarios")
async def get_simulation_scenarios(
    difficulty: Optional[str] = None,
    current_user: CurrentUser = None,
    service: SimulationService = Depends(get_simulation_service),
):
    """Get available simulation scenarios."""
    scenarios = service.get_scenarios(difficulty)
    return {
        "scenarios": [
            ScenarioResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                difficulty=s.difficulty,
                estimated_duration=s.estimated_duration,
                objectives=s.objectives,
            ).model_dump()
            for s in scenarios
        ],
        "total": len(scenarios),
    }


@router.get("/simulations/scenarios/{scenario_id}")
async def get_simulation_scenario(
    scenario_id: str,
    current_user: CurrentUser = None,
    service: SimulationService = Depends(get_simulation_service),
):
    """Get a specific simulation scenario with full details."""
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    return scenario.model_dump()


@router.post("/simulations/scenarios/{scenario_id}/start")
async def start_simulation(
    scenario_id: str,
    current_user: CurrentUser,
    service: SimulationService = Depends(get_simulation_service),
):
    """Start a simulation scenario."""
    try:
        session = service.start_simulation(
            scenario_id=scenario_id,
            user_id=str(current_user.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    scenario = service.get_scenario(scenario_id)

    return {
        "session_id": session.session_id,
        "scenario_id": scenario_id,
        "started_at": session.started_at,
        "status": session.status,
        "current_phase": session.current_phase,
        "scenario": {
            "name": scenario.name if scenario else scenario_id,
            "background": scenario.background if scenario else "",
            "initial_situation": scenario.initial_situation if scenario else "",
            "objectives": scenario.objectives if scenario else [],
        },
        "artifacts": service.get_scenario_artifacts(scenario_id),
    }


@router.get("/simulations/sessions/{session_id}")
async def get_simulation_session(
    session_id: str,
    current_user: CurrentUser,
    service: SimulationService = Depends(get_simulation_service),
):
    """Get a simulation session status."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return session.model_dump()


@router.post("/simulations/sessions/{session_id}/complete")
async def complete_simulation(
    session_id: str,
    current_user: CurrentUser,
    service: SimulationService = Depends(get_simulation_service),
):
    """Complete a simulation session and get the score."""
    session = service.complete_simulation(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "score": session.score,
        "completed_objectives": session.completed_objectives,
        "findings": session.findings,
        "hints_used": session.hints_used,
    }
