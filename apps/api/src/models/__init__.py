"""SQLAlchemy models."""
from src.models.user import User, UserRole
from src.models.incident import Incident, IncidentStatus, IncidentSeverity, AffectedSystem
from src.models.evidence import EvidenceEntry, EvidenceType
from src.models.checklist import ChecklistItem, ChecklistStatus
from src.models.decision import DecisionPath, DecisionNode, DecisionTree
from src.models.phase import PhaseProgress, IRPhase, PhaseStatus
from src.models.threat_intel import (
    IOC, ThreatActor, Campaign, ThreatFeed,
    ThreatLevel, IOCType, IOCStatus,
    ActorMotivation, ActorSophistication
)
from src.models.vulnerability import (
    Asset, CVEEntry, Vulnerability, VulnerabilityComment,
    VulnerabilityScan, ScanSchedule,
    VulnerabilitySeverity, VulnerabilityStatus, ScanStatus, ScanType,
    AssetType, AssetCriticality
)
from src.models.risk import (
    Risk, RiskControl, RiskAssessment, TreatmentAction, RiskAppetite,
    RiskCategory, RiskStatus, LikelihoodLevel, ImpactLevel, RiskLevel,
    TreatmentType, ControlType, ControlStatus,
    risk_control_association, risk_vulnerability_association, risk_threat_association
)
from src.models.cmdb import (
    ConfigurationItem, SoftwareItem, SoftwareInstallation, SoftwareLicense,
    HardwareSpec, AssetLifecycle, AssetRelationship, AssetChange,
    ConfigurationItemType, ConfigurationItemStatus, AssetLifecycleStage,
    RelationshipType, ChangeType, SoftwareCategory, LicenseType
)
from src.models.soc import (
    SOCAlert, AlertComment, SOCCase, CaseTask, CaseTimeline,
    SOCPlaybook, PlaybookExecution, SOCMetrics, ShiftHandover,
    AlertSeverity, AlertStatus, AlertSource,
    CaseStatus, CasePriority, PlaybookStatus, PlaybookTriggerType,
    ActionType, ExecutionStatus
)
from src.models.tprm import (
    Vendor, VendorAssessment, AssessmentFinding, VendorContract, QuestionnaireTemplate,
    VendorStatus, VendorTier, VendorCategory,
    AssessmentStatus, AssessmentType, RiskRating,
    ContractStatus, FindingSeverity, FindingStatus
)
from src.models.integrations import (
    Integration, IntegrationSyncLog, WebhookEvent, IntegrationTemplate, SecurityAwarenessMetrics,
    IntegrationType, IntegrationCategory, IntegrationStatus,
    SyncDirection, SyncFrequency
)
from src.models.reporting import (
    ReportTemplate, GeneratedReport, ReportSchedule, ReportDistribution,
    Dashboard, DashboardWidget, MetricSnapshot, SavedQuery,
    ReportType, ReportFormat, ReportStatus, ScheduleFrequency, WidgetType
)
from src.models.notifications import (
    Notification, NotificationPreference, NotificationTemplate,
    WebhookSubscription, NotificationLog,
    NotificationType, NotificationPriority, NotificationChannel
)
from src.models.user_management import (
    Team, TeamMember, Role, Permission, UserSession,
    UserInvitation, ActivityLog, APIKey,
    TeamRole, InvitationStatus, SessionStatus,
    role_permissions, user_roles
)

__all__ = [
    "User",
    "UserRole",
    "Incident",
    "IncidentStatus",
    "IncidentSeverity",
    "AffectedSystem",
    "EvidenceEntry",
    "EvidenceType",
    "ChecklistItem",
    "ChecklistStatus",
    "DecisionPath",
    "DecisionNode",
    "DecisionTree",
    "PhaseProgress",
    "IRPhase",
    "PhaseStatus",
    # Threat Intel
    "IOC",
    "ThreatActor",
    "Campaign",
    "ThreatFeed",
    "ThreatLevel",
    "IOCType",
    "IOCStatus",
    "ActorMotivation",
    "ActorSophistication",
    # Vulnerability Management
    "Asset",
    "CVEEntry",
    "Vulnerability",
    "VulnerabilityComment",
    "VulnerabilityScan",
    "ScanSchedule",
    "VulnerabilitySeverity",
    "VulnerabilityStatus",
    "ScanStatus",
    "ScanType",
    "AssetType",
    "AssetCriticality",
    # Risk Management
    "Risk",
    "RiskControl",
    "RiskAssessment",
    "TreatmentAction",
    "RiskAppetite",
    "RiskCategory",
    "RiskStatus",
    "LikelihoodLevel",
    "ImpactLevel",
    "RiskLevel",
    "TreatmentType",
    "ControlType",
    "ControlStatus",
    "risk_control_association",
    "risk_vulnerability_association",
    "risk_threat_association",
    # CMDB
    "ConfigurationItem",
    "SoftwareItem",
    "SoftwareInstallation",
    "SoftwareLicense",
    "HardwareSpec",
    "AssetLifecycle",
    "AssetRelationship",
    "AssetChange",
    "ConfigurationItemType",
    "ConfigurationItemStatus",
    "AssetLifecycleStage",
    "RelationshipType",
    "ChangeType",
    "SoftwareCategory",
    "LicenseType",
    # SOC
    "SOCAlert",
    "AlertComment",
    "SOCCase",
    "CaseTask",
    "CaseTimeline",
    "SOCPlaybook",
    "PlaybookExecution",
    "SOCMetrics",
    "ShiftHandover",
    "AlertSeverity",
    "AlertStatus",
    "AlertSource",
    "CaseStatus",
    "CasePriority",
    "PlaybookStatus",
    "PlaybookTriggerType",
    "ActionType",
    "ExecutionStatus",
    # TPRM
    "Vendor",
    "VendorAssessment",
    "AssessmentFinding",
    "VendorContract",
    "QuestionnaireTemplate",
    "VendorStatus",
    "VendorTier",
    "VendorCategory",
    "AssessmentStatus",
    "AssessmentType",
    "RiskRating",
    "ContractStatus",
    "FindingSeverity",
    "FindingStatus",
    # Integrations
    "Integration",
    "IntegrationSyncLog",
    "WebhookEvent",
    "IntegrationTemplate",
    "SecurityAwarenessMetrics",
    "IntegrationType",
    "IntegrationCategory",
    "IntegrationStatus",
    "SyncDirection",
    "SyncFrequency",
    # Reporting
    "ReportTemplate",
    "GeneratedReport",
    "ReportSchedule",
    "ReportDistribution",
    "Dashboard",
    "DashboardWidget",
    "MetricSnapshot",
    "SavedQuery",
    "ReportType",
    "ReportFormat",
    "ReportStatus",
    "ScheduleFrequency",
    "WidgetType",
    # Notifications
    "Notification",
    "NotificationPreference",
    "NotificationTemplate",
    "WebhookSubscription",
    "NotificationLog",
    "NotificationType",
    "NotificationPriority",
    "NotificationChannel",
    # User Management
    "Team",
    "TeamMember",
    "Role",
    "Permission",
    "UserSession",
    "UserInvitation",
    "ActivityLog",
    "APIKey",
    "TeamRole",
    "InvitationStatus",
    "SessionStatus",
    "role_permissions",
    "user_roles",
]
