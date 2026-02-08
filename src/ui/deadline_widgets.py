"""
Deadline Widgets for ISORA

Reusable countdown timer widgets for regulatory compliance deadlines.
Supports GDPR 72h, NIS2 (24h, 72h, 30d), and custom deadlines.
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal
from dataclasses import dataclass
from enum import Enum


class DeadlineStatus(str, Enum):
    """Status based on time remaining."""
    OK = "ok"           # > 48h remaining (green)
    WARNING = "warning" # 24-48h remaining (yellow)
    URGENT = "urgent"   # < 24h remaining (red)
    OVERDUE = "overdue" # Past deadline (black)


@dataclass
class Deadline:
    """A deadline with metadata."""
    name: str
    deadline_time: datetime
    description: Optional[str] = None
    regulation: Optional[str] = None  # e.g., "GDPR", "NIS2", "DORA"
    article: Optional[str] = None     # e.g., "Art. 33", "Art. 23"


def get_deadline_status(deadline: datetime, now: Optional[datetime] = None) -> DeadlineStatus:
    """Calculate deadline status based on time remaining.

    Args:
        deadline: The deadline datetime (UTC)
        now: Current time (defaults to now)

    Returns:
        DeadlineStatus enum value
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Ensure timezone awareness
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    remaining = deadline - now

    if remaining.total_seconds() <= 0:
        return DeadlineStatus.OVERDUE
    elif remaining.total_seconds() < 24 * 3600:  # < 24h
        return DeadlineStatus.URGENT
    elif remaining.total_seconds() < 48 * 3600:  # < 48h
        return DeadlineStatus.WARNING
    else:
        return DeadlineStatus.OK


def get_status_color(status: DeadlineStatus) -> str:
    """Get CSS color for deadline status.

    Args:
        status: The deadline status

    Returns:
        CSS color string
    """
    colors = {
        DeadlineStatus.OK: "#28a745",       # Green
        DeadlineStatus.WARNING: "#ffc107",  # Yellow
        DeadlineStatus.URGENT: "#dc3545",   # Red
        DeadlineStatus.OVERDUE: "#1a1a1a",  # Black
    }
    return colors.get(status, "#6c757d")


def get_status_bg_color(status: DeadlineStatus) -> str:
    """Get CSS background color for deadline status.

    Args:
        status: The deadline status

    Returns:
        CSS color string
    """
    colors = {
        DeadlineStatus.OK: "#d4edda",       # Light green
        DeadlineStatus.WARNING: "#fff3cd",  # Light yellow
        DeadlineStatus.URGENT: "#f8d7da",   # Light red
        DeadlineStatus.OVERDUE: "#343a40",  # Dark gray
    }
    return colors.get(status, "#e9ecef")


def format_time_remaining(deadline: datetime, now: Optional[datetime] = None) -> str:
    """Format time remaining until deadline.

    Args:
        deadline: The deadline datetime (UTC)
        now: Current time (defaults to now)

    Returns:
        Formatted time string (e.g., "23:45:30" or "-05:30:00" if overdue)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Ensure timezone awareness
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    remaining = deadline - now
    total_seconds = int(remaining.total_seconds())

    if total_seconds < 0:
        # Overdue
        total_seconds = abs(total_seconds)
        sign = "-"
    else:
        sign = ""

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{sign}{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def render_deadline_widget(
    deadline: Deadline,
    compact: bool = False,
    show_progress: bool = True,
) -> None:
    """Render a single deadline countdown widget.

    Args:
        deadline: The Deadline object to render
        compact: If True, render a smaller version
        show_progress: If True, show a progress bar
    """
    now = datetime.now(timezone.utc)
    status = get_deadline_status(deadline.deadline_time, now)
    time_remaining = format_time_remaining(deadline.deadline_time, now)
    color = get_status_color(status)
    bg_color = get_status_bg_color(status)

    text_color = "#ffffff" if status == DeadlineStatus.OVERDUE else "#333333"

    if compact:
        # Compact inline widget
        st.markdown(f"""
        <div style="
            background: {bg_color};
            color: {text_color};
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 4px solid {color};
            margin: 4px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 500;">{deadline.name}</span>
                <span style="font-family: monospace; font-weight: bold;">{time_remaining}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Full widget with more details
        status_emoji = {
            DeadlineStatus.OK: "",
            DeadlineStatus.WARNING: "",
            DeadlineStatus.URGENT: "",
            DeadlineStatus.OVERDUE: "",
        }.get(status, "")

        st.markdown(f"""
        <div style="
            background: {bg_color};
            color: {text_color};
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid {color};
            margin: 8px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-weight: 600; font-size: 14px;">{status_emoji} {deadline.name}</div>
                    {f'<div style="font-size: 11px; margin-top: 2px; opacity: 0.8;">{deadline.regulation} {deadline.article}</div>' if deadline.regulation else ''}
                    {f'<div style="font-size: 12px; margin-top: 4px;">{deadline.description}</div>' if deadline.description else ''}
                </div>
                <div style="text-align: right;">
                    <div style="font-family: monospace; font-size: 20px; font-weight: bold;">{time_remaining}</div>
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px;">
                        {"OVERDUE" if status == DeadlineStatus.OVERDUE else "REMAINING"}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_gdpr_72h_timer(
    detection_time: datetime,
    dpa_notified: bool = False,
    lang: str = "en",
) -> None:
    """Render the GDPR 72h notification deadline timer.

    Args:
        detection_time: When the breach was detected
        dpa_notified: If True, the DPA has been notified
        lang: Language code
    """
    # Ensure timezone awareness
    if detection_time.tzinfo is None:
        detection_time = detection_time.replace(tzinfo=timezone.utc)

    deadline_time = detection_time + timedelta(hours=72)

    labels = {
        "en": {
            "title": "GDPR 72h Deadline",
            "description": "Data Protection Authority notification required",
            "notified": "DPA Notified",
        },
        "de": {
            "title": "DSGVO 72h Frist",
            "description": "Meldung an Datenschutzaufsichtsbehorde erforderlich",
            "notified": "Behorde informiert",
        }
    }
    l = labels.get(lang, labels["en"])

    if dpa_notified:
        st.success(f"{l['notified']}")
    else:
        deadline = Deadline(
            name=l["title"],
            deadline_time=deadline_time,
            description=l["description"],
            regulation="GDPR",
            article="Art. 33",
        )
        render_deadline_widget(deadline)


def render_nis2_deadlines(
    detection_time: datetime,
    early_warning_sent: bool = False,
    notification_sent: bool = False,
    final_report_sent: bool = False,
    lang: str = "en",
) -> None:
    """Render NIS2 directive deadline timers.

    NIS2 has 3 deadlines:
    - Early Warning: 24h
    - Notification: 72h
    - Final Report: 30 days

    Args:
        detection_time: When the incident was detected
        early_warning_sent: If True, early warning has been sent
        notification_sent: If True, notification has been sent
        final_report_sent: If True, final report has been submitted
        lang: Language code
    """
    # Ensure timezone awareness
    if detection_time.tzinfo is None:
        detection_time = detection_time.replace(tzinfo=timezone.utc)

    labels = {
        "en": {
            "early_warning": "NIS2 Early Warning",
            "early_warning_desc": "Initial alert to CSIRT",
            "notification": "NIS2 Notification",
            "notification_desc": "Incident details to CSIRT",
            "final_report": "NIS2 Final Report",
            "final_report_desc": "Complete incident report",
            "completed": "Completed",
        },
        "de": {
            "early_warning": "NIS2 Fruhwarnung",
            "early_warning_desc": "Erstmeldung an CSIRT",
            "notification": "NIS2 Meldung",
            "notification_desc": "Vorfalldetails an CSIRT",
            "final_report": "NIS2 Abschlussbericht",
            "final_report_desc": "Vollstandiger Vorfallbericht",
            "completed": "Abgeschlossen",
        }
    }
    l = labels.get(lang, labels["en"])

    # 24h Early Warning
    if early_warning_sent:
        st.success(f"{l['early_warning']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["early_warning"],
            deadline_time=detection_time + timedelta(hours=24),
            description=l["early_warning_desc"],
            regulation="NIS2",
            article="Art. 23(4)(a)",
        )
        render_deadline_widget(deadline, compact=True)

    # 72h Notification
    if notification_sent:
        st.success(f"{l['notification']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["notification"],
            deadline_time=detection_time + timedelta(hours=72),
            description=l["notification_desc"],
            regulation="NIS2",
            article="Art. 23(4)(b)",
        )
        render_deadline_widget(deadline, compact=True)

    # 30 days Final Report
    if final_report_sent:
        st.success(f"{l['final_report']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["final_report"],
            deadline_time=detection_time + timedelta(days=30),
            description=l["final_report_desc"],
            regulation="NIS2",
            article="Art. 23(4)(d)",
        )
        render_deadline_widget(deadline, compact=True)


def render_dora_deadlines(
    detection_time: datetime,
    initial_report_sent: bool = False,
    intermediate_reports: int = 0,
    final_report_sent: bool = False,
    lang: str = "en",
) -> None:
    """Render DORA (Digital Operational Resilience Act) deadline timers.

    DORA deadlines for major ICT incidents:
    - Initial Report: Within 4 hours (or 24h for non-business hours)
    - Intermediate Reports: As updates occur
    - Final Report: Within 1 month

    Args:
        detection_time: When the incident was detected
        initial_report_sent: If True, initial report has been sent
        intermediate_reports: Number of intermediate reports sent
        final_report_sent: If True, final report has been submitted
        lang: Language code
    """
    # Ensure timezone awareness
    if detection_time.tzinfo is None:
        detection_time = detection_time.replace(tzinfo=timezone.utc)

    labels = {
        "en": {
            "initial": "DORA Initial Report",
            "initial_desc": "Initial notification to competent authority",
            "intermediate": "DORA Intermediate Report",
            "intermediate_desc": "Status updates as situation evolves",
            "final": "DORA Final Report",
            "final_desc": "Complete root cause analysis",
            "completed": "Completed",
            "reports_sent": "reports sent",
        },
        "de": {
            "initial": "DORA Erstmeldung",
            "initial_desc": "Erste Meldung an zustandige Behorde",
            "intermediate": "DORA Zwischenbericht",
            "intermediate_desc": "Statusaktualisierungen bei Anderungen",
            "final": "DORA Abschlussbericht",
            "final_desc": "Vollstandige Ursachenanalyse",
            "completed": "Abgeschlossen",
            "reports_sent": "Berichte gesendet",
        }
    }
    l = labels.get(lang, labels["en"])

    # 4h Initial Report (using 24h for safety/non-business hours scenario)
    if initial_report_sent:
        st.success(f"{l['initial']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["initial"],
            deadline_time=detection_time + timedelta(hours=4),
            description=l["initial_desc"],
            regulation="DORA",
            article="Art. 19",
        )
        render_deadline_widget(deadline, compact=True)

    # Intermediate reports (no fixed deadline, show count)
    st.info(f"{l['intermediate']}: {intermediate_reports} {l['reports_sent']}")

    # 1 month Final Report
    if final_report_sent:
        st.success(f"{l['final']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["final"],
            deadline_time=detection_time + timedelta(days=30),
            description=l["final_desc"],
            regulation="DORA",
            article="Art. 19",
        )
        render_deadline_widget(deadline, compact=True)


def render_kritis_deadlines(
    detection_time: datetime,
    initial_notification_sent: bool = False,
    detailed_report_sent: bool = False,
    lang: str = "en",
) -> None:
    """Render KRITIS (German Critical Infrastructure) deadline timers.

    KRITIS deadlines per BSI-Gesetz:
    - Initial Notification: 24h
    - Detailed Report: 72h

    Args:
        detection_time: When the incident was detected
        initial_notification_sent: If True, initial notification sent
        detailed_report_sent: If True, detailed report submitted
        lang: Language code
    """
    # Ensure timezone awareness
    if detection_time.tzinfo is None:
        detection_time = detection_time.replace(tzinfo=timezone.utc)

    labels = {
        "en": {
            "initial": "KRITIS Initial Notification",
            "initial_desc": "Report to BSI",
            "detailed": "KRITIS Detailed Report",
            "detailed_desc": "Complete incident details to BSI",
            "completed": "Completed",
        },
        "de": {
            "initial": "KRITIS Erstmeldung",
            "initial_desc": "Meldung an BSI",
            "detailed": "KRITIS Detailbericht",
            "detailed_desc": "Vollstandige Vorfalldetails an BSI",
            "completed": "Abgeschlossen",
        }
    }
    l = labels.get(lang, labels["en"])

    # 24h Initial Notification
    if initial_notification_sent:
        st.success(f"{l['initial']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["initial"],
            deadline_time=detection_time + timedelta(hours=24),
            description=l["initial_desc"],
            regulation="KRITIS",
            article="BSIG 8b",
        )
        render_deadline_widget(deadline, compact=True)

    # 72h Detailed Report
    if detailed_report_sent:
        st.success(f"{l['detailed']}: {l['completed']}")
    else:
        deadline = Deadline(
            name=l["detailed"],
            deadline_time=detection_time + timedelta(hours=72),
            description=l["detailed_desc"],
            regulation="KRITIS",
            article="BSI-KritisV",
        )
        render_deadline_widget(deadline, compact=True)


def render_compliance_deadlines_sidebar(
    detection_time: datetime,
    regulations: List[str],
    statuses: Optional[dict] = None,
    lang: str = "en",
) -> None:
    """Render a compact sidebar widget showing all relevant compliance deadlines.

    Args:
        detection_time: When the incident was detected
        regulations: List of applicable regulations ["GDPR", "NIS2", "DORA", "KRITIS"]
        statuses: Dict with completion statuses for each deadline
        lang: Language code
    """
    if statuses is None:
        statuses = {}

    labels = {
        "en": {"title": "Compliance Deadlines"},
        "de": {"title": "Compliance-Fristen"},
    }
    l = labels.get(lang, labels["en"])

    st.markdown(f"**{l['title']}**")

    if "GDPR" in regulations:
        render_gdpr_72h_timer(
            detection_time,
            dpa_notified=statuses.get("gdpr_dpa_notified", False),
            lang=lang,
        )

    if "NIS2" in regulations:
        render_nis2_deadlines(
            detection_time,
            early_warning_sent=statuses.get("nis2_early_warning", False),
            notification_sent=statuses.get("nis2_notification", False),
            final_report_sent=statuses.get("nis2_final_report", False),
            lang=lang,
        )

    if "DORA" in regulations:
        render_dora_deadlines(
            detection_time,
            initial_report_sent=statuses.get("dora_initial", False),
            intermediate_reports=statuses.get("dora_intermediate_count", 0),
            final_report_sent=statuses.get("dora_final", False),
            lang=lang,
        )

    if "KRITIS" in regulations:
        render_kritis_deadlines(
            detection_time,
            initial_notification_sent=statuses.get("kritis_initial", False),
            detailed_report_sent=statuses.get("kritis_detailed", False),
            lang=lang,
        )
