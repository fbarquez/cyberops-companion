"""
NIS2 Directive Compliance Module

Handles NIS2 (Network and Information Security Directive 2) compliance
including notification management, deadline tracking, and report generation.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

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

    def __init__(self):
        """Initialize the NIS2 manager with in-memory storage."""
        self._notifications: Dict[str, Dict[str, Any]] = {}
        self._early_warnings: Dict[str, Dict[str, Any]] = {}
        self._incident_notifications: Dict[str, Dict[str, Any]] = {}
        self._final_reports: Dict[str, Dict[str, Any]] = {}

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

        self._notifications[incident_id] = {
            "notification_id": notification_id,
            "incident_id": incident_id,
            "entity_type": entity_type.value,
            "sector": sector.value,
            "organization_name": organization_name,
            "member_state": member_state,
            "detection_time": detection_time.isoformat(),
            "early_warning_deadline": notification.early_warning_deadline.isoformat(),
            "notification_deadline": notification.notification_deadline.isoformat(),
            "final_report_deadline": notification.final_report_deadline.isoformat(),
            "primary_contact": primary_contact.model_dump(),
            "technical_contact": technical_contact.model_dump() if technical_contact else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

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
        notification_data = self._notifications.get(incident_id)
        if not notification_data:
            raise ValueError(f"No NIS2 notification found for incident {incident_id}")

        warning_id = f"EW-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(notification_data["early_warning_deadline"])

        self._early_warnings[incident_id] = {
            "warning_id": warning_id,
            "notification_id": notification_data["notification_id"],
            "incident_id": incident_id,
            "submitted_at": now.isoformat(),
            "deadline": deadline.isoformat(),
            "suspected_cause": suspected_cause,
            "cross_border_suspected": cross_border_suspected,
            "initial_assessment": initial_assessment,
            "status": NIS2NotificationStatus.SUBMITTED.value,
        }

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
        notification_data = self._notifications.get(incident_id)
        if not notification_data:
            raise ValueError(f"No NIS2 notification found for incident {incident_id}")

        early_warning = self._early_warnings.get(incident_id)
        early_warning_id = early_warning["warning_id"] if early_warning else None

        notification_id = f"IN-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(notification_data["notification_deadline"])

        self._incident_notifications[incident_id] = {
            "notification_id": notification_id,
            "parent_notification_id": notification_data["notification_id"],
            "incident_id": incident_id,
            "early_warning_id": early_warning_id,
            "submitted_at": now.isoformat(),
            "deadline": deadline.isoformat(),
            "incident_description": incident_description,
            "severity": severity.value,
            "incident_type": incident_type,
            "root_cause_preliminary": root_cause_preliminary,
            "impact": impact.model_dump(),
            "mitigation_measures": mitigation_measures,
            "containment_status": containment_status,
            "status": NIS2NotificationStatus.SUBMITTED.value,
        }

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
        notification_data = self._notifications.get(incident_id)
        if not notification_data:
            raise ValueError(f"No NIS2 notification found for incident {incident_id}")

        incident_notif = self._incident_notifications.get(incident_id)
        incident_notification_id = incident_notif["notification_id"] if incident_notif else None

        report_id = f"FR-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        deadline = datetime.fromisoformat(notification_data["final_report_deadline"])

        self._final_reports[incident_id] = {
            "report_id": report_id,
            "notification_id": notification_data["notification_id"],
            "incident_id": incident_id,
            "incident_notification_id": incident_notification_id,
            "submitted_at": now.isoformat(),
            "deadline": deadline.isoformat(),
            "incident_description": incident_description,
            "root_cause_analysis": root_cause_analysis,
            "threat_type": threat_type,
            "attack_techniques": attack_techniques,
            "total_impact_assessment": total_impact_assessment,
            "services_affected": services_affected,
            "recovery_time_hours": recovery_time_hours,
            "lessons_learned": lessons_learned,
            "preventive_measures": preventive_measures,
            "security_improvements": security_improvements,
            "other_csirts_notified": other_csirts_notified or [],
            "enisa_notified": enisa_notified,
            "status": NIS2NotificationStatus.SUBMITTED.value,
        }

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
        notification_data = self._notifications.get(incident_id)
        if not notification_data:
            return None

        result = dict(notification_data)
        result["early_warning"] = self._early_warnings.get(incident_id)
        result["incident_notification"] = self._incident_notifications.get(incident_id)
        result["final_report"] = self._final_reports.get(incident_id)

        return result

    def get_deadlines(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get deadline status for an incident.

        Args:
            incident_id: Incident identifier

        Returns:
            Dict with deadline information or None
        """
        notification_data = self._notifications.get(incident_id)
        if not notification_data:
            return None

        now = datetime.now(timezone.utc)

        early_warning_deadline = datetime.fromisoformat(notification_data["early_warning_deadline"])
        notification_deadline = datetime.fromisoformat(notification_data["notification_deadline"])
        final_report_deadline = datetime.fromisoformat(notification_data["final_report_deadline"])

        early_warning = self._early_warnings.get(incident_id)
        incident_notif = self._incident_notifications.get(incident_id)
        final_report = self._final_reports.get(incident_id)

        return {
            "early_warning": {
                "deadline": early_warning_deadline.isoformat(),
                "submitted": early_warning is not None,
                "overdue": now > early_warning_deadline and early_warning is None,
                "remaining_hours": max(0, (early_warning_deadline - now).total_seconds() / 3600) if early_warning is None else None,
            },
            "notification": {
                "deadline": notification_deadline.isoformat(),
                "submitted": incident_notif is not None,
                "overdue": now > notification_deadline and incident_notif is None,
                "remaining_hours": max(0, (notification_deadline - now).total_seconds() / 3600) if incident_notif is None else None,
            },
            "final_report": {
                "deadline": final_report_deadline.isoformat(),
                "submitted": final_report is not None,
                "overdue": now > final_report_deadline and final_report is None,
                "remaining_days": max(0, (final_report_deadline - now).total_seconds() / 86400) if final_report is None else None,
            },
        }

    def get_all_sectors(self) -> List[Dict[str, str]]:
        """Get all NIS2 sectors with their entity types."""
        return [
            {
                "id": sector.value,
                "name": sector.name.replace("_", " ").title(),
                "entity_type": SECTOR_ENTITY_TYPE.get(sector, NIS2EntityType.IMPORTANT).value,
            }
            for sector in NIS2Sector
        ]

    def get_member_states(self) -> Dict[str, Dict[str, str]]:
        """Get all EU member states with their CSIRTs."""
        return EU_MEMBER_STATES

    def calculate_deadlines(
        self,
        detection_time: datetime,
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate all NIS2 deadlines from detection time.

        Args:
            detection_time: When the incident was detected

        Returns:
            Dictionary with all deadlines
        """
        if detection_time.tzinfo is None:
            detection_time = detection_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        early_warning = detection_time + timedelta(hours=24)
        notification = detection_time + timedelta(hours=72)
        final_report = detection_time + timedelta(days=30)

        return {
            "early_warning": {
                "name": "Early Warning (24h)",
                "deadline": early_warning.isoformat(),
                "overdue": now > early_warning,
                "remaining_hours": max(0, (early_warning - now).total_seconds() / 3600),
            },
            "notification": {
                "name": "Incident Notification (72h)",
                "deadline": notification.isoformat(),
                "overdue": now > notification,
                "remaining_hours": max(0, (notification - now).total_seconds() / 3600),
            },
            "final_report": {
                "name": "Final Report (30 days)",
                "deadline": final_report.isoformat(),
                "overdue": now > final_report,
                "remaining_days": max(0, (final_report - now).total_seconds() / 86400),
            },
        }

    def export_notification_report(
        self,
        incident_id: str,
        format: str = "markdown",
    ) -> str:
        """Export a complete NIS2 notification report.

        Args:
            incident_id: Incident identifier
            format: Output format (markdown, json)

        Returns:
            Formatted report string
        """
        notification = self.get_notification(incident_id)
        if not notification:
            raise ValueError(f"No notification found for incident {incident_id}")

        if format == "json":
            import json
            return json.dumps(notification, indent=2, default=str)

        # Markdown format
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


# Singleton instance
_nis2_manager: Optional[NIS2DirectiveManager] = None


def get_nis2_manager() -> NIS2DirectiveManager:
    """Get the singleton NIS2 manager instance."""
    global _nis2_manager
    if _nis2_manager is None:
        _nis2_manager = NIS2DirectiveManager()
    return _nis2_manager
