"""Security Awareness & Training schemas."""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from src.models.awareness import (
    CourseCategory, CourseDifficulty, CourseStatus, ModuleType, QuestionType,
    EnrollmentStatus, CampaignStatus, PhishingResult, BadgeCategory
)


# ============================================================================
# Training Course Schemas
# ============================================================================

class CourseBase(BaseModel):
    """Base course schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    category: CourseCategory
    difficulty: Optional[CourseDifficulty] = CourseDifficulty.BEGINNER
    estimated_duration_minutes: Optional[int] = Field(30, ge=1, le=480)
    passing_score: Optional[int] = Field(80, ge=0, le=100)
    max_attempts: Optional[int] = Field(3, ge=1, le=10)
    certificate_enabled: Optional[bool] = True
    thumbnail_url: Optional[str] = None
    objectives: Optional[List[str]] = []
    target_audience: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    compliance_frameworks: Optional[List[str]] = []
    control_references: Optional[List[str]] = []
    mandatory_for: Optional[List[str]] = []
    recurrence_days: Optional[int] = Field(None, ge=30, le=730)  # 30 days to 2 years
    deadline_days: Optional[int] = Field(None, ge=1, le=90)


class CourseCreate(CourseBase):
    """Schema for creating a course."""
    prerequisite_ids: Optional[List[str]] = []


class CourseUpdate(BaseModel):
    """Schema for updating a course."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    category: Optional[CourseCategory] = None
    difficulty: Optional[CourseDifficulty] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    certificate_enabled: Optional[bool] = None
    thumbnail_url: Optional[str] = None
    objectives: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    compliance_frameworks: Optional[List[str]] = None
    control_references: Optional[List[str]] = None
    mandatory_for: Optional[List[str]] = None
    recurrence_days: Optional[int] = Field(None, ge=30, le=730)
    deadline_days: Optional[int] = Field(None, ge=1, le=90)
    is_featured: Optional[bool] = None
    prerequisite_ids: Optional[List[str]] = None


class CourseResponse(CourseBase):
    """Schema for course response."""
    id: str
    course_code: str
    status: CourseStatus
    is_featured: bool
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Computed fields
    modules_count: Optional[int] = 0
    enrolled_count: Optional[int] = 0
    completion_rate: Optional[float] = 0.0
    average_score: Optional[float] = None
    prerequisite_courses: Optional[List["CourseResponse"]] = []

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """Schema for paginated course list."""
    items: List[CourseResponse]
    total: int
    page: int
    size: int
    pages: int


class CourseCatalogItem(BaseModel):
    """Schema for course catalog display."""
    id: str
    course_code: str
    title: str
    short_description: Optional[str] = None
    category: CourseCategory
    difficulty: CourseDifficulty
    estimated_duration_minutes: int
    thumbnail_url: Optional[str] = None
    is_featured: bool
    modules_count: int
    enrolled_count: int
    average_score: Optional[float] = None

    # User-specific
    user_enrollment_status: Optional[EnrollmentStatus] = None
    user_progress_percent: Optional[float] = None


class CourseCatalogResponse(BaseModel):
    """Schema for course catalog."""
    items: List[CourseCatalogItem]
    total: int
    page: int
    size: int
    pages: int
    categories: List[dict]  # [{category, count}]


# ============================================================================
# Training Module Schemas
# ============================================================================

class ModuleBase(BaseModel):
    """Base module schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    module_type: ModuleType
    content: Optional[dict] = None
    estimated_duration_minutes: Optional[int] = Field(10, ge=1, le=120)
    is_mandatory: Optional[bool] = True
    requires_completion_to_proceed: Optional[bool] = True


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""
    course_id: str
    order: Optional[int] = None
    attachment_id: Optional[str] = None


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    module_type: Optional[ModuleType] = None
    content: Optional[dict] = None
    order: Optional[int] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=120)
    is_mandatory: Optional[bool] = None
    requires_completion_to_proceed: Optional[bool] = None
    attachment_id: Optional[str] = None
    is_active: Optional[bool] = None


class ModuleResponse(ModuleBase):
    """Schema for module response."""
    id: str
    course_id: str
    order: int
    attachment_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # For quiz modules
    has_quiz: bool = False
    quiz_id: Optional[str] = None

    # User-specific
    user_completed: Optional[bool] = None
    user_progress_percent: Optional[float] = None

    class Config:
        from_attributes = True


class ModuleListResponse(BaseModel):
    """Schema for module list."""
    items: List[ModuleResponse]
    total: int


class ModuleContentResponse(ModuleResponse):
    """Schema for module with full content."""
    content_data: Optional[dict] = None  # Full content for viewing


# ============================================================================
# Quiz Schemas
# ============================================================================

class QuizQuestionOption(BaseModel):
    """Schema for quiz question option."""
    id: str
    text: str
    is_correct: Optional[bool] = None  # Hidden from students


class QuizQuestionBase(BaseModel):
    """Base quiz question schema."""
    question_text: str = Field(..., min_length=1)
    question_type: QuestionType = QuestionType.SINGLE_CHOICE
    options: List[QuizQuestionOption] = []
    matching_data: Optional[dict] = None
    explanation: Optional[str] = None
    points: Optional[int] = Field(1, ge=1, le=10)


class QuizQuestionCreate(QuizQuestionBase):
    """Schema for creating a question."""
    order: Optional[int] = None


class QuizQuestionUpdate(BaseModel):
    """Schema for updating a question."""
    question_text: Optional[str] = Field(None, min_length=1)
    question_type: Optional[QuestionType] = None
    options: Optional[List[QuizQuestionOption]] = None
    matching_data: Optional[dict] = None
    explanation: Optional[str] = None
    points: Optional[int] = Field(None, ge=1, le=10)
    order: Optional[int] = None


class QuizQuestionResponse(QuizQuestionBase):
    """Schema for question response."""
    id: str
    quiz_id: str
    order: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuizQuestionStudentView(BaseModel):
    """Schema for question shown to students (no correct answers)."""
    id: str
    question_text: str
    question_type: QuestionType
    options: List[dict]  # Without is_correct
    points: int
    order: int


class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str = Field(..., min_length=1, max_length=255)
    instructions: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=120)
    passing_score: Optional[int] = Field(80, ge=0, le=100)
    randomize_questions: Optional[bool] = True
    randomize_answers: Optional[bool] = True
    show_correct_answers: Optional[bool] = True
    max_attempts: Optional[int] = Field(3, ge=1, le=10)


class QuizCreate(QuizBase):
    """Schema for creating a quiz."""
    module_id: str
    questions: Optional[List[QuizQuestionCreate]] = []


class QuizUpdate(BaseModel):
    """Schema for updating a quiz."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    instructions: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=120)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    randomize_questions: Optional[bool] = None
    randomize_answers: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=10)


class QuizResponse(QuizBase):
    """Schema for quiz response."""
    id: str
    module_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    questions_count: int = 0
    total_points: int = 0

    class Config:
        from_attributes = True


class QuizDetailResponse(QuizResponse):
    """Schema for quiz with questions."""
    questions: List[QuizQuestionResponse] = []


class QuizStudentView(BaseModel):
    """Schema for quiz shown to students."""
    id: str
    title: str
    instructions: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score: int
    max_attempts: int
    questions_count: int
    total_points: int

    # User-specific
    attempts_remaining: int
    best_score: Optional[float] = None


class QuizStartResponse(BaseModel):
    """Schema for starting a quiz attempt."""
    attempt_id: str
    quiz_id: str
    started_at: datetime
    time_limit_minutes: Optional[int] = None
    questions: List[QuizQuestionStudentView]


class QuizAnswer(BaseModel):
    """Schema for quiz answer submission."""
    question_id: str
    selected_options: List[str]  # Option IDs


class QuizSubmitRequest(BaseModel):
    """Schema for submitting quiz answers."""
    answers: List[QuizAnswer]


class QuizResultQuestion(BaseModel):
    """Schema for quiz result per question."""
    question_id: str
    question_text: str
    selected_answer: List[str]
    correct_answer: List[str]
    is_correct: bool
    points_earned: int
    points_possible: int
    explanation: Optional[str] = None


class QuizAttemptResponse(BaseModel):
    """Schema for quiz attempt response."""
    id: str
    quiz_id: str
    user_id: str
    attempt_number: int
    score: float
    points_earned: int
    points_possible: int
    passed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None

    # Include results if showing correct answers
    results: Optional[List[QuizResultQuestion]] = None

    class Config:
        from_attributes = True


# ============================================================================
# Enrollment & Progress Schemas
# ============================================================================

class EnrollmentCreate(BaseModel):
    """Schema for enrolling in a course."""
    course_id: str
    deadline: Optional[date] = None
    assignment_reason: Optional[str] = None


class BulkEnrollmentRequest(BaseModel):
    """Schema for bulk enrollment."""
    course_id: str
    user_ids: List[str]
    deadline: Optional[date] = None
    assignment_reason: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response."""
    id: str
    course_id: str
    user_id: str
    status: EnrollmentStatus
    progress_percent: float
    modules_completed: int
    total_modules: int
    highest_quiz_score: Optional[float] = None
    average_quiz_score: Optional[float] = None
    enrolled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[date] = None
    last_activity_at: Optional[datetime] = None
    certificate_issued: bool
    certificate_url: Optional[str] = None
    assigned_by: Optional[str] = None
    assignment_reason: Optional[str] = None
    created_at: datetime

    # Related data
    course_title: Optional[str] = None
    course_category: Optional[CourseCategory] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class EnrollmentListResponse(BaseModel):
    """Schema for enrollment list."""
    items: List[EnrollmentResponse]
    total: int
    page: int
    size: int
    pages: int


class MyLearningItem(BaseModel):
    """Schema for user's learning item."""
    enrollment_id: str
    course_id: str
    course_code: str
    course_title: str
    course_category: CourseCategory
    course_difficulty: CourseDifficulty
    thumbnail_url: Optional[str] = None
    status: EnrollmentStatus
    progress_percent: float
    modules_completed: int
    total_modules: int
    deadline: Optional[date] = None
    is_overdue: bool = False
    last_activity_at: Optional[datetime] = None
    next_module_id: Optional[str] = None
    next_module_title: Optional[str] = None


class MyLearningResponse(BaseModel):
    """Schema for user's learning dashboard."""
    in_progress: List[MyLearningItem]
    completed: List[MyLearningItem]
    assigned: List[MyLearningItem]  # Not yet started
    overdue: int
    due_soon: int  # Within 7 days


class ModuleProgressUpdate(BaseModel):
    """Schema for updating module progress."""
    completion_percent: Optional[float] = Field(None, ge=0, le=100)
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    last_position_seconds: Optional[int] = Field(None, ge=0)  # For videos
    is_completed: Optional[bool] = None


class ModuleProgressResponse(BaseModel):
    """Schema for module progress response."""
    id: str
    enrollment_id: str
    module_id: str
    user_id: str
    is_completed: bool
    completion_percent: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_spent_seconds: int
    last_position_seconds: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Phishing Campaign Schemas
# ============================================================================

class PhishingTemplateBase(BaseModel):
    """Base phishing template schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=500)
    sender_name: str = Field(..., min_length=1, max_length=255)
    sender_email: str = Field(..., min_length=1, max_length=255)
    body_html: str = Field(..., min_length=1)
    body_text: Optional[str] = None
    landing_page_html: Optional[str] = None
    landing_page_url: Optional[str] = None
    difficulty: Optional[str] = "medium"
    red_flags: Optional[List[str]] = []


class PhishingTemplateCreate(PhishingTemplateBase):
    """Schema for creating a template."""
    pass


class PhishingTemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    sender_name: Optional[str] = Field(None, min_length=1, max_length=255)
    sender_email: Optional[str] = Field(None, min_length=1, max_length=255)
    body_html: Optional[str] = Field(None, min_length=1)
    body_text: Optional[str] = None
    landing_page_html: Optional[str] = None
    landing_page_url: Optional[str] = None
    difficulty: Optional[str] = None
    red_flags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PhishingTemplateResponse(PhishingTemplateBase):
    """Schema for template response."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Usage stats
    campaigns_count: Optional[int] = 0

    class Config:
        from_attributes = True


class PhishingTemplateListResponse(BaseModel):
    """Schema for template list."""
    items: List[PhishingTemplateResponse]
    total: int
    page: int
    size: int
    pages: int


class PhishingCampaignBase(BaseModel):
    """Base campaign schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    target_departments: Optional[List[str]] = []
    target_user_ids: Optional[List[str]] = []
    exclude_user_ids: Optional[List[str]] = []
    send_window_start_hour: Optional[int] = Field(9, ge=0, le=23)
    send_window_end_hour: Optional[int] = Field(17, ge=0, le=23)
    randomize_send_time: Optional[bool] = True
    training_course_id: Optional[str] = None
    auto_enroll_on_fail: Optional[bool] = True


class PhishingCampaignCreate(PhishingCampaignBase):
    """Schema for creating a campaign."""
    template_id: str


class PhishingCampaignUpdate(BaseModel):
    """Schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    target_departments: Optional[List[str]] = None
    target_user_ids: Optional[List[str]] = None
    exclude_user_ids: Optional[List[str]] = None
    send_window_start_hour: Optional[int] = Field(None, ge=0, le=23)
    send_window_end_hour: Optional[int] = Field(None, ge=0, le=23)
    randomize_send_time: Optional[bool] = None
    training_course_id: Optional[str] = None
    auto_enroll_on_fail: Optional[bool] = None


class PhishingCampaignResponse(PhishingCampaignBase):
    """Schema for campaign response."""
    id: str
    template_id: str
    status: CampaignStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    total_targets: int
    emails_sent: int
    emails_opened: int
    links_clicked: int
    credentials_submitted: int
    reported_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    # Computed
    template_name: Optional[str] = None
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    report_rate: Optional[float] = None

    class Config:
        from_attributes = True


class PhishingCampaignListResponse(BaseModel):
    """Schema for campaign list."""
    items: List[PhishingCampaignResponse]
    total: int
    page: int
    size: int
    pages: int


class PhishingTargetResponse(BaseModel):
    """Schema for phishing target response."""
    id: str
    campaign_id: str
    user_id: str
    tracking_id: str
    result: PhishingResult
    email_sent_at: Optional[datetime] = None
    email_opened_at: Optional[datetime] = None
    link_clicked_at: Optional[datetime] = None
    credentials_submitted_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    training_assigned: bool
    created_at: datetime

    # User info
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_department: Optional[str] = None

    class Config:
        from_attributes = True


class PhishingCampaignResultsResponse(BaseModel):
    """Schema for campaign results."""
    campaign: PhishingCampaignResponse
    targets: List[PhishingTargetResponse]
    total: int
    page: int
    size: int
    pages: int

    # Summary stats
    results_by_status: dict  # {status: count}


class PhishingTrackEvent(BaseModel):
    """Schema for tracking phishing events (internal)."""
    tracking_id: str
    event_type: str  # "open", "click", "submit"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    submitted_data: Optional[dict] = None


# ============================================================================
# Badge & Gamification Schemas
# ============================================================================

class BadgeBase(BaseModel):
    """Base badge schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    category: BadgeCategory
    icon: Optional[str] = "award"
    color: Optional[str] = "gold"
    criteria: dict = {}
    points: Optional[int] = Field(10, ge=0, le=100)
    is_rare: Optional[bool] = False


class BadgeCreate(BadgeBase):
    """Schema for creating a badge."""
    pass


class BadgeUpdate(BaseModel):
    """Schema for updating a badge."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[BadgeCategory] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    criteria: Optional[dict] = None
    points: Optional[int] = Field(None, ge=0, le=100)
    is_rare: Optional[bool] = None
    is_active: Optional[bool] = None


class BadgeResponse(BadgeBase):
    """Schema for badge response."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Stats
    earned_count: Optional[int] = 0

    class Config:
        from_attributes = True


class BadgeListResponse(BaseModel):
    """Schema for badge list."""
    items: List[BadgeResponse]
    total: int


class UserBadgeResponse(BaseModel):
    """Schema for user's earned badge."""
    id: str
    badge_id: str
    user_id: str
    earned_at: datetime
    earned_for: Optional[str] = None

    # Badge details
    badge_name: str
    badge_description: str
    badge_category: BadgeCategory
    badge_icon: str
    badge_color: str
    badge_points: int
    badge_is_rare: bool

    class Config:
        from_attributes = True


class UserBadgesResponse(BaseModel):
    """Schema for user's badges."""
    items: List[UserBadgeResponse]
    total: int
    total_points: int


# ============================================================================
# Leaderboard & Stats Schemas
# ============================================================================

class TrainingStatsResponse(BaseModel):
    """Schema for user training stats."""
    user_id: str
    user_name: Optional[str] = None
    courses_completed: int
    courses_in_progress: int
    modules_completed: int
    quizzes_passed: int
    total_points: int
    average_quiz_score: float
    total_training_time_minutes: int
    current_streak_days: int
    longest_streak_days: int
    last_activity_date: Optional[date] = None
    phishing_tests_received: int
    phishing_emails_reported: int
    phishing_links_clicked: int
    badges_earned: int
    rank: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry."""
    rank: int
    user_id: str
    user_name: str
    user_avatar: Optional[str] = None
    department: Optional[str] = None
    total_points: int
    courses_completed: int
    badges_earned: int
    current_streak_days: int


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard."""
    entries: List[LeaderboardEntry]
    total_users: int
    period: str  # "all_time", "monthly", "weekly"

    # Current user's position if not in top
    current_user_rank: Optional[int] = None
    current_user_points: Optional[int] = None


# ============================================================================
# Dashboard & Reports Schemas
# ============================================================================

class TrainingDashboardStats(BaseModel):
    """Dashboard statistics for Security Awareness."""
    # Courses
    total_courses: int
    published_courses: int
    draft_courses: int
    courses_by_category: dict

    # Enrollments
    total_enrollments: int
    enrollments_in_progress: int
    enrollments_completed: int
    enrollments_overdue: int
    completion_rate: float
    average_quiz_score: float

    # User-specific
    my_courses_in_progress: int
    my_courses_completed: int
    my_pending_assignments: int
    my_overdue_assignments: int

    # Phishing
    active_campaigns: int
    completed_campaigns: int
    overall_phishing_click_rate: float
    overall_phishing_report_rate: float

    # Gamification
    my_total_points: int
    my_rank: Optional[int] = None
    my_badges: int


class CourseComplianceReport(BaseModel):
    """Schema for course compliance."""
    course_id: str
    course_title: str
    course_category: CourseCategory
    is_mandatory: bool

    total_assigned: int
    completed: int
    in_progress: int
    not_started: int
    overdue: int
    compliance_rate: float
    average_score: Optional[float] = None


class DepartmentComplianceReport(BaseModel):
    """Schema for department compliance."""
    department: str
    total_users: int
    total_required_trainings: int
    completed_trainings: int
    in_progress_trainings: int
    overdue_trainings: int
    compliance_rate: float
    average_score: Optional[float] = None

    # Phishing
    phishing_tests: int
    phishing_clicks: int
    phishing_reports: int


class ComplianceReportResponse(BaseModel):
    """Schema for training compliance report."""
    generated_at: datetime
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # Overall stats
    total_users: int
    total_required_trainings: int
    completed_trainings: int
    compliance_rate: float

    # By course
    courses: List[CourseComplianceReport]

    # By department
    departments: List[DepartmentComplianceReport]


class PhishingAnalyticsResponse(BaseModel):
    """Schema for phishing analytics."""
    period: str
    campaigns_count: int
    total_emails_sent: int
    overall_open_rate: float
    overall_click_rate: float
    overall_report_rate: float

    # Trends
    click_rate_trend: List[dict]  # [{date, rate}]
    report_rate_trend: List[dict]

    # By difficulty
    results_by_difficulty: dict  # {difficulty: {sent, clicked, reported}}

    # Top reporters
    top_reporters: List[dict]  # [{user_id, user_name, reports_count}]


# Forward reference updates
CourseResponse.model_rebuild()
