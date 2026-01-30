"""
Compliance and Threat Intelligence UI Components for IR Companion.

Provides Streamlit components for displaying:
- Compliance validation results
- Threat intelligence enrichment
- MITRE ATT&CK mappings
- CVE information
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional, List, Dict, Any, Callable
import streamlit as st

from src.integrations.models import (
    ComplianceFramework,
    ComplianceCheck,
    ComplianceStatus,
    ComplianceReport,
    ThreatIntelligence,
    ATTACKTechnique,
    CVEInfo,
)
from src.utils.translations import t, DEFAULT_LANGUAGE


def render_compliance_dashboard(
    phase: str,
    compliance_results: Dict[str, List[ComplianceCheck]],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render the main compliance dashboard for a phase.

    Args:
        phase: Current IR phase
        compliance_results: Results from ComplianceHub.validate_phase_compliance()
        lang: Language code
    """
    st.markdown(f"### {t('compliance.phase_compliance', lang)}: {phase.replace('_', ' ').title()}")

    if not compliance_results:
        st.info(t('compliance.validate', lang))
        return

    # Calculate overall statistics
    total_controls = 0
    compliant_count = 0
    partial_count = 0
    gap_count = 0

    for checks in compliance_results.values():
        for check in checks:
            total_controls += 1
            if check.status == ComplianceStatus.COMPLIANT:
                compliant_count += 1
            elif check.status == ComplianceStatus.PARTIAL:
                partial_count += 1
            elif check.status == ComplianceStatus.GAP:
                gap_count += 1

    # Overall score
    if total_controls > 0:
        score = ((compliant_count + (partial_count * 0.5)) / total_controls) * 100
    else:
        score = 0

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(t('compliance.compliance_score', lang), f"{score:.0f}%")
    with col2:
        st.metric(t('compliance.controls_compliant', lang), compliant_count)
    with col3:
        st.metric(t('compliance.controls_partial', lang), partial_count)
    with col4:
        st.metric(t('compliance.controls_gap', lang), gap_count)

    # Progress bar
    st.progress(score / 100)

    st.divider()

    # Results by framework
    for framework, checks in compliance_results.items():
        render_framework_results(framework, checks, lang)


def render_framework_results(
    framework: str,
    checks: List[ComplianceCheck],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render compliance results for a single framework."""
    framework_names = {
        "bsi_grundschutz": t('compliance.framework_bsi', lang),
        "nist_csf_2": t('compliance.framework_nist_csf', lang),
        "nist_800_53": t('compliance.framework_nist_800_53', lang),
        "iso_27001": t('compliance.framework_iso_27001', lang),
        "iso_27035": t('compliance.framework_iso_27035', lang),
        "owasp_top_10": t('compliance.framework_owasp', lang),
    }

    framework_name = framework_names.get(framework, framework)

    # Calculate framework score
    compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT)
    total = len(checks)
    score = (compliant / total * 100) if total > 0 else 0

    with st.expander(f"**{framework_name}** - {score:.0f}% ({compliant}/{total})", expanded=False):
        # Table of controls
        for check in checks:
            _render_compliance_check(check, lang)


def _render_compliance_check(check: ComplianceCheck, lang: str) -> None:
    """Render a single compliance check result."""
    status_icons = {
        ComplianceStatus.COMPLIANT: "✅",
        ComplianceStatus.PARTIAL: "⚠️",
        ComplianceStatus.GAP: "❌",
        ComplianceStatus.NOT_EVALUATED: "⏸️",
        ComplianceStatus.NOT_APPLICABLE: "➖",
    }

    status_labels = {
        ComplianceStatus.COMPLIANT: t('compliance.status_compliant', lang),
        ComplianceStatus.PARTIAL: t('compliance.status_partial', lang),
        ComplianceStatus.GAP: t('compliance.status_gap', lang),
        ComplianceStatus.NOT_EVALUATED: t('compliance.status_not_evaluated', lang),
    }

    icon = status_icons.get(check.status, "❓")
    label = status_labels.get(check.status, check.status.value)

    col1, col2, col3 = st.columns([0.15, 0.55, 0.3])

    with col1:
        st.markdown(f"**{check.control_id}**")

    with col2:
        st.markdown(f"{icon} {check.control_name}")

    with col3:
        priority_colors = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }
        priority_icon = priority_colors.get(check.remediation_priority, "⚪")
        st.caption(f"{priority_icon} {check.remediation_priority or 'N/A'}")

    # Show recommendation for gaps
    if check.status in [ComplianceStatus.GAP, ComplianceStatus.PARTIAL] and check.recommendation:
        st.caption(f"→ {check.recommendation}")

    st.markdown("---")


def render_framework_selector(
    lang: str = DEFAULT_LANGUAGE,
) -> List[ComplianceFramework]:
    """
    Render framework selection widget.

    Returns:
        List of selected ComplianceFramework enums
    """
    st.markdown(f"#### {t('compliance.select_frameworks', lang)}")

    framework_options = {
        "bsi_grundschutz": t('compliance.framework_bsi', lang),
        "nist_csf_2": t('compliance.framework_nist_csf', lang),
        "iso_27001": t('compliance.framework_iso_27001', lang),
        "owasp_top_10": t('compliance.framework_owasp', lang),
    }

    selected = []

    cols = st.columns(len(framework_options))
    for i, (fw_value, fw_label) in enumerate(framework_options.items()):
        with cols[i]:
            # OWASP not selected by default
            default_selected = fw_value != "owasp_top_10"
            if st.checkbox(fw_label, value=default_selected, key=f"fw_{fw_value}"):
                selected.append(ComplianceFramework(fw_value))

    return selected


def render_threat_intelligence(
    intel: ThreatIntelligence,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render threat intelligence enrichment results.

    Args:
        intel: ThreatIntelligence object from ComplianceHub
        lang: Language code
    """
    st.markdown(f"### {t('compliance.threat_intel_title', lang)}")

    if intel.ransomware_family:
        st.info(f"**{t('compliance.ransomware_family', lang)}:** {intel.ransomware_family}")

    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs([
        t('compliance.attack_techniques', lang),
        t('compliance.cve_enrichment', lang),
        t('compliance.mitigations', lang),
    ])

    with tab1:
        render_attack_techniques(intel.mapped_techniques, intel.primary_tactics, lang)

    with tab2:
        render_cve_information(intel.related_cves, intel.critical_cves, intel.actively_exploited_cves, lang)

    with tab3:
        render_mitigations(intel.recommended_mitigations, intel.mitigation_recommendations, lang)


def render_attack_techniques(
    techniques: List[ATTACKTechnique],
    primary_tactics: List[str],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render MITRE ATT&CK technique mapping."""
    if not techniques:
        st.info(t('compliance.loading_data', lang))
        return

    # Primary tactics
    if primary_tactics:
        st.markdown(f"**{t('compliance.primary_tactics', lang)}:**")
        tactic_cols = st.columns(min(len(primary_tactics), 5))
        for i, tactic in enumerate(primary_tactics[:5]):
            with tactic_cols[i]:
                st.markdown(f"`{tactic}`")
        st.markdown("")

    # Techniques table
    st.markdown(f"**{t('compliance.mapped_techniques', lang)}:** {len(techniques)}")

    for tech in techniques[:15]:  # Limit to 15
        _render_technique(tech, lang)


def _render_technique(tech: ATTACKTechnique, lang: str) -> None:
    """Render a single ATT&CK technique."""
    col1, col2, col3 = st.columns([0.2, 0.5, 0.3])

    with col1:
        st.markdown(f"[**{tech.technique_id}**]({tech.url})")

    with col2:
        st.markdown(tech.name)
        if tech.tactics:
            st.caption(f"Tactics: {', '.join(tech.tactics[:3])}")

    with col3:
        if tech.relevance_score > 0:
            st.progress(tech.relevance_score)
        if tech.relevance_indicators:
            with st.expander("IOCs", expanded=False):
                for indicator in tech.relevance_indicators[:3]:
                    st.caption(f"• {indicator}")


def render_cve_information(
    cves: List[CVEInfo],
    critical_cves: List[str],
    kev_cves: List[str],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render CVE enrichment information."""
    if not cves:
        st.info(t('compliance.no_cves', lang))
        return

    # Critical and KEV warnings
    if kev_cves:
        st.error(f"**{t('compliance.kev_cves', lang)}:** {', '.join(kev_cves)}")

    if critical_cves:
        st.warning(f"**{t('compliance.critical_cves', lang)}:** {', '.join(critical_cves)}")

    # CVE list
    st.markdown(f"**{t('compliance.related_cves', lang)}:** {len(cves)}")

    for cve in cves[:10]:
        _render_cve(cve, lang)


def _render_cve(cve: CVEInfo, lang: str) -> None:
    """Render a single CVE."""
    severity_colors = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }

    col1, col2, col3 = st.columns([0.25, 0.5, 0.25])

    with col1:
        st.markdown(f"**{cve.cve_id}**")
        if cve.cisa_kev:
            st.markdown("⚠️ **KEV**")

    with col2:
        desc = cve.description[:100] + "..." if len(cve.description) > 100 else cve.description
        st.caption(desc)

    with col3:
        if cve.cvss_v3:
            icon = severity_colors.get(cve.cvss_v3.severity, "⚪")
            st.markdown(f"{icon} {cve.cvss_v3.severity}")
            st.caption(f"Score: {cve.cvss_v3.base_score}")

    st.markdown("---")


def render_mitigations(
    detailed_mitigations: List[Dict[str, str]],
    recommendations: List[str],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render mitigation recommendations."""
    st.markdown(f"**{t('compliance.mitigations', lang)}:**")

    if detailed_mitigations:
        for mit in detailed_mitigations[:8]:
            mit_id = mit.get("id", "")
            mit_name = mit.get("name", "")
            st.markdown(f"• **{mit_id}**: {mit_name}")

    if recommendations:
        st.markdown("")
        st.markdown("**Additional Recommendations:**")
        for rec in recommendations[:5]:
            st.caption(f"→ {rec}")


def render_ioc_input(
    lang: str = DEFAULT_LANGUAGE,
) -> List[Dict[str, str]]:
    """
    Render IOC input form.

    Returns:
        List of IOC dictionaries with 'type' and 'value' keys
    """
    st.markdown(f"#### {t('compliance.ioc_correlation', lang)}")

    ioc_types = t('compliance.ioc_types', lang)

    # Session state for IOCs
    if "iocs" not in st.session_state:
        st.session_state.iocs = []

    # Input form
    with st.form("ioc_form"):
        col1, col2 = st.columns([0.3, 0.7])

        with col1:
            ioc_type = st.selectbox(
                t('compliance.ioc_type', lang),
                options=list(ioc_types.keys()),
                format_func=lambda x: ioc_types[x],
            )

        with col2:
            ioc_value = st.text_input(
                t('compliance.ioc_value', lang),
                placeholder="e.g., 192.168.1.1 or vssadmin delete shadows",
            )

        if st.form_submit_button(t('compliance.add_ioc', lang)):
            if ioc_value:
                st.session_state.iocs.append({
                    "type": ioc_type,
                    "value": ioc_value,
                })

    # Display current IOCs
    if st.session_state.iocs:
        st.markdown("**Current IOCs:**")
        for i, ioc in enumerate(st.session_state.iocs):
            col1, col2, col3 = st.columns([0.2, 0.7, 0.1])
            with col1:
                st.caption(f"`{ioc['type']}`")
            with col2:
                st.caption(ioc['value'])
            with col3:
                if st.button("X", key=f"del_ioc_{i}"):
                    st.session_state.iocs.pop(i)
                    st.rerun()

    return st.session_state.iocs


def render_compliance_report_export(
    report: ComplianceReport,
    export_callback: Callable[[str], str],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render compliance report export section.

    Args:
        report: ComplianceReport object
        export_callback: Function to generate export content
        lang: Language code
    """
    st.markdown(f"### {t('compliance.generate_report', lang)}")

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t('compliance.controls_total', lang), report.total_controls)
    with col2:
        st.metric(t('compliance.controls_compliant', lang), report.compliant_count)
    with col3:
        st.metric(t('compliance.controls_gap', lang), report.gap_count)
    with col4:
        st.metric(t('compliance.compliance_score', lang), f"{report.compliance_score:.0f}%")

    # Critical gaps
    if report.critical_gaps:
        st.markdown(f"#### {t('compliance.critical_gaps', lang)}")
        for gap in report.critical_gaps[:5]:
            st.error(f"**{gap.control_id}**: {gap.control_name}")
            if gap.recommendation:
                st.caption(f"→ {gap.recommendation}")
    else:
        st.success(t('compliance.no_critical_gaps', lang))

    st.divider()

    # Export buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button(t('compliance.generate_report', lang), use_container_width=True):
            content = export_callback("markdown")
            st.session_state.compliance_report_content = content
            st.success("Report generated!")

    with col2:
        if "compliance_report_content" in st.session_state:
            st.download_button(
                t('compliance.download_report', lang),
                data=st.session_state.compliance_report_content,
                file_name=f"compliance_report_{report.incident_id}.md",
                mime="text/markdown",
                use_container_width=True,
            )


def render_compliance_summary_card(
    framework: str,
    compliant: int,
    total: int,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render a compact compliance summary card."""
    framework_names = {
        "bsi_grundschutz": "BSI",
        "nist_csf_2": "NIST CSF",
        "iso_27001": "ISO 27001",
    }

    name = framework_names.get(framework, framework)
    score = (compliant / total * 100) if total > 0 else 0

    if score >= 80:
        color = "🟢"
    elif score >= 50:
        color = "🟡"
    else:
        color = "🔴"

    st.markdown(f"{color} **{name}**: {score:.0f}% ({compliant}/{total})")


def render_attack_navigator_link(techniques: List[ATTACKTechnique]) -> None:
    """Render link to ATT&CK Navigator with techniques pre-selected."""
    if not techniques:
        return

    tech_ids = [t.technique_id for t in techniques[:20]]
    # ATT&CK Navigator doesn't have a direct URL API, but we can show the IDs
    st.markdown("**ATT&CK Navigator:**")
    st.code(",".join(tech_ids), language=None)
    st.caption("Copy these IDs to paste into [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)")


# =============================================================================
# Cross-Framework Mapping Components
# =============================================================================

def render_cross_framework_dashboard(
    mapping_data: Dict[str, Any],
    coverage_data: Optional[Dict[str, Any]] = None,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render the cross-framework mapping dashboard.

    Args:
        mapping_data: Data from ComplianceHub.get_cross_framework_mapping()
        coverage_data: Optional coverage data from calculate_unified_coverage()
        lang: Language code
    """
    st.markdown(f"### {t('compliance.cross_framework_title', lang)}")

    # Coverage summary if available
    if coverage_data:
        render_unified_coverage_summary(coverage_data, lang)
        st.divider()

    # Mapping matrix
    render_framework_mapping_matrix(mapping_data, lang)


def render_unified_coverage_summary(
    coverage_data: Dict[str, Any],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render unified coverage summary across all frameworks."""
    unified = coverage_data.get("unified_coverage", {})
    framework_coverage = coverage_data.get("framework_coverage", {})

    # Main unified score
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score = unified.get("percentage", 0)
        st.metric(
            t("compliance.unified_score", lang),
            f"{score:.0f}%",
            help=t("compliance.unified_score_help", lang),
        )

    with col2:
        st.metric(
            t("compliance.controls_covered", lang),
            f"{unified.get('covered', 0)}/{unified.get('total', 0)}",
        )

    with col3:
        gaps_count = len(coverage_data.get("gaps", []))
        st.metric(
            t("compliance.gaps_remaining", lang),
            gaps_count,
        )

    with col4:
        frameworks_count = len([f for f in framework_coverage.values() if f.get("covered", 0) > 0])
        st.metric(
            t("compliance.frameworks_active", lang),
            f"{frameworks_count}/5",
        )

    # Progress bar
    st.progress(unified.get("percentage", 0) / 100)

    # Per-framework breakdown
    st.markdown(f"#### {t('compliance.framework_breakdown', lang)}")

    framework_names = {
        "bsi_grundschutz": "BSI",
        "nist_csf_2": "NIST CSF",
        "nist_800_53": "NIST 800-53",
        "iso_27001": "ISO 27001",
        "owasp_top_10": "OWASP",
    }

    cols = st.columns(5)
    for i, (fw_key, fw_name) in enumerate(framework_names.items()):
        with cols[i]:
            fw_data = framework_coverage.get(fw_key, {})
            pct = fw_data.get("percentage", 0)
            covered = fw_data.get("covered", 0)
            total = fw_data.get("total", 0)

            if pct >= 80:
                color = "🟢"
            elif pct >= 50:
                color = "🟡"
            elif pct > 0:
                color = "🟠"
            else:
                color = "⚪"

            st.markdown(f"{color} **{fw_name}**")
            st.caption(f"{pct:.0f}% ({covered}/{total})")


def render_framework_mapping_matrix(
    mapping_data: Dict[str, Any],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render the cross-framework control mapping matrix."""
    st.markdown(f"#### {t('compliance.mapping_matrix', lang)}")

    rows = mapping_data.get("rows", [])

    if not rows:
        st.info(t("compliance.no_mappings", lang))
        return

    # Create expandable sections by category
    categories = {}
    for row in rows:
        cat = row.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(row)

    category_names = {
        "detection": t("phases.detection", lang),
        "analysis": t("phases.analysis", lang),
        "containment": t("phases.containment", lang),
        "access_control": t("compliance.access_control", lang),
        "cryptography": t("compliance.cryptography", lang),
        "injection": t("compliance.injection", lang),
        "vulnerability": t("compliance.vulnerability", lang),
        "recovery": t("phases.recovery", lang),
        "post_incident": t("phases.post_incident", lang),
        "reporting": t("compliance.reporting", lang),
    }

    for cat, cat_rows in categories.items():
        cat_name = category_names.get(cat, cat.title())

        with st.expander(f"**{cat_name}** ({len(cat_rows)} controls)", expanded=False):
            for row in cat_rows:
                render_unified_control_row(row, lang)


def render_unified_control_row(
    row: Dict[str, Any],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render a single unified control with all framework mappings."""
    unified_id = row.get("unified_id", "")
    name = row.get("name", "")

    st.markdown(f"**{unified_id}**: {name}")

    # Create columns for each framework
    col1, col2, col3, col4, col5 = st.columns(5)

    framework_cols = [
        (col1, "bsi_grundschutz", "BSI"),
        (col2, "nist_csf_2", "NIST CSF"),
        (col3, "nist_800_53", "NIST 800-53"),
        (col4, "iso_27001", "ISO 27001"),
        (col5, "owasp_top_10", "OWASP"),
    ]

    for col, fw_key, fw_name in framework_cols:
        with col:
            controls = row.get(fw_key, ["-"])
            if controls and controls != ["-"]:
                for ctrl in controls[:3]:  # Limit to 3
                    st.caption(f"`{ctrl}`")
            else:
                st.caption("-")

    st.markdown("---")


def render_control_equivalents(
    control_id: str,
    framework: str,
    equivalents: Dict[str, List[Dict[str, str]]],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render equivalent controls in other frameworks.

    Args:
        control_id: Source control ID
        framework: Source framework name
        equivalents: Dict mapping framework to equivalent controls
        lang: Language code
    """
    if not equivalents:
        st.info(t("compliance.no_equivalents", lang))
        return

    st.markdown(f"#### {t('compliance.equivalent_controls', lang)}: `{control_id}`")

    framework_names = {
        "bsi_grundschutz": "BSI IT-Grundschutz",
        "nist_csf_2": "NIST CSF 2.0",
        "nist_800_53": "NIST SP 800-53",
        "iso_27001": "ISO 27001:2022",
        "iso_27035": "ISO 27035",
        "owasp_top_10": "OWASP Top 10",
    }

    for fw, controls in equivalents.items():
        fw_name = framework_names.get(fw, fw)
        st.markdown(f"**{fw_name}:**")

        for ctrl in controls:
            ctrl_id = ctrl.get("id", "")
            ctrl_name = ctrl.get("name", "")
            st.markdown(f"- `{ctrl_id}`: {ctrl_name}")

        st.markdown("")


def render_coverage_gaps(
    gaps: List[Dict[str, Any]],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render list of coverage gaps that need attention."""
    if not gaps:
        st.success(t("compliance.no_gaps", lang))
        return

    st.markdown(f"#### {t('compliance.coverage_gaps', lang)}")

    # Group by category
    gaps_by_category = {}
    for gap in gaps:
        cat = gap.get("category", "other")
        if cat not in gaps_by_category:
            gaps_by_category[cat] = []
        gaps_by_category[cat].append(gap)

    for cat, cat_gaps in gaps_by_category.items():
        st.markdown(f"**{cat.replace('_', ' ').title()}**")

        for gap in cat_gaps:
            unified_id = gap.get("unified_id", "")
            name = gap.get("name", "")
            phases = ", ".join(gap.get("phases", []))
            frameworks = len(gap.get("frameworks_affected", []))

            st.warning(
                f"**{unified_id}**: {name}\n\n"
                f"Phases: {phases} | Affects {frameworks} frameworks"
            )


def render_cross_framework_export(
    hub,  # ComplianceHub instance
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render export options for cross-framework mapping."""
    st.markdown(f"#### {t('compliance.export_mapping', lang)}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(t("compliance.export_markdown", lang), use_container_width=True):
            content = hub.export_cross_framework_matrix("markdown")
            st.session_state.cross_framework_export = content
            st.success(t("compliance.export_ready", lang))

    with col2:
        if st.button(t("compliance.export_csv", lang), use_container_width=True):
            content = hub.export_cross_framework_matrix("csv")
            st.session_state.cross_framework_export_csv = content
            st.success(t("compliance.export_ready", lang))

    # Download buttons
    if "cross_framework_export" in st.session_state:
        st.download_button(
            t("compliance.download_markdown", lang),
            data=st.session_state.cross_framework_export,
            file_name="cross_framework_mapping.md",
            mime="text/markdown",
        )

    if "cross_framework_export_csv" in st.session_state:
        st.download_button(
            t("compliance.download_csv", lang),
            data=st.session_state.cross_framework_export_csv,
            file_name="cross_framework_mapping.csv",
            mime="text/csv",
        )
