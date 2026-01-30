"""
NIS2 Directive Compliance Module

Handles NIS2 (Network and Information Security Directive 2) compliance
including notification management, deadline tracking, and report generation.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config, DATA_DIR
from src.integrations.nis2_models import (
    NIS2Notification,
    NIS2EarlyWarning,
    NIS2IncidentNotification,
    NIS2FinalReport,
    NIS2EntityType,
    NIS2Sector,
    NIS2IncidentSeverity,
    NIS2NotificationStatus,
    NIS2ContactPerson,
    NIS2IncidentImpact,
    EU_MEMBER_STATES,
    SECTOR_ENTITY_TYPE,
)


class NIS2DirectiveManager:
    """Manager for NIS2 directive compliance and notifications."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the NIS2 manager.

        Args:
            db_path: Path to SQLite database. Defaults to config setting.
        """
        config = get_config()
        self.db_path = db_path or config.database.db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context management."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database tables for NIS2 notifications."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Main notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nis2_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id TEXT UNIQUE NOT NULL,
                    incident_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    organization_name TEXT NOT NULL,
                    member_state TEXT NOT NULL,
                    detection_time TEXT NOT NULL,
                    early_warning_deadline TEXT NOT NULL,
                    notification_deadline TEXT NOT NULL,
                    final_report_deadline TEXT NOT NULL,
                    primary_contact_json TEXT,
                    technical_contact_json TEXT,
                    csirt_reference TEXT,
                    national_authority_reference TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Early warnings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nis2_early_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    warning_id TEXT UNIQUE NOT NULL,
                    notification_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    submitted_at TEXT,
                    deadline TEXT NOT NULL,
                    suspected_cause TEXT,
                    cross_border_suspected INTEGER DEFAULT 0,
                    initial_assessment TEXT,
                    status TEXT DEFAULT 'pending',
                    csirt_reference TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (notification_id) REFERENCES nis2_notifications(notification_id)
                )
            """)

            # Incident notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nis2_incident_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id TEXT UNIQUE NOT NULL,
                    parent_notification_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    early_warning_id TEXT,
                    submitted_at TEXT,
                    deadline TEXT NOT NULL,
                    incident_description TEXT,
                    severity TEXT,
                    incident_type TEXT,
                    root_cause_preliminary TEXT,
                    impact_json TEXT,
                    mitigation_measures_json TEXT,
                    containment_status TEXT DEFAULT 'ongoing',
                    status TEXT DEFAULT 'pending',
                    csirt_reference TEXT,
                    csirt_feedback TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_notification_id) REFERENCES nis2_notifications(notification_id)
                )
            """)

            # Final reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nis2_final_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    notification_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    incident_notification_id TEXT,
                    submitted_at TEXT,
                    deadline TEXT NOT NULL,
                    incident_description TEXT,
                    root_cause_analysis TEXT,
                    threat_type TEXT,
                    attack_techniques_json TEXT,
                    total_impact_assessment TEXT,
                    services_affected_json TEXT,
                    recovery_time_hours REAL,
                    lessons_learned TEXT,
                    preventive_measures_json TEXT,
                    security_improvements_json TEXT,
                    other_csirts_notified_json TEXT,
                    enisa_notified INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (notification_id) REFERENCES nis2_notifications(notification_id)
                )
            """)

            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nis2_notifications_incident
                ON nis2_notifications(incident_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_nis2_notifications_status
                ON nis2_notifications(member_state, entity_type)
            """)

            conn.commit()

    def create_notification(
        self,
        incident_id: str,
        entity_type: NIS2EntityType,
        sector: NIS2Sector,
        organization_name: str,
        member_state: str,
        detection_time: datetime,
        primary_contact: NIS2ContactPerson,
        technical_contact: Optional[NIS2ContactPerson] = None,
    ) -> NIS2Notification:
        """Create a new NIS2 notification for an incident.

        Args:
            incident_id: Unique incident identifier
            entity_type: Essential or Important entity classification
            sector: NIS2 sector
            organization_name: Organization name
            member_state: EU member state ISO code
            detection_time: When incident was detected
            primary_contact: Primary contact person
            technical_contact: Optional technical contact

        Returns:
            Created NIS2Notification
        """
        notification = NIS2Notification.create(
            incident_id=incident_id,
            entity_type=entity_type,
            sector=sector,
            organization_name=organization_name,
            member_state=member_state,
            detection_time=detection_time,
            primary_contact=primary_contact,
            technical_contact=technical_contact,
        )

        notification_id = f"NIS2-{uuid.uuid4().hex[:12].upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO nis2_notifications (
                    notification_id, incident_id, entity_type, sector,
                    organization_name, member_state, detection_time,
                    early_warning_deadline, notification_deadline,
                    final_report_deadline, primary_contact_json,
                    technical_contact_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification_id,
                incident_id,
                entity_type.value,
                sector.value,
                organization_name,
                member_state,
                detection_time.isoformat(),
                notification.early_warning_deadline.isoformat(),
                notification.notification_deadline.isoformat(),
                notification.final_report_deadline.isoformat(),
                json.dumps(primary_contact.model_dump()),
                json.dumps(technical_contact.model_dump()) if technical_contact else None,
            ))
            conn.commit()

        return notification

    def submit_early_warning(
        self,
        incident_id: str,
        suspected_cause: Optional[str] = None,
        cross_border_suspected: bool = False,
        initial_assessment: str = "",
    ) -> NIS2EarlyWarning:
        """Submit an early warning for an incident.

        Args:
            incident_id: Incident identifier
            suspected_cause: malicious, technical_failure, or unknown
            cross_border_suspected: Whether cross-border impact is suspected
            initial_assessment: Brief initial assessment

        Returns:
            Created NIS2EarlyWarning
        """
        # Get parent notification
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT notification_id, early_warning_deadline
                FROM nis2_notifications
                WHERE incident_id = ?
            """, (incident_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"No NIS2 notification found for incident {incident_id}")

            notification_id = row["notification_id"]
            deadline = datetime.fromisoformat(row["early_warning_deadline"])

            warning_id = f"EW-{uuid.uuid4().hex[:12].upper()}"
            now = datetime.now(timezone.utc)

            cursor.execute("""
                INSERT INTO nis2_early_warnings (
                    warning_id, notification_id, incident_id,
                    submitted_at, deadline, suspected_cause,
                    cross_border_suspected, initial_assessment, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                warning_id,
                notification_id,
                incident_id,
                now.isoformat(),
                deadline.isoformat(),
                suspected_cause,
                1 if cross_border_suspected else 0,
                initial_assessment,
                NIS2NotificationStatus.SUBMITTED.value,
            ))
            conn.commit()

        return NIS2EarlyWarning(
            notification_id=warning_id,
            incident_id=incident_id,
            submitted_at=now,
            deadline=deadline,
            suspected_cause=suspected_cause,
            cross_border_suspected=cross_border_suspected,
            initial_assessment=initial_assessment,
            status=NIS2NotificationStatus.SUBMITTED,
        )

    def submit_incident_notification(
        self,
        incident_id: str,
        incident_description: str,
        severity: NIS2IncidentSeverity,
        incident_type: str,
        impact: NIS2IncidentImpact,
        mitigation_measures: List[str],
        containment_status: str = "ongoing",
        root_cause_preliminary: Optional[str] = None,
    ) -> NIS2IncidentNotification:
        """Submit the full incident notification.

        Args:
            incident_id: Incident identifier
            incident_description: Detailed description
            severity: Incident severity classification
            incident_type: Type of incident (ransomware, ddos, etc.)
            impact: Impact assessment
            mitigation_measures: List of mitigation measures taken
            containment_status: Current containment status
            root_cause_preliminary: Preliminary root cause if known

        Returns:
            Created NIS2IncidentNotification
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get parent notification and early warning
            cursor.execute("""
                SELECT n.notification_id, n.notification_deadline, e.warning_id
                FROM nis2_notifications n
                LEFT JOIN nis2_early_warnings e ON n.notification_id = e.notification_id
                WHERE n.incident_id = ?
            """, (incident_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"No NIS2 notification found for incident {incident_id}")

            parent_id = row["notification_id"]
            deadline = datetime.fromisoformat(row["notification_deadline"])
            early_warning_id = row["warning_id"]

            notification_id = f"IN-{uuid.uuid4().hex[:12].upper()}"
            now = datetime.now(timezone.utc)

            cursor.execute("""
                INSERT INTO nis2_incident_notifications (
                    notification_id, parent_notification_id, incident_id,
                    early_warning_id, submitted_at, deadline,
                    incident_description, severity, incident_type,
                    root_cause_preliminary, impact_json,
                    mitigation_measures_json, containment_status, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification_id,
                parent_id,
                incident_id,
                early_warning_id,
                now.isoformat(),
                deadline.isoformat(),
                incident_description,
                severity.value,
                incident_type,
                root_cause_preliminary,
                json.dumps(impact.model_dump()),
                json.dumps(mitigation_measures),
                containment_status,
                NIS2NotificationStatus.SUBMITTED.value,
            ))
            conn.commit()

        return NIS2IncidentNotification(
            notification_id=notification_id,
            incident_id=incident_id,
            early_warning_id=early_warning_id,
            submitted_at=now,
            deadline=deadline,
            incident_description=incident_description,
            severity=severity,
            incident_type=incident_type,
            root_cause_preliminary=root_cause_preliminary,
            impact=impact,
            mitigation_measures=mitigation_measures,
            containment_status=containment_status,
            status=NIS2NotificationStatus.SUBMITTED,
        )

    def submit_final_report(
        self,
        incident_id: str,
        incident_description: str,
        root_cause_analysis: str,
        threat_type: str,
        attack_techniques: List[str],
        total_impact_assessment: str,
        services_affected: List[str],
        lessons_learned: str,
        preventive_measures: List[str],
        security_improvements: List[str],
        recovery_time_hours: Optional[float] = None,
        other_csirts_notified: Optional[List[str]] = None,
        enisa_notified: bool = False,
    ) -> NIS2FinalReport:
        """Submit the final incident report.

        Args:
            incident_id: Incident identifier
            incident_description: Full incident description
            root_cause_analysis: Complete root cause analysis
            threat_type: Type of threat
            attack_techniques: MITRE ATT&CK techniques if applicable
            total_impact_assessment: Summary of total impact
            services_affected: List of affected services
            lessons_learned: Lessons learned from incident
            preventive_measures: Preventive measures to implement
            security_improvements: Security improvements planned
            recovery_time_hours: Time to recover in hours
            other_csirts_notified: Other CSIRTs that were notified
            enisa_notified: Whether ENISA was notified

        Returns:
            Created NIS2FinalReport
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT n.notification_id, n.final_report_deadline, i.notification_id as inc_notif_id
                FROM nis2_notifications n
                LEFT JOIN nis2_incident_notifications i ON n.notification_id = i.parent_notification_id
                WHERE n.incident_id = ?
            """, (incident_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"No NIS2 notification found for incident {incident_id}")

            parent_id = row["notification_id"]
            deadline = datetime.fromisoformat(row["final_report_deadline"])
            incident_notification_id = row["inc_notif_id"]

            report_id = f"FR-{uuid.uuid4().hex[:12].upper()}"
            now = datetime.now(timezone.utc)

            cursor.execute("""
                INSERT INTO nis2_final_reports (
                    report_id, notification_id, incident_id,
                    incident_notification_id, submitted_at, deadline,
                    incident_description, root_cause_analysis, threat_type,
                    attack_techniques_json, total_impact_assessment,
                    services_affected_json, recovery_time_hours,
                    lessons_learned, preventive_measures_json,
                    security_improvements_json, other_csirts_notified_json,
                    enisa_notified, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                parent_id,
                incident_id,
                incident_notification_id,
                now.isoformat(),
                deadline.isoformat(),
                incident_description,
                root_cause_analysis,
                threat_type,
                json.dumps(attack_techniques),
                total_impact_assessment,
                json.dumps(services_affected),
                recovery_time_hours,
                lessons_learned,
                json.dumps(preventive_measures),
                json.dumps(security_improvements),
                json.dumps(other_csirts_notified or []),
                1 if enisa_notified else 0,
                NIS2NotificationStatus.SUBMITTED.value,
            ))
            conn.commit()

        return NIS2FinalReport(
            report_id=report_id,
            incident_id=incident_id,
            notification_id=incident_notification_id,
            submitted_at=now,
            deadline=deadline,
            incident_description=incident_description,
            root_cause_analysis=root_cause_analysis,
            threat_type=threat_type,
            attack_techniques=attack_techniques,
            total_impact_assessment=total_impact_assessment,
            services_affected=services_affected,
            recovery_time_hours=recovery_time_hours,
            lessons_learned=lessons_learned,
            preventive_measures=preventive_measures,
            security_improvements=security_improvements,
            other_csirts_notified=other_csirts_notified or [],
            enisa_notified=enisa_notified,
            status=NIS2NotificationStatus.SUBMITTED,
        )

    def get_notification(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get complete notification status for an incident.

        Args:
            incident_id: Incident identifier

        Returns:
            Dict with notification details or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get main notification
            cursor.execute("""
                SELECT * FROM nis2_notifications WHERE incident_id = ?
            """, (incident_id,))
            notif_row = cursor.fetchone()

            if not notif_row:
                return None

            result = dict(notif_row)
            result["primary_contact"] = json.loads(result["primary_contact_json"]) if result["primary_contact_json"] else None
            result["technical_contact"] = json.loads(result["technical_contact_json"]) if result["technical_contact_json"] else None

            # Get early warning
            cursor.execute("""
                SELECT * FROM nis2_early_warnings WHERE incident_id = ?
            """, (incident_id,))
            ew_row = cursor.fetchone()
            result["early_warning"] = dict(ew_row) if ew_row else None

            # Get incident notification
            cursor.execute("""
                SELECT * FROM nis2_incident_notifications WHERE incident_id = ?
            """, (incident_id,))
            in_row = cursor.fetchone()
            if in_row:
                in_dict = dict(in_row)
                in_dict["impact"] = json.loads(in_dict["impact_json"]) if in_dict["impact_json"] else None
                in_dict["mitigation_measures"] = json.loads(in_dict["mitigation_measures_json"]) if in_dict["mitigation_measures_json"] else []
                result["incident_notification"] = in_dict
            else:
                result["incident_notification"] = None

            # Get final report
            cursor.execute("""
                SELECT * FROM nis2_final_reports WHERE incident_id = ?
            """, (incident_id,))
            fr_row = cursor.fetchone()
            if fr_row:
                fr_dict = dict(fr_row)
                fr_dict["attack_techniques"] = json.loads(fr_dict["attack_techniques_json"]) if fr_dict["attack_techniques_json"] else []
                fr_dict["services_affected"] = json.loads(fr_dict["services_affected_json"]) if fr_dict["services_affected_json"] else []
                fr_dict["preventive_measures"] = json.loads(fr_dict["preventive_measures_json"]) if fr_dict["preventive_measures_json"] else []
                fr_dict["security_improvements"] = json.loads(fr_dict["security_improvements_json"]) if fr_dict["security_improvements_json"] else []
                fr_dict["other_csirts_notified"] = json.loads(fr_dict["other_csirts_notified_json"]) if fr_dict["other_csirts_notified_json"] else []
                result["final_report"] = fr_dict
            else:
                result["final_report"] = None

            return result

    def get_overdue_notifications(self) -> List[Dict[str, Any]]:
        """Get all notifications with overdue deadlines.

        Returns:
            List of notifications with overdue status
        """
        now = datetime.now(timezone.utc).isoformat()
        overdue = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check early warnings
            cursor.execute("""
                SELECT n.*, e.warning_id, e.status as ew_status
                FROM nis2_notifications n
                LEFT JOIN nis2_early_warnings e ON n.notification_id = e.notification_id
                WHERE n.early_warning_deadline < ?
                AND (e.status IS NULL OR e.status = 'pending')
            """, (now,))
            for row in cursor.fetchall():
                overdue.append({
                    "type": "early_warning",
                    "incident_id": row["incident_id"],
                    "deadline": row["early_warning_deadline"],
                    "organization": row["organization_name"],
                })

            # Check incident notifications
            cursor.execute("""
                SELECT n.*, i.notification_id as in_id, i.status as in_status
                FROM nis2_notifications n
                LEFT JOIN nis2_incident_notifications i ON n.notification_id = i.parent_notification_id
                WHERE n.notification_deadline < ?
                AND (i.status IS NULL OR i.status = 'pending')
            """, (now,))
            for row in cursor.fetchall():
                overdue.append({
                    "type": "incident_notification",
                    "incident_id": row["incident_id"],
                    "deadline": row["notification_deadline"],
                    "organization": row["organization_name"],
                })

            # Check final reports
            cursor.execute("""
                SELECT n.*, f.report_id, f.status as fr_status
                FROM nis2_notifications n
                LEFT JOIN nis2_final_reports f ON n.notification_id = f.notification_id
                WHERE n.final_report_deadline < ?
                AND (f.status IS NULL OR f.status = 'pending')
            """, (now,))
            for row in cursor.fetchall():
                overdue.append({
                    "type": "final_report",
                    "incident_id": row["incident_id"],
                    "deadline": row["final_report_deadline"],
                    "organization": row["organization_name"],
                })

        return overdue

    def export_notification_report(
        self,
        incident_id: str,
        format: str = "markdown",
    ) -> str:
        """Export a complete NIS2 notification report.

        Args:
            incident_id: Incident identifier
            format: Output format (markdown, html, json)

        Returns:
            Formatted report string
        """
        notification = self.get_notification(incident_id)
        if not notification:
            raise ValueError(f"No notification found for incident {incident_id}")

        if format == "json":
            return json.dumps(notification, indent=2, default=str)

        # Markdown/HTML format
        report = f"# NIS2 Notification Report\n\n"
        report += f"**Incident ID:** {notification['incident_id']}\n"
        report += f"**Organization:** {notification['organization_name']}\n"
        report += f"**Member State:** {EU_MEMBER_STATES.get(notification['member_state'], {}).get('name', notification['member_state'])}\n"
        report += f"**Sector:** {notification['sector']}\n"
        report += f"**Entity Type:** {notification['entity_type']}\n\n"

        report += "## Deadlines\n\n"
        report += f"- Early Warning (24h): {notification['early_warning_deadline']}\n"
        report += f"- Notification (72h): {notification['notification_deadline']}\n"
        report += f"- Final Report (30d): {notification['final_report_deadline']}\n\n"

        if notification.get("early_warning"):
            ew = notification["early_warning"]
            report += "## Early Warning\n\n"
            report += f"**Status:** {ew['status']}\n"
            report += f"**Submitted:** {ew.get('submitted_at', 'N/A')}\n"
            report += f"**Suspected Cause:** {ew.get('suspected_cause', 'Unknown')}\n"
            report += f"**Cross-border:** {'Yes' if ew.get('cross_border_suspected') else 'No'}\n\n"

        if notification.get("incident_notification"):
            inn = notification["incident_notification"]
            report += "## Incident Notification\n\n"
            report += f"**Status:** {inn['status']}\n"
            report += f"**Submitted:** {inn.get('submitted_at', 'N/A')}\n"
            report += f"**Severity:** {inn.get('severity', 'N/A')}\n"
            report += f"**Type:** {inn.get('incident_type', 'N/A')}\n\n"
            report += f"### Description\n{inn.get('incident_description', 'N/A')}\n\n"

        if notification.get("final_report"):
            fr = notification["final_report"]
            report += "## Final Report\n\n"
            report += f"**Status:** {fr['status']}\n"
            report += f"**Submitted:** {fr.get('submitted_at', 'N/A')}\n\n"
            report += f"### Root Cause Analysis\n{fr.get('root_cause_analysis', 'N/A')}\n\n"
            report += f"### Lessons Learned\n{fr.get('lessons_learned', 'N/A')}\n\n"

        if format == "html":
            # Basic HTML conversion
            report = report.replace("# ", "<h1>").replace("\n## ", "</h1>\n<h2>")
            report = report.replace("\n### ", "</h2>\n<h3>")
            report = f"<html><body>{report}</body></html>"

        return report


def get_entity_type_for_sector(sector: NIS2Sector) -> NIS2EntityType:
    """Get the default entity type for a sector.

    Args:
        sector: NIS2 sector

    Returns:
        Entity type (Essential or Important)
    """
    return SECTOR_ENTITY_TYPE.get(sector, NIS2EntityType.IMPORTANT)


def get_csirt_for_member_state(member_state: str) -> Optional[str]:
    """Get the national CSIRT name for a member state.

    Args:
        member_state: ISO country code

    Returns:
        CSIRT name or None
    """
    state_info = EU_MEMBER_STATES.get(member_state.upper())
    return state_info.get("csirt") if state_info else None
