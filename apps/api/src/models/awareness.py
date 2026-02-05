"""
Security Awareness & Training Models.

Database models for Training Courses, Modules, Quizzes,
Phishing Campaigns, Gamification, and Compliance Tracking.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Date, Text, Integer, Boolean, Float,
    ForeignKey, Enum as SQLEnum, JSON, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from src.db.database import Base
from src.models.mixins import TenantMixin


# ============================================================================
# Enums
# ============================================================================

class CourseCategory(str, enum.Enum):
    """Training course category."""
    SECURITY_FUNDAMENTALS = "security_fundamentals"
    PHISHING_AWARENESS = "phishing_awareness"
    DATA_PROTECTION = "data_protection"
    PASSWORD_SECURITY = "password_security"
    SOCIAL_ENGINEERING = "social_engineering"
    COMPLIANCE = "compliance"
    INCIDENT_RESPONSE = "incident_response"
    PHYSICAL_SECURITY = "physical_security"
    MOBILE_SECURITY = "mobile_security"
    CLOUD_SECURITY = "cloud_security"
    PRIVACY = "privacy"
    CUSTOM = "custom"


class CourseDifficulty(str, enum.Enum):
    """Course difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatus(str, enum.Enum):
    """Course publication status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ModuleType(str, enum.Enum):
    """Training module content type."""
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    DOCUMENT = "document"
    EXTERNAL_LINK = "external_link"


class QuestionType(str, enum.Enum):
    """Quiz question type."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"


class EnrollmentStatus(str, enum.Enum):
    """User enrollment status."""
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    DROPPED = "dropped"


class CampaignStatus(str, enum.Enum):
    """Phishing campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PhishingResult(str, enum.Enum):
    """Individual phishing test result."""
    PENDING = "pending"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPORTED = "reported"
    NO_ACTION = "no_action"


class BadgeCategory(str, enum.Enum):
    """Badge/achievement category."""
    COMPLETION = "completion"
    STREAK = "streak"
    PERFORMANCE = "performance"
    PHISHING = "phishing"
    MILESTONE = "milestone"
    SPECIAL = "special"


# ============================================================================
# Association Tables
# ============================================================================

course_prerequisite = Table(
    'course_prerequisites',
    Base.metadata,
    Column('course_id', String(36), ForeignKey('training_courses.id'), primary_key=True),
    Column('prerequisite_id', String(36), ForeignKey('training_courses.id'), primary_key=True)
)


# ============================================================================
# Models
# ============================================================================

class TrainingCourse(TenantMixin, Base):
    """Training course catalog."""
    __tablename__ = "training_courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identification
    course_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g., SAT-001
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Classification
    category = mapped_column(SQLEnum(CourseCategory), nullable=False, index=True)
    difficulty = mapped_column(SQLEnum(CourseDifficulty), default=CourseDifficulty.BEGINNER)
    status = mapped_column(SQLEnum(CourseStatus), default=CourseStatus.DRAFT, index=True)

    # Course details
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)  # Total course duration
    passing_score: Mapped[int] = mapped_column(Integer, default=80)  # Minimum % to pass
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)  # Quiz retry attempts
    certificate_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Content
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    objectives = mapped_column(JSON, default=[])  # Learning objectives
    target_audience = mapped_column(JSON, default=[])  # e.g., ["all_employees", "it_staff"]
    tags = mapped_column(JSON, default=[])

    # Compliance mapping
    compliance_frameworks = mapped_column(JSON, default=[])  # e.g., ["iso27001", "gdpr"]
    control_references = mapped_column(JSON, default=[])  # e.g., ["A.7.2.2"]
    mandatory_for = mapped_column(JSON, default=[])  # Departments where mandatory

    # Scheduling
    recurrence_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Days until re-training needed
    deadline_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Days to complete after assignment

    # Publishing
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Metadata
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    modules = relationship("TrainingModule", back_populates="course", cascade="all, delete-orphan", order_by="TrainingModule.order")
    enrollments = relationship("TrainingEnrollment", back_populates="course", cascade="all, delete-orphan")
    prerequisites = relationship(
        "TrainingCourse",
        secondary=course_prerequisite,
        primaryjoin=id == course_prerequisite.c.course_id,
        secondaryjoin=id == course_prerequisite.c.prerequisite_id,
    )


class TrainingModule(TenantMixin, Base):
    """Training module (lesson) within a course."""
    __tablename__ = "training_modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_courses.id"), nullable=False)

    # Identification
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Content type and data
    module_type = mapped_column(SQLEnum(ModuleType), nullable=False)
    content = mapped_column(JSON, nullable=True)  # Structured content based on type
    # For VIDEO: {"url": "...", "duration_seconds": 300, "transcript": "..."}
    # For TEXT: {"html": "...", "markdown": "..."}
    # For QUIZ: {"questions": [...]} - links to Quiz model
    # For EXTERNAL_LINK: {"url": "...", "description": "..."}

    # Order and navigation
    order: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=10)

    # Requirements
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_completion_to_proceed: Mapped[bool] = mapped_column(Boolean, default=True)

    # Attachments
    attachment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("attachments.id"), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("TrainingCourse", back_populates="modules")
    quiz = relationship("Quiz", back_populates="module", uselist=False, cascade="all, delete-orphan")
    progress = relationship("ModuleProgress", back_populates="module", cascade="all, delete-orphan")


class Quiz(TenantMixin, Base):
    """Quiz for a training module."""
    __tablename__ = "training_quizzes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_modules.id"), nullable=False, unique=True)

    # Quiz settings
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = no limit
    passing_score: Mapped[int] = mapped_column(Integer, default=80)  # Percentage
    randomize_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    randomize_answers: Mapped[bool] = mapped_column(Boolean, default=True)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True)  # After completion
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    module = relationship("TrainingModule", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(TenantMixin, Base):
    """Question in a quiz."""
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    quiz_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_quizzes.id"), nullable=False)

    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type = mapped_column(SQLEnum(QuestionType), default=QuestionType.SINGLE_CHOICE)

    # Options for multiple choice (JSON array)
    # [{"id": "a", "text": "Option A", "is_correct": true}, ...]
    options = mapped_column(JSON, nullable=False, default=[])

    # For matching questions
    # {"left": ["A", "B"], "right": ["1", "2"], "correct_pairs": {"A": "1", "B": "2"}}
    matching_data = mapped_column(JSON, nullable=True)

    # Explanation shown after answering
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scoring
    points: Mapped[int] = mapped_column(Integer, default=1)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")


class TrainingEnrollment(TenantMixin, Base):
    """User enrollment in a training course."""
    __tablename__ = "training_enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_courses.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Status
    status = mapped_column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ENROLLED, index=True)

    # Progress
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    modules_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_modules: Mapped[int] = mapped_column(Integer, default=0)

    # Scores
    highest_quiz_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_quiz_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timing
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Completion
    certificate_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Assignment context
    assigned_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assignment_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., "Annual compliance"

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("TrainingCourse", back_populates="enrollments")
    user = relationship("User", foreign_keys=[user_id])
    module_progress = relationship("ModuleProgress", back_populates="enrollment", cascade="all, delete-orphan")


class ModuleProgress(TenantMixin, Base):
    """User progress on individual modules."""
    __tablename__ = "module_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    enrollment_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_enrollments.id"), nullable=False)
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_modules.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Progress
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # For video modules
    last_position_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollment = relationship("TrainingEnrollment", back_populates="module_progress")
    module = relationship("TrainingModule", back_populates="progress")


class QuizAttempt(TenantMixin, Base):
    """User attempt at a quiz."""
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    quiz_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_quizzes.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    enrollment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("training_enrollments.id"), nullable=True)

    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)

    # Results
    score: Mapped[float] = mapped_column(Float, default=0.0)  # Percentage
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    points_possible: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Answers
    answers = mapped_column(JSON, default=[])  # [{question_id, answer, is_correct}]

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", foreign_keys=[user_id])


# ============================================================================
# Phishing Simulation Models
# ============================================================================

class PhishingTemplate(TenantMixin, Base):
    """Email template for phishing simulations."""
    __tablename__ = "phishing_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "credential_harvest", "malware"

    # Email content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Landing page (for credential harvesting)
    landing_page_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    landing_page_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Difficulty indicator (how convincing)
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")  # easy, medium, hard

    # Indicators for training (what to look for)
    red_flags = mapped_column(JSON, default=[])  # ["suspicious sender", "urgency", "spelling errors"]

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    campaigns = relationship("PhishingCampaign", back_populates="template")


class PhishingCampaign(TenantMixin, Base):
    """Phishing simulation campaign."""
    __tablename__ = "phishing_campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    template_id: Mapped[str] = mapped_column(String(36), ForeignKey("phishing_templates.id"), nullable=False)

    # Campaign info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status = mapped_column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, index=True)

    # Scheduling
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Target audience
    target_departments = mapped_column(JSON, default=[])  # Empty = all
    target_user_ids = mapped_column(JSON, default=[])  # Specific users
    exclude_user_ids = mapped_column(JSON, default=[])  # Exclusions

    # Sending configuration
    send_window_start_hour: Mapped[int] = mapped_column(Integer, default=9)  # 9 AM
    send_window_end_hour: Mapped[int] = mapped_column(Integer, default=17)  # 5 PM
    randomize_send_time: Mapped[bool] = mapped_column(Boolean, default=True)

    # Results summary (cached for performance)
    total_targets: Mapped[int] = mapped_column(Integer, default=0)
    emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    emails_opened: Mapped[int] = mapped_column(Integer, default=0)
    links_clicked: Mapped[int] = mapped_column(Integer, default=0)
    credentials_submitted: Mapped[int] = mapped_column(Integer, default=0)
    reported_count: Mapped[int] = mapped_column(Integer, default=0)

    # Training integration
    training_course_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("training_courses.id"), nullable=True)
    auto_enroll_on_fail: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    template = relationship("PhishingTemplate", back_populates="campaigns")
    targets = relationship("PhishingTarget", back_populates="campaign", cascade="all, delete-orphan")


class PhishingTarget(TenantMixin, Base):
    """Individual target in a phishing campaign."""
    __tablename__ = "phishing_targets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("phishing_campaigns.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Unique tracking
    tracking_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # For tracking clicks

    # Status
    result = mapped_column(SQLEnum(PhishingResult), default=PhishingResult.PENDING, index=True)

    # Events
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    email_opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    link_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    credentials_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Submitted data (if credential harvesting)
    submitted_data = mapped_column(JSON, nullable=True)  # Sanitized, no actual passwords stored

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Training triggered
    training_assigned: Mapped[bool] = mapped_column(Boolean, default=False)
    training_enrollment_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("PhishingCampaign", back_populates="targets")
    user = relationship("User", foreign_keys=[user_id])


# ============================================================================
# Gamification Models
# ============================================================================

class Badge(TenantMixin, Base):
    """Achievement badge definition."""
    __tablename__ = "training_badges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Badge info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category = mapped_column(SQLEnum(BadgeCategory), nullable=False)

    # Visual
    icon: Mapped[str] = mapped_column(String(50), default="award")  # Lucide icon name
    color: Mapped[str] = mapped_column(String(50), default="gold")

    # Criteria (JSON for flexibility)
    # Examples:
    # {"type": "courses_completed", "count": 5}
    # {"type": "quiz_score", "min_score": 100, "course_id": "..."}
    # {"type": "phishing_reported", "count": 3}
    # {"type": "streak_days", "count": 7}
    criteria = mapped_column(JSON, nullable=False, default={})

    # Points
    points: Mapped[int] = mapped_column(Integer, default=10)

    # Rarity
    is_rare: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    earned_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(TenantMixin, Base):
    """Badge earned by a user."""
    __tablename__ = "user_badges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    badge_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_badges.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Context
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    earned_for: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., course name

    # Notification
    notified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    badge = relationship("Badge", back_populates="earned_badges")
    user = relationship("User", foreign_keys=[user_id])


class TrainingStats(TenantMixin, Base):
    """Aggregated training statistics per user (for leaderboard)."""
    __tablename__ = "training_stats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # Progress
    courses_completed: Mapped[int] = mapped_column(Integer, default=0)
    courses_in_progress: Mapped[int] = mapped_column(Integer, default=0)
    modules_completed: Mapped[int] = mapped_column(Integer, default=0)
    quizzes_passed: Mapped[int] = mapped_column(Integer, default=0)

    # Scores
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    average_quiz_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Time
    total_training_time_minutes: Mapped[int] = mapped_column(Integer, default=0)

    # Streaks
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Phishing
    phishing_tests_received: Mapped[int] = mapped_column(Integer, default=0)
    phishing_emails_reported: Mapped[int] = mapped_column(Integer, default=0)
    phishing_links_clicked: Mapped[int] = mapped_column(Integer, default=0)

    # Badges
    badges_earned: Mapped[int] = mapped_column(Integer, default=0)

    # Rank (updated periodically)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
