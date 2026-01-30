"""
UI Components for CyberOps Companion

Reusable Streamlit components for the incident response interface.
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional, List, Dict, Any, Callable
import streamlit as st

from src.models.phase import IRPhase, PHASE_ORDER
from src.models.checklist import ChecklistPhase, ChecklistItem, ChecklistStatus
from src.models.decision import DecisionTree, DecisionNode, ConfidenceLevel
from src.models.evidence import EvidenceEntry

from src.utils.translations import t, DEFAULT_LANGUAGE


def render_phase_indicator(
    current_phase: IRPhase,
    phase_statuses: Dict[str, str],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render the phase progress indicator.

    Shows all phases with their status and highlights the current phase.
    """
    st.markdown(f"### {t('phases.title', lang)}")

    # Create columns for each phase
    cols = st.columns(len(PHASE_ORDER))

    phase_names = {
        "detection": t("phases.detection", lang),
        "analysis": t("phases.analysis", lang),
        "containment": t("phases.containment", lang),
        "eradication": t("phases.eradication", lang),
        "recovery": t("phases.recovery", lang),
        "post_incident": t("phases.post_incident", lang),
    }

    status_symbols = {
        "not_started": "[ ]",
        "in_progress": "[>]",
        "completed": "[x]",
        "skipped": "[-]",
    }

    for i, phase in enumerate(PHASE_ORDER):
        with cols[i]:
            is_current = phase == current_phase
            status = phase_statuses.get(phase.value, "not_started")
            status_symbol = status_symbols.get(status, "[ ]")

            phase_name = phase_names.get(phase.value, phase.value)

            # Highlight current phase
            if is_current:
                st.markdown(f"**{phase_name}**")
                st.markdown(f"{status_symbol} *{t('phases.current', lang)}*")
            else:
                st.markdown(f"{phase_name}")
                st.markdown(f"{status_symbol}")


def render_progress_bar(
    completed: int,
    total: int,
    label: str = "Progress",
) -> None:
    """Render a progress bar with label."""
    if total == 0:
        percentage = 100
    else:
        percentage = int((completed / total) * 100)

    st.progress(percentage / 100, text=f"{label}: {completed}/{total} ({percentage}%)")


def render_checklist(
    checklist: ChecklistPhase,
    on_complete: Callable[[str], None],
    on_skip: Callable[[str, str], None],
    operator: str,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render an interactive checklist.

    Args:
        checklist: The checklist to render
        on_complete: Callback when item is completed
        on_skip: Callback when item is skipped (requires reason)
        operator: Name of the current operator
        lang: Language code
    """
    progress = checklist.get_progress()

    st.markdown(f"### {checklist.phase_name} {t('checklist.title', lang)}")
    render_progress_bar(progress["completed"], progress["total"], t("checklist.progress", lang))

    if progress["mandatory_remaining"] > 0:
        st.warning(f"{progress['mandatory_remaining']} {t('checklist.mandatory_remaining', lang)}")

    # Group items by status
    available = checklist.get_available_items()
    blocked = checklist.get_blocked_items()
    completed_ids = checklist.get_completed_ids()

    # Render available items
    if available:
        st.markdown(f"#### {t('checklist.available_items', lang)}")
        for item in sorted(available, key=lambda x: x.order):
            _render_checklist_item(item, on_complete, on_skip, operator, lang)

    # Render blocked items
    if blocked:
        st.markdown(f"#### {t('checklist.blocked_items', lang)}")
        st.caption(t("checklist.complete_deps_first", lang))
        for item in sorted(blocked, key=lambda x: x.order):
            _render_blocked_item(item, lang)

    # Render completed items (collapsed)
    completed_items = [i for i in checklist.items if i.id in completed_ids]
    if completed_items:
        with st.expander(f"{t('checklist.completed_items', lang)} ({len(completed_items)})"):
            for item in completed_items:
                _render_completed_item(item, lang)


def _render_checklist_item(
    item: ChecklistItem,
    on_complete: Callable[[str], None],
    on_skip: Callable[[str, str], None],
    operator: str,
    lang: str,
) -> None:
    """Render a single actionable checklist item."""
    col1, col2, col3 = st.columns([0.7, 0.15, 0.15])

    with col1:
        # Item text with indicators
        indicators = []
        if item.mandatory:
            indicators.append(f"**[{t('checklist.required', lang)}]**")
        if item.forensic_critical:
            indicators.append(f"*{t('checklist.forensic_critical', lang)}*")

        indicator_str = " ".join(indicators)
        st.markdown(f"[ ] {item.text} {indicator_str}")

        if item.help_text:
            st.caption(item.help_text)

        if item.warning:
            st.warning(item.warning)

    with col2:
        if st.button(t("checklist.complete", lang), key=f"complete_{item.id}"):
            on_complete(item.id)

    with col3:
        if not item.mandatory:
            if st.button(t("checklist.skip", lang), key=f"skip_{item.id}"):
                # Show skip reason dialog
                st.session_state[f"skip_dialog_{item.id}"] = True

    # Skip reason dialog
    if st.session_state.get(f"skip_dialog_{item.id}"):
        with st.form(f"skip_form_{item.id}"):
            reason = st.text_input(t("checklist.skip_reason", lang))
            submitted = st.form_submit_button(t("checklist.confirm_skip", lang))
            if submitted and reason:
                on_skip(item.id, reason)
                st.session_state[f"skip_dialog_{item.id}"] = False
                st.rerun()


def _render_blocked_item(item: ChecklistItem, lang: str) -> None:
    """Render a blocked checklist item."""
    st.markdown(f"[X] ~~{item.text}~~")
    deps = ", ".join(item.depends_on)
    st.caption(f"{t('checklist.blocked_by', lang)}: {deps}")


def _render_completed_item(item: ChecklistItem, lang: str) -> None:
    """Render a completed checklist item."""
    status_symbol = "[x]" if item.status == ChecklistStatus.COMPLETED else "[-]"
    st.markdown(f"{status_symbol} {item.text}")

    if item.completed_at:
        st.caption(f"{t('checklist.completed', lang)}: {item.completed_at.strftime('%H:%M:%S')} - {item.completed_by}")

    if item.notes:
        st.caption(f"{t('checklist.note', lang)}: {item.notes}")

    if item.skip_reason:
        st.caption(f"{t('checklist.skipped', lang)}: {item.skip_reason}")


def render_decision_tree(
    tree: DecisionTree,
    on_decision: Callable[[str, Optional[str]], None],
    operator: str,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render an interactive decision tree.

    Args:
        tree: The decision tree to render
        on_decision: Callback when a decision is made (option_id, rationale)
        operator: Name of the current operator
        lang: Language code
    """
    current_node = tree.get_current_node()

    if not current_node:
        if tree.completed:
            st.success(t("decisions.all_decided", lang))
            _render_decision_history(tree, lang)
        else:
            st.info(t("decisions.no_trees", lang))
        return

    st.markdown(f"### {t('decisions.decision_point', lang)}: {current_node.title}")

    # Question
    st.markdown(f"**{current_node.question}**")

    if current_node.context:
        st.info(current_node.context)

    if current_node.help_text:
        with st.expander(t("decisions.need_help", lang)):
            st.markdown(current_node.help_text)

    # Options
    st.markdown(f"#### {t('decisions.options', lang)}")

    for option in current_node.options:
        _render_decision_option(option, on_decision, operator, lang)

    # Decision history
    if tree.path_taken:
        with st.expander(f"{t('decisions.previous_decisions', lang)} ({len(tree.path_taken)})"):
            _render_decision_history(tree, lang)


def _render_decision_option(
    option: Any,  # DecisionOption
    on_decision: Callable[[str, Optional[str]], None],
    operator: str,
    lang: str,
) -> None:
    """Render a single decision option."""
    confidence_labels = {
        ConfidenceLevel.HIGH: t("decisions.confidence_high", lang),
        ConfidenceLevel.MEDIUM: t("decisions.confidence_medium", lang),
        ConfidenceLevel.LOW: t("decisions.confidence_low", lang),
    }

    with st.container():
        col1, col2 = st.columns([0.8, 0.2])

        with col1:
            # Option header
            header = option.label
            if option.recommended:
                header += f" *{t('decisions.recommended', lang)}*"

            st.markdown(f"**{header}**")
            st.markdown(option.description)

            # Confidence badge
            confidence = confidence_labels.get(option.confidence, "UNKNOWN")
            st.caption(f"{t('decisions.confidence', lang)}: {confidence}")

            if option.warning:
                st.warning(option.warning)

        with col2:
            # Selection button
            button_type = "primary" if option.recommended else "secondary"

            if option.requires_confirmation:
                if st.button(
                    t("decisions.select", lang),
                    key=f"opt_{option.id}",
                    type=button_type,
                ):
                    st.session_state[f"confirm_{option.id}"] = True

                if st.session_state.get(f"confirm_{option.id}"):
                    st.warning(t("decisions.affects_evidence", lang))
                    if st.button(t("decisions.confirm", lang), key=f"confirm_btn_{option.id}"):
                        _show_rationale_form(option.id, on_decision, lang)
                        st.session_state[f"confirm_{option.id}"] = False
            else:
                if st.button(
                    t("decisions.select", lang),
                    key=f"opt_{option.id}",
                    type=button_type,
                ):
                    _show_rationale_form(option.id, on_decision, lang)

        st.divider()


def _show_rationale_form(
    option_id: str,
    on_decision: Callable[[str, Optional[str]], None],
    lang: str,
) -> None:
    """Show form to capture decision rationale."""
    with st.form(f"rationale_{option_id}"):
        rationale = st.text_area(
            t("decisions.rationale", lang),
            placeholder=t("decisions.rationale_placeholder", lang),
        )
        if st.form_submit_button(t("decisions.confirm_decision", lang)):
            on_decision(option_id, rationale if rationale else None)
            st.rerun()


def _render_decision_history(tree: DecisionTree, lang: str) -> None:
    """Render the history of decisions made."""
    confidence_labels = {
        ConfidenceLevel.HIGH: t("decisions.confidence_high", lang),
        ConfidenceLevel.MEDIUM: t("decisions.confidence_medium", lang),
        ConfidenceLevel.LOW: t("decisions.confidence_low", lang),
    }

    for i, path in enumerate(tree.path_taken, 1):
        confidence = confidence_labels.get(path.confidence, "UNKNOWN")
        st.markdown(f"**{i}. {path.selected_option_label}**")
        st.caption(
            f"{t('decisions.confidence', lang)}: {confidence} | "
            f"{path.decided_at.strftime('%H:%M:%S')} | "
            f"{path.operator}"
        )
        if path.rationale:
            st.caption(f"{t('decisions.rationale', lang).replace(':', '')}: {path.rationale}")


def render_evidence_log(
    entries: List[EvidenceEntry],
    on_add_entry: Callable[[str, str, str], None],
    operator: str,
    current_phase: str,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render the evidence log with add entry form.

    Args:
        entries: List of evidence entries to display
        on_add_entry: Callback to add new entry (description, type, notes)
        operator: Current operator name
        current_phase: Current IR phase
        lang: Language code
    """
    st.markdown(f"### {t('evidence.title', lang)}")

    # Add entry form
    with st.expander(f"+ {t('evidence.add_entry', lang)}", expanded=False):
        with st.form("add_evidence"):
            entry_types = t("evidence.types", lang)
            entry_type = st.selectbox(
                t("evidence.entry_type", lang),
                options=list(entry_types.keys()),
                format_func=lambda x: entry_types[x],
            )

            description = st.text_area(
                t("evidence.description", lang),
                placeholder=t("evidence.description_placeholder", lang),
            )

            system = st.text_input(
                t("evidence.system_affected", lang),
                placeholder="e.g., WS-PC-0142",
            )

            evidence_preserved = st.checkbox(
                t("evidence.evidence_preserved", lang),
                value=True,
            )

            if st.form_submit_button(t("evidence.log_entry", lang)):
                if description:
                    on_add_entry(description, entry_type, system)
                    st.success(t("evidence.entry_logged", lang))
                    st.rerun()
                else:
                    st.error(t("evidence.description_required", lang))

    # Recent entries
    st.markdown(f"#### {t('evidence.recent_entries', lang)}")

    if not entries:
        st.info(t("evidence.no_entries", lang))
        return

    for entry in reversed(entries[-10:]):  # Show last 10
        _render_evidence_entry(entry, lang)


def _render_evidence_entry(entry: EvidenceEntry, lang: str) -> None:
    """Render a single evidence entry."""
    entry_types = t("evidence.types", lang)
    type_name = entry_types.get(entry.entry_type.value, entry.entry_type.value)

    timestamp = entry.timestamp.strftime("%H:%M:%S")

    col1, col2 = st.columns([0.15, 0.85])

    with col1:
        st.markdown(f"**{timestamp}**")
        st.caption(f"[{type_name}]")

    with col2:
        st.markdown(entry.description)

        details = []
        if entry.system_affected:
            details.append(f"{t('evidence.system', lang)}: {entry.system_affected}")
        if entry.operator:
            details.append(f"{t('evidence.by', lang)}: {entry.operator}")
        if not entry.evidence_preserved:
            details.append(f"! {t('evidence.evidence_modified', lang)}")

        if details:
            st.caption(" | ".join(details))

    st.divider()


def render_simulation_banner(
    simulation_id: str,
    scenario_name: str,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render a banner indicating simulation mode is active."""
    st.warning(
        f"""
        **{t('simulation.simulation_active', lang)}**

        {t('simulation.scenario', lang)}: {scenario_name}
        {t('simulation.simulation_id', lang)}: {simulation_id}

        {t('simulation.is_training', lang)}
        """
    )


def render_forensic_warning(message: str) -> None:
    """Render a forensic warning message."""
    st.error(f"**FORENSIC WARNING:** {message}")


def render_confirmation_dialog(
    title: str,
    message: str,
    on_confirm: Callable[[], None],
    on_cancel: Callable[[], None],
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
) -> None:
    """Render a confirmation dialog."""
    st.markdown(f"### {title}")
    st.markdown(message)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(confirm_text, type="primary"):
            on_confirm()
    with col2:
        if st.button(cancel_text):
            on_cancel()
