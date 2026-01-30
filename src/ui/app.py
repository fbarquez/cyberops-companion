"""
CyberOps Companion - Main Streamlit Application

Incident Response Decision Support Tool
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from datetime import datetime, timezone
from typing import Optional

from config import get_config, ensure_directories

from src.core.workflow import WorkflowEngine
from src.core.evidence_logger import EvidenceLogger
from src.core.checklist_manager import ChecklistManager
from src.core.decision_engine import DecisionEngine
from src.core.report_generator import ReportGenerator

from src.models.incident import Incident, IncidentStatus
from src.models.phase import IncidentPhaseTracker, IRPhase, PHASE_ORDER
from src.models.evidence import EvidenceType

from src.simulation.scenario_runner import ScenarioRunner

from src.ui.components import (
    render_checklist,
    render_decision_tree,
    render_evidence_log,
    render_progress_bar,
)

from src.ui.compliance_components import (
    render_compliance_dashboard,
    render_framework_selector,
    render_threat_intelligence,
    render_ioc_input,
    render_compliance_report_export,
    render_compliance_summary_card,
    render_attack_navigator_link,
    render_cross_framework_dashboard,
    render_coverage_gaps,
    render_cross_framework_export,
)
from src.ui.bsi_meldung_components import render_bsi_meldung_dashboard
from src.ui.ioc_enrichment_components import render_ioc_enrichment_dashboard
from src.ui.executive_dashboard_components import render_executive_dashboard
from src.ui.playbook_generator_components import render_playbook_generator
from src.ui.communication_templates_components import render_communication_templates
from src.ui.lessons_learned_components import render_lessons_learned_dashboard
from src.ui.mitre_navigator_components import render_mitre_navigator
from src.ui.styles import inject_styles, get_theme_toggle_html
from src.ui.keyboard_shortcuts import inject_keyboard_shortcuts

from src.integrations import (
    ComplianceHub,
    ComplianceFramework,
    IOCEnricher,
)

from src.utils.translations import t, DEFAULT_LANGUAGE


def get_lang() -> str:
    return st.session_state.get("language", DEFAULT_LANGUAGE)


def init_session_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.incident = None
        st.session_state.phase_tracker = None
        st.session_state.checklists = None
        st.session_state.decision_trees = {}
        st.session_state.current_view = "home"
        st.session_state.simulation_active = False
        st.session_state.operator_name = ""
        st.session_state.language = DEFAULT_LANGUAGE
        st.session_state.theme = "light"  # Theme: "light" or "dark"
        st.session_state.compliance_hub = None
        st.session_state.compliance_results = {}
        st.session_state.threat_intel = None
        st.session_state.selected_frameworks = []
        st.session_state.ioc_enricher = None


def format_elapsed(start_time: datetime) -> str:
    now = datetime.now(timezone.utc)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    elapsed = now - start_time
    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main():
    config = get_config()
    st.set_page_config(
        page_title="CyberOps Companion",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    ensure_directories()
    init_session_state()

    # Inject styles with current theme
    current_theme = st.session_state.get("theme", "light")
    inject_styles(theme=current_theme)

    lang = get_lang()

    # Inject keyboard shortcuts
    inject_keyboard_shortcuts(lang=lang)

    # Initialize managers
    workflow_engine = WorkflowEngine()
    evidence_logger = EvidenceLogger()
    checklist_manager = ChecklistManager()
    decision_engine = DecisionEngine()
    report_generator = ReportGenerator()
    scenario_runner = ScenarioRunner()

    # Sidebar - clean and simple
    with st.sidebar:
        st.header("CyberOps Companion")

        if st.session_state.incident:
            incident = st.session_state.incident
            tracker = st.session_state.phase_tracker

            st.caption(f"ID: {incident.id[:8]}")
            st.caption(f"Time: {format_elapsed(incident.created_at)}")

            st.divider()

            # Simple navigation
            nav_options = ["dashboard", "overview", "checklist", "decisions", "evidence", "compliance", "playbook", "templates", "lessons", "navigator", "export"]
            view = st.radio(
                "Navigation",
                options=nav_options,
                format_func=lambda x: t(f"nav.{x}", lang),
                index=nav_options.index(st.session_state.current_view) if st.session_state.current_view in nav_options else 0,
                label_visibility="collapsed",
            )
            if view != st.session_state.current_view:
                st.session_state.current_view = view
                st.rerun()

            st.divider()

            if st.button("Close Incident", use_container_width=True):
                st.session_state.incident = None
                st.session_state.phase_tracker = None
                st.session_state.checklists = None
                st.session_state.simulation_active = False
                st.session_state.current_view = "home"
                st.rerun()

        else:
            if st.button(t("nav.new_incident", lang), use_container_width=True):
                st.session_state.current_view = "new_incident"
                st.rerun()

            if st.button(t("nav.simulation", lang), use_container_width=True):
                st.session_state.current_view = "simulation"
                st.rerun()

            st.divider()
            st.caption("Tools")

            if st.button(t("nav.playbook", lang), use_container_width=True):
                st.session_state.current_view = "playbook"
                st.rerun()

            if st.button(t("nav.templates", lang), use_container_width=True):
                st.session_state.current_view = "templates"
                st.rerun()

            if st.button(t("nav.lessons", lang), use_container_width=True):
                st.session_state.current_view = "lessons"
                st.rerun()

            if st.button(t("nav.navigator", lang), use_container_width=True):
                st.session_state.current_view = "navigator"
                st.rerun()

        # Settings at bottom
        st.divider()

        # Theme toggle
        theme_label = get_theme_toggle_html(current_theme)
        if st.button(theme_label, key="theme_toggle", use_container_width=True):
            new_theme = "light" if current_theme == "dark" else "dark"
            st.session_state.theme = new_theme
            st.rerun()

        # Language toggle
        lang_sel = st.radio(
            "Language",
            options=["de", "en"],
            format_func=lambda x: "DE" if x == "de" else "EN",
            index=0 if lang == "de" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )
        if lang_sel != lang:
            st.session_state.language = lang_sel
            st.rerun()

    # Main content
    view = st.session_state.current_view

    if view == "home":
        render_home(lang)
    elif view == "new_incident":
        render_new_incident(workflow_engine, checklist_manager, evidence_logger, lang)
    elif view == "simulation":
        render_simulation(scenario_runner, workflow_engine, checklist_manager, evidence_logger, lang)
    elif view == "dashboard":
        render_executive_dashboard_view(checklist_manager, evidence_logger, lang)
    elif view == "overview":
        render_overview(workflow_engine, lang)
    elif view == "checklist":
        render_checklist_view(checklist_manager, evidence_logger, lang)
    elif view == "decisions":
        render_decisions(decision_engine, evidence_logger, lang)
    elif view == "evidence":
        render_evidence(evidence_logger, lang)
    elif view == "compliance":
        render_compliance(checklist_manager, evidence_logger, lang)
    elif view == "playbook":
        render_playbook_generator(lang)
    elif view == "templates":
        render_communication_templates(lang)
    elif view == "lessons":
        render_lessons_learned_dashboard(lang)
    elif view == "navigator":
        render_mitre_navigator(lang)
    elif view == "export":
        render_export(report_generator, evidence_logger, lang)


def render_home(lang: str):
    st.title("CyberOps Companion")
    st.write(t("app.subtitle", lang))

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("home.production_incident", lang))
        st.caption(t("home.start_real_workflow", lang))
        if st.button(t("nav.new_incident", lang), key="home_new"):
            st.session_state.current_view = "new_incident"
            st.rerun()

    with col2:
        st.subheader(t("home.training_mode", lang))
        st.caption(t("home.practice_simulation", lang))
        if st.button(t("home.start_simulation", lang), key="home_sim"):
            st.session_state.current_view = "simulation"
            st.rerun()


def render_new_incident(
    workflow_engine: WorkflowEngine,
    checklist_manager: ChecklistManager,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    st.title(t("incident.new_incident", lang))

    # Simple warning
    st.warning(t("forensic.do_not_power_off", lang))

    with st.form("new_incident"):
        title = st.text_input(t("incident.title", lang) + " *")
        analyst = st.text_input(t("incident.your_name", lang) + " *", value=st.session_state.operator_name)

        detection_sources = t("incident.detection_sources", lang)
        source = st.selectbox(
            t("incident.detection_source", lang),
            options=list(detection_sources.keys()),
            format_func=lambda x: detection_sources[x],
        )

        system = st.text_input(t("incident.affected_system", lang))
        indicator = st.text_area(t("incident.initial_indicator", lang), height=80)

        if st.form_submit_button(t("incident.start_response", lang)):
            if not title or not analyst:
                st.error(t("incident.title_required", lang))
            else:
                incident, tracker = workflow_engine.create_incident(
                    title=title,
                    analyst_name=analyst,
                    detection_source=source,
                    initial_indicator=indicator,
                    is_simulation=False,
                )

                if system:
                    from src.models.incident import AffectedSystem
                    incident.add_affected_system(AffectedSystem(hostname=system))

                checklists = checklist_manager.create_incident_checklist(incident.id)

                evidence_logger.log_entry(
                    incident_id=incident.id,
                    description=f"Incident created: {title}",
                    entry_type=EvidenceType.SYSTEM,
                    phase="detection",
                    operator=analyst,
                )

                st.session_state.incident = incident
                st.session_state.phase_tracker = tracker
                st.session_state.checklists = checklists
                st.session_state.operator_name = analyst
                st.session_state.current_view = "overview"
                st.rerun()


def render_simulation(
    scenario_runner: ScenarioRunner,
    workflow_engine: WorkflowEngine,
    checklist_manager: ChecklistManager,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    st.title(t("simulation.title", lang))
    st.info(t("simulation.info", lang))

    scenarios = scenario_runner.list_scenarios()

    for scenario in scenarios:
        with st.expander(f"{scenario['name']} ({scenario['difficulty']})"):
            st.write(scenario["description"])

            briefing = scenario_runner.get_scenario_briefing(scenario["id"])
            st.write(f"**{t('simulation.background', lang)}:** {briefing['background']}")

            analyst = st.text_input(
                t("incident.your_name", lang),
                value=st.session_state.operator_name,
                key=f"analyst_{scenario['id']}",
            )

            if st.button(t("simulation.start_scenario", lang), key=f"start_{scenario['id']}"):
                if not analyst:
                    st.error(t("simulation.enter_name", lang))
                else:
                    scenario_runner.start_simulation(scenario["id"])

                    incident, tracker = workflow_engine.create_incident(
                        title=f"[SIM] {scenario['name']}",
                        analyst_name=analyst,
                        detection_source="other",
                        initial_indicator="Simulation",
                        is_simulation=True,
                    )

                    checklists = checklist_manager.create_incident_checklist(incident.id)

                    evidence_logger.log_entry(
                        incident_id=incident.id,
                        description=f"Simulation started: {scenario['name']}",
                        entry_type=EvidenceType.SYSTEM,
                        phase="detection",
                        operator=analyst,
                    )

                    st.session_state.incident = incident
                    st.session_state.phase_tracker = tracker
                    st.session_state.checklists = checklists
                    st.session_state.operator_name = analyst
                    st.session_state.simulation_active = True
                    st.session_state.current_view = "overview"
                    st.rerun()


def render_executive_dashboard_view(
    checklist_manager: ChecklistManager,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    """Render the Executive Dashboard view."""
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker
    checklists = st.session_state.checklists

    if not incident:
        st.error(t("executive.no_incident", lang))
        return

    st.title(t("executive.title", lang))

    if incident.is_simulation:
        st.caption("[SIMULATION]")

    # Get evidence entries
    evidence_entries = evidence_logger.get_entries(incident.id)

    # Get decisions (from evidence log, filter by type)
    decisions = [e for e in evidence_entries if hasattr(e, 'entry_type') and
                 (e.entry_type == "decision" or
                  (hasattr(e.entry_type, 'value') and e.entry_type.value == "decision"))]

    # Get compliance results from session state
    compliance_results = st.session_state.compliance_results

    # Render the dashboard
    render_executive_dashboard(
        incident=incident,
        phase_tracker=tracker,
        checklists=checklists or {},
        evidence_entries=evidence_entries,
        decisions=decisions,
        compliance_results=compliance_results,
        lang=lang,
    )


def render_overview(workflow_engine: WorkflowEngine, lang: str):
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker
    checklists = st.session_state.checklists

    if not incident:
        st.error("No active incident")
        return

    # Header
    st.title(incident.title)

    if incident.is_simulation:
        st.caption("[SIMULATION]")

    # Phase progress - simple text
    st.subheader(t("phases.title", lang))

    phase_names = {
        "detection": t("phases.detection", lang),
        "analysis": t("phases.analysis", lang),
        "containment": t("phases.containment", lang),
        "eradication": t("phases.eradication", lang),
        "recovery": t("phases.recovery", lang),
        "post_incident": t("phases.post_incident", lang),
    }

    cols = st.columns(6)
    for i, phase in enumerate(PHASE_ORDER):
        status = tracker.phases[phase.value].status
        is_current = phase == tracker.current_phase

        with cols[i]:
            if status == "completed":
                st.write(f"[x] {phase_names[phase.value]}")
            elif is_current:
                st.write(f"**> {phase_names[phase.value]}**")
            else:
                st.write(f"[ ] {phase_names[phase.value]}")

    st.divider()

    # Current phase info
    phase_info = workflow_engine.get_current_phase_info(tracker)
    definition = phase_info.get("definition")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"{t('phases.current_phase', lang)}: {phase_names[tracker.current_phase.value]}")

        if definition:
            st.write(f"**{t('phases.objective', lang)}:** {definition['objective']}")

            if definition.get("critical_reminders"):
                for reminder in definition["critical_reminders"]:
                    st.warning(reminder)

        # Progress
        checklist = checklists.get(tracker.current_phase.value)
        if checklist:
            progress = checklist.get_progress()
            st.progress(progress['completed'] / progress['total'] if progress['total'] > 0 else 0)
            st.caption(f"{progress['completed']}/{progress['total']} items completed")

    with col2:
        st.subheader(t("phases.quick_actions", lang))

        if st.button(t("phases.go_to_checklist", lang), use_container_width=True):
            st.session_state.current_view = "checklist"
            st.rerun()

        if st.button(t("phases.make_decision", lang), use_container_width=True):
            st.session_state.current_view = "decisions"
            st.rerun()

        if st.button(t("phases.log_evidence", lang), use_container_width=True):
            st.session_state.current_view = "evidence"
            st.rerun()


def render_checklist_view(
    checklist_manager: ChecklistManager,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker
    checklists = st.session_state.checklists

    if not incident or not checklists:
        st.error("No active incident")
        return

    current_phase = tracker.current_phase.value
    checklist = checklists.get(current_phase)

    if not checklist:
        st.error(f"No checklist for phase: {current_phase}")
        return

    def on_complete(item_id: str):
        item = checklist.get_item(item_id)
        if item:
            checklist_manager.complete_item(checklist, item_id, st.session_state.operator_name)
            evidence_logger.log_entry(
                incident_id=incident.id,
                description=f"Completed: {item.text}",
                entry_type=EvidenceType.ACTION,
                phase=current_phase,
                operator=st.session_state.operator_name,
            )

    def on_skip(item_id: str, reason: str):
        item = checklist.get_item(item_id)
        if item:
            checklist_manager.skip_item(checklist, item_id, st.session_state.operator_name, reason)
            evidence_logger.log_entry(
                incident_id=incident.id,
                description=f"Skipped: {item.text} - {reason}",
                entry_type=EvidenceType.ACTION,
                phase=current_phase,
                operator=st.session_state.operator_name,
            )

    render_checklist(
        checklist=checklist,
        on_complete=on_complete,
        on_skip=on_skip,
        operator=st.session_state.operator_name,
        lang=lang,
    )


def render_decisions(
    decision_engine: DecisionEngine,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker

    if not incident:
        st.error("No active incident")
        return

    current_phase = tracker.current_phase.value

    if current_phase not in st.session_state.decision_trees:
        phase_trees = decision_engine.get_trees_for_phase(current_phase)
        st.session_state.decision_trees[current_phase] = [
            decision_engine.create_incident_tree(tree.id)
            for tree in phase_trees
        ]

    trees = st.session_state.decision_trees.get(current_phase, [])

    if not trees:
        st.info(t("decisions.no_trees", lang))
        return

    st.title(t("decisions.title", lang))

    for tree in trees:
        if tree:
            st.subheader(tree.name)

            def on_decision(option_id: str, rationale: Optional[str]):
                path = decision_engine.make_decision(
                    tree=tree,
                    incident_id=incident.id,
                    option_id=option_id,
                    operator=st.session_state.operator_name,
                    rationale=rationale,
                )
                evidence_logger.log_decision(
                    incident_id=incident.id,
                    description=f"Decision: {path.selected_option_label}",
                    decision_node_id=path.node_id,
                    decision_option_selected=path.selected_option_id,
                    phase=current_phase,
                    operator=st.session_state.operator_name,
                    rationale=rationale,
                )

            render_decision_tree(
                tree=tree,
                on_decision=on_decision,
                operator=st.session_state.operator_name,
                lang=lang,
            )


def render_evidence(evidence_logger: EvidenceLogger, lang: str):
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker

    if not incident:
        st.error("No active incident")
        return

    entries = evidence_logger.get_entries(incident.id)

    def on_add_entry(description: str, entry_type: str, system: Optional[str]):
        evidence_logger.log_entry(
            incident_id=incident.id,
            description=description,
            entry_type=EvidenceType(entry_type),
            phase=tracker.current_phase.value,
            system_affected=system if system else None,
            operator=st.session_state.operator_name,
        )

    render_evidence_log(
        entries=entries,
        on_add_entry=on_add_entry,
        operator=st.session_state.operator_name,
        current_phase=tracker.current_phase.value,
        lang=lang,
    )


def render_compliance(
    checklist_manager: ChecklistManager,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    """Render the compliance validation and threat intelligence view."""
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker
    checklists = st.session_state.checklists

    if not incident:
        st.error("No active incident")
        return

    st.title(t("compliance.title", lang))

    # Initialize ComplianceHub if not already done
    if st.session_state.compliance_hub is None:
        st.session_state.compliance_hub = ComplianceHub(offline_mode=True)

    hub = st.session_state.compliance_hub

    # Initialize IOC Enricher
    if st.session_state.ioc_enricher is None:
        st.session_state.ioc_enricher = IOCEnricher(offline_mode=True)

    enricher = st.session_state.ioc_enricher

    # Tabs for different compliance sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        t("compliance.validation", lang),
        t("compliance.cross_framework_title", lang),
        t("ioc_enrichment.title", lang),
        t("bsi_meldung.title", lang),
        t("compliance.threat_intel_title", lang),
        t("compliance.generate_report", lang),
    ])

    with tab1:
        _render_compliance_validation(hub, tracker, checklists, evidence_logger, incident, lang)

    with tab2:
        _render_cross_framework_tab(hub, tracker, lang)

    with tab3:
        _render_ioc_enrichment_tab(enricher, lang)

    with tab4:
        _render_bsi_meldung_tab(incident, evidence_logger, lang)

    with tab5:
        _render_threat_intel_tab(hub, incident, lang)

    with tab6:
        _render_compliance_report_tab(hub, incident, lang)


def _render_compliance_validation(
    hub: ComplianceHub,
    tracker,
    checklists: dict,
    evidence_logger: EvidenceLogger,
    incident,
    lang: str,
):
    """Render the compliance validation section."""
    current_phase = tracker.current_phase.value

    # Framework selection
    selected_frameworks = render_framework_selector(lang)
    st.session_state.selected_frameworks = selected_frameworks

    st.divider()

    # Gather incident data from current state
    checklist = checklists.get(current_phase)
    completed_actions = []
    if checklist:
        for item in checklist.items:
            if item.status == "completed":
                completed_actions.append(item.id)

    # Get evidence
    entries = evidence_logger.get_entries(incident.id)
    evidence_descriptions = [e.description for e in entries]

    incident_data = {
        "completed_actions": completed_actions,
        "evidence_collected": evidence_descriptions,
        "documentation_provided": [
            e.description for e in entries
            if (e.entry_type.value if hasattr(e.entry_type, 'value') else e.entry_type) in ["document", "screenshot"]
        ],
    }

    # Validate button
    col1, col2 = st.columns([1, 3])
    with col1:
        validate_btn = st.button(
            t("compliance.validate", lang),
            use_container_width=True,
            type="primary",
        )

    if validate_btn and selected_frameworks:
        with st.spinner(t("compliance.loading_data", lang)):
            results = hub.validate_phase_compliance(
                phase=current_phase,
                incident_data=incident_data,
                frameworks=selected_frameworks,
                operator=st.session_state.operator_name,
            )
            st.session_state.compliance_results[current_phase] = results

    # Display results
    if current_phase in st.session_state.compliance_results:
        render_compliance_dashboard(
            phase=current_phase,
            compliance_results=st.session_state.compliance_results[current_phase],
            lang=lang,
        )


def _render_cross_framework_tab(hub: ComplianceHub, tracker, lang: str):
    """Render the cross-framework mapping section."""
    current_phase = tracker.current_phase.value

    st.markdown(f"### {t('compliance.cross_framework_title', lang)}")
    st.caption(t("compliance.unified_score_help", lang))

    # Get mapping data
    mapping_data = hub.get_cross_framework_mapping()

    # Calculate coverage if we have compliance results
    coverage_data = None
    if st.session_state.compliance_results:
        # Build completed controls dict from results
        completed_controls = {}
        for phase_results in st.session_state.compliance_results.values():
            if isinstance(phase_results, dict):
                for fw, checks in phase_results.items():
                    if fw not in completed_controls:
                        completed_controls[fw] = []
                    for check in checks:
                        if hasattr(check, 'status') and check.status.value == "compliant":
                            completed_controls[fw].append(check.control_id)

        if completed_controls:
            coverage_data = hub.calculate_unified_coverage(completed_controls)

    # Render the dashboard
    render_cross_framework_dashboard(mapping_data, coverage_data, lang)

    st.divider()

    # Show phase-specific controls
    st.markdown(f"#### Controls for Phase: {current_phase.replace('_', ' ').title()}")
    phase_mapping = hub.get_cross_framework_mapping(phase=current_phase)

    if phase_mapping and phase_mapping.get("controls"):
        for ctrl in phase_mapping["controls"]:
            with st.expander(f"**{ctrl['unified_id']}**: {ctrl['name']}", expanded=False):
                st.markdown(f"*{ctrl['description']}*")

                st.markdown("**Framework Controls:**")
                for fw, controls in ctrl["framework_controls"].items():
                    if controls:
                        st.markdown(f"- **{fw.upper()}**: {', '.join(controls)}")

                if ctrl.get("evidence_requirements"):
                    st.markdown("**Evidence Required:**")
                    for req in ctrl["evidence_requirements"]:
                        st.caption(f"- {req}")
    else:
        st.info(f"No specific controls mapped for {current_phase} phase")

    st.divider()

    # Coverage gaps
    if coverage_data and coverage_data.get("gaps"):
        render_coverage_gaps(coverage_data["gaps"], lang)
        st.divider()

    # Export options
    render_cross_framework_export(hub, lang)


def _render_bsi_meldung_tab(incident, evidence_logger: EvidenceLogger, lang: str):
    """Render the BSI Meldepflicht (notification) section."""
    st.markdown(f"### {t('bsi_meldung.dashboard_title', lang)}")

    # Get evidence entries for auto-population
    evidence_entries = evidence_logger.get_entries(incident.id)

    # Render the BSI Meldung dashboard
    render_bsi_meldung_dashboard(incident, evidence_entries, lang)


def _render_ioc_enrichment_tab(enricher: IOCEnricher, lang: str):
    """Render the IOC Auto-Enrichment section."""
    st.markdown(f"### {t('ioc_enrichment.dashboard_title', lang)}")

    # Show offline mode notice
    if enricher.offline_mode:
        st.info(f"🔄 {t('ioc_enrichment.offline_mode', lang)}")

    # Render the IOC enrichment dashboard
    render_ioc_enrichment_dashboard(enricher, lang)


def _render_threat_intel_tab(hub: ComplianceHub, incident, lang: str):
    """Render the threat intelligence enrichment section."""
    st.markdown(f"### {t('compliance.threat_intel_title', lang)}")

    # IOC input
    iocs = render_ioc_input(lang)

    st.divider()

    # Ransomware family input
    col1, col2 = st.columns([1, 1])
    with col1:
        ransomware_family = st.text_input(
            t("compliance.ransomware_family", lang),
            placeholder="e.g., LockBit, BlackCat, Conti",
        )

    with col2:
        st.markdown("")
        st.markdown("")
        enrich_btn = st.button(
            t("compliance.enrich", lang),
            use_container_width=True,
            type="primary",
        )

    if enrich_btn and (iocs or ransomware_family):
        with st.spinner(t("compliance.loading_data", lang)):
            # Preload MITRE data if needed
            if not hub.mitre._attack_data:
                hub.mitre.load_attack_data()

            intel = hub.enrich_with_threat_intelligence(
                incident_id=incident.id,
                iocs=iocs,
                ransomware_family=ransomware_family if ransomware_family else None,
            )
            st.session_state.threat_intel = intel

    # Display threat intelligence
    if st.session_state.threat_intel:
        render_threat_intelligence(st.session_state.threat_intel, lang)

        # ATT&CK Navigator link
        if st.session_state.threat_intel.mapped_techniques:
            st.divider()
            render_attack_navigator_link(st.session_state.threat_intel.mapped_techniques)


def _render_compliance_report_tab(hub: ComplianceHub, incident, lang: str):
    """Render the compliance report generation section."""
    st.markdown(f"### {t('compliance.generate_report', lang)}")

    if not st.session_state.compliance_results:
        st.info(t("compliance.validate", lang))
        return

    # Generate report from current results
    report = hub.generate_compliance_report(
        incident_id=incident.id,
        phase_results=st.session_state.compliance_results,
        operator=st.session_state.operator_name,
    )

    def export_callback(format: str) -> str:
        return hub.export_compliance_report(
            report=report,
            format=format,
            include_details=True,
        )

    render_compliance_report_export(report, export_callback, lang)


def render_export(
    report_generator: ReportGenerator,
    evidence_logger: EvidenceLogger,
    lang: str,
):
    incident = st.session_state.incident
    tracker = st.session_state.phase_tracker
    checklists = st.session_state.checklists

    if not incident:
        st.error("No active incident")
        return

    st.title(t("export.title", lang))

    evidence_export = evidence_logger.export_chain(incident.id)

    all_trees = []
    for phase_trees in st.session_state.decision_trees.values():
        all_trees.extend([tree for tree in phase_trees if tree])

    # Simple metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(t("export.evidence_entries", lang), evidence_export["total_entries"])

    with col2:
        total_decisions = sum(len(tree.path_taken) for tree in all_trees)
        st.metric(t("export.decisions_made", lang), total_decisions)

    with col3:
        progress = tracker.get_overall_progress()
        st.metric(t("export.phase_progress", lang), f"{progress['percentage']}%")

    st.divider()

    lessons = st.text_area(t("export.lessons_learned", lang), height=100)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(t("export.export_markdown", lang), use_container_width=True):
            path = report_generator.export_report_only(
                incident=incident,
                phase_tracker=tracker,
                checklists=checklists,
                decision_trees=all_trees,
                evidence_export=evidence_export,
                lessons_learned=lessons if lessons else None,
            )
            st.success(f"Exported: {path}")

    with col2:
        if st.button(t("export.verify_integrity", lang), use_container_width=True):
            is_valid, _, message = evidence_logger.verify_chain(incident.id)
            if is_valid:
                st.success(message)
            else:
                st.error(message)


if __name__ == "__main__":
    main()
