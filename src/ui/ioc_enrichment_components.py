"""
IOC Enrichment UI Components for CyberOps Companion.

Provides Streamlit components for IOC enrichment functionality.
"""

import streamlit as st
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.integrations.ioc_enrichment import (
    IOCEnricher,
    IOCType,
    ThreatLevel,
    EnrichmentSource,
    EnrichmentResult,
)
from src.utils.translations import t


def render_ioc_enrichment_dashboard(
    enricher: IOCEnricher,
    lang: str = "de",
) -> None:
    """
    Render the complete IOC enrichment dashboard.

    Args:
        enricher: IOCEnricher instance
        lang: Language code
    """
    # Initialize session state for enrichment results
    if "enrichment_results" not in st.session_state:
        st.session_state.enrichment_results = []
    if "enrichment_history" not in st.session_state:
        st.session_state.enrichment_history = []

    # Main layout with tabs
    tab1, tab2, tab3 = st.tabs([
        t("ioc_enrichment.single_lookup", lang),
        t("ioc_enrichment.batch_analysis", lang),
        t("ioc_enrichment.history", lang),
    ])

    with tab1:
        render_single_ioc_lookup(enricher, lang)

    with tab2:
        render_batch_analysis(enricher, lang)

    with tab3:
        render_enrichment_history(enricher, lang)


def render_single_ioc_lookup(enricher: IOCEnricher, lang: str) -> None:
    """Render single IOC lookup interface."""
    st.markdown(f"#### {t('ioc_enrichment.enter_ioc', lang)}")

    col1, col2 = st.columns([3, 1])

    with col1:
        ioc_value = st.text_input(
            t("ioc_enrichment.ioc_value", lang),
            placeholder="e.g., 192.168.1.1, evil-domain.com, a1b2c3d4...",
            key="single_ioc_input",
        )

    with col2:
        ioc_type_options = {
            "auto": t("ioc_enrichment.auto_detect", lang),
            "ip": "IP Address",
            "domain": "Domain",
            "url": "URL",
            "md5": "MD5 Hash",
            "sha1": "SHA1 Hash",
            "sha256": "SHA256 Hash",
            "email": "Email",
        }
        selected_type = st.selectbox(
            t("ioc_enrichment.ioc_type", lang),
            options=list(ioc_type_options.keys()),
            format_func=lambda x: ioc_type_options[x],
            key="single_ioc_type",
        )

    # Source selection
    with st.expander(t("ioc_enrichment.select_sources", lang), expanded=False):
        available_sources = [
            EnrichmentSource.VIRUSTOTAL,
            EnrichmentSource.ABUSEIPDB,
            EnrichmentSource.SHODAN,
            EnrichmentSource.GREYNOISE,
            EnrichmentSource.OTX_ALIENVAULT,
        ]

        source_names = {
            EnrichmentSource.VIRUSTOTAL: "VirusTotal",
            EnrichmentSource.ABUSEIPDB: "AbuseIPDB",
            EnrichmentSource.SHODAN: "Shodan",
            EnrichmentSource.GREYNOISE: "GreyNoise",
            EnrichmentSource.OTX_ALIENVAULT: "OTX AlienVault",
        }

        selected_sources = []
        cols = st.columns(3)
        for i, source in enumerate(available_sources):
            with cols[i % 3]:
                if st.checkbox(source_names[source], value=True, key=f"source_{source.value}"):
                    selected_sources.append(source)

    # Enrich button
    if st.button(
        t("ioc_enrichment.enrich_button", lang),
        type="primary",
        disabled=not ioc_value,
    ):
        if ioc_value:
            with st.spinner(t("ioc_enrichment.enriching", lang)):
                # Determine IOC type
                ioc_type = None if selected_type == "auto" else IOCType(selected_type)

                # Perform enrichment
                result = enricher.enrich(
                    ioc_value,
                    ioc_type=ioc_type,
                    sources=selected_sources if selected_sources else None,
                )

                # Store in session state
                st.session_state.enrichment_results = [result]
                st.session_state.enrichment_history.append(result)

    # Display results
    if st.session_state.enrichment_results:
        st.divider()
        for result in st.session_state.enrichment_results:
            render_enrichment_result(result, lang, expanded=True)


def render_batch_analysis(enricher: IOCEnricher, lang: str) -> None:
    """Render batch IOC analysis interface."""
    st.markdown(f"#### {t('ioc_enrichment.batch_title', lang)}")

    st.info(t("ioc_enrichment.batch_info", lang))

    # Text area for multiple IOCs
    iocs_text = st.text_area(
        t("ioc_enrichment.enter_iocs", lang),
        placeholder="192.168.1.1\nevil-domain.com\na1b2c3d4e5f6...\nhttps://malware.com/payload",
        height=200,
        key="batch_iocs",
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button(
            t("ioc_enrichment.analyze_all", lang),
            type="primary",
            disabled=not iocs_text,
        ):
            if iocs_text:
                # Parse IOCs (one per line)
                iocs = [line.strip() for line in iocs_text.split("\n") if line.strip()]

                if len(iocs) > 50:
                    st.warning(t("ioc_enrichment.too_many_iocs", lang))
                    iocs = iocs[:50]

                with st.spinner(f"{t('ioc_enrichment.analyzing', lang)} {len(iocs)} IOCs..."):
                    results = enricher.enrich_batch(iocs)
                    st.session_state.enrichment_results = results
                    st.session_state.enrichment_history.extend(results)

    with col2:
        # File upload option
        uploaded_file = st.file_uploader(
            t("ioc_enrichment.upload_file", lang),
            type=["txt", "csv"],
            key="ioc_file_upload",
        )

        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            iocs = [line.strip() for line in content.split("\n") if line.strip()]
            st.info(f"{t('ioc_enrichment.found_iocs', lang)}: {len(iocs)}")

    # Display batch results
    if st.session_state.enrichment_results and len(st.session_state.enrichment_results) > 1:
        st.divider()
        render_batch_results_summary(st.session_state.enrichment_results, enricher, lang)


def render_batch_results_summary(
    results: List[EnrichmentResult],
    enricher: IOCEnricher,
    lang: str,
) -> None:
    """Render summary of batch analysis results."""
    st.markdown(f"### {t('ioc_enrichment.results_summary', lang)}")

    # Statistics
    threat_counts = {
        ThreatLevel.CRITICAL: 0,
        ThreatLevel.HIGH: 0,
        ThreatLevel.MEDIUM: 0,
        ThreatLevel.LOW: 0,
        ThreatLevel.CLEAN: 0,
        ThreatLevel.UNKNOWN: 0,
    }

    for result in results:
        threat_counts[result.overall_threat_level] += 1

    # Display metrics
    cols = st.columns(6)
    threat_colors = {
        ThreatLevel.CRITICAL: "red",
        ThreatLevel.HIGH: "orange",
        ThreatLevel.MEDIUM: "yellow",
        ThreatLevel.LOW: "green",
        ThreatLevel.CLEAN: "gray",
        ThreatLevel.UNKNOWN: "blue",
    }

    threat_labels = {
        ThreatLevel.CRITICAL: t("ioc_enrichment.threat_critical", lang),
        ThreatLevel.HIGH: t("ioc_enrichment.threat_high", lang),
        ThreatLevel.MEDIUM: t("ioc_enrichment.threat_medium", lang),
        ThreatLevel.LOW: t("ioc_enrichment.threat_low", lang),
        ThreatLevel.CLEAN: t("ioc_enrichment.threat_clean", lang),
        ThreatLevel.UNKNOWN: t("ioc_enrichment.threat_unknown", lang),
    }

    for i, (level, count) in enumerate(threat_counts.items()):
        with cols[i]:
            st.metric(threat_labels[level], count)

    # Results table
    st.markdown(f"#### {t('ioc_enrichment.detailed_results', lang)}")

    # Sort by risk score (highest first)
    sorted_results = sorted(results, key=lambda x: x.risk_score, reverse=True)

    for result in sorted_results:
        render_enrichment_result(result, lang, expanded=False)

    # Export options
    st.divider()
    render_export_options(results, enricher, lang)


def render_enrichment_result(
    result: EnrichmentResult,
    lang: str,
    expanded: bool = False,
) -> None:
    """Render a single enrichment result."""
    # Determine visual indicators
    threat_icons = {
        ThreatLevel.CRITICAL: "🔴",
        ThreatLevel.HIGH: "🟠",
        ThreatLevel.MEDIUM: "🟡",
        ThreatLevel.LOW: "🟢",
        ThreatLevel.CLEAN: "⚪",
        ThreatLevel.UNKNOWN: "❓",
    }

    icon = threat_icons.get(result.overall_threat_level, "❓")
    threat_label = result.overall_threat_level.value.upper()

    # Create expander title
    title = f"{icon} **{result.ioc_value}** | {threat_label} | Score: {result.risk_score:.0f}/100"

    with st.expander(title, expanded=expanded):
        # Basic info row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"**{t('ioc_enrichment.type', lang)}**")
            st.code(result.ioc_type.value)

        with col2:
            st.markdown(f"**{t('ioc_enrichment.threat_level', lang)}**")
            _render_threat_badge(result.overall_threat_level, lang)

        with col3:
            st.markdown(f"**{t('ioc_enrichment.risk_score', lang)}**")
            _render_risk_gauge(result.risk_score)

        with col4:
            st.markdown(f"**{t('ioc_enrichment.confidence', lang)}**")
            st.progress(result.confidence)
            st.caption(f"{result.confidence * 100:.0f}%")

        st.divider()

        # Source results
        st.markdown(f"##### {t('ioc_enrichment.source_results', lang)}")

        source_cols = st.columns(min(len(result.source_results), 3))
        for i, (source, source_result) in enumerate(result.source_results.items()):
            with source_cols[i % 3]:
                _render_source_result(source, source_result, lang)

        # Tags and categories
        if result.categories or result.tags:
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                if result.categories:
                    st.markdown(f"**{t('ioc_enrichment.categories', lang)}**")
                    st.write(" ".join([f"`{cat}`" for cat in result.categories[:10]]))

            with col2:
                if result.tags:
                    st.markdown(f"**{t('ioc_enrichment.tags', lang)}**")
                    st.write(" ".join([f"`{tag}`" for tag in result.tags[:10]]))

        # Geographic info
        if result.geographic_info:
            st.divider()
            st.markdown(f"##### {t('ioc_enrichment.geographic_info', lang)}")
            geo_cols = st.columns(3)
            for i, (key, value) in enumerate(result.geographic_info.items()):
                with geo_cols[i % 3]:
                    st.metric(key.upper(), value)

        # Recommendations
        if result.recommended_actions:
            st.divider()
            st.markdown(f"##### {t('ioc_enrichment.recommendations', lang)}")
            for action in result.recommended_actions[:5]:
                if action.startswith("IMMEDIATE"):
                    st.error(action)
                else:
                    st.warning(action)

        # MITRE ATT&CK
        if result.mitre_techniques:
            st.divider()
            st.markdown(f"##### {t('ioc_enrichment.mitre_techniques', lang)}")
            for tech in result.mitre_techniques[:5]:
                st.markdown(f"- `{tech}`")

        # Related IOCs
        if result.related_iocs:
            st.divider()
            st.markdown(f"##### {t('ioc_enrichment.related_iocs', lang)}")
            for related in result.related_iocs[:5]:
                st.code(related)


def _render_threat_badge(threat_level: ThreatLevel, lang: str) -> None:
    """Render a colored threat level badge."""
    colors = {
        ThreatLevel.CRITICAL: "#dc3545",
        ThreatLevel.HIGH: "#fd7e14",
        ThreatLevel.MEDIUM: "#ffc107",
        ThreatLevel.LOW: "#28a745",
        ThreatLevel.CLEAN: "#6c757d",
        ThreatLevel.UNKNOWN: "#17a2b8",
    }

    color = colors.get(threat_level, "#6c757d")
    label = threat_level.value.upper()

    st.markdown(
        f'<span style="background-color: {color}; color: white; '
        f'padding: 4px 8px; border-radius: 4px; font-weight: bold;">'
        f'{label}</span>',
        unsafe_allow_html=True,
    )


def _render_risk_gauge(score: float) -> None:
    """Render a risk score gauge."""
    if score >= 80:
        color = "red"
    elif score >= 60:
        color = "orange"
    elif score >= 40:
        color = "yellow"
    elif score >= 20:
        color = "lightgreen"
    else:
        color = "green"

    st.markdown(
        f'<div style="background: linear-gradient(to right, {color} {score}%, #ddd {score}%); '
        f'height: 20px; border-radius: 10px; text-align: center; line-height: 20px;">'
        f'<strong>{score:.0f}</strong></div>',
        unsafe_allow_html=True,
    )


def _render_source_result(
    source: EnrichmentSource,
    result,
    lang: str,
) -> None:
    """Render result from a single source."""
    source_names = {
        EnrichmentSource.VIRUSTOTAL: "VirusTotal",
        EnrichmentSource.ABUSEIPDB: "AbuseIPDB",
        EnrichmentSource.SHODAN: "Shodan",
        EnrichmentSource.GREYNOISE: "GreyNoise",
        EnrichmentSource.OTX_ALIENVAULT: "OTX",
        EnrichmentSource.MISP: "MISP",
        EnrichmentSource.INTERNAL: "Internal",
    }

    source_icons = {
        EnrichmentSource.VIRUSTOTAL: "🦠",
        EnrichmentSource.ABUSEIPDB: "🛡️",
        EnrichmentSource.SHODAN: "🔍",
        EnrichmentSource.GREYNOISE: "📡",
        EnrichmentSource.OTX_ALIENVAULT: "👽",
    }

    name = source_names.get(source, source.value)
    icon = source_icons.get(source, "📊")

    with st.container():
        st.markdown(f"**{icon} {name}**")

        if not result.available:
            st.caption(f"⚠️ {result.error or 'Not available'}")
        else:
            threat_icons = {
                ThreatLevel.CRITICAL: "🔴",
                ThreatLevel.HIGH: "🟠",
                ThreatLevel.MEDIUM: "🟡",
                ThreatLevel.LOW: "🟢",
                ThreatLevel.CLEAN: "⚪",
                ThreatLevel.UNKNOWN: "❓",
            }
            icon = threat_icons.get(result.threat_level, "❓")

            st.caption(f"{icon} {result.threat_level.value}")

            if result.detections > 0:
                st.caption(
                    f"{t('ioc_enrichment.detections', lang)}: "
                    f"{result.detections}/{result.total_engines}"
                )

            if result.raw_score is not None:
                st.caption(f"Score: {result.raw_score:.1f}")


def render_enrichment_history(enricher: IOCEnricher, lang: str) -> None:
    """Render enrichment history."""
    st.markdown(f"#### {t('ioc_enrichment.history_title', lang)}")

    if not st.session_state.enrichment_history:
        st.info(t("ioc_enrichment.no_history", lang))
        return

    # Clear history button
    if st.button(t("ioc_enrichment.clear_history", lang)):
        st.session_state.enrichment_history = []
        st.rerun()

    # Display history in reverse chronological order
    for i, result in enumerate(reversed(st.session_state.enrichment_history)):
        render_enrichment_result(result, lang, expanded=False)


def render_export_options(
    results: List[EnrichmentResult],
    enricher: IOCEnricher,
    lang: str,
) -> None:
    """Render export options for enrichment results."""
    st.markdown(f"#### {t('ioc_enrichment.export_title', lang)}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(t("ioc_enrichment.export_json", lang)):
            json_content = enricher.export_results(results, "json")
            st.download_button(
                label=t("ioc_enrichment.download_json", lang),
                data=json_content,
                file_name=f"ioc_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

    with col2:
        if st.button(t("ioc_enrichment.export_csv", lang)):
            csv_content = enricher.export_results(results, "csv")
            st.download_button(
                label=t("ioc_enrichment.download_csv", lang),
                data=csv_content,
                file_name=f"ioc_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    with col3:
        if st.button(t("ioc_enrichment.export_markdown", lang)):
            md_content = enricher.export_results(results, "markdown")
            st.download_button(
                label=t("ioc_enrichment.download_markdown", lang),
                data=md_content,
                file_name=f"ioc_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )

    with col4:
        if st.button(t("ioc_enrichment.export_stix", lang)):
            stix_content = enricher.export_results(results, "stix")
            st.download_button(
                label=t("ioc_enrichment.download_stix", lang),
                data=stix_content,
                file_name=f"ioc_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.stix.json",
                mime="application/json",
            )


def render_quick_enrichment_widget(
    enricher: IOCEnricher,
    lang: str,
) -> Optional[EnrichmentResult]:
    """
    Render a compact IOC enrichment widget for embedding in other views.

    Returns the enrichment result if an IOC was analyzed.
    """
    with st.container():
        st.markdown(f"**{t('ioc_enrichment.quick_lookup', lang)}**")

        col1, col2 = st.columns([4, 1])

        with col1:
            ioc = st.text_input(
                t("ioc_enrichment.ioc_value", lang),
                placeholder="IP, domain, hash...",
                key="quick_ioc_input",
                label_visibility="collapsed",
            )

        with col2:
            analyze = st.button("🔍", key="quick_analyze")

        if analyze and ioc:
            with st.spinner("..."):
                result = enricher.enrich(ioc.strip())

                # Compact display
                threat_icons = {
                    ThreatLevel.CRITICAL: "🔴",
                    ThreatLevel.HIGH: "🟠",
                    ThreatLevel.MEDIUM: "🟡",
                    ThreatLevel.LOW: "🟢",
                    ThreatLevel.CLEAN: "⚪",
                    ThreatLevel.UNKNOWN: "❓",
                }

                icon = threat_icons.get(result.overall_threat_level, "❓")
                st.markdown(
                    f"{icon} **{result.overall_threat_level.value.upper()}** "
                    f"(Score: {result.risk_score:.0f})"
                )

                if result.recommended_actions:
                    st.caption(result.recommended_actions[0])

                return result

    return None


def render_ioc_timeline(
    results: List[EnrichmentResult],
    lang: str,
) -> None:
    """Render a timeline view of IOC enrichments."""
    if not results:
        return

    st.markdown(f"#### {t('ioc_enrichment.timeline', lang)}")

    # Sort by enrichment time
    sorted_results = sorted(results, key=lambda x: x.enrichment_time, reverse=True)

    for result in sorted_results[:20]:  # Limit to last 20
        threat_icons = {
            ThreatLevel.CRITICAL: "🔴",
            ThreatLevel.HIGH: "🟠",
            ThreatLevel.MEDIUM: "🟡",
            ThreatLevel.LOW: "🟢",
            ThreatLevel.CLEAN: "⚪",
            ThreatLevel.UNKNOWN: "❓",
        }

        icon = threat_icons.get(result.overall_threat_level, "❓")
        time_str = result.enrichment_time.strftime("%H:%M:%S")

        st.markdown(
            f"`{time_str}` {icon} **{result.ioc_value}** - "
            f"{result.overall_threat_level.value} ({result.risk_score:.0f})"
        )
