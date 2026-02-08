"""
Lessons Learned Database Components for ISORA.

Document, search, and analyze lessons from past incidents.
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import os

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class LessonCategory(str, Enum):
    DETECTION = "detection"
    RESPONSE = "response"
    CONTAINMENT = "containment"
    RECOVERY = "recovery"
    COMMUNICATION = "communication"
    TOOLING = "tooling"
    PROCESS = "process"
    TRAINING = "training"
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"


class LessonPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LessonStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    WONT_FIX = "wont_fix"


class IncidentTypeTag(str, Enum):
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    DATA_BREACH = "data_breach"
    DDOS = "ddos"
    MALWARE = "malware"
    INSIDER = "insider"
    APT = "apt"
    WEB_ATTACK = "web_attack"
    ACCOUNT_COMPROMISE = "account_compromise"
    OTHER = "other"


@dataclass
class LessonLearned:
    id: str
    title: str
    description: str
    category: LessonCategory
    priority: LessonPriority
    status: LessonStatus
    incident_type: IncidentTypeTag
    incident_id: Optional[str] = None
    incident_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    what_happened: str = ""
    what_worked: str = ""
    what_failed: str = ""
    root_cause: str = ""
    recommendations: List[str] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


# Storage file path
LESSONS_FILE = "data/lessons_learned.json"


def _ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs("data", exist_ok=True)


def _load_lessons() -> List[LessonLearned]:
    """Load lessons from storage."""
    _ensure_data_dir()
    if not os.path.exists(LESSONS_FILE):
        return []

    try:
        with open(LESSONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        lessons = []
        for item in data:
            # Convert string dates back to proper types
            if item.get("incident_date"):
                item["incident_date"] = date.fromisoformat(item["incident_date"])
            if item.get("created_at"):
                item["created_at"] = datetime.fromisoformat(item["created_at"])
            if item.get("updated_at"):
                item["updated_at"] = datetime.fromisoformat(item["updated_at"])

            # Convert enums
            item["category"] = LessonCategory(item["category"])
            item["priority"] = LessonPriority(item["priority"])
            item["status"] = LessonStatus(item["status"])
            item["incident_type"] = IncidentTypeTag(item["incident_type"])

            lessons.append(LessonLearned(**item))

        return lessons
    except Exception as e:
        st.error(f"Fehler beim Laden der Lessons: {e}")
        return []


def _save_lessons(lessons: List[LessonLearned]):
    """Save lessons to storage."""
    _ensure_data_dir()

    data = []
    for lesson in lessons:
        item = {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "category": lesson.category.value,
            "priority": lesson.priority.value,
            "status": lesson.status.value,
            "incident_type": lesson.incident_type.value,
            "incident_id": lesson.incident_id,
            "incident_date": lesson.incident_date.isoformat() if lesson.incident_date else None,
            "created_at": lesson.created_at.isoformat(),
            "updated_at": lesson.updated_at.isoformat(),
            "created_by": lesson.created_by,
            "what_happened": lesson.what_happened,
            "what_worked": lesson.what_worked,
            "what_failed": lesson.what_failed,
            "root_cause": lesson.root_cause,
            "recommendations": lesson.recommendations,
            "action_items": lesson.action_items,
            "tags": lesson.tags,
            "affected_systems": lesson.affected_systems,
            "metrics": lesson.metrics,
        }
        data.append(item)

    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_category_labels() -> Dict[LessonCategory, str]:
    """Get display labels for categories."""
    return {
        LessonCategory.DETECTION: "Erkennung",
        LessonCategory.RESPONSE: "Reaktion",
        LessonCategory.CONTAINMENT: "Eindaemmung",
        LessonCategory.RECOVERY: "Wiederherstellung",
        LessonCategory.COMMUNICATION: "Kommunikation",
        LessonCategory.TOOLING: "Tools & Technologie",
        LessonCategory.PROCESS: "Prozesse",
        LessonCategory.TRAINING: "Training & Awareness",
        LessonCategory.TECHNICAL: "Technisch",
        LessonCategory.ORGANIZATIONAL: "Organisatorisch",
    }


def get_priority_labels() -> Dict[LessonPriority, str]:
    """Get display labels for priorities."""
    return {
        LessonPriority.CRITICAL: "Kritisch",
        LessonPriority.HIGH: "Hoch",
        LessonPriority.MEDIUM: "Mittel",
        LessonPriority.LOW: "Niedrig",
    }


def get_status_labels() -> Dict[LessonStatus, str]:
    """Get display labels for status."""
    return {
        LessonStatus.OPEN: "Offen",
        LessonStatus.IN_PROGRESS: "In Bearbeitung",
        LessonStatus.IMPLEMENTED: "Umgesetzt",
        LessonStatus.WONT_FIX: "Nicht umsetzen",
    }


def get_incident_type_labels() -> Dict[IncidentTypeTag, str]:
    """Get display labels for incident types."""
    return {
        IncidentTypeTag.RANSOMWARE: "Ransomware",
        IncidentTypeTag.PHISHING: "Phishing",
        IncidentTypeTag.DATA_BREACH: "Datenleck",
        IncidentTypeTag.DDOS: "DDoS",
        IncidentTypeTag.MALWARE: "Malware",
        IncidentTypeTag.INSIDER: "Insider-Bedrohung",
        IncidentTypeTag.APT: "APT",
        IncidentTypeTag.WEB_ATTACK: "Web-Angriff",
        IncidentTypeTag.ACCOUNT_COMPROMISE: "Account-Kompromittierung",
        IncidentTypeTag.OTHER: "Sonstiges",
    }


def render_lessons_learned_dashboard(lang: str = "de") -> None:
    """Render the lessons learned dashboard."""
    st.header("Lessons Learned Database")
    st.caption("Dokumentation und Analyse von Erkenntnissen aus Vorfaellen")

    # Initialize session state
    if "lessons_view" not in st.session_state:
        st.session_state.lessons_view = "list"
    if "selected_lesson_id" not in st.session_state:
        st.session_state.selected_lesson_id = None

    # Load lessons
    lessons = _load_lessons()

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Uebersicht", "Neue Lesson", "Suche", "Statistiken"])

    with tab1:
        _render_lessons_list(lessons)

    with tab2:
        _render_new_lesson_form(lessons)

    with tab3:
        _render_search(lessons)

    with tab4:
        _render_statistics(lessons)


def _render_lessons_list(lessons: List[LessonLearned]) -> None:
    """Render the lessons list view."""
    st.subheader(f"Alle Lessons ({len(lessons)})")

    if not lessons:
        st.info("Noch keine Lessons Learned erfasst. Erstellen Sie die erste im Tab 'Neue Lesson'.")
        return

    # Filter options
    col1, col2, col3 = st.columns(3)

    category_labels = get_category_labels()
    status_labels = get_status_labels()
    priority_labels = get_priority_labels()

    with col1:
        filter_status = st.selectbox(
            "Status",
            options=["Alle"] + list(status_labels.values()),
            key="list_filter_status",
        )

    with col2:
        filter_priority = st.selectbox(
            "Prioritaet",
            options=["Alle"] + list(priority_labels.values()),
            key="list_filter_priority",
        )

    with col3:
        filter_category = st.selectbox(
            "Kategorie",
            options=["Alle"] + list(category_labels.values()),
            key="list_filter_category",
        )

    # Apply filters
    filtered = lessons
    if filter_status != "Alle":
        status_key = [k for k, v in status_labels.items() if v == filter_status][0]
        filtered = [l for l in filtered if l.status == status_key]
    if filter_priority != "Alle":
        priority_key = [k for k, v in priority_labels.items() if v == filter_priority][0]
        filtered = [l for l in filtered if l.priority == priority_key]
    if filter_category != "Alle":
        category_key = [k for k, v in category_labels.items() if v == filter_category][0]
        filtered = [l for l in filtered if l.category == category_key]

    st.divider()

    # Sort by date (newest first)
    filtered = sorted(filtered, key=lambda x: x.created_at, reverse=True)

    # Display lessons
    for lesson in filtered:
        _render_lesson_card(lesson, lessons)


def _render_lesson_card(lesson: LessonLearned, all_lessons: List[LessonLearned]) -> None:
    """Render a single lesson card."""
    priority_labels = get_priority_labels()
    status_labels = get_status_labels()
    category_labels = get_category_labels()
    incident_labels = get_incident_type_labels()

    priority_colors = {
        LessonPriority.CRITICAL: "red",
        LessonPriority.HIGH: "orange",
        LessonPriority.MEDIUM: "blue",
        LessonPriority.LOW: "green",
    }

    with st.expander(f"**{lesson.title}** | {priority_labels[lesson.priority]} | {status_labels[lesson.status]}"):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Kategorie:** {category_labels[lesson.category]}")
            st.markdown(f"**Vorfallstyp:** {incident_labels[lesson.incident_type]}")
            st.markdown(f"**Beschreibung:** {lesson.description}")

            if lesson.what_happened:
                st.markdown(f"**Was ist passiert:** {lesson.what_happened[:200]}...")

            if lesson.recommendations:
                st.markdown("**Empfehlungen:**")
                for rec in lesson.recommendations[:3]:
                    st.markdown(f"- {rec}")

            if lesson.tags:
                st.markdown(f"**Tags:** {', '.join(lesson.tags)}")

        with col2:
            st.markdown(f"**ID:** {lesson.id[:8]}")
            st.markdown(f"**Erstellt:** {lesson.created_at.strftime('%d.%m.%Y')}")
            if lesson.incident_date:
                st.markdown(f"**Vorfall:** {lesson.incident_date.strftime('%d.%m.%Y')}")

            # Action buttons
            if st.button("Details", key=f"detail_{lesson.id}", use_container_width=True):
                st.session_state.selected_lesson_id = lesson.id
                _show_lesson_detail(lesson)

            if st.button("Bearbeiten", key=f"edit_{lesson.id}", use_container_width=True):
                st.session_state.edit_lesson_id = lesson.id

            if st.button("Loeschen", key=f"delete_{lesson.id}", use_container_width=True):
                all_lessons.remove(lesson)
                _save_lessons(all_lessons)
                st.rerun()


def _show_lesson_detail(lesson: LessonLearned) -> None:
    """Show detailed lesson view in a modal-like display."""
    priority_labels = get_priority_labels()
    status_labels = get_status_labels()
    category_labels = get_category_labels()
    incident_labels = get_incident_type_labels()

    st.divider()
    st.subheader(f"Details: {lesson.title}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Prioritaet", priority_labels[lesson.priority])
    with col2:
        st.metric("Status", status_labels[lesson.status])
    with col3:
        st.metric("Kategorie", category_labels[lesson.category])
    with col4:
        st.metric("Vorfallstyp", incident_labels[lesson.incident_type])

    st.divider()

    st.markdown("### Beschreibung")
    st.markdown(lesson.description)

    if lesson.what_happened:
        st.markdown("### Was ist passiert?")
        st.markdown(lesson.what_happened)

    if lesson.what_worked:
        st.markdown("### Was hat funktioniert?")
        st.markdown(lesson.what_worked)

    if lesson.what_failed:
        st.markdown("### Was hat nicht funktioniert?")
        st.markdown(lesson.what_failed)

    if lesson.root_cause:
        st.markdown("### Root Cause")
        st.markdown(lesson.root_cause)

    if lesson.recommendations:
        st.markdown("### Empfehlungen")
        for i, rec in enumerate(lesson.recommendations, 1):
            st.markdown(f"{i}. {rec}")

    if lesson.action_items:
        st.markdown("### Action Items")
        for item in lesson.action_items:
            status_icon = "[x]" if item.get("completed") else "[ ]"
            st.markdown(f"{status_icon} {item.get('description', '')} - {item.get('owner', 'N/A')}")

    if lesson.metrics:
        st.markdown("### Metriken")
        for key, value in lesson.metrics.items():
            st.markdown(f"- **{key}:** {value}")


def _render_new_lesson_form(lessons: List[LessonLearned]) -> None:
    """Render form for creating a new lesson."""
    st.subheader("Neue Lesson Learned erfassen")

    category_labels = get_category_labels()
    priority_labels = get_priority_labels()
    incident_labels = get_incident_type_labels()

    with st.form("new_lesson_form"):
        # Basic info
        title = st.text_input("Titel *", placeholder="Kurzer, aussagekraeftiger Titel")
        description = st.text_area("Beschreibung *", placeholder="Zusammenfassung der Lesson Learned", height=100)

        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Kategorie *", options=list(category_labels.values()))
        with col2:
            priority = st.selectbox("Prioritaet *", options=list(priority_labels.values()), index=2)
        with col3:
            incident_type = st.selectbox("Vorfallstyp *", options=list(incident_labels.values()))

        st.divider()

        # Details
        col1, col2 = st.columns(2)
        with col1:
            incident_id = st.text_input("Incident-ID", placeholder="z.B. INC-2024-0042")
            incident_date_input = st.date_input("Datum des Vorfalls", value=None)
        with col2:
            created_by = st.text_input("Erstellt von", placeholder="Ihr Name")
            tags_input = st.text_input("Tags (kommagetrennt)", placeholder="ransomware, backup, recovery")

        st.divider()

        # Analysis
        what_happened = st.text_area("Was ist passiert?", placeholder="Detaillierte Beschreibung des Vorfalls", height=100)
        what_worked = st.text_area("Was hat funktioniert?", placeholder="Positive Aspekte der Reaktion", height=100)
        what_failed = st.text_area("Was hat nicht funktioniert?", placeholder="Verbesserungspotential", height=100)
        root_cause = st.text_area("Root Cause", placeholder="Grundursache des Vorfalls", height=80)

        st.divider()

        # Recommendations
        recommendations_input = st.text_area(
            "Empfehlungen (eine pro Zeile)",
            placeholder="Empfehlung 1\nEmpfehlung 2\nEmpfehlung 3",
            height=100,
        )

        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_detection_time = st.text_input("Zeit bis Erkennung", placeholder="z.B. 2 Stunden")
        with col2:
            metric_containment_time = st.text_input("Zeit bis Eindaemmung", placeholder="z.B. 4 Stunden")
        with col3:
            metric_recovery_time = st.text_input("Zeit bis Recovery", placeholder="z.B. 24 Stunden")

        submitted = st.form_submit_button("Lesson Learned speichern", use_container_width=True)

        if submitted:
            if not title or not description:
                st.error("Titel und Beschreibung sind erforderlich.")
            else:
                # Find enum keys from labels
                category_key = [k for k, v in category_labels.items() if v == category][0]
                priority_key = [k for k, v in priority_labels.items() if v == priority][0]
                incident_key = [k for k, v in incident_labels.items() if v == incident_type][0]

                # Parse recommendations
                recommendations = [r.strip() for r in recommendations_input.split("\n") if r.strip()]

                # Parse tags
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]

                # Build metrics
                metrics = {}
                if metric_detection_time:
                    metrics["detection_time"] = metric_detection_time
                if metric_containment_time:
                    metrics["containment_time"] = metric_containment_time
                if metric_recovery_time:
                    metrics["recovery_time"] = metric_recovery_time

                # Create lesson
                new_lesson = LessonLearned(
                    id=str(uuid.uuid4()),
                    title=title,
                    description=description,
                    category=category_key,
                    priority=priority_key,
                    status=LessonStatus.OPEN,
                    incident_type=incident_key,
                    incident_id=incident_id if incident_id else None,
                    incident_date=incident_date_input if incident_date_input else None,
                    created_by=created_by,
                    what_happened=what_happened,
                    what_worked=what_worked,
                    what_failed=what_failed,
                    root_cause=root_cause,
                    recommendations=recommendations,
                    tags=tags,
                    metrics=metrics,
                )

                lessons.append(new_lesson)
                _save_lessons(lessons)
                st.success(f"Lesson Learned '{title}' wurde gespeichert!")
                st.rerun()


def _render_search(lessons: List[LessonLearned]) -> None:
    """Render search interface."""
    st.subheader("Lessons durchsuchen")

    # Search input
    search_query = st.text_input("Suchbegriff", placeholder="Suche in Titel, Beschreibung, Tags...")

    col1, col2 = st.columns(2)
    with col1:
        incident_labels = get_incident_type_labels()
        search_incident_type = st.multiselect(
            "Vorfallstyp",
            options=list(incident_labels.values()),
        )
    with col2:
        category_labels = get_category_labels()
        search_category = st.multiselect(
            "Kategorie",
            options=list(category_labels.values()),
        )

    st.divider()

    # Perform search
    results = lessons

    if search_query:
        query_lower = search_query.lower()
        results = [
            l for l in results
            if query_lower in l.title.lower()
            or query_lower in l.description.lower()
            or query_lower in l.what_happened.lower()
            or query_lower in l.what_worked.lower()
            or query_lower in l.what_failed.lower()
            or any(query_lower in tag.lower() for tag in l.tags)
        ]

    if search_incident_type:
        incident_keys = [k for k, v in incident_labels.items() if v in search_incident_type]
        results = [l for l in results if l.incident_type in incident_keys]

    if search_category:
        category_keys = [k for k, v in category_labels.items() if v in search_category]
        results = [l for l in results if l.category in category_keys]

    st.markdown(f"**{len(results)} Ergebnisse gefunden**")

    for lesson in results:
        priority_labels = get_priority_labels()
        status_labels = get_status_labels()

        with st.expander(f"{lesson.title} | {priority_labels[lesson.priority]}"):
            st.markdown(f"**Beschreibung:** {lesson.description}")
            if lesson.recommendations:
                st.markdown("**Empfehlungen:**")
                for rec in lesson.recommendations[:3]:
                    st.markdown(f"- {rec}")
            if lesson.tags:
                st.markdown(f"**Tags:** {', '.join(lesson.tags)}")


def _render_statistics(lessons: List[LessonLearned]) -> None:
    """Render statistics and analytics."""
    st.subheader("Statistiken & Analyse")

    if not lessons:
        st.info("Noch keine Daten fuer Statistiken verfuegbar.")
        return

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Gesamt Lessons", len(lessons))
    with col2:
        open_count = len([l for l in lessons if l.status == LessonStatus.OPEN])
        st.metric("Offen", open_count)
    with col3:
        implemented = len([l for l in lessons if l.status == LessonStatus.IMPLEMENTED])
        st.metric("Umgesetzt", implemented)
    with col4:
        critical = len([l for l in lessons if l.priority == LessonPriority.CRITICAL])
        st.metric("Kritisch", critical)

    st.divider()

    # Distribution charts (text-based)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Nach Kategorie")
        category_labels = get_category_labels()
        category_counts = {}
        for lesson in lessons:
            label = category_labels[lesson.category]
            category_counts[label] = category_counts.get(label, 0) + 1

        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(lessons) * 100
            bar = "=" * int(pct / 5)
            st.text(f"{cat[:15]:<15} {bar} {count} ({pct:.0f}%)")

    with col2:
        st.markdown("### Nach Vorfallstyp")
        incident_labels = get_incident_type_labels()
        incident_counts = {}
        for lesson in lessons:
            label = incident_labels[lesson.incident_type]
            incident_counts[label] = incident_counts.get(label, 0) + 1

        for inc, count in sorted(incident_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(lessons) * 100
            bar = "=" * int(pct / 5)
            st.text(f"{inc[:15]:<15} {bar} {count} ({pct:.0f}%)")

    st.divider()

    # Priority distribution
    st.markdown("### Nach Prioritaet")
    priority_labels = get_priority_labels()
    for priority in LessonPriority:
        count = len([l for l in lessons if l.priority == priority])
        pct = count / len(lessons) * 100
        st.text(f"{priority_labels[priority]:<10} {'=' * int(pct / 2)} {count} ({pct:.0f}%)")

    st.divider()

    # Status distribution
    st.markdown("### Nach Status")
    status_labels = get_status_labels()
    for status in LessonStatus:
        count = len([l for l in lessons if l.status == status])
        pct = count / len(lessons) * 100 if lessons else 0
        st.text(f"{status_labels[status]:<15} {'=' * int(pct / 2)} {count} ({pct:.0f}%)")

    st.divider()

    # Top tags
    st.markdown("### Haeufigste Tags")
    all_tags = {}
    for lesson in lessons:
        for tag in lesson.tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1

    if all_tags:
        for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]:
            st.text(f"  {tag}: {count}")
    else:
        st.text("  Keine Tags erfasst")

    st.divider()

    # Export
    st.markdown("### Export")
    col1, col2, col3 = st.columns(3)

    with col1:
        json_export = _generate_json_export(lessons)
        st.download_button(
            label="JSON Export",
            data=json_export,
            file_name=f"lessons_learned_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        csv_export = _generate_csv_export(lessons)
        st.download_button(
            label="CSV Export",
            data=csv_export,
            file_name=f"lessons_learned_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col3:
        if FPDF_AVAILABLE:
            pdf_export = _generate_pdf_export(lessons)
            st.download_button(
                label="PDF Export",
                data=pdf_export,
                file_name=f"lessons_learned_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("PDF (n/a)", disabled=True, use_container_width=True)


def _generate_json_export(lessons: List[LessonLearned]) -> str:
    """Generate JSON export of all lessons."""
    data = {
        "exported": datetime.now().isoformat(),
        "total_lessons": len(lessons),
        "lessons": [],
    }

    category_labels = get_category_labels()
    priority_labels = get_priority_labels()
    status_labels = get_status_labels()
    incident_labels = get_incident_type_labels()

    for lesson in lessons:
        item = {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "category": category_labels[lesson.category],
            "priority": priority_labels[lesson.priority],
            "status": status_labels[lesson.status],
            "incident_type": incident_labels[lesson.incident_type],
            "incident_id": lesson.incident_id,
            "incident_date": lesson.incident_date.isoformat() if lesson.incident_date else None,
            "created_at": lesson.created_at.isoformat(),
            "created_by": lesson.created_by,
            "what_happened": lesson.what_happened,
            "what_worked": lesson.what_worked,
            "what_failed": lesson.what_failed,
            "root_cause": lesson.root_cause,
            "recommendations": lesson.recommendations,
            "tags": lesson.tags,
            "metrics": lesson.metrics,
        }
        data["lessons"].append(item)

    return json.dumps(data, indent=2, ensure_ascii=False)


def _generate_csv_export(lessons: List[LessonLearned]) -> str:
    """Generate CSV export of lessons."""
    category_labels = get_category_labels()
    priority_labels = get_priority_labels()
    status_labels = get_status_labels()
    incident_labels = get_incident_type_labels()

    lines = ["ID;Titel;Kategorie;Prioritaet;Status;Vorfallstyp;Erstellt;Tags;Empfehlungen"]

    for lesson in lessons:
        tags = "|".join(lesson.tags)
        recs = "|".join(lesson.recommendations[:3])
        line = ";".join([
            lesson.id[:8],
            lesson.title.replace(";", ","),
            category_labels[lesson.category],
            priority_labels[lesson.priority],
            status_labels[lesson.status],
            incident_labels[lesson.incident_type],
            lesson.created_at.strftime("%Y-%m-%d"),
            tags,
            recs.replace(";", ",")[:100],
        ])
        lines.append(line)

    return "\n".join(lines)


def _generate_pdf_export(lessons: List[LessonLearned]) -> bytes:
    """Generate PDF export of lessons."""
    if not FPDF_AVAILABLE:
        return b""

    category_labels = get_category_labels()
    priority_labels = get_priority_labels()
    status_labels = get_status_labels()
    incident_labels = get_incident_type_labels()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Lessons Learned Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Exportiert: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Gesamt: {len(lessons)} Lessons", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # Statistics summary
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Zusammenfassung", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    open_count = len([l for l in lessons if l.status == LessonStatus.OPEN])
    implemented = len([l for l in lessons if l.status == LessonStatus.IMPLEMENTED])
    critical = len([l for l in lessons if l.priority == LessonPriority.CRITICAL])

    pdf.cell(0, 6, f"Offen: {open_count} | Umgesetzt: {implemented} | Kritisch: {critical}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Lessons
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Lessons", new_x="LMARGIN", new_y="NEXT")

    for lesson in lessons[:50]:  # Limit to 50 for PDF
        pdf.set_font("Helvetica", "B", 10)
        title_text = f"{lesson.title[:60]}{'...' if len(lesson.title) > 60 else ''}"
        pdf.cell(0, 6, title_text, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        meta = f"{priority_labels[lesson.priority]} | {status_labels[lesson.status]} | {category_labels[lesson.category]}"
        pdf.cell(0, 5, meta, new_x="LMARGIN", new_y="NEXT")

        desc = lesson.description[:150] + "..." if len(lesson.description) > 150 else lesson.description
        pdf.cell(0, 5, desc[:85], new_x="LMARGIN", new_y="NEXT")
        if len(desc) > 85:
            pdf.cell(0, 5, desc[85:170], new_x="LMARGIN", new_y="NEXT")

        if lesson.recommendations:
            pdf.set_font("Helvetica", "I", 9)
            rec_text = f"Empfehlung: {lesson.recommendations[0][:70]}..."
            pdf.cell(0, 5, rec_text, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(5)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Generiert mit ISORA", align="C")

    return bytes(pdf.output())
