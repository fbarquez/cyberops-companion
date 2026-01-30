"""
BSI Meldung UI Components for CyberOps Companion.

Provides Streamlit components for:
- BSI incident notification form
- Deadline tracking
- Export functionality
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from src.integrations.bsi_meldung import (
    BSIMeldung,
    BSIMeldungGenerator,
    IncidentCategory,
    ImpactLevel,
    KRITISSector,
    NotificationType,
    ContactPerson,
)
from src.utils.translations import t, DEFAULT_LANGUAGE


def render_bsi_meldung_dashboard(
    incident,
    evidence_entries: List[Any],
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render the main BSI Meldung dashboard.

    Args:
        incident: Current incident object
        evidence_entries: List of evidence entries
        lang: Language code
    """
    st.markdown(f"### {t('bsi_meldung.title', lang)}")

    # Initialize generator
    generator = BSIMeldungGenerator()

    # Initialize session state for meldung
    if "bsi_meldung" not in st.session_state:
        st.session_state.bsi_meldung = None
    if "bsi_meldung_org" not in st.session_state:
        st.session_state.bsi_meldung_org = {}
    if "bsi_meldung_contact" not in st.session_state:
        st.session_state.bsi_meldung_contact = {}

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        t("bsi_meldung.deadlines", lang),
        t("bsi_meldung.form", lang),
        t("bsi_meldung.preview", lang),
        t("bsi_meldung.export", lang),
    ])

    with tab1:
        render_deadline_tracker(incident, generator, lang)

    with tab2:
        render_meldung_form(incident, evidence_entries, generator, lang)

    with tab3:
        render_meldung_preview(lang)

    with tab4:
        render_meldung_export(generator, lang)


def render_deadline_tracker(
    incident,
    generator: BSIMeldungGenerator,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render deadline tracking section."""
    st.markdown(f"#### {t('bsi_meldung.deadline_tracker', lang)}")

    # Get detection time from incident
    detection_time = incident.created_at
    if detection_time.tzinfo is None:
        detection_time = detection_time.replace(tzinfo=timezone.utc)

    # Check if KRITIS
    is_kritis = st.session_state.bsi_meldung_org.get("is_kritis", False)

    # Calculate deadlines
    deadlines = generator.calculate_deadlines(detection_time, is_kritis)

    # Sort by urgency (overdue first, then by remaining time)
    sorted_deadlines = sorted(
        deadlines.items(),
        key=lambda x: (not x[1]["overdue"], x[1]["remaining"])
    )

    # Display deadlines
    for key, deadline in sorted_deadlines:
        remaining = deadline["remaining"]
        overdue = deadline["overdue"]

        # Skip non-applicable deadlines
        if key.startswith("kritis") and not is_kritis:
            continue

        col1, col2, col3 = st.columns([0.4, 0.35, 0.25])

        with col1:
            if overdue:
                st.error(f"**{deadline['name']}**")
            elif remaining.total_seconds() < 12 * 3600:  # Less than 12 hours
                st.warning(f"**{deadline['name']}**")
            else:
                st.info(f"**{deadline['name']}**")

        with col2:
            st.caption(deadline["description"])

        with col3:
            if overdue:
                st.markdown("**:red[ÜBERFÄLLIG]**")
            else:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                if hours > 24:
                    days = hours // 24
                    st.markdown(f"**{days}d {hours % 24}h**")
                else:
                    st.markdown(f"**{hours}h {minutes}m**")

    st.divider()

    # Quick action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("bsi_meldung.create_initial", lang), use_container_width=True, type="primary"):
            st.session_state.active_meldung_tab = "form"
            st.rerun()

    with col2:
        st.checkbox(
            t("bsi_meldung.is_kritis", lang),
            key="kritis_checkbox",
            value=is_kritis,
            on_change=lambda: st.session_state.bsi_meldung_org.update(
                {"is_kritis": st.session_state.kritis_checkbox}
            ),
        )


def render_meldung_form(
    incident,
    evidence_entries: List[Any],
    generator: BSIMeldungGenerator,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render the BSI notification form."""
    st.markdown(f"#### {t('bsi_meldung.form', lang)}")

    with st.form("bsi_meldung_form"):
        # Notification Type
        st.markdown(f"##### {t('bsi_meldung.notification_type', lang)}")
        notification_type = st.selectbox(
            t("bsi_meldung.type", lang),
            options=["erstmeldung", "folgemeldung", "abschlussmeldung"],
            format_func=lambda x: {
                "erstmeldung": "Erstmeldung (Initial)",
                "folgemeldung": "Folgemeldung (Follow-up)",
                "abschlussmeldung": "Abschlussmeldung (Final)",
            }[x],
        )

        reference_id = ""
        if notification_type != "erstmeldung":
            reference_id = st.text_input(
                t("bsi_meldung.reference_id", lang),
                placeholder="BSI-INC-XXXX-YYYYMMDD",
            )

        st.divider()

        # Organization Information
        st.markdown(f"##### {t('bsi_meldung.organization', lang)}")

        col1, col2 = st.columns(2)
        with col1:
            org_name = st.text_input(
                t("bsi_meldung.org_name", lang) + " *",
                value=st.session_state.bsi_meldung_org.get("name", ""),
            )
        with col2:
            org_sector = st.selectbox(
                t("bsi_meldung.sector", lang),
                options=[
                    "nicht_kritis", "energie", "wasser", "ernaehrung",
                    "it_telekommunikation", "gesundheit", "finanz_versicherung",
                    "transport_verkehr", "staat_verwaltung", "medien_kultur",
                ],
                format_func=lambda x: {
                    "nicht_kritis": "Kein KRITIS-Sektor",
                    "energie": "Energie",
                    "wasser": "Wasser",
                    "ernaehrung": "Ernährung",
                    "it_telekommunikation": "IT und Telekommunikation",
                    "gesundheit": "Gesundheit",
                    "finanz_versicherung": "Finanz- und Versicherungswesen",
                    "transport_verkehr": "Transport und Verkehr",
                    "staat_verwaltung": "Staat und Verwaltung",
                    "medien_kultur": "Medien und Kultur",
                }[x],
            )

        org_address = st.text_area(
            t("bsi_meldung.org_address", lang),
            value=st.session_state.bsi_meldung_org.get("address", ""),
            height=80,
        )

        col1, col2 = st.columns(2)
        with col1:
            is_kritis = st.checkbox(
                t("bsi_meldung.is_kritis", lang),
                value=st.session_state.bsi_meldung_org.get("is_kritis", False),
            )
        with col2:
            kritis_number = ""
            if is_kritis:
                kritis_number = st.text_input(
                    t("bsi_meldung.kritis_number", lang),
                    value=st.session_state.bsi_meldung_org.get("kritis_number", ""),
                )

        st.divider()

        # Contact Information
        st.markdown(f"##### {t('bsi_meldung.contact', lang)}")

        col1, col2 = st.columns(2)
        with col1:
            contact_name = st.text_input(
                t("bsi_meldung.contact_name", lang) + " *",
                value=st.session_state.bsi_meldung_contact.get("name", ""),
            )
            contact_email = st.text_input(
                t("bsi_meldung.contact_email", lang) + " *",
                value=st.session_state.bsi_meldung_contact.get("email", ""),
            )
        with col2:
            contact_role = st.text_input(
                t("bsi_meldung.contact_role", lang),
                value=st.session_state.bsi_meldung_contact.get("role", "IT-Sicherheitsbeauftragter"),
            )
            contact_phone = st.text_input(
                t("bsi_meldung.contact_phone", lang) + " *",
                value=st.session_state.bsi_meldung_contact.get("phone", ""),
            )

        available_24_7 = st.checkbox(t("bsi_meldung.available_24_7", lang))

        st.divider()

        # Incident Information (pre-filled from incident)
        st.markdown(f"##### {t('bsi_meldung.incident_info', lang)}")

        incident_title = st.text_input(
            t("bsi_meldung.incident_title", lang) + " *",
            value=incident.title if incident else "",
        )

        incident_category = st.selectbox(
            t("bsi_meldung.incident_category", lang),
            options=[
                "ransomware", "malware", "dos_ddos", "phishing", "apt",
                "data_breach", "unauthorized_access", "insider_threat",
                "supply_chain", "vulnerability_exploitation", "other",
            ],
            format_func=lambda x: {
                "ransomware": "Ransomware / Verschlüsselungstrojaner",
                "malware": "Schadsoftware (Malware)",
                "dos_ddos": "DoS/DDoS-Angriff",
                "phishing": "Phishing / Social Engineering",
                "apt": "APT / Staatliche Akteure",
                "data_breach": "Datenpanne / Datenabfluss",
                "unauthorized_access": "Unbefugter Zugriff",
                "insider_threat": "Insider-Bedrohung",
                "supply_chain": "Supply-Chain-Angriff",
                "vulnerability_exploitation": "Ausnutzung von Schwachstellen",
                "other": "Sonstiges",
            }[x],
            index=0,  # Default to ransomware since this is ransomware-focused
        )

        incident_description = st.text_area(
            t("bsi_meldung.incident_description", lang) + " *",
            height=150,
            placeholder="Beschreiben Sie den Vorfall detailliert...",
        )

        st.divider()

        # Impact Assessment
        st.markdown(f"##### {t('bsi_meldung.impact', lang)}")

        col1, col2, col3 = st.columns(3)
        with col1:
            impact_level = st.selectbox(
                t("bsi_meldung.impact_level", lang),
                options=["unbekannt", "gering", "mittel", "hoch", "kritisch"],
                format_func=lambda x: {
                    "kritisch": "Kritisch",
                    "hoch": "Hoch",
                    "mittel": "Mittel",
                    "gering": "Gering",
                    "unbekannt": "Unbekannt",
                }[x],
            )
        with col2:
            affected_systems = st.number_input(
                t("bsi_meldung.affected_systems", lang),
                min_value=0,
                value=0,
            )
        with col3:
            affected_users = st.number_input(
                t("bsi_meldung.affected_users", lang),
                min_value=0,
                value=0,
            )

        impact_description = st.text_area(
            t("bsi_meldung.impact_description", lang),
            height=100,
        )

        col1, col2 = st.columns(2)
        with col1:
            data_affected = st.checkbox(t("bsi_meldung.data_affected", lang))
        with col2:
            if data_affected:
                data_types = st.multiselect(
                    t("bsi_meldung.data_types", lang),
                    options=[
                        "Personenbezogene Daten",
                        "Geschäftsgeheimnisse",
                        "Finanzdaten",
                        "Gesundheitsdaten",
                        "Zugangsdaten",
                        "Sonstige sensible Daten",
                    ],
                )
            else:
                data_types = []

        st.divider()

        # Technical Details
        st.markdown(f"##### {t('bsi_meldung.technical', lang)}")

        malware_family = st.text_input(
            t("bsi_meldung.malware_family", lang),
            placeholder="z.B. LockBit, BlackCat, Conti...",
        )

        attack_vectors = st.text_area(
            t("bsi_meldung.attack_vectors", lang),
            placeholder="Ein Angriffsvektor pro Zeile...",
            height=80,
        )

        cves = st.text_input(
            t("bsi_meldung.cves", lang),
            placeholder="z.B. CVE-2024-1234, CVE-2024-5678",
        )

        st.divider()

        # Response Actions
        st.markdown(f"##### {t('bsi_meldung.response', lang)}")

        containment_measures = st.text_area(
            t("bsi_meldung.containment_measures", lang),
            placeholder="Eine Maßnahme pro Zeile...",
            height=100,
        )

        eradication_measures = st.text_area(
            t("bsi_meldung.eradication_measures", lang),
            placeholder="Eine Maßnahme pro Zeile...",
            height=100,
        )

        st.divider()

        # External Support
        st.markdown(f"##### {t('bsi_meldung.external', lang)}")

        col1, col2 = st.columns(2)
        with col1:
            external_support = st.checkbox(t("bsi_meldung.external_support", lang))
            if external_support:
                external_details = st.text_input(t("bsi_meldung.external_details", lang))
            else:
                external_details = ""

        with col2:
            law_enforcement = st.checkbox(t("bsi_meldung.law_enforcement", lang))
            if law_enforcement:
                law_ref = st.text_input(t("bsi_meldung.law_reference", lang))
            else:
                law_ref = ""

        st.divider()

        # Submit button
        submitted = st.form_submit_button(
            t("bsi_meldung.generate", lang),
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not org_name or not contact_name or not contact_email or not contact_phone or not incident_title or not incident_description:
                st.error(t("bsi_meldung.required_fields", lang))
            else:
                # Save organization and contact data
                st.session_state.bsi_meldung_org = {
                    "name": org_name,
                    "address": org_address,
                    "sector": org_sector,
                    "is_kritis": is_kritis,
                    "kritis_number": kritis_number,
                }
                st.session_state.bsi_meldung_contact = {
                    "name": contact_name,
                    "role": contact_role,
                    "email": contact_email,
                    "phone": contact_phone,
                    "available_24_7": available_24_7,
                }

                # Create meldung
                meldung = BSIMeldung(
                    meldung_id=f"BSI-{incident.id[:8]}-{datetime.now().strftime('%Y%m%d%H%M')}",
                    notification_type=NotificationType(notification_type),
                    reference_id=reference_id if reference_id else None,
                    organization_name=org_name,
                    organization_address=org_address,
                    organization_sector=KRITISSector(org_sector),
                    is_kritis_operator=is_kritis,
                    kritis_registration_number=kritis_number,
                    primary_contact=ContactPerson(
                        name=contact_name,
                        role=contact_role,
                        email=contact_email,
                        phone=contact_phone,
                        available_24_7=available_24_7,
                    ),
                    incident_id=incident.id,
                    incident_title=incident_title,
                    incident_category=IncidentCategory(incident_category),
                    incident_description=incident_description,
                    detection_time=incident.created_at,
                    impact_level=ImpactLevel(impact_level),
                    impact_description=impact_description,
                    affected_systems_count=affected_systems,
                    affected_users_count=affected_users,
                    data_affected=data_affected,
                    data_types_affected=data_types if data_affected else [],
                    malware_family=malware_family,
                    attack_vectors=[v.strip() for v in attack_vectors.split("\n") if v.strip()],
                    cves_exploited=[c.strip() for c in cves.split(",") if c.strip()],
                    containment_measures=[m.strip() for m in containment_measures.split("\n") if m.strip()],
                    eradication_measures=[m.strip() for m in eradication_measures.split("\n") if m.strip()],
                    external_support_requested=external_support,
                    external_support_details=external_details,
                    law_enforcement_notified=law_enforcement,
                    law_enforcement_reference=law_ref,
                )

                st.session_state.bsi_meldung = meldung
                st.success(t("bsi_meldung.generated", lang))


def render_meldung_preview(lang: str = DEFAULT_LANGUAGE) -> None:
    """Render preview of the generated notification."""
    st.markdown(f"#### {t('bsi_meldung.preview', lang)}")

    if not st.session_state.get("bsi_meldung"):
        st.info(t("bsi_meldung.no_meldung", lang))
        return

    meldung = st.session_state.bsi_meldung
    generator = BSIMeldungGenerator()

    # Show preview in expanders
    with st.expander(t("bsi_meldung.preview_summary", lang), expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Meldungs-ID:** `{meldung.meldung_id}`")
            st.markdown(f"**Typ:** {generator._get_notification_type_label(meldung.notification_type)}")
            st.markdown(f"**Organisation:** {meldung.organization_name}")
            st.markdown(f"**KRITIS:** {'Ja' if meldung.is_kritis_operator else 'Nein'}")

        with col2:
            st.markdown(f"**Vorfall:** {meldung.incident_title}")
            st.markdown(f"**Kategorie:** {generator._get_category_label(meldung.incident_category)}")
            st.markdown(f"**Schweregrad:** {generator._get_impact_label(meldung.impact_level)}")
            st.markdown(f"**Betroffene Systeme:** {meldung.affected_systems_count}")

    with st.expander(t("bsi_meldung.preview_full", lang), expanded=False):
        md_content = generator.export_markdown(meldung)
        st.markdown(md_content)


def render_meldung_export(
    generator: BSIMeldungGenerator,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Render export options for the notification."""
    st.markdown(f"#### {t('bsi_meldung.export', lang)}")

    if not st.session_state.get("bsi_meldung"):
        st.info(t("bsi_meldung.no_meldung", lang))
        return

    meldung = st.session_state.bsi_meldung

    st.markdown(t("bsi_meldung.export_formats", lang))

    col1, col2, col3 = st.columns(3)

    with col1:
        # Markdown export
        md_content = generator.export_markdown(meldung)
        st.download_button(
            label=t("bsi_meldung.download_md", lang),
            data=md_content,
            file_name=f"{meldung.meldung_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:
        # HTML export (for printing/PDF)
        html_content = generator.export_html(meldung)
        st.download_button(
            label=t("bsi_meldung.download_html", lang),
            data=html_content,
            file_name=f"{meldung.meldung_id}.html",
            mime="text/html",
            use_container_width=True,
        )

    with col3:
        # JSON export (for API submission)
        json_content = generator.export_json(meldung)
        st.download_button(
            label=t("bsi_meldung.download_json", lang),
            data=json_content,
            file_name=f"{meldung.meldung_id}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()

    # Instructions
    st.markdown(f"#### {t('bsi_meldung.next_steps', lang)}")
    st.markdown("""
    1. **HTML-Datei herunterladen** und im Browser öffnen
    2. **Drucken als PDF** (Strg+P / Cmd+P)
    3. **Per E-Mail senden an:** meldestelle@bsi.bund.de
    4. **Oder online melden unter:** [BSI Meldestelle](https://www.bsi.bund.de/DE/IT-Sicherheitsvorfall/Unternehmen/Meldepflicht/meldepflicht_node.html)

    **Wichtig:** Bei KRITIS-Vorfällen ist die telefonische Vorabmeldung empfohlen:
    - **BSI-Lagezentrum:** +49 228 99 9582-0
    """)


def render_deadline_widget(
    incident,
    is_kritis: bool = False,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Render a compact deadline widget for the sidebar or overview.

    Args:
        incident: Current incident
        is_kritis: Whether organization is KRITIS operator
        lang: Language code
    """
    generator = BSIMeldungGenerator()

    detection_time = incident.created_at
    if detection_time.tzinfo is None:
        detection_time = detection_time.replace(tzinfo=timezone.utc)

    deadlines = generator.calculate_deadlines(detection_time, is_kritis)

    # Find most urgent deadline
    urgent_deadline = None
    for key, deadline in deadlines.items():
        if key.startswith("kritis") and not is_kritis:
            continue
        if deadline["overdue"]:
            urgent_deadline = deadline
            break
        if urgent_deadline is None or deadline["remaining"] < urgent_deadline["remaining"]:
            urgent_deadline = deadline

    if urgent_deadline:
        if urgent_deadline["overdue"]:
            st.error(f"**{urgent_deadline['name']}**: ÜBERFÄLLIG")
        else:
            remaining = urgent_deadline["remaining"]
            hours = int(remaining.total_seconds() // 3600)
            if hours < 24:
                st.warning(f"**{urgent_deadline['name']}**: {hours}h verbleibend")
            else:
                days = hours // 24
                st.info(f"**{urgent_deadline['name']}**: {days} Tage")
