"""
MITRE ATT&CK Navigator Components for IR Companion.

Visual matrix display of ATT&CK techniques with detection status tracking.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import os

from src.integrations.mitre_integration import MITREATTACKIntegration

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class TechniqueStatus(str, Enum):
    """Detection status for a technique."""
    NOT_APPLICABLE = "not_applicable"
    NOT_DETECTED = "not_detected"
    SUSPECTED = "suspected"
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    MITIGATED = "mitigated"


# ATT&CK Enterprise Tactics in kill chain order
TACTICS_ORDER = [
    ("reconnaissance", "Reconnaissance", "TA0043"),
    ("resource-development", "Resource Development", "TA0042"),
    ("initial-access", "Initial Access", "TA0001"),
    ("execution", "Execution", "TA0002"),
    ("persistence", "Persistence", "TA0003"),
    ("privilege-escalation", "Privilege Escalation", "TA0004"),
    ("defense-evasion", "Defense Evasion", "TA0005"),
    ("credential-access", "Credential Access", "TA0006"),
    ("discovery", "Discovery", "TA0007"),
    ("lateral-movement", "Lateral Movement", "TA0008"),
    ("collection", "Collection", "TA0009"),
    ("command-and-control", "Command and Control", "TA0011"),
    ("exfiltration", "Exfiltration", "TA0010"),
    ("impact", "Impact", "TA0040"),
]

# Status colors for visualization
STATUS_COLORS = {
    TechniqueStatus.NOT_APPLICABLE: "#404040",
    TechniqueStatus.NOT_DETECTED: "#1a1a2e",
    TechniqueStatus.SUSPECTED: "#ffa500",
    TechniqueStatus.DETECTED: "#ff4444",
    TechniqueStatus.CONFIRMED: "#cc0000",
    TechniqueStatus.MITIGATED: "#00aa00",
}

STATUS_LABELS = {
    TechniqueStatus.NOT_APPLICABLE: "N/A",
    TechniqueStatus.NOT_DETECTED: "Nicht erkannt",
    TechniqueStatus.SUSPECTED: "Verdacht",
    TechniqueStatus.DETECTED: "Erkannt",
    TechniqueStatus.CONFIRMED: "Bestaetigt",
    TechniqueStatus.MITIGATED: "Mitigiert",
}


@dataclass
class TechniqueAnnotation:
    """Annotation for a technique in the navigator."""
    technique_id: str
    status: TechniqueStatus = TechniqueStatus.NOT_DETECTED
    score: int = 0  # 0-100
    comment: str = ""
    evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NavigatorLayer:
    """A layer in the ATT&CK Navigator."""
    name: str
    description: str = ""
    created: datetime = field(default_factory=datetime.now)
    annotations: Dict[str, TechniqueAnnotation] = field(default_factory=dict)

    def add_annotation(self, technique_id: str, status: TechniqueStatus,
                       comment: str = "", evidence: List[str] = None):
        """Add or update annotation for a technique."""
        self.annotations[technique_id] = TechniqueAnnotation(
            technique_id=technique_id,
            status=status,
            comment=comment,
            evidence=evidence or [],
        )

    def get_status(self, technique_id: str) -> TechniqueStatus:
        """Get status for a technique."""
        if technique_id in self.annotations:
            return self.annotations[technique_id].status
        return TechniqueStatus.NOT_DETECTED

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics by status."""
        stats = {status: 0 for status in TechniqueStatus}
        for annotation in self.annotations.values():
            stats[annotation.status] += 1
        return stats


def _init_session_state():
    """Initialize session state for navigator."""
    if "navigator_layer" not in st.session_state:
        st.session_state.navigator_layer = NavigatorLayer(
            name="Incident Analysis",
            description="ATT&CK techniques identified in current incident"
        )
    if "mitre_integration" not in st.session_state:
        st.session_state.mitre_integration = MITREATTACKIntegration()
    if "navigator_view" not in st.session_state:
        st.session_state.navigator_view = "matrix"
    if "selected_technique" not in st.session_state:
        st.session_state.selected_technique = None


def render_mitre_navigator(lang: str = "de") -> None:
    """Render the MITRE ATT&CK Navigator view."""
    _init_session_state()

    st.header("MITRE ATT&CK Navigator")
    st.caption("Visualisierung und Tracking von ATT&CK-Techniken")

    # Load ATT&CK data
    integration = st.session_state.mitre_integration
    with st.spinner("Lade ATT&CK-Daten..."):
        data_loaded = integration.load_attack_data()

    if not data_loaded:
        st.warning("ATT&CK-Daten konnten nicht geladen werden. Offline-Modus aktiv.")

    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Matrix", "Techniken", "Statistiken", "Import/Export", "Empfehlungen"
    ])

    with tab1:
        _render_matrix_view(integration)

    with tab2:
        _render_techniques_list(integration)

    with tab3:
        _render_statistics()

    with tab4:
        _render_import_export(integration)

    with tab5:
        _render_recommendations(integration)


def _render_matrix_view(integration: MITREATTACKIntegration) -> None:
    """Render the ATT&CK matrix visualization."""
    st.subheader("ATT&CK Enterprise Matrix")

    layer = st.session_state.navigator_layer

    # Legend
    st.markdown("**Legende:**")
    legend_cols = st.columns(6)
    for i, (status, label) in enumerate(STATUS_LABELS.items()):
        with legend_cols[i]:
            color = STATUS_COLORS[status]
            st.markdown(
                f'<div style="background-color:{color};color:white;padding:4px 8px;'
                f'border-radius:4px;text-align:center;font-size:12px;">{label}</div>',
                unsafe_allow_html=True
            )

    st.divider()

    # Quick actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ransomware-Techniken laden", use_container_width=True):
            _load_ransomware_techniques(integration)
            st.rerun()
    with col2:
        if st.button("Alle zuruecksetzen", use_container_width=True):
            st.session_state.navigator_layer = NavigatorLayer(
                name="Incident Analysis",
                description="ATT&CK techniques identified in current incident"
            )
            st.rerun()
    with col3:
        incident = st.session_state.get("current_incident")
        if incident and st.button("Aus Incident laden", use_container_width=True):
            _load_from_incident(integration, incident)
            st.rerun()

    st.divider()

    # Matrix display - show tactics as expandable sections
    techniques_by_tactic = _group_techniques_by_tactic(integration)

    # Display each tactic
    for tactic_id, tactic_name, tactic_code in TACTICS_ORDER:
        techniques = techniques_by_tactic.get(tactic_id, [])
        if not techniques:
            continue

        # Count detected techniques in this tactic
        detected_count = sum(
            1 for t in techniques
            if layer.get_status(t.technique_id) in [
                TechniqueStatus.DETECTED,
                TechniqueStatus.CONFIRMED,
                TechniqueStatus.SUSPECTED
            ]
        )

        header_color = "#cc0000" if detected_count > 0 else "#333"

        with st.expander(
            f"**{tactic_name}** ({tactic_code}) - {len(techniques)} Techniken, "
            f"{detected_count} markiert",
            expanded=detected_count > 0
        ):
            _render_tactic_techniques(techniques, layer, tactic_id)


def _render_tactic_techniques(techniques: List, layer: NavigatorLayer, tactic_id: str) -> None:
    """Render techniques for a tactic."""
    # Create grid of techniques (4 columns)
    cols_per_row = 4

    for i in range(0, len(techniques), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(techniques):
                tech = techniques[i + j]
                with col:
                    _render_technique_cell(tech, layer, tactic_id)


def _render_technique_cell(technique, layer: NavigatorLayer, tactic_id: str) -> None:
    """Render a single technique cell."""
    status = layer.get_status(technique.technique_id)
    color = STATUS_COLORS[status]

    # Truncate name for display
    display_name = technique.name[:25] + "..." if len(technique.name) > 25 else technique.name

    # Create clickable cell
    cell_html = f'''
    <div style="
        background-color:{color};
        color:white;
        padding:8px;
        border-radius:4px;
        margin:2px;
        font-size:11px;
        min-height:60px;
        cursor:pointer;
    ">
        <strong>{technique.technique_id}</strong><br/>
        {display_name}
    </div>
    '''
    st.markdown(cell_html, unsafe_allow_html=True)

    # Status selector - use tactic_id in key to make it unique
    current_idx = list(TechniqueStatus).index(status)
    new_status = st.selectbox(
        "Status",
        options=list(TechniqueStatus),
        index=current_idx,
        format_func=lambda x: STATUS_LABELS[x],
        key=f"status_{tactic_id}_{technique.technique_id}",
        label_visibility="collapsed",
    )

    if new_status != status:
        layer.add_annotation(technique.technique_id, new_status)


def _render_techniques_list(integration: MITREATTACKIntegration) -> None:
    """Render searchable techniques list."""
    st.subheader("Techniken durchsuchen")

    layer = st.session_state.navigator_layer

    # Search
    search = st.text_input("Suche (ID oder Name)", placeholder="z.B. T1486 oder Ransomware")

    # Filter by status
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.multiselect(
            "Nach Status filtern",
            options=list(TechniqueStatus),
            format_func=lambda x: STATUS_LABELS[x],
        )
    with col2:
        filter_tactic = st.multiselect(
            "Nach Taktik filtern",
            options=[t[1] for t in TACTICS_ORDER],
        )

    st.divider()

    # Get all techniques
    all_techniques = list(integration._techniques.values())

    # Apply filters
    if search:
        search_lower = search.lower()
        all_techniques = [
            t for t in all_techniques
            if search_lower in t.technique_id.lower() or search_lower in t.name.lower()
        ]

    if filter_status:
        all_techniques = [
            t for t in all_techniques
            if layer.get_status(t.technique_id) in filter_status
        ]

    if filter_tactic:
        tactic_ids = [t[0] for t in TACTICS_ORDER if t[1] in filter_tactic]
        all_techniques = [
            t for t in all_techniques
            if any(tactic in t.tactics for tactic in tactic_ids)
        ]

    st.markdown(f"**{len(all_techniques)} Techniken gefunden**")

    # Display techniques
    for tech in all_techniques[:50]:  # Limit display
        status = layer.get_status(tech.technique_id)
        color = STATUS_COLORS[status]

        with st.expander(f"{tech.technique_id}: {tech.name}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Taktiken:** {', '.join(tech.tactics)}")
                st.markdown(f"**Plattformen:** {', '.join(tech.platforms[:5])}")

                if tech.description:
                    st.markdown("**Beschreibung:**")
                    st.markdown(tech.description[:500] + "..." if len(tech.description) > 500 else tech.description)

                if tech.detection:
                    st.markdown("**Erkennung:**")
                    st.markdown(tech.detection[:300] + "..." if len(tech.detection) > 300 else tech.detection)

                if tech.mitigations:
                    st.markdown("**Mitigationen:**")
                    for mit in tech.mitigations[:3]:
                        st.markdown(f"- {mit.get('name', 'N/A')}")

                st.markdown(f"[MITRE ATT&CK Link]({tech.url})")

            with col2:
                st.markdown("**Status setzen:**")
                new_status = st.selectbox(
                    "Status",
                    options=list(TechniqueStatus),
                    index=list(TechniqueStatus).index(status),
                    format_func=lambda x: STATUS_LABELS[x],
                    key=f"list_status_{tech.technique_id}",
                    label_visibility="collapsed",
                )

                if new_status != status:
                    layer.add_annotation(tech.technique_id, new_status)
                    st.rerun()

                comment = st.text_area(
                    "Kommentar",
                    value=layer.annotations.get(tech.technique_id, TechniqueAnnotation(tech.technique_id)).comment,
                    key=f"comment_{tech.technique_id}",
                    height=100,
                )

                if st.button("Speichern", key=f"save_{tech.technique_id}"):
                    annotation = layer.annotations.get(tech.technique_id) or TechniqueAnnotation(tech.technique_id)
                    annotation.comment = comment
                    layer.annotations[tech.technique_id] = annotation
                    st.success("Gespeichert!")


def _render_statistics() -> None:
    """Render statistics view."""
    st.subheader("Statistiken")

    layer = st.session_state.navigator_layer
    stats = layer.get_statistics()

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    total_annotated = sum(stats.values())
    detected = stats[TechniqueStatus.DETECTED] + stats[TechniqueStatus.CONFIRMED]
    suspected = stats[TechniqueStatus.SUSPECTED]
    mitigated = stats[TechniqueStatus.MITIGATED]

    with col1:
        st.metric("Markierte Techniken", total_annotated)
    with col2:
        st.metric("Erkannt/Bestaetigt", detected)
    with col3:
        st.metric("Verdacht", suspected)
    with col4:
        st.metric("Mitigiert", mitigated)

    st.divider()

    # Status breakdown
    st.markdown("### Verteilung nach Status")
    for status, count in stats.items():
        if count > 0:
            color = STATUS_COLORS[status]
            label = STATUS_LABELS[status]
            bar_width = min(count * 10, 100)
            st.markdown(
                f'<div style="display:flex;align-items:center;margin:4px 0;">'
                f'<div style="width:120px;">{label}</div>'
                f'<div style="background-color:{color};width:{bar_width}%;height:20px;'
                f'border-radius:4px;margin-right:10px;"></div>'
                f'<div>{count}</div></div>',
                unsafe_allow_html=True
            )

    st.divider()

    # Tactics coverage
    st.markdown("### Abdeckung nach Taktik")
    integration = st.session_state.mitre_integration
    techniques_by_tactic = _group_techniques_by_tactic(integration)

    for tactic_id, tactic_name, tactic_code in TACTICS_ORDER:
        techniques = techniques_by_tactic.get(tactic_id, [])
        if not techniques:
            continue

        detected_count = sum(
            1 for t in techniques
            if layer.get_status(t.technique_id) in [
                TechniqueStatus.DETECTED,
                TechniqueStatus.CONFIRMED,
                TechniqueStatus.SUSPECTED
            ]
        )

        pct = (detected_count / len(techniques) * 100) if techniques else 0
        bar_color = "#cc0000" if pct > 30 else "#ffa500" if pct > 0 else "#333"

        st.markdown(
            f'<div style="display:flex;align-items:center;margin:4px 0;">'
            f'<div style="width:180px;font-size:12px;">{tactic_name}</div>'
            f'<div style="background-color:{bar_color};width:{pct}%;height:16px;'
            f'border-radius:2px;margin-right:10px;min-width:2px;"></div>'
            f'<div style="font-size:12px;">{detected_count}/{len(techniques)} ({pct:.0f}%)</div></div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Annotated techniques list
    st.markdown("### Markierte Techniken")
    if layer.annotations:
        for tech_id, annotation in sorted(layer.annotations.items()):
            if annotation.status != TechniqueStatus.NOT_DETECTED:
                technique = integration.get_technique_by_id(tech_id)
                name = technique.name if technique else "Unknown"
                color = STATUS_COLORS[annotation.status]
                label = STATUS_LABELS[annotation.status]

                st.markdown(
                    f'<div style="display:flex;align-items:center;padding:4px;'
                    f'border-left:4px solid {color};margin:4px 0;background:#1a1a2e;">'
                    f'<strong style="width:80px;">{tech_id}</strong>'
                    f'<span style="flex:1;">{name}</span>'
                    f'<span style="background:{color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:11px;">{label}</span></div>',
                    unsafe_allow_html=True
                )
                if annotation.comment:
                    st.caption(f"Kommentar: {annotation.comment}")
    else:
        st.info("Noch keine Techniken markiert.")


def _render_import_export(integration: MITREATTACKIntegration) -> None:
    """Render import/export view."""
    st.subheader("Import / Export")

    layer = st.session_state.navigator_layer

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Export")

        # Layer name
        layer.name = st.text_input("Layer-Name", value=layer.name)
        layer.description = st.text_area("Beschreibung", value=layer.description, height=80)

        # Export formats
        st.markdown("**Export-Format:**")

        # Navigator JSON (compatible with ATT&CK Navigator)
        if st.button("ATT&CK Navigator JSON", use_container_width=True):
            json_data = _export_navigator_json(layer, integration)
            st.download_button(
                label="Download Navigator JSON",
                data=json_data,
                file_name=f"attack_navigator_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
            )

        # Markdown
        if st.button("Markdown Report", use_container_width=True):
            md_data = _export_markdown(layer, integration)
            st.download_button(
                label="Download Markdown",
                data=md_data,
                file_name=f"attack_report_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
            )

        # CSV
        if st.button("CSV Export", use_container_width=True):
            csv_data = _export_csv(layer, integration)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"attack_techniques_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

        # PDF
        if FPDF_AVAILABLE:
            if st.button("PDF Report", use_container_width=True):
                pdf_data = _export_pdf(layer, integration)
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name=f"attack_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                )

    with col2:
        st.markdown("### Import")

        uploaded_file = st.file_uploader(
            "ATT&CK Navigator JSON hochladen",
            type=["json"],
            help="Importieren Sie eine Navigator-Layer-Datei"
        )

        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                imported_layer = _import_navigator_json(data)
                if imported_layer:
                    st.session_state.navigator_layer = imported_layer
                    st.success(f"Layer '{imported_layer.name}' importiert!")
                    st.rerun()
            except Exception as e:
                st.error(f"Import fehlgeschlagen: {e}")

        st.divider()

        st.markdown("### Vorlagen")

        if st.button("Ransomware-Vorlage", use_container_width=True):
            _load_ransomware_techniques(integration)
            st.success("Ransomware-Techniken geladen!")
            st.rerun()

        if st.button("Phishing-Vorlage", use_container_width=True):
            _load_phishing_techniques(integration)
            st.success("Phishing-Techniken geladen!")
            st.rerun()

        if st.button("APT-Vorlage", use_container_width=True):
            _load_apt_techniques(integration)
            st.success("APT-Techniken geladen!")
            st.rerun()


def _render_recommendations(integration: MITREATTACKIntegration) -> None:
    """Render recommendations based on detected techniques."""
    st.subheader("Empfehlungen")

    layer = st.session_state.navigator_layer

    # Get detected techniques
    detected_ids = [
        tech_id for tech_id, annotation in layer.annotations.items()
        if annotation.status in [TechniqueStatus.DETECTED, TechniqueStatus.CONFIRMED, TechniqueStatus.SUSPECTED]
    ]

    if not detected_ids:
        st.info("Keine Techniken erkannt. Markieren Sie Techniken in der Matrix, um Empfehlungen zu erhalten.")
        return

    st.markdown(f"**{len(detected_ids)} erkannte Techniken**")

    # Detection recommendations
    st.markdown("### Erkennungsempfehlungen")
    detection_recs = set()
    for tech_id in detected_ids:
        technique = integration.get_technique_by_id(tech_id)
        if technique and technique.data_sources:
            for ds in technique.data_sources[:2]:
                detection_recs.add(f"Monitoring aktivieren: {ds}")

    for rec in list(detection_recs)[:10]:
        st.markdown(f"- {rec}")

    st.divider()

    # Mitigation recommendations
    st.markdown("### Mitigationsempfehlungen")
    all_mitigations: Dict[str, Dict] = {}

    for tech_id in detected_ids:
        technique = integration.get_technique_by_id(tech_id)
        if technique:
            for mit in technique.mitigations:
                mit_id = mit.get("id", "")
                if mit_id and mit_id not in all_mitigations:
                    all_mitigations[mit_id] = {
                        "name": mit.get("name", ""),
                        "description": mit.get("description", "")[:200],
                        "techniques": [tech_id],
                    }
                elif mit_id:
                    all_mitigations[mit_id]["techniques"].append(tech_id)

    # Sort by number of techniques covered
    sorted_mits = sorted(
        all_mitigations.items(),
        key=lambda x: len(x[1]["techniques"]),
        reverse=True
    )

    for mit_id, mit_data in sorted_mits[:10]:
        tech_count = len(mit_data["techniques"])
        st.markdown(
            f"**{mit_id}: {mit_data['name']}** (deckt {tech_count} Techniken ab)"
        )
        if mit_data["description"]:
            st.caption(mit_data["description"])

    st.divider()

    # Priority matrix
    st.markdown("### Priorisierung")

    # Group by tactic to identify attack phase
    techniques_by_tactic: Dict[str, List[str]] = {}
    for tech_id in detected_ids:
        technique = integration.get_technique_by_id(tech_id)
        if technique:
            for tactic in technique.tactics:
                if tactic not in techniques_by_tactic:
                    techniques_by_tactic[tactic] = []
                techniques_by_tactic[tactic].append(tech_id)

    # Determine attack stage
    early_stage = ["initial-access", "execution", "persistence"]
    mid_stage = ["privilege-escalation", "defense-evasion", "credential-access", "discovery"]
    late_stage = ["lateral-movement", "collection", "exfiltration", "impact"]

    early_count = sum(len(techniques_by_tactic.get(t, [])) for t in early_stage)
    mid_count = sum(len(techniques_by_tactic.get(t, [])) for t in mid_stage)
    late_count = sum(len(techniques_by_tactic.get(t, [])) for t in late_stage)

    if late_count > mid_count and late_count > early_count:
        st.error("KRITISCH: Angriff in spaeter Phase erkannt (Lateral Movement/Exfiltration/Impact)")
        st.markdown("**Sofortige Massnahmen:**")
        st.markdown("1. Netzwerkisolation betroffener Systeme")
        st.markdown("2. Backup-Integritaet pruefen")
        st.markdown("3. Incident Response Team aktivieren")
    elif mid_count > early_count:
        st.warning("WARNUNG: Angriff in mittlerer Phase (Privilege Escalation/Discovery)")
        st.markdown("**Empfohlene Massnahmen:**")
        st.markdown("1. Credential-Reset fuer betroffene Accounts")
        st.markdown("2. Erhoehtes Monitoring aktivieren")
        st.markdown("3. Betroffene Systeme analysieren")
    else:
        st.info("Angriff in frueher Phase erkannt (Initial Access/Execution)")
        st.markdown("**Empfohlene Massnahmen:**")
        st.markdown("1. Einfallstor identifizieren und schliessen")
        st.markdown("2. Betroffene Systeme isolieren")
        st.markdown("3. Forensische Sicherung durchfuehren")


def _group_techniques_by_tactic(integration: MITREATTACKIntegration) -> Dict[str, List]:
    """Group techniques by their primary tactic."""
    techniques_by_tactic: Dict[str, List] = {}

    for technique in integration._techniques.values():
        if technique.is_subtechnique:
            continue  # Skip subtechniques for cleaner display

        for tactic in technique.tactics:
            if tactic not in techniques_by_tactic:
                techniques_by_tactic[tactic] = []
            techniques_by_tactic[tactic].append(technique)

    # Sort techniques by ID within each tactic
    for tactic in techniques_by_tactic:
        techniques_by_tactic[tactic].sort(key=lambda t: t.technique_id)

    return techniques_by_tactic


def _load_ransomware_techniques(integration: MITREATTACKIntegration) -> None:
    """Load ransomware-related techniques as detected."""
    layer = st.session_state.navigator_layer

    ransomware_ids = list(integration.RANSOMWARE_TECHNIQUES.keys())
    for tech_id in ransomware_ids:
        layer.add_annotation(tech_id, TechniqueStatus.SUSPECTED, "Ransomware-typische Technik")


def _load_phishing_techniques(integration: MITREATTACKIntegration) -> None:
    """Load phishing-related techniques."""
    layer = st.session_state.navigator_layer

    phishing_ids = [
        "T1566", "T1566.001", "T1566.002",  # Phishing
        "T1204", "T1204.001", "T1204.002",  # User Execution
        "T1059", "T1059.001", "T1059.005",  # Scripting
        "T1547", "T1053",  # Persistence
        "T1071", "T1105",  # C2
    ]

    for tech_id in phishing_ids:
        layer.add_annotation(tech_id, TechniqueStatus.SUSPECTED, "Phishing-typische Technik")


def _load_apt_techniques(integration: MITREATTACKIntegration) -> None:
    """Load APT-related techniques."""
    layer = st.session_state.navigator_layer

    apt_ids = [
        "T1190", "T1133",  # Initial Access
        "T1059", "T1047",  # Execution
        "T1547", "T1053", "T1543",  # Persistence
        "T1068", "T1055",  # Privilege Escalation
        "T1070", "T1027", "T1562",  # Defense Evasion
        "T1003", "T1555",  # Credential Access
        "T1082", "T1083", "T1018",  # Discovery
        "T1021", "T1570",  # Lateral Movement
        "T1560", "T1074",  # Collection
        "T1071", "T1095",  # C2
        "T1041", "T1567",  # Exfiltration
    ]

    for tech_id in apt_ids:
        layer.add_annotation(tech_id, TechniqueStatus.SUSPECTED, "APT-typische Technik")


def _load_from_incident(integration: MITREATTACKIntegration, incident) -> None:
    """Load techniques from current incident IOCs."""
    layer = st.session_state.navigator_layer

    # Get IOCs from incident if available
    iocs = []
    if hasattr(incident, "iocs"):
        iocs = incident.iocs
    elif "iocs" in st.session_state:
        iocs = st.session_state.iocs

    if iocs:
        techniques = integration.correlate_iocs_to_techniques(iocs)
        for tech in techniques:
            layer.add_annotation(
                tech.technique_id,
                TechniqueStatus.DETECTED,
                f"IOC-Korrelation: {', '.join(tech.relevance_indicators[:2])}"
            )


def _export_navigator_json(layer: NavigatorLayer, integration: MITREATTACKIntegration) -> str:
    """Export in ATT&CK Navigator JSON format."""
    # Navigator layer format
    techniques = []

    for tech_id, annotation in layer.annotations.items():
        technique = integration.get_technique_by_id(tech_id)
        if not technique:
            continue

        # Map status to score (0-100)
        score_map = {
            TechniqueStatus.NOT_APPLICABLE: 0,
            TechniqueStatus.NOT_DETECTED: 0,
            TechniqueStatus.SUSPECTED: 50,
            TechniqueStatus.DETECTED: 75,
            TechniqueStatus.CONFIRMED: 100,
            TechniqueStatus.MITIGATED: 25,
        }

        # Map status to color
        color_map = {
            TechniqueStatus.NOT_APPLICABLE: "#404040",
            TechniqueStatus.NOT_DETECTED: "",
            TechniqueStatus.SUSPECTED: "#ffa500",
            TechniqueStatus.DETECTED: "#ff4444",
            TechniqueStatus.CONFIRMED: "#cc0000",
            TechniqueStatus.MITIGATED: "#00aa00",
        }

        tech_entry = {
            "techniqueID": tech_id,
            "score": score_map.get(annotation.status, 0),
            "color": color_map.get(annotation.status, ""),
            "comment": annotation.comment,
            "enabled": True,
        }

        # Add tactic if available
        if technique.tactics:
            tech_entry["tactic"] = technique.tactics[0]

        techniques.append(tech_entry)

    navigator_layer = {
        "name": layer.name,
        "versions": {
            "attack": "14",
            "navigator": "4.9.1",
            "layer": "4.5"
        },
        "domain": "enterprise-attack",
        "description": layer.description,
        "filters": {
            "platforms": ["Windows", "Linux", "macOS"]
        },
        "sorting": 0,
        "layout": {
            "layout": "side",
            "aggregateFunction": "average",
            "showID": True,
            "showName": True
        },
        "hideDisabled": False,
        "techniques": techniques,
        "gradient": {
            "colors": ["#ffffff", "#ff6666"],
            "minValue": 0,
            "maxValue": 100
        },
        "metadata": [
            {"name": "created", "value": layer.created.isoformat()},
            {"name": "exported", "value": datetime.now().isoformat()},
        ]
    }

    return json.dumps(navigator_layer, indent=2, ensure_ascii=False)


def _export_markdown(layer: NavigatorLayer, integration: MITREATTACKIntegration) -> str:
    """Export as Markdown report."""
    lines = [
        f"# ATT&CK Analysis Report: {layer.name}",
        "",
        f"**Erstellt:** {layer.created.strftime('%Y-%m-%d %H:%M')}",
        f"**Exportiert:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**Beschreibung:** {layer.description}",
        "",
        "---",
        "",
        "## Zusammenfassung",
        "",
    ]

    stats = layer.get_statistics()
    detected = stats[TechniqueStatus.DETECTED] + stats[TechniqueStatus.CONFIRMED]
    suspected = stats[TechniqueStatus.SUSPECTED]

    lines.extend([
        f"- **Erkannte Techniken:** {detected}",
        f"- **Verdaechtige Techniken:** {suspected}",
        f"- **Mitigierte Techniken:** {stats[TechniqueStatus.MITIGATED]}",
        "",
        "---",
        "",
        "## Erkannte Techniken",
        "",
        "| ID | Name | Status | Taktiken | Kommentar |",
        "|---|---|---|---|---|",
    ])

    for tech_id, annotation in sorted(layer.annotations.items()):
        if annotation.status in [TechniqueStatus.DETECTED, TechniqueStatus.CONFIRMED, TechniqueStatus.SUSPECTED]:
            technique = integration.get_technique_by_id(tech_id)
            name = technique.name if technique else "Unknown"
            tactics = ", ".join(technique.tactics[:2]) if technique else ""
            status = STATUS_LABELS[annotation.status]
            comment = annotation.comment[:50] + "..." if len(annotation.comment) > 50 else annotation.comment

            lines.append(f"| {tech_id} | {name} | {status} | {tactics} | {comment} |")

    lines.extend([
        "",
        "---",
        "",
        "## Empfohlene Mitigationen",
        "",
    ])

    # Collect mitigations
    all_mits = {}
    for tech_id, annotation in layer.annotations.items():
        if annotation.status in [TechniqueStatus.DETECTED, TechniqueStatus.CONFIRMED]:
            technique = integration.get_technique_by_id(tech_id)
            if technique:
                for mit in technique.mitigations:
                    mit_id = mit.get("id", "")
                    if mit_id and mit_id not in all_mits:
                        all_mits[mit_id] = mit.get("name", "")

    for mit_id, mit_name in list(all_mits.items())[:10]:
        lines.append(f"- **{mit_id}:** {mit_name}")

    lines.extend([
        "",
        "---",
        "",
        "*Generiert mit IR Companion MITRE ATT&CK Navigator*",
    ])

    return "\n".join(lines)


def _export_csv(layer: NavigatorLayer, integration: MITREATTACKIntegration) -> str:
    """Export as CSV."""
    lines = ["ID;Name;Status;Taktiken;Plattformen;Kommentar"]

    for tech_id, annotation in sorted(layer.annotations.items()):
        technique = integration.get_technique_by_id(tech_id)
        if not technique:
            continue

        name = technique.name.replace(";", ",")
        status = STATUS_LABELS[annotation.status]
        tactics = "|".join(technique.tactics)
        platforms = "|".join(technique.platforms[:3])
        comment = annotation.comment.replace(";", ",")[:100]

        lines.append(f"{tech_id};{name};{status};{tactics};{platforms};{comment}")

    return "\n".join(lines)


def _export_pdf(layer: NavigatorLayer, integration: MITREATTACKIntegration) -> bytes:
    """Export as PDF report."""
    if not FPDF_AVAILABLE:
        return b""

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "MITRE ATT&CK Analysis Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Layer: {layer.name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, f"Exportiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # Statistics
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Zusammenfassung", new_x="LMARGIN", new_y="NEXT")

    stats = layer.get_statistics()
    pdf.set_font("Helvetica", "", 10)

    detected = stats[TechniqueStatus.DETECTED] + stats[TechniqueStatus.CONFIRMED]
    pdf.cell(0, 6, f"Erkannte Techniken: {detected}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Verdaechtige Techniken: {stats[TechniqueStatus.SUSPECTED]}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Mitigierte Techniken: {stats[TechniqueStatus.MITIGATED]}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Techniques table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Erkannte Techniken", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)

    for tech_id, annotation in sorted(layer.annotations.items()):
        if annotation.status not in [TechniqueStatus.DETECTED, TechniqueStatus.CONFIRMED, TechniqueStatus.SUSPECTED]:
            continue

        technique = integration.get_technique_by_id(tech_id)
        if not technique:
            continue

        name = technique.name[:40] + "..." if len(technique.name) > 40 else technique.name
        status = STATUS_LABELS[annotation.status]

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"{tech_id}: {name}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 4, f"Status: {status} | Taktiken: {', '.join(technique.tactics[:2])}", new_x="LMARGIN", new_y="NEXT")

        if annotation.comment:
            comment = annotation.comment[:80] + "..." if len(annotation.comment) > 80 else annotation.comment
            pdf.cell(0, 4, f"Kommentar: {comment}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Generiert mit IR Companion", align="C")

    return bytes(pdf.output())


def _import_navigator_json(data: Dict) -> Optional[NavigatorLayer]:
    """Import from ATT&CK Navigator JSON format."""
    try:
        layer = NavigatorLayer(
            name=data.get("name", "Imported Layer"),
            description=data.get("description", ""),
        )

        for tech in data.get("techniques", []):
            tech_id = tech.get("techniqueID", "")
            if not tech_id:
                continue

            score = tech.get("score", 0)
            comment = tech.get("comment", "")
            color = tech.get("color", "")

            # Map score/color to status
            if score >= 75 or color == "#cc0000":
                status = TechniqueStatus.CONFIRMED
            elif score >= 50 or color in ["#ff4444", "#ffa500"]:
                status = TechniqueStatus.DETECTED
            elif score > 0:
                status = TechniqueStatus.SUSPECTED
            elif color == "#00aa00":
                status = TechniqueStatus.MITIGATED
            else:
                status = TechniqueStatus.NOT_DETECTED

            layer.add_annotation(tech_id, status, comment)

        return layer
    except Exception as e:
        return None


# Alias for app.py integration
def render_mitre_navigator_view(lang: str = "de") -> None:
    """Alias for render_mitre_navigator."""
    render_mitre_navigator(lang)
