"""
Executive Dashboard Components for IR Companion.

Professional, minimalist dashboard for management-level visibility.
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import io

from src.utils.translations import t

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Alert:
    severity: AlertSeverity
    title: str
    message: str


@dataclass
class SLADeadline:
    name: str
    deadline: datetime
    regulation: str
    status: str  # on_track, at_risk, breached


@dataclass
class IncidentMetrics:
    time_since_detection: timedelta = field(default_factory=lambda: timedelta(0))
    overall_progress: float = 0.0
    phase_progress: float = 0.0
    checklist_completion: float = 0.0
    mandatory_items_complete: int = 0
    mandatory_items_total: int = 0
    phase_completion: Dict[str, float] = field(default_factory=dict)
    affected_systems_count: int = 0
    evidence_entries_count: int = 0
    decisions_made_count: int = 0
    critical_actions_pending: int = 0
    actions_last_hour: int = 0
    compliance_score: float = 0.0
    frameworks_validated: int = 0
    compliance_gaps: int = 0
    risk_level: str = "unknown"
    risk_score: int = 0
    containment_status: str = "not_started"
    active_alerts: List[Alert] = field(default_factory=list)
    deadlines: List[SLADeadline] = field(default_factory=list)


def calculate_incident_metrics(
    incident,
    phase_tracker,
    checklists: Dict,
    evidence_entries: List,
    decisions: List,
    compliance_results: Optional[Dict] = None,
) -> IncidentMetrics:
    """Calculate metrics for the incident."""
    metrics = IncidentMetrics()
    now = datetime.now(timezone.utc)

    # Time metrics
    if incident and incident.created_at:
        created = incident.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        metrics.time_since_detection = now - created

    # Phase progress
    phase_order = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
    current_phase = "detection"

    if phase_tracker:
        current_phase = phase_tracker.current_phase.value
        if current_phase in phase_order:
            current_idx = phase_order.index(current_phase)
            metrics.overall_progress = (current_idx / len(phase_order)) * 100

            if current_idx >= 3:
                metrics.containment_status = "eradicated"
            elif current_idx >= 2:
                metrics.containment_status = "contained"
            elif current_idx >= 1:
                metrics.containment_status = "analyzing"
            else:
                metrics.containment_status = "detecting"

    # Checklist metrics
    total_items = 0
    completed_items = 0
    mandatory_total = 0
    mandatory_complete = 0
    critical_pending = 0

    for phase_name, checklist in checklists.items():
        phase_total = 0
        phase_complete = 0

        if checklist and hasattr(checklist, 'items'):
            for item in checklist.items:
                total_items += 1
                phase_total += 1

                if hasattr(item, 'status') and item.status in ["completed", "skipped"]:
                    completed_items += 1
                    phase_complete += 1

                if hasattr(item, 'required') and item.required:
                    mandatory_total += 1
                    if hasattr(item, 'status') and item.status in ["completed", "skipped"]:
                        mandatory_complete += 1
                    elif hasattr(item, 'forensic_critical') and item.forensic_critical:
                        critical_pending += 1

        metrics.phase_completion[phase_name] = (phase_complete / phase_total * 100) if phase_total > 0 else 0

    metrics.checklist_completion = (completed_items / total_items * 100) if total_items > 0 else 0
    metrics.mandatory_items_complete = mandatory_complete
    metrics.mandatory_items_total = mandatory_total
    metrics.critical_actions_pending = critical_pending

    # Current phase progress
    if current_phase in checklists and checklists[current_phase]:
        checklist = checklists[current_phase]
        phase_total = len(checklist.items) if hasattr(checklist, 'items') else 0
        phase_complete = sum(
            1 for item in checklist.items
            if hasattr(item, 'status') and item.status in ["completed", "skipped"]
        ) if hasattr(checklist, 'items') else 0
        metrics.phase_progress = (phase_complete / phase_total * 100) if phase_total > 0 else 0

    # Evidence and decisions
    metrics.evidence_entries_count = len(evidence_entries) if evidence_entries else 0
    metrics.decisions_made_count = len(decisions) if decisions else 0

    # Activity metrics
    if evidence_entries:
        one_hour_ago = now - timedelta(hours=1)
        for entry in evidence_entries:
            if hasattr(entry, 'timestamp'):
                entry_time = entry.timestamp
                if entry_time.tzinfo is None:
                    entry_time = entry_time.replace(tzinfo=timezone.utc)
                if entry_time > one_hour_ago:
                    metrics.actions_last_hour += 1

    # Affected systems
    affected_systems = set()
    if evidence_entries:
        for entry in evidence_entries:
            if hasattr(entry, 'system_id') and entry.system_id:
                affected_systems.add(entry.system_id)
    metrics.affected_systems_count = max(len(affected_systems), 1)

    # Risk calculation
    risk_score = 50
    if metrics.critical_actions_pending > 3:
        risk_score += 40
    elif metrics.critical_actions_pending > 0:
        risk_score += 20
    if metrics.containment_status == "detecting":
        risk_score += 20
    elif metrics.containment_status == "analyzing":
        risk_score += 10
    elif metrics.containment_status in ["contained", "eradicated"]:
        risk_score -= 20
    if metrics.overall_progress > 50:
        risk_score -= 15

    metrics.risk_score = max(0, min(100, risk_score))

    if metrics.risk_score >= 80:
        metrics.risk_level = "critical"
    elif metrics.risk_score >= 60:
        metrics.risk_level = "high"
    elif metrics.risk_score >= 40:
        metrics.risk_level = "medium"
    else:
        metrics.risk_level = "low"

    # Alerts
    metrics.active_alerts = _generate_alerts(metrics)

    # Deadlines
    if incident and incident.created_at:
        metrics.deadlines = _calculate_deadlines(incident.created_at)

    # Compliance
    if compliance_results:
        total_checks = 0
        compliant_checks = 0
        gaps = 0
        for phase_results in compliance_results.values():
            if isinstance(phase_results, dict):
                for fw_checks in phase_results.values():
                    if isinstance(fw_checks, list):
                        for check in fw_checks:
                            total_checks += 1
                            if hasattr(check, 'status'):
                                if check.status.value == "compliant":
                                    compliant_checks += 1
                                elif check.status.value == "gap":
                                    gaps += 1
        metrics.compliance_score = (compliant_checks / total_checks * 100) if total_checks > 0 else 0
        metrics.compliance_gaps = gaps
        metrics.frameworks_validated = len(compliance_results)

    return metrics


def _generate_alerts(metrics: IncidentMetrics) -> List[Alert]:
    """Generate alerts based on current state."""
    alerts = []
    hours_elapsed = metrics.time_since_detection.total_seconds() / 3600

    if metrics.critical_actions_pending > 0:
        alerts.append(Alert(
            severity=AlertSeverity.CRITICAL,
            title="Kritische Aktionen ausstehend",
            message=f"{metrics.critical_actions_pending} forensisch kritische Aufgaben offen",
        ))

    if hours_elapsed > 24 and metrics.containment_status in ["detecting", "analyzing"]:
        alerts.append(Alert(
            severity=AlertSeverity.CRITICAL,
            title="Eindaemmung ueberfaellig",
            message="Vorfall seit mehr als 24h ohne Eindaemmung",
        ))

    if metrics.actions_last_hour == 0 and hours_elapsed > 1:
        alerts.append(Alert(
            severity=AlertSeverity.WARNING,
            title="Keine aktuelle Aktivitaet",
            message="Keine Aktionen in der letzten Stunde",
        ))

    return alerts


def _calculate_deadlines(incident_start: datetime) -> List[SLADeadline]:
    """Calculate regulatory deadlines."""
    deadlines = []
    now = datetime.now(timezone.utc)

    if incident_start.tzinfo is None:
        incident_start = incident_start.replace(tzinfo=timezone.utc)

    # KRITIS - 24h
    kritis_deadline = incident_start + timedelta(hours=24)
    kritis_status = "breached" if now > kritis_deadline else "at_risk" if now > kritis_deadline - timedelta(hours=4) else "on_track"
    deadlines.append(SLADeadline("KRITIS Erstmeldung", kritis_deadline, "BSIG 8b", kritis_status))

    # NIS2/GDPR - 72h
    nis2_deadline = incident_start + timedelta(hours=72)
    nis2_status = "breached" if now > nis2_deadline else "at_risk" if now > nis2_deadline - timedelta(hours=12) else "on_track"
    deadlines.append(SLADeadline("NIS2/DSGVO Meldung", nis2_deadline, "NIS2 Art.23", nis2_status))

    # Internal - 4h
    internal_deadline = incident_start + timedelta(hours=4)
    internal_status = "breached" if now > internal_deadline else "at_risk" if now > internal_deadline - timedelta(hours=1) else "on_track"
    deadlines.append(SLADeadline("Eindaemmung (intern)", internal_deadline, "Internal SLA", internal_status))

    # Final - 30d
    final_deadline = incident_start + timedelta(days=30)
    final_status = "breached" if now > final_deadline else "at_risk" if now > final_deadline - timedelta(days=5) else "on_track"
    deadlines.append(SLADeadline("Abschlussbericht", final_deadline, "BSI-KritisV", final_status))

    return deadlines


def render_executive_dashboard(
    incident,
    phase_tracker,
    checklists: Dict,
    evidence_entries: List,
    decisions: List,
    compliance_results: Optional[Dict],
    lang: str = "de",
) -> None:
    """Render the executive dashboard."""
    if not incident:
        st.warning(t("executive.no_incident", lang))
        return

    metrics = calculate_incident_metrics(
        incident, phase_tracker, checklists,
        evidence_entries, decisions, compliance_results,
    )

    # Header
    _render_header(incident, metrics)

    # Alerts
    if metrics.active_alerts:
        _render_alerts(metrics.active_alerts)

    st.divider()

    # Key Metrics Row
    _render_key_metrics(metrics)

    st.divider()

    # Main Content - 3 columns
    col1, col2, col3 = st.columns([2, 1.5, 1.5])

    with col1:
        _render_phase_timeline(phase_tracker, checklists)
        st.markdown("")
        _render_recent_activity(evidence_entries)

    with col2:
        _render_phase_progress(phase_tracker, metrics)
        st.markdown("")
        _render_deadlines(metrics)

    with col3:
        _render_risk_indicator(metrics)
        st.markdown("")
        _render_impact_summary(metrics)
        st.markdown("")
        _render_compliance_summary(metrics)

    st.divider()

    # Executive Summary
    _render_executive_summary(incident, metrics, phase_tracker)

    st.divider()

    # Export
    _render_export_options(incident, metrics, phase_tracker)


def _render_header(incident, metrics: IncidentMetrics) -> None:
    """Render dashboard header."""
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        st.markdown(f"## {incident.title}")
        sim_badge = " [SIMULATION]" if incident.is_simulation else ""
        st.caption(f"ID: {incident.id[:8]} | Analyst: {incident.analyst_name}{sim_badge}")

    with col2:
        risk_labels = {"critical": "KRITISCH", "high": "HOCH", "medium": "MITTEL", "low": "NIEDRIG", "unknown": "---"}
        st.metric("Risiko", risk_labels.get(metrics.risk_level, "---"), f"{metrics.risk_score}/100")

    with col3:
        hours = int(metrics.time_since_detection.total_seconds() // 3600)
        minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
        st.metric("Laufzeit", f"{hours:02d}:{minutes:02d}", "Stunden")

    with col4:
        st.metric("Fortschritt", f"{metrics.overall_progress:.0f}%", "Gesamt")


def _render_alerts(alerts: List[Alert]) -> None:
    """Render alert notifications."""
    for alert in alerts[:3]:
        if alert.severity == AlertSeverity.CRITICAL:
            st.error(f"**{alert.title}**: {alert.message}")
        elif alert.severity == AlertSeverity.WARNING:
            st.warning(f"**{alert.title}**: {alert.message}")


def _render_key_metrics(metrics: IncidentMetrics) -> None:
    """Render key metrics row."""
    cols = st.columns(8)

    data = [
        ("Phase", f"{metrics.phase_progress:.0f}%"),
        ("Pflicht", f"{metrics.mandatory_items_complete}/{metrics.mandatory_items_total}"),
        ("Kritisch", str(metrics.critical_actions_pending)),
        ("Beweise", str(metrics.evidence_entries_count)),
        ("Entscheid.", str(metrics.decisions_made_count)),
        ("Systeme", str(metrics.affected_systems_count)),
        ("Letzte 1h", str(metrics.actions_last_hour)),
        ("Compliance", f"{metrics.compliance_score:.0f}%"),
    ]

    for i, (label, value) in enumerate(data):
        with cols[i]:
            st.metric(label, value)


def _render_phase_timeline(phase_tracker, checklists: Dict) -> None:
    """Render phase timeline."""
    st.markdown("#### Phasen-Timeline")

    phase_order = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
    phase_labels = {
        "detection": "Erkennung",
        "analysis": "Analyse",
        "containment": "Eindaemmung",
        "eradication": "Beseitigung",
        "recovery": "Wiederherst.",
        "post_incident": "Nachbereitung",
    }

    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"
    current_idx = phase_order.index(current_phase) if current_phase in phase_order else 0

    # Use columns for timeline
    cols = st.columns(len(phase_order))

    for i, phase in enumerate(phase_order):
        with cols[i]:
            # Calculate completion
            completion = 0
            if phase in checklists and checklists[phase] and hasattr(checklists[phase], 'items'):
                items = checklists[phase].items
                if items:
                    done = sum(1 for item in items if hasattr(item, 'status') and item.status in ["completed", "skipped"])
                    completion = (done / len(items)) * 100

            # Status indicator
            if i < current_idx:
                status = "[OK]"
            elif i == current_idx:
                status = "[>>]"
            else:
                status = "[  ]"

            st.markdown(f"**{status}**")
            st.caption(phase_labels.get(phase, phase))
            st.progress(completion / 100)
            st.caption(f"{completion:.0f}%")


def _render_recent_activity(evidence_entries: List) -> None:
    """Render recent activity list."""
    st.markdown("#### Letzte Aktivitaeten")

    if not evidence_entries:
        st.info("Noch keine Aktivitaeten dokumentiert")
        return

    for entry in evidence_entries[-5:]:
        time_str = entry.timestamp.strftime("%H:%M") if hasattr(entry, 'timestamp') else ""
        desc = entry.description[:60] + "..." if len(entry.description) > 60 else entry.description
        entry_type = ""
        if hasattr(entry, 'entry_type'):
            if hasattr(entry.entry_type, 'value'):
                entry_type = entry.entry_type.value
            else:
                entry_type = str(entry.entry_type)

        st.markdown(f"`{time_str}` **{entry_type}**: {desc}")


def _render_phase_progress(phase_tracker, metrics: IncidentMetrics) -> None:
    """Render phase progress bars."""
    st.markdown("#### Phasen-Fortschritt")

    phase_order = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
    phase_labels = {
        "detection": "Erkennung",
        "analysis": "Analyse",
        "containment": "Eindaemmung",
        "eradication": "Beseitigung",
        "recovery": "Wiederherstellung",
        "post_incident": "Nachbereitung",
    }

    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"

    for phase in phase_order:
        progress = metrics.phase_completion.get(phase, 0)

        if phase == current_phase:
            marker = ">>"
        elif progress >= 100:
            marker = "OK"
        elif progress > 0:
            marker = ".."
        else:
            marker = "  "

        col1, col2 = st.columns([4, 1])
        with col1:
            st.caption(f"[{marker}] {phase_labels.get(phase, phase)}")
            st.progress(progress / 100)
        with col2:
            st.caption(f"{progress:.0f}%")


def _render_deadlines(metrics: IncidentMetrics) -> None:
    """Render deadline tracker."""
    st.markdown("#### Fristen & SLAs")

    if not metrics.deadlines:
        st.info("Keine Fristen definiert")
        return

    now = datetime.now(timezone.utc)

    for deadline in metrics.deadlines:
        dl_time = deadline.deadline
        if dl_time.tzinfo is None:
            dl_time = dl_time.replace(tzinfo=timezone.utc)

        time_diff = dl_time - now

        if time_diff.total_seconds() < 0:
            time_str = "UEBERFAELLIG"
        else:
            hours = int(time_diff.total_seconds() // 3600)
            if hours > 24:
                days = hours // 24
                time_str = f"{days}d {hours % 24}h"
            else:
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                time_str = f"{hours}h {minutes}m"

        status_marker = {"on_track": "[OK]", "at_risk": "[!!]", "breached": "[XX]"}.get(deadline.status, "[??]")

        st.markdown(f"{status_marker} **{deadline.name}**")
        st.caption(f"{deadline.regulation} | {time_str}")


def _render_risk_indicator(metrics: IncidentMetrics) -> None:
    """Render risk indicator."""
    st.markdown("#### Risiko-Bewertung")

    risk_labels = {"critical": "KRITISCH", "high": "HOCH", "medium": "MITTEL", "low": "NIEDRIG", "unknown": "UNBEKANNT"}

    st.metric("Risiko-Score", f"{metrics.risk_score}/100", risk_labels.get(metrics.risk_level, "---"))

    st.caption("**Faktoren:**")
    factors = []
    if metrics.critical_actions_pending > 0:
        factors.append(f"- {metrics.critical_actions_pending} kritische Aktionen offen")
    if metrics.containment_status in ["detecting", "analyzing"]:
        factors.append("- Noch nicht eingedaemmt")
    if metrics.time_since_detection.total_seconds() > 24 * 3600:
        factors.append("- >24h seit Erkennung")
    if not factors:
        factors.append("- Keine kritischen Faktoren")

    for f in factors:
        st.caption(f)


def _render_impact_summary(metrics: IncidentMetrics) -> None:
    """Render impact summary."""
    st.markdown("#### Auswirkung")

    containment_labels = {
        "not_started": "Nicht gestartet",
        "detecting": "Erkennung",
        "analyzing": "Analyse",
        "contained": "Eingedaemmt",
        "eradicated": "Beseitigt",
    }

    st.metric("Status", containment_labels.get(metrics.containment_status, "Unbekannt"))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Systeme", metrics.affected_systems_count)
    with col2:
        st.metric("Beweise", metrics.evidence_entries_count)


def _render_compliance_summary(metrics: IncidentMetrics) -> None:
    """Render compliance summary."""
    st.markdown("#### Compliance")

    if metrics.compliance_score == 0 and metrics.frameworks_validated == 0:
        st.info("Keine Validierung durchgefuehrt")
        return

    st.metric("Score", f"{metrics.compliance_score:.0f}%")
    st.caption(f"{metrics.frameworks_validated} Framework(s) | {metrics.compliance_gaps} Luecken")


def _render_executive_summary(incident, metrics: IncidentMetrics, phase_tracker) -> None:
    """Render executive summary."""
    st.markdown("#### Management-Zusammenfassung")

    hours = int(metrics.time_since_detection.total_seconds() // 3600)
    minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} Minuten"

    phase_labels = {
        "detection": "Erkennung",
        "analysis": "Analyse",
        "containment": "Eindaemmung",
        "eradication": "Beseitigung",
        "recovery": "Wiederherstellung",
        "post_incident": "Nachbereitung",
    }
    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"
    phase_label = phase_labels.get(current_phase, current_phase)

    risk_labels = {"critical": "Kritisch", "high": "Hoch", "medium": "Mittel", "low": "Niedrig"}
    risk_label = risk_labels.get(metrics.risk_level, "Unbekannt")

    containment_labels = {
        "not_started": "noch nicht begonnen",
        "detecting": "in der Erkennungsphase",
        "analyzing": "wird analysiert",
        "contained": "erfolgreich eingedaemmt",
        "eradicated": "vollstaendig beseitigt",
    }
    containment_text = containment_labels.get(metrics.containment_status, "unbekannt")

    # Build summary as plain text
    summary = f"""
**Vorfall:** {incident.title}

**Status:** Der Vorfall ist seit **{time_str}** aktiv. Das Incident-Response-Team befindet sich in der Phase **"{phase_label}"** mit einem Gesamtfortschritt von **{metrics.overall_progress:.0f}%**.

**Risikobewertung:** Das aktuelle Risikoniveau ist **{risk_label}** (Score: {metrics.risk_score}/100). Die Bedrohung ist {containment_text}.

**Ressourcen:** {metrics.affected_systems_count} System(e) betroffen, {metrics.evidence_entries_count} Beweisstuecke dokumentiert, {metrics.decisions_made_count} Entscheidungen getroffen.

**Ausstehend:** {metrics.mandatory_items_total - metrics.mandatory_items_complete} Pflichtaufgaben verbleibend, {metrics.critical_actions_pending} kritische Aktionen offen.
"""

    # Deadline warnings
    overdue = [d for d in metrics.deadlines if d.status == "breached"]
    at_risk = [d for d in metrics.deadlines if d.status == "at_risk"]

    if overdue:
        summary += f"\n**UEBERFAELLIG:** {', '.join([d.name for d in overdue])}"
    if at_risk:
        summary += f"\n**Gefaehrdet:** {', '.join([d.name for d in at_risk])}"

    if metrics.compliance_score > 0:
        summary += f"\n\n**Compliance:** {metrics.compliance_score:.0f}% der validierten Kontrollen erfuellt."

    st.markdown(summary)


def _render_export_options(incident, metrics: IncidentMetrics, phase_tracker) -> None:
    """Render export options."""
    st.markdown("#### Export")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if FPDF_AVAILABLE:
            pdf_content = _generate_pdf_report(incident, metrics, phase_tracker)
            st.download_button(
                label="PDF Report",
                data=pdf_content,
                file_name=f"report_{incident.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("PDF (nicht verfuegbar)", disabled=True, use_container_width=True)

    with col2:
        latex_content = _generate_latex_report(incident, metrics, phase_tracker)
        st.download_button(
            label="LaTeX Report",
            data=latex_content,
            file_name=f"report_{incident.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.tex",
            mime="application/x-latex",
            use_container_width=True,
        )

    with col3:
        html_content = _generate_html_report(incident, metrics, phase_tracker)
        st.download_button(
            label="HTML Report",
            data=html_content,
            file_name=f"report_{incident.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            use_container_width=True,
        )

    with col4:
        json_content = _generate_json_report(incident, metrics, phase_tracker)
        st.download_button(
            label="JSON Metriken",
            data=json_content,
            file_name=f"metrics_{incident.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col5:
        if st.button("Aktualisieren", use_container_width=True):
            st.rerun()


def _generate_executive_summary_text(incident, metrics: IncidentMetrics, phase_tracker) -> str:
    """Generate executive summary as plain text."""
    hours = int(metrics.time_since_detection.total_seconds() // 3600)
    minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} Minuten"

    phase_labels = {
        "detection": "Erkennung",
        "analysis": "Analyse",
        "containment": "Eindaemmung",
        "eradication": "Beseitigung",
        "recovery": "Wiederherstellung",
        "post_incident": "Nachbereitung",
    }
    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"
    phase_label = phase_labels.get(current_phase, current_phase)

    risk_labels = {"critical": "Kritisch", "high": "Hoch", "medium": "Mittel", "low": "Niedrig"}
    risk_label = risk_labels.get(metrics.risk_level, "Unbekannt")

    containment_labels = {
        "not_started": "noch nicht begonnen",
        "detecting": "in der Erkennungsphase",
        "analyzing": "wird analysiert",
        "contained": "erfolgreich eingedaemmt",
        "eradicated": "vollstaendig beseitigt",
    }
    containment_text = containment_labels.get(metrics.containment_status, "unbekannt")

    summary = f"""Der Vorfall "{incident.title}" ist seit {time_str} aktiv. Das Incident-Response-Team befindet sich in der Phase "{phase_label}" mit einem Gesamtfortschritt von {metrics.overall_progress:.0f}%.

Das aktuelle Risikoniveau ist {risk_label} (Score: {metrics.risk_score}/100). Die Bedrohung ist {containment_text}.

Ressourcen: {metrics.affected_systems_count} System(e) betroffen, {metrics.evidence_entries_count} Beweisstuecke dokumentiert, {metrics.decisions_made_count} Entscheidungen getroffen.

Ausstehend: {metrics.mandatory_items_total - metrics.mandatory_items_complete} Pflichtaufgaben verbleibend, {metrics.critical_actions_pending} kritische Aktionen offen."""

    overdue = [d for d in metrics.deadlines if d.status == "breached"]
    at_risk = [d for d in metrics.deadlines if d.status == "at_risk"]

    if overdue:
        summary += f"\n\nUEBERFAELLIG: {', '.join([d.name for d in overdue])}"
    if at_risk:
        summary += f"\n\nGefaehrdet: {', '.join([d.name for d in at_risk])}"

    if metrics.compliance_score > 0:
        summary += f"\n\nCompliance: {metrics.compliance_score:.0f}% der validierten Kontrollen erfuellt."

    return summary


def _generate_html_report(incident, metrics: IncidentMetrics, phase_tracker) -> str:
    """Generate HTML report."""
    hours = int(metrics.time_since_detection.total_seconds() // 3600)
    minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"

    executive_summary = _generate_executive_summary_text(incident, metrics, phase_tracker)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Executive Report - {incident.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; border-radius: 4px; text-align: center; min-width: 120px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        .summary {{ background: #f9f9f9; padding: 20px; border-left: 4px solid #333; margin: 20px 0; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <h1>Executive Incident Report</h1>
    <p><strong>Vorfall:</strong> {incident.title}</p>
    <p><strong>ID:</strong> {incident.id}</p>
    <p><strong>Analyst:</strong> {incident.analyst_name}</p>
    <p><strong>Report:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Management-Zusammenfassung</h2>
    <div class="summary">
        <p>{executive_summary.replace(chr(10), '</p><p>')}</p>
    </div>

    <div>
        <div class="metric"><div class="metric-value">{hours:02d}:{minutes:02d}</div><div class="metric-label">Laufzeit</div></div>
        <div class="metric"><div class="metric-value">{metrics.overall_progress:.0f}%</div><div class="metric-label">Fortschritt</div></div>
        <div class="metric"><div class="metric-value">{metrics.risk_score}</div><div class="metric-label">Risiko-Score</div></div>
        <div class="metric"><div class="metric-value">{metrics.affected_systems_count}</div><div class="metric-label">Systeme</div></div>
    </div>

    <h2>Metriken</h2>
    <table>
        <tr><th>Metrik</th><th>Wert</th></tr>
        <tr><td>Aktuelle Phase</td><td>{current_phase}</td></tr>
        <tr><td>Phasen-Fortschritt</td><td>{metrics.phase_progress:.0f}%</td></tr>
        <tr><td>Pflichtaufgaben</td><td>{metrics.mandatory_items_complete}/{metrics.mandatory_items_total}</td></tr>
        <tr><td>Kritische Aktionen</td><td>{metrics.critical_actions_pending}</td></tr>
        <tr><td>Beweise</td><td>{metrics.evidence_entries_count}</td></tr>
        <tr><td>Entscheidungen</td><td>{metrics.decisions_made_count}</td></tr>
        <tr><td>Compliance Score</td><td>{metrics.compliance_score:.0f}%</td></tr>
    </table>

    <h2>Fristen</h2>
    <table>
        <tr><th>Frist</th><th>Deadline</th><th>Status</th></tr>"""

    for d in metrics.deadlines:
        status_label = {"on_track": "Im Plan", "at_risk": "Gefaehrdet", "breached": "Ueberfaellig"}.get(d.status, d.status)
        html += f"<tr><td>{d.name}</td><td>{d.deadline.strftime('%Y-%m-%d %H:%M')}</td><td>{status_label}</td></tr>"

    html += f"""
    </table>

    <div class="footer">
        <p>Generiert von IR Companion | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""

    return html


def _generate_json_report(incident, metrics: IncidentMetrics, phase_tracker) -> str:
    """Generate JSON report."""
    executive_summary = _generate_executive_summary_text(incident, metrics, phase_tracker)

    data = {
        "generated": datetime.now().isoformat(),
        "incident": {
            "id": incident.id,
            "title": incident.title,
            "analyst": incident.analyst_name,
        },
        "executive_summary": executive_summary,
        "phase": phase_tracker.current_phase.value if phase_tracker else None,
        "metrics": {
            "elapsed_hours": metrics.time_since_detection.total_seconds() / 3600,
            "overall_progress": metrics.overall_progress,
            "phase_progress": metrics.phase_progress,
            "risk_score": metrics.risk_score,
            "risk_level": metrics.risk_level,
            "containment_status": metrics.containment_status,
            "mandatory_complete": metrics.mandatory_items_complete,
            "mandatory_total": metrics.mandatory_items_total,
            "critical_pending": metrics.critical_actions_pending,
            "evidence_count": metrics.evidence_entries_count,
            "decisions_count": metrics.decisions_made_count,
            "affected_systems": metrics.affected_systems_count,
            "compliance_score": metrics.compliance_score,
        },
        "deadlines": [
            {"name": d.name, "deadline": d.deadline.isoformat(), "status": d.status}
            for d in metrics.deadlines
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def _generate_text_report(incident, metrics: IncidentMetrics, phase_tracker) -> str:
    """Generate text report."""
    hours = int(metrics.time_since_detection.total_seconds() // 3600)
    minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"

    executive_summary = _generate_executive_summary_text(incident, metrics, phase_tracker)

    text = f"""================================================================================
                    INCIDENT RESPONSE STATUS UPDATE
================================================================================

VORFALL
-------
Titel:      {incident.title}
ID:         {incident.id}
Analyst:    {incident.analyst_name}

MANAGEMENT-ZUSAMMENFASSUNG
--------------------------
{executive_summary}

STATUS
------
Laufzeit:       {hours}h {minutes}m
Phase:          {current_phase}
Fortschritt:    {metrics.overall_progress:.0f}%
Risiko:         {metrics.risk_level.upper()} ({metrics.risk_score}/100)
Eindaemmung:    {metrics.containment_status}

METRIKEN
--------
Systeme:        {metrics.affected_systems_count}
Beweise:        {metrics.evidence_entries_count}
Entscheidungen: {metrics.decisions_made_count}
Pflicht:        {metrics.mandatory_items_complete}/{metrics.mandatory_items_total}
Kritisch:       {metrics.critical_actions_pending}
Compliance:     {metrics.compliance_score:.0f}%

FRISTEN
-------"""

    for d in metrics.deadlines:
        status = {"on_track": "[OK]", "at_risk": "[!!]", "breached": "[XX]"}.get(d.status, "[??]")
        text += f"\n{status} {d.name}: {d.deadline.strftime('%Y-%m-%d %H:%M')}"

    text += f"""

================================================================================
Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================"""

    return text


def _generate_latex_report(incident, metrics: IncidentMetrics, phase_tracker) -> str:
    """Generate LaTeX report."""
    hours = int(metrics.time_since_detection.total_seconds() // 3600)
    minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"

    executive_summary = _generate_executive_summary_text(incident, metrics, phase_tracker)
    executive_summary_latex = executive_summary.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%").replace("$", "\\$").replace("#", "\\#").replace("_", "\\_").replace("{", "\\{").replace("}", "\\}").replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}")

    phase_labels = {
        "detection": "Erkennung",
        "analysis": "Analyse",
        "containment": "Eindaemmung",
        "eradication": "Beseitigung",
        "recovery": "Wiederherstellung",
        "post_incident": "Nachbereitung",
    }
    phase_label = phase_labels.get(current_phase, current_phase)

    risk_labels = {"critical": "Kritisch", "high": "Hoch", "medium": "Mittel", "low": "Niedrig"}
    risk_label = risk_labels.get(metrics.risk_level, "Unbekannt")

    def escape_latex(text):
        """Escape special LaTeX characters."""
        replacements = [
            ("\\", "\\textbackslash{}"),
            ("&", "\\&"),
            ("%", "\\%"),
            ("$", "\\$"),
            ("#", "\\#"),
            ("_", "\\_"),
            ("{", "\\{"),
            ("}", "\\}"),
            ("~", "\\textasciitilde{}"),
            ("^", "\\textasciicircum{}"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    latex = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage[german]{{babel}}
\\usepackage{{geometry}}
\\usepackage{{booktabs}}
\\usepackage{{longtable}}
\\usepackage{{xcolor}}
\\usepackage{{fancyhdr}}
\\usepackage{{lastpage}}

\\geometry{{margin=2.5cm}}

\\definecolor{{risklow}}{{RGB}}{{76, 175, 80}}
\\definecolor{{riskmedium}}{{RGB}}{{255, 193, 7}}
\\definecolor{{riskhigh}}{{RGB}}{{255, 152, 0}}
\\definecolor{{riskcritical}}{{RGB}}{{244, 67, 54}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{Executive Incident Report}}
\\fancyhead[R]{{\\today}}
\\fancyfoot[C]{{Seite \\thepage\\ von \\pageref{{LastPage}}}}

\\begin{{document}}

\\begin{{center}}
\\LARGE\\textbf{{Executive Incident Report}}\\\\[0.5cm]
\\large {escape_latex(incident.title)}\\\\[0.3cm]
\\normalsize ID: {escape_latex(incident.id[:8])} | Analyst: {escape_latex(incident.analyst_name)}
\\end{{center}}

\\vspace{{1cm}}

\\section*{{Management-Zusammenfassung}}
{executive_summary_latex}

\\section*{{Status-Uebersicht}}
\\begin{{tabular}}{{ll}}
\\toprule
\\textbf{{Metrik}} & \\textbf{{Wert}} \\\\
\\midrule
Laufzeit & {hours}h {minutes}m \\\\
Aktuelle Phase & {phase_label} \\\\
Gesamtfortschritt & {metrics.overall_progress:.0f}\\% \\\\
Risikoniveau & {risk_label} ({metrics.risk_score}/100) \\\\
Eindaemmung & {metrics.containment_status} \\\\
\\bottomrule
\\end{{tabular}}

\\section*{{Detaillierte Metriken}}
\\begin{{tabular}}{{ll}}
\\toprule
\\textbf{{Metrik}} & \\textbf{{Wert}} \\\\
\\midrule
Betroffene Systeme & {metrics.affected_systems_count} \\\\
Beweisstuecke & {metrics.evidence_entries_count} \\\\
Entscheidungen & {metrics.decisions_made_count} \\\\
Pflichtaufgaben & {metrics.mandatory_items_complete}/{metrics.mandatory_items_total} \\\\
Kritische Aktionen & {metrics.critical_actions_pending} \\\\
Compliance Score & {metrics.compliance_score:.0f}\\% \\\\
\\bottomrule
\\end{{tabular}}

\\section*{{Fristen und SLAs}}
\\begin{{tabular}}{{llll}}
\\toprule
\\textbf{{Frist}} & \\textbf{{Regulation}} & \\textbf{{Deadline}} & \\textbf{{Status}} \\\\
\\midrule
"""

    for d in metrics.deadlines:
        status_label = {"on_track": "Im Plan", "at_risk": "Gefaehrdet", "breached": "Ueberfaellig"}.get(d.status, d.status)
        latex += f"{escape_latex(d.name)} & {escape_latex(d.regulation)} & {d.deadline.strftime('%Y-%m-%d %H:%M')} & {status_label} \\\\\n"

    latex += f"""\\bottomrule
\\end{{tabular}}

\\vfill

\\begin{{center}}
\\small Generiert von IR Companion | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
\\end{{center}}

\\end{{document}}
"""

    return latex


def _generate_pdf_report(incident, metrics: IncidentMetrics, phase_tracker) -> bytes:
    """Generate PDF report using fpdf2."""
    if not FPDF_AVAILABLE:
        return b""

    hours = int(metrics.time_since_detection.total_seconds() // 3600)
    minutes = int((metrics.time_since_detection.total_seconds() % 3600) // 60)
    current_phase = phase_tracker.current_phase.value if phase_tracker else "detection"

    executive_summary = _generate_executive_summary_text(incident, metrics, phase_tracker)

    phase_labels = {
        "detection": "Erkennung",
        "analysis": "Analyse",
        "containment": "Eindaemmung",
        "eradication": "Beseitigung",
        "recovery": "Wiederherstellung",
        "post_incident": "Nachbereitung",
    }
    phase_label = phase_labels.get(current_phase, current_phase)

    risk_labels = {"critical": "Kritisch", "high": "Hoch", "medium": "Mittel", "low": "Niedrig"}
    risk_label = risk_labels.get(metrics.risk_level, "Unbekannt")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Executive Incident Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, incident.title, new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"ID: {incident.id[:8]} | Analyst: {incident.analyst_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, f"Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.ln(10)

    # Executive Summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Management-Zusammenfassung", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, executive_summary)

    pdf.ln(10)

    # Status Overview
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Status-Uebersicht", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)

    # Table-like layout for status
    col_width = 60
    row_height = 8

    status_data = [
        ("Laufzeit", f"{hours}h {minutes}m"),
        ("Aktuelle Phase", phase_label),
        ("Gesamtfortschritt", f"{metrics.overall_progress:.0f}%"),
        ("Risikoniveau", f"{risk_label} ({metrics.risk_score}/100)"),
        ("Eindaemmung", metrics.containment_status),
    ]

    for label, value in status_data:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_width, row_height, label)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_width, row_height, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    # Detailed Metrics
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Detaillierte Metriken", new_x="LMARGIN", new_y="NEXT")

    metrics_data = [
        ("Betroffene Systeme", str(metrics.affected_systems_count)),
        ("Beweisstuecke", str(metrics.evidence_entries_count)),
        ("Entscheidungen", str(metrics.decisions_made_count)),
        ("Pflichtaufgaben", f"{metrics.mandatory_items_complete}/{metrics.mandatory_items_total}"),
        ("Kritische Aktionen", str(metrics.critical_actions_pending)),
        ("Compliance Score", f"{metrics.compliance_score:.0f}%"),
    ]

    for label, value in metrics_data:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(col_width, row_height, label)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_width, row_height, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    # Deadlines
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Fristen und SLAs", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, row_height, "Frist")
    pdf.cell(40, row_height, "Regulation")
    pdf.cell(50, row_height, "Deadline")
    pdf.cell(40, row_height, "Status", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for d in metrics.deadlines:
        status_label = {"on_track": "Im Plan", "at_risk": "Gefaehrdet", "breached": "Ueberfaellig"}.get(d.status, d.status)
        pdf.cell(50, row_height, d.name)
        pdf.cell(40, row_height, d.regulation)
        pdf.cell(50, row_height, d.deadline.strftime("%Y-%m-%d %H:%M"))
        pdf.cell(40, row_height, status_label, new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, f"Generiert von IR Companion | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="C")

    return bytes(pdf.output())
