"""Pydantic schemas for API validation."""
from src.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    Token, TokenPayload
)
from src.schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentList,
    AffectedSystemCreate, AffectedSystemResponse
)
from src.schemas.evidence import (
    EvidenceCreate, EvidenceResponse, EvidenceChainResponse,
    ChainVerificationResult
)
from src.schemas.checklist import (
    ChecklistItemResponse, ChecklistPhaseResponse,
    ChecklistItemComplete, ChecklistItemSkip, ChecklistProgress
)
from src.schemas.decision import (
    DecisionTreeResponse, DecisionNodeResponse, DecisionMake,
    DecisionPathResponse, DecisionHistoryResponse
)
from src.schemas.phase import (
    PhaseProgressResponse, PhaseAdvanceRequest, PhaseTimelineResponse
)
from src.schemas.threat_intel import (
    IOCCreate, IOCUpdate, IOCResponse, IOCListResponse, IOCBulkCreate,
    EnrichIOCRequest, EnrichBatchRequest, EnrichmentResponse,
    ThreatActorCreate, ThreatActorUpdate, ThreatActorResponse, ThreatActorListResponse,
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignListResponse,
    ThreatFeedCreate, ThreatFeedResponse, ThreatIntelStats
)
from src.schemas.vulnerability import (
    AssetCreate, AssetUpdate, AssetResponse, AssetListResponse,
    CVECreate, CVEResponse,
    VulnerabilityCreate, VulnerabilityUpdate, VulnerabilityStatusUpdate,
    VulnerabilityResponse, VulnerabilityListResponse,
    VulnerabilityCommentCreate, VulnerabilityCommentResponse,
    ScanCreate, ScanResponse, ScanListResponse,
    ScanScheduleCreate, ScanScheduleResponse,
    VulnerabilityStats, VulnerabilityImport, ImportResult
)
from src.schemas.risk import (
    RiskCategory, RiskStatus, LikelihoodLevel, ImpactLevel, RiskLevel,
    TreatmentType, ControlType, ControlStatus,
    RiskCreate, RiskUpdate, RiskResponse, RiskListResponse,
    RiskAssessmentCreate, RiskAssessmentResponse, RiskAcceptanceRequest,
    RiskControlCreate, RiskControlUpdate, RiskControlResponse, RiskControlListResponse,
    TreatmentActionCreate, TreatmentActionUpdate, TreatmentActionResponse,
    RiskMatrixCell, RiskMatrix, RiskStats,
    RiskAppetiteCreate, RiskAppetiteResponse
)
from src.schemas.cmdb import (
    ConfigurationItemCreate, ConfigurationItemUpdate, ConfigurationItemResponse, ConfigurationItemListResponse,
    SoftwareItemCreate, SoftwareItemUpdate, SoftwareItemResponse, SoftwareItemListResponse,
    SoftwareInstallationCreate, SoftwareInstallationResponse,
    SoftwareLicenseCreate, SoftwareLicenseResponse,
    HardwareSpecCreate, HardwareSpecUpdate, HardwareSpecResponse,
    AssetLifecycleCreate, AssetLifecycleUpdate, AssetLifecycleResponse,
    AssetRelationshipCreate, AssetRelationshipResponse,
    AssetChangeCreate, AssetChangeResponse, AssetChangeListResponse,
    CMDBStats, DependencyMap,
    ConfigurationItemType, ConfigurationItemStatus, SoftwareCategory
)
from src.schemas.soc import (
    AlertCreate, AlertUpdate, AlertAssign, AlertResolve,
    AlertCommentCreate, AlertCommentResponse,
    AlertResponse, AlertListResponse, AlertBulkCreate,
    CaseCreate, CaseUpdate, CaseEscalate, CaseResolve,
    CaseTaskCreate, CaseTaskUpdate, CaseTaskResponse,
    CaseTimelineCreate, CaseTimelineResponse,
    CaseResponse, CaseListResponse,
    PlaybookCreate, PlaybookUpdate, PlaybookResponse, PlaybookListResponse,
    PlaybookExecutionCreate, PlaybookExecutionResponse,
    ShiftHandoverCreate, ShiftHandoverResponse,
    SOCDashboardStats, SOCMetricsResponse,
    AlertSeverity, AlertStatus, AlertSource,
    CaseStatus, CasePriority, PlaybookStatus, PlaybookTriggerType
)
from src.schemas.tprm import (
    VendorCreate, VendorUpdate, VendorResponse, VendorListResponse,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse, AssessmentListResponse,
    FindingCreate, FindingUpdate, FindingResponse, FindingListResponse,
    ContractCreate, ContractUpdate, ContractResponse, ContractListResponse,
    QuestionnaireTemplateCreate, QuestionnaireTemplateUpdate, QuestionnaireTemplateResponse,
    TPRMDashboardStats
)
from src.schemas.integrations import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse, IntegrationListResponse,
    SyncLogResponse, SyncLogListResponse,
    WebhookEventResponse, WebhookEventListResponse,
    IntegrationTemplateResponse,
    SecurityAwarenessMetricsResponse,
    TestConnectionRequest, TestConnectionResponse,
    ManualSyncRequest, ManualSyncResponse,
    IntegrationsDashboardStats
)
from src.schemas.reporting import (
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplateResponse,
    GenerateReportRequest, GeneratedReportResponse, GeneratedReportListResponse,
    ReportScheduleCreate, ReportScheduleUpdate, ReportScheduleResponse, ReportScheduleListResponse,
    DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListResponse,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidgetResponse,
    ExecutiveDashboardStats, TrendData, TrendDataPoint, MetricValue
)
from src.schemas.notifications import (
    NotificationCreate, NotificationBulkCreate, NotificationResponse, NotificationUpdate,
    NotificationMarkRead, NotificationStats,
    NotificationPreferenceCreate, NotificationPreferenceUpdate, NotificationPreferenceResponse,
    WebhookSubscriptionCreate, WebhookSubscriptionUpdate, WebhookSubscriptionResponse,
    WebhookTest, WebhookTestResult, NotificationEvent,
    NotificationType, NotificationPriority, NotificationChannel
)
from src.schemas.attack_paths import (
    GraphScopeType, GraphStatus, PathStatus, SimulationType, SimulationStatus,
    JewelType, BusinessImpact, DataClassification, EntryType, ExposureLevel, TargetCriticality,
    GraphNode, GraphEdge,
    AttackGraphCreate, AttackGraphUpdate, AttackGraphResponse, AttackGraphListResponse, AttackGraphStatistics,
    AttackPathResponse, AttackPathListResponse, AttackPathStatusUpdate, AttackPathRemediation,
    AttackPathSimulationCreate, AttackPathSimulationResponse, AttackPathSimulationListResponse,
    CrownJewelCreate, CrownJewelUpdate, CrownJewelResponse, CrownJewelListResponse,
    EntryPointCreate, EntryPointUpdate, EntryPointResponse, EntryPointListResponse,
    AttackPathDashboard, ChokepointInfo, ChokepointListResponse
)
from src.schemas.documents import (
    DocumentCategory, DocumentStatus, VersionType, ApprovalStatus, ApprovalType, AcknowledgmentStatus, ReviewOutcome,
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse, DocumentDetailResponse,
    DocumentVersionCreate, DocumentVersionResponse, DocumentVersionListResponse, VersionComparisonResponse,
    ApproverAssignment, DocumentApprovalCreate, DocumentApprovalDecision, DocumentApprovalResponse, DocumentApprovalListResponse,
    PendingApprovalItem, PendingApprovalsResponse,
    AcknowledgmentAssignment, AcknowledgmentConfirm, AcknowledgmentDecline, DocumentAcknowledgmentResponse, AcknowledgmentListResponse,
    PendingAcknowledgmentItem, PendingAcknowledgmentsResponse,
    DocumentReviewCreate, DocumentReviewResponse, DocumentReviewListResponse,
    DueForReviewItem, DueForReviewResponse,
    SubmitForReviewRequest, RejectDocumentRequest, PublishDocumentRequest,
    DocumentDashboardStats, AcknowledgmentComplianceReport, ComplianceReportResponse
)
from src.schemas.awareness import (
    CourseCategory, CourseDifficulty, CourseStatus, ModuleType, QuestionType,
    EnrollmentStatus, CampaignStatus, PhishingResult, BadgeCategory,
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse, CourseCatalogItem, CourseCatalogResponse,
    ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse, ModuleContentResponse,
    QuizQuestionOption, QuizQuestionCreate, QuizQuestionUpdate, QuizQuestionResponse, QuizQuestionStudentView,
    QuizCreate, QuizUpdate, QuizResponse, QuizDetailResponse, QuizStudentView, QuizStartResponse,
    QuizAnswer, QuizSubmitRequest, QuizResultQuestion, QuizAttemptResponse,
    EnrollmentCreate, BulkEnrollmentRequest, EnrollmentResponse, EnrollmentListResponse,
    MyLearningItem, MyLearningResponse, ModuleProgressUpdate, ModuleProgressResponse,
    PhishingTemplateCreate, PhishingTemplateUpdate, PhishingTemplateResponse, PhishingTemplateListResponse,
    PhishingCampaignCreate, PhishingCampaignUpdate, PhishingCampaignResponse, PhishingCampaignListResponse,
    PhishingTargetResponse, PhishingCampaignResultsResponse, PhishingTrackEvent,
    BadgeCreate, BadgeUpdate, BadgeResponse, BadgeListResponse, UserBadgeResponse, UserBadgesResponse,
    TrainingStatsResponse, LeaderboardEntry, LeaderboardResponse,
    TrainingDashboardStats, CourseComplianceReport, DepartmentComplianceReport, ComplianceReportResponse as TrainingComplianceReportResponse,
    PhishingAnalyticsResponse
)

__all__ = [
    # User
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload",
    # Incident
    "IncidentCreate", "IncidentUpdate", "IncidentResponse", "IncidentList",
    "AffectedSystemCreate", "AffectedSystemResponse",
    # Evidence
    "EvidenceCreate", "EvidenceResponse", "EvidenceChainResponse",
    "ChainVerificationResult",
    # Checklist
    "ChecklistItemResponse", "ChecklistPhaseResponse",
    "ChecklistItemComplete", "ChecklistItemSkip", "ChecklistProgress",
    # Decision
    "DecisionTreeResponse", "DecisionNodeResponse", "DecisionMake",
    "DecisionPathResponse", "DecisionHistoryResponse",
    # Phase
    "PhaseProgressResponse", "PhaseAdvanceRequest", "PhaseTimelineResponse",
    # Threat Intel
    "IOCCreate", "IOCUpdate", "IOCResponse", "IOCListResponse", "IOCBulkCreate",
    "EnrichIOCRequest", "EnrichBatchRequest", "EnrichmentResponse",
    "ThreatActorCreate", "ThreatActorUpdate", "ThreatActorResponse", "ThreatActorListResponse",
    "CampaignCreate", "CampaignUpdate", "CampaignResponse", "CampaignListResponse",
    "ThreatFeedCreate", "ThreatFeedResponse", "ThreatIntelStats",
    # Vulnerability Management
    "AssetCreate", "AssetUpdate", "AssetResponse", "AssetListResponse",
    "CVECreate", "CVEResponse",
    "VulnerabilityCreate", "VulnerabilityUpdate", "VulnerabilityStatusUpdate",
    "VulnerabilityResponse", "VulnerabilityListResponse",
    "VulnerabilityCommentCreate", "VulnerabilityCommentResponse",
    "ScanCreate", "ScanResponse", "ScanListResponse",
    "ScanScheduleCreate", "ScanScheduleResponse",
    "VulnerabilityStats", "VulnerabilityImport", "ImportResult",
    # Risk Management
    "RiskCategory", "RiskStatus", "LikelihoodLevel", "ImpactLevel", "RiskLevel",
    "TreatmentType", "ControlType", "ControlStatus",
    "RiskCreate", "RiskUpdate", "RiskResponse", "RiskListResponse",
    "RiskAssessmentCreate", "RiskAssessmentResponse", "RiskAcceptanceRequest",
    "RiskControlCreate", "RiskControlUpdate", "RiskControlResponse", "RiskControlListResponse",
    "TreatmentActionCreate", "TreatmentActionUpdate", "TreatmentActionResponse",
    "RiskMatrixCell", "RiskMatrix", "RiskStats",
    "RiskAppetiteCreate", "RiskAppetiteResponse",
    # CMDB
    "ConfigurationItemCreate", "ConfigurationItemUpdate", "ConfigurationItemResponse", "ConfigurationItemListResponse",
    "SoftwareItemCreate", "SoftwareItemUpdate", "SoftwareItemResponse", "SoftwareItemListResponse",
    "SoftwareInstallationCreate", "SoftwareInstallationResponse",
    "SoftwareLicenseCreate", "SoftwareLicenseResponse",
    "HardwareSpecCreate", "HardwareSpecUpdate", "HardwareSpecResponse",
    "AssetLifecycleCreate", "AssetLifecycleUpdate", "AssetLifecycleResponse",
    "AssetRelationshipCreate", "AssetRelationshipResponse",
    "AssetChangeCreate", "AssetChangeResponse", "AssetChangeListResponse",
    "CMDBStats", "DependencyMap",
    "ConfigurationItemType", "ConfigurationItemStatus", "SoftwareCategory",
    # SOC
    "AlertCreate", "AlertUpdate", "AlertAssign", "AlertResolve",
    "AlertCommentCreate", "AlertCommentResponse",
    "AlertResponse", "AlertListResponse", "AlertBulkCreate",
    "CaseCreate", "CaseUpdate", "CaseEscalate", "CaseResolve",
    "CaseTaskCreate", "CaseTaskUpdate", "CaseTaskResponse",
    "CaseTimelineCreate", "CaseTimelineResponse",
    "CaseResponse", "CaseListResponse",
    "PlaybookCreate", "PlaybookUpdate", "PlaybookResponse", "PlaybookListResponse",
    "PlaybookExecutionCreate", "PlaybookExecutionResponse",
    "ShiftHandoverCreate", "ShiftHandoverResponse",
    "SOCDashboardStats", "SOCMetricsResponse",
    "AlertSeverity", "AlertStatus", "AlertSource",
    "CaseStatus", "CasePriority", "PlaybookStatus", "PlaybookTriggerType",
    # TPRM
    "VendorCreate", "VendorUpdate", "VendorResponse", "VendorListResponse",
    "AssessmentCreate", "AssessmentUpdate", "AssessmentResponse", "AssessmentListResponse",
    "FindingCreate", "FindingUpdate", "FindingResponse", "FindingListResponse",
    "ContractCreate", "ContractUpdate", "ContractResponse", "ContractListResponse",
    "QuestionnaireTemplateCreate", "QuestionnaireTemplateUpdate", "QuestionnaireTemplateResponse",
    "TPRMDashboardStats",
    # Integrations
    "IntegrationCreate", "IntegrationUpdate", "IntegrationResponse", "IntegrationListResponse",
    "SyncLogResponse", "SyncLogListResponse",
    "WebhookEventResponse", "WebhookEventListResponse",
    "IntegrationTemplateResponse",
    "SecurityAwarenessMetricsResponse",
    "TestConnectionRequest", "TestConnectionResponse",
    "ManualSyncRequest", "ManualSyncResponse",
    "IntegrationsDashboardStats",
    # Reporting
    "ReportTemplateCreate", "ReportTemplateUpdate", "ReportTemplateResponse",
    "GenerateReportRequest", "GeneratedReportResponse", "GeneratedReportListResponse",
    "ReportScheduleCreate", "ReportScheduleUpdate", "ReportScheduleResponse", "ReportScheduleListResponse",
    "DashboardCreate", "DashboardUpdate", "DashboardResponse", "DashboardListResponse",
    "DashboardWidgetCreate", "DashboardWidgetUpdate", "DashboardWidgetResponse",
    "ExecutiveDashboardStats", "TrendData", "TrendDataPoint", "MetricValue",
    # Notifications
    "NotificationCreate", "NotificationBulkCreate", "NotificationResponse", "NotificationUpdate",
    "NotificationMarkRead", "NotificationStats",
    "NotificationPreferenceCreate", "NotificationPreferenceUpdate", "NotificationPreferenceResponse",
    "WebhookSubscriptionCreate", "WebhookSubscriptionUpdate", "WebhookSubscriptionResponse",
    "WebhookTest", "WebhookTestResult", "NotificationEvent",
    "NotificationType", "NotificationPriority", "NotificationChannel",
    # Attack Path Analysis
    "GraphScopeType", "GraphStatus", "PathStatus", "SimulationType", "SimulationStatus",
    "JewelType", "BusinessImpact", "DataClassification", "EntryType", "ExposureLevel", "TargetCriticality",
    "GraphNode", "GraphEdge",
    "AttackGraphCreate", "AttackGraphUpdate", "AttackGraphResponse", "AttackGraphListResponse", "AttackGraphStatistics",
    "AttackPathResponse", "AttackPathListResponse", "AttackPathStatusUpdate", "AttackPathRemediation",
    "AttackPathSimulationCreate", "AttackPathSimulationResponse", "AttackPathSimulationListResponse",
    "CrownJewelCreate", "CrownJewelUpdate", "CrownJewelResponse", "CrownJewelListResponse",
    "EntryPointCreate", "EntryPointUpdate", "EntryPointResponse", "EntryPointListResponse",
    "AttackPathDashboard", "ChokepointInfo", "ChokepointListResponse",
    # Document & Policy Management
    "DocumentCategory", "DocumentStatus", "VersionType", "ApprovalStatus", "ApprovalType", "AcknowledgmentStatus", "ReviewOutcome",
    "DocumentCreate", "DocumentUpdate", "DocumentResponse", "DocumentListResponse", "DocumentDetailResponse",
    "DocumentVersionCreate", "DocumentVersionResponse", "DocumentVersionListResponse", "VersionComparisonResponse",
    "ApproverAssignment", "DocumentApprovalCreate", "DocumentApprovalDecision", "DocumentApprovalResponse", "DocumentApprovalListResponse",
    "PendingApprovalItem", "PendingApprovalsResponse",
    "AcknowledgmentAssignment", "AcknowledgmentConfirm", "AcknowledgmentDecline", "DocumentAcknowledgmentResponse", "AcknowledgmentListResponse",
    "PendingAcknowledgmentItem", "PendingAcknowledgmentsResponse",
    "DocumentReviewCreate", "DocumentReviewResponse", "DocumentReviewListResponse",
    "DueForReviewItem", "DueForReviewResponse",
    "SubmitForReviewRequest", "RejectDocumentRequest", "PublishDocumentRequest",
    "DocumentDashboardStats", "AcknowledgmentComplianceReport", "ComplianceReportResponse",
    # Security Awareness & Training
    "CourseCategory", "CourseDifficulty", "CourseStatus", "ModuleType", "QuestionType",
    "EnrollmentStatus", "CampaignStatus", "PhishingResult", "BadgeCategory",
    "CourseCreate", "CourseUpdate", "CourseResponse", "CourseListResponse", "CourseCatalogItem", "CourseCatalogResponse",
    "ModuleCreate", "ModuleUpdate", "ModuleResponse", "ModuleListResponse", "ModuleContentResponse",
    "QuizQuestionOption", "QuizQuestionCreate", "QuizQuestionUpdate", "QuizQuestionResponse", "QuizQuestionStudentView",
    "QuizCreate", "QuizUpdate", "QuizResponse", "QuizDetailResponse", "QuizStudentView", "QuizStartResponse",
    "QuizAnswer", "QuizSubmitRequest", "QuizResultQuestion", "QuizAttemptResponse",
    "EnrollmentCreate", "BulkEnrollmentRequest", "EnrollmentResponse", "EnrollmentListResponse",
    "MyLearningItem", "MyLearningResponse", "ModuleProgressUpdate", "ModuleProgressResponse",
    "PhishingTemplateCreate", "PhishingTemplateUpdate", "PhishingTemplateResponse", "PhishingTemplateListResponse",
    "PhishingCampaignCreate", "PhishingCampaignUpdate", "PhishingCampaignResponse", "PhishingCampaignListResponse",
    "PhishingTargetResponse", "PhishingCampaignResultsResponse", "PhishingTrackEvent",
    "BadgeCreate", "BadgeUpdate", "BadgeResponse", "BadgeListResponse", "UserBadgeResponse", "UserBadgesResponse",
    "TrainingStatsResponse", "LeaderboardEntry", "LeaderboardResponse",
    "TrainingDashboardStats", "CourseComplianceReport", "DepartmentComplianceReport", "TrainingComplianceReportResponse",
    "PhishingAnalyticsResponse",
]
