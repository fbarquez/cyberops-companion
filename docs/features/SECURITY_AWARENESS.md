# Security Awareness & Training

Complete security awareness and training platform for employee education, phishing simulation, gamification, and compliance tracking. Essential component of an ISMS (Information Security Management System) for ISO 27001:2022 compliance.

## Overview

The Security Awareness & Training module provides:
- Course management with video, text, and interactive content
- Module-based learning with progress tracking
- Quiz system with multiple question types
- Phishing simulation campaigns
- Gamification with badges, points, and leaderboards
- Compliance reporting for training completion
- User enrollment and deadline management
- Multi-language support (EN/DE)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               Security Awareness & Training Module               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │    Courses       │  │    Modules       │  │   Quizzes    │  │
│  │  - Categories    │  │  - Video/Text    │  │  - Questions │  │
│  │  - Difficulty    │  │  - Interactive   │  │  - Attempts  │  │
│  │  - Compliance    │  │  - Documents     │  │  - Scoring   │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                               │
│                                 ▼                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    TrainingService                        │  │
│  │  - Enrollment management (enroll, bulk assign)            │  │
│  │  - Progress tracking (module completion, time spent)      │  │
│  │  - Quiz scoring (auto-grade, attempt limits)              │  │
│  │  - Compliance reporting                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                 │                               │
│           ┌─────────────────────┼─────────────────────┐        │
│           │                     │                     │        │
│           ▼                     ▼                     ▼        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Gamification   │  │    Phishing      │  │  Reporting   │  │
│  │  - Badges        │  │  - Templates     │  │  - Dashboard │  │
│  │  - Points        │  │  - Campaigns     │  │  - Compliance│  │
│  │  - Leaderboard   │  │  - Tracking      │  │  - Analytics │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Course Categories

```python
class CourseCategory(str, enum.Enum):
    SECURITY_FUNDAMENTALS = "security_fundamentals"  # Basic security concepts
    PHISHING_AWARENESS = "phishing_awareness"        # Email/SMS threats
    DATA_PROTECTION = "data_protection"              # GDPR, data handling
    PASSWORD_SECURITY = "password_security"          # Credentials management
    SOCIAL_ENGINEERING = "social_engineering"        # Human-based attacks
    COMPLIANCE = "compliance"                        # Regulatory training
    INCIDENT_RESPONSE = "incident_response"          # Report & respond
    SECURE_CODING = "secure_coding"                  # Developer-focused
```

## Database Models

### 1. TrainingCourse

Main course entity with metadata, learning objectives, and compliance mapping.

```python
class TrainingCourse(TenantMixin, Base):
    id: UUID
    tenant_id: FK → organizations.id

    # Identification
    course_code: str          # e.g., "SEC-001", "PHI-002"
    title: str
    description: str
    category: CourseCategory
    difficulty: CourseDifficulty  # beginner, intermediate, advanced
    status: CourseStatus          # draft, published, archived

    # Configuration
    estimated_duration_minutes: int
    passing_score: int = 80       # Quiz pass threshold
    certificate_enabled: bool
    is_mandatory: bool

    # Learning objectives
    objectives: JSON              # List of learning outcomes

    # Targeting
    target_roles: JSON            # Roles required to take
    target_departments: JSON

    # Compliance mapping
    compliance_frameworks: JSON   # ["iso27001", "nis2"]
    control_references: JSON      # ["A.7.2.2", "A.6.3"]
```

### 2. TrainingModule

Individual learning units within a course.

```python
class ModuleType(str, enum.Enum):
    VIDEO = "video"                # Video content
    TEXT = "text"                  # Written content
    INTERACTIVE = "interactive"   # Interactive exercises
    QUIZ = "quiz"                  # Quiz/assessment
    DOCUMENT = "document"          # PDF/document download
    EXTERNAL_LINK = "external_link"  # External resource

class TrainingModule(TenantMixin, Base):
    id: UUID
    course_id: FK → training_courses.id

    # Content
    title: str
    description: str
    module_type: ModuleType
    content: Text                  # HTML/Markdown content
    video_url: str                 # For video modules
    external_url: str              # For external links
    attachment_id: FK              # For documents

    # Configuration
    order_index: int               # Module sequence
    estimated_duration_minutes: int
    is_required: bool = True
    quiz_id: FK                    # Optional linked quiz
```

### 3. Quiz & QuizQuestion

Assessment system with multiple question types.

```python
class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"    # One correct answer
    MULTIPLE_CHOICE = "multiple_choice"  # Multiple correct
    TRUE_FALSE = "true_false"          # Boolean
    MATCHING = "matching"              # Pair matching
    SHORT_ANSWER = "short_answer"      # Text input

class QuizQuestion(TenantMixin, Base):
    id: UUID
    quiz_id: FK → quizzes.id

    question_type: QuestionType
    question_text: str
    options: JSON                  # Answer options
    correct_answers: JSON          # Correct answer indices
    explanation: str               # Post-answer explanation
    points: int = 1
    order_index: int
```

### 4. TrainingEnrollment

Tracks user enrollments and progress.

```python
class EnrollmentStatus(str, enum.Enum):
    ENROLLED = "enrolled"          # Just enrolled
    IN_PROGRESS = "in_progress"   # Started learning
    COMPLETED = "completed"       # Finished course
    FAILED = "failed"             # Failed quiz
    EXPIRED = "expired"           # Past deadline

class TrainingEnrollment(TenantMixin, Base):
    id: UUID
    user_id: FK → users.id
    course_id: FK → training_courses.id

    status: EnrollmentStatus
    progress_percent: float = 0

    # Timing
    enrolled_at: datetime
    started_at: datetime
    completed_at: datetime
    deadline: datetime            # Assignment deadline

    # Results
    quiz_score: float
    attempts_used: int
    certificate_issued: bool
    certificate_issued_at: datetime
```

### 5. PhishingCampaign & PhishingTarget

Simulated phishing for awareness testing.

```python
class PhishingCampaign(TenantMixin, Base):
    id: UUID
    name: str
    description: str
    template_id: FK → phishing_templates.id
    status: CampaignStatus        # draft, scheduled, running, completed

    # Schedule
    scheduled_start: datetime
    scheduled_end: datetime

    # Targeting
    target_users: JSON            # Specific user IDs
    target_roles: JSON            # Role-based targeting
    target_departments: JSON

    # Results
    emails_sent: int
    emails_opened: int
    links_clicked: int
    data_submitted: int           # Clicked + entered data

class PhishingTarget(TenantMixin, Base):
    id: UUID
    campaign_id: FK
    user_id: FK

    tracking_id: str              # Unique tracking token
    email_sent_at: datetime
    email_opened_at: datetime
    link_clicked_at: datetime
    data_submitted_at: datetime
    reported_at: datetime         # User reported as phishing

    result: PhishingResult        # sent, opened, clicked, submitted, reported
```

### 6. Gamification (Badge & UserBadge)

Achievement and recognition system.

```python
class BadgeCategory(str, enum.Enum):
    COMPLETION = "completion"      # Course completion
    ACHIEVEMENT = "achievement"   # Special accomplishments
    STREAK = "streak"             # Consistency
    SPECIAL = "special"           # Event-based

class Badge(TenantMixin, Base):
    id: UUID
    name: str
    description: str
    category: BadgeCategory
    icon: str                     # Icon name
    color: str                    # Hex color
    points_value: int             # Points awarded

    # Automatic criteria
    criteria: JSON                # {"type": "courses_completed", "value": 5}

class UserBadge(TenantMixin, Base):
    id: UUID
    user_id: FK
    badge_id: FK
    awarded_at: datetime
    awarded_reason: str
```

## API Endpoints (~35)

### Courses & Modules
```
GET    /training/catalog              # Public course catalog
GET    /training/courses              # Admin: list all courses
POST   /training/courses              # Create course
GET    /training/courses/{id}         # Get course details
PUT    /training/courses/{id}         # Update course
DELETE /training/courses/{id}         # Delete course
POST   /training/courses/{id}/publish # Publish course

GET    /training/courses/{id}/modules # List course modules
POST   /training/courses/{id}/modules # Create module
GET    /training/modules/{id}         # Get module
PUT    /training/modules/{id}         # Update module
DELETE /training/modules/{id}         # Delete module
```

### Enrollment & Progress
```
POST   /training/enroll/{course_id}   # Self-enroll
POST   /training/courses/{id}/bulk-enroll  # Bulk assignment
GET    /training/my-learning          # Current user's enrollments

GET    /training/modules/{id}/progress    # Get progress
POST   /training/modules/{id}/progress    # Update progress
POST   /training/modules/{id}/complete    # Mark complete
```

### Quizzes
```
GET    /training/quizzes/{id}             # Get quiz info
GET    /training/quizzes/{id}/questions   # Get questions (for attempt)
POST   /training/quizzes/{id}/start       # Start attempt
POST   /training/quizzes/attempts/{id}/submit  # Submit answers
GET    /training/quizzes/attempts/{id}    # Get attempt results
```

### Gamification
```
GET    /training/leaderboard          # Get leaderboard
GET    /training/my-stats             # Current user stats
GET    /training/my-badges            # Current user badges
GET    /training/badges               # List all badges
POST   /training/badges               # Create badge (admin)
POST   /training/users/{id}/badges/{badge_id}  # Award badge
```

### Phishing Campaigns
```
GET    /phishing/templates            # List templates
POST   /phishing/templates            # Create template
GET    /phishing/campaigns            # List campaigns
POST   /phishing/campaigns            # Create campaign
GET    /phishing/campaigns/{id}       # Campaign details
POST   /phishing/campaigns/{id}/launch  # Launch campaign
GET    /phishing/campaigns/{id}/results  # Campaign results
GET    /phishing/track/{tracking_id}  # Tracking pixel/link
```

### Reports
```
GET    /training/dashboard            # Dashboard stats
GET    /training/compliance-report    # Compliance report
```

## Frontend Pages

### 1. Training Catalog (`/training`)

```
┌─────────────────────────────────────────────────────────────┐
│  Security Awareness Training                                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Courses │ │ Quizzes │ │ Points  │ │ Badges  │           │
│  │   12    │ │    8    │ │  2,450  │ │    5    │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────────────────┤
│  Tabs: [Catalog] [My Learning] [Leaderboard]                │
├─────────────────────────────────────────────────────────────┤
│  Category: [All ▾]  Difficulty: [All ▾]  🔍 Search         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ 🔒 Security         │  │ 🎣 Phishing         │          │
│  │ Fundamentals        │  │ Awareness           │          │
│  │                     │  │                     │          │
│  │ Beginner · 45 min   │  │ Beginner · 30 min   │          │
│  │ 5 modules           │  │ 4 modules           │          │
│  │ ISO 27001 A.7.2.2   │  │ ISO 27001 A.7.2.2   │          │
│  │                     │  │                     │          │
│  │ [Start Learning]    │  │ [Continue →]  65%   │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Course Detail (`/training/[id]`)

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back   Security Fundamentals                    SEC-001  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────┐ ┌───────────────┐ │
│  │ Description...                       │ │ Your Progress │ │
│  │                                     │ │               │ │
│  │ ⏱ 45 minutes · 📚 5 modules        │ │    65%        │ │
│  │ 🎯 80% to pass · 🏆 Certificate    │ │  ████████░░   │ │
│  │                                     │ │               │ │
│  │ Learning Objectives:                │ │ 3/5 modules   │ │
│  │ ✓ Understand security principles   │ │               │ │
│  │ ✓ Identify common threats          │ │ [Continue →]  │ │
│  │ ✓ Apply security best practices    │ └───────────────┘ │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  Course Content                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ 1. Introduction to Security        │ Video │ 10m │   │
│  │ ✓ 2. Common Threats & Attacks        │ Text  │ 15m │   │
│  │ ✓ 3. Password Best Practices         │ Video │ 8m  │   │
│  │ → 4. Social Engineering Defense      │ Text  │ 12m │   │
│  │ ○ 5. Final Assessment               │ Quiz  │ 10m │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Module Viewer (`/training/[id]/module/[moduleId]`)

```
┌─────────────────────────────────────────────────────────────┐
│  ← Course   Module 4: Social Engineering Defense            │
│             Video · 12 minutes                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │              [Video Player Area]                    │   │
│  │                                                     │   │
│  │                    ▶️ Play                          │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Progress: ████████████████░░░░  80%                       │
│  Time spent: 9:45                                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Ready to complete this module?                      │   │
│  │ Mark as complete to track your progress.            │   │
│  │                                    [Mark Complete ✓]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [← Previous]                              [Next Module →]  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Compliance Mapping

The training module supports mapping courses to compliance frameworks:

| Framework | Control | Description |
|-----------|---------|-------------|
| ISO 27001:2022 | A.6.3 | Information security awareness, education and training |
| ISO 27001:2022 | A.7.2.2 | Information security awareness, education and training |
| NIS2 | Art. 21.2.g | Basic cyber hygiene practices and cybersecurity training |
| BSI IT-Grundschutz | ORP.3 | Awareness and Training |

## Gamification System

### Points Calculation
- Course completion: 100 base points × difficulty multiplier
- Quiz passing: 50 points + bonus for score above 90%
- Daily login streak: 10 points/day
- Phishing report (correct): 25 points
- Badge earned: badge point value

### Badge Criteria Examples
```json
// First Course Completed
{"type": "courses_completed", "value": 1}

// Perfect Quiz Score
{"type": "quiz_score", "value": 100}

// 7-Day Learning Streak
{"type": "streak_days", "value": 7}

// Phishing Reporter (5 reports)
{"type": "phishing_reports", "value": 5}
```

### Leaderboard
- Displays top 100 learners
- Filterable by department, time period
- Shows rank, name, points, badges, streak

## Phishing Simulation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Create    │────▶│   Launch    │────▶│   Track     │
│  Campaign   │     │  Campaign   │     │  Results    │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
 Select template    Send emails         Record events:
 Target users       with tracking       - Email opened
 Set schedule       URLs/pixels         - Link clicked
                                        - Data submitted
                                        - Reported
```

### Tracking Events
1. **Email Sent**: Initial delivery
2. **Email Opened**: Tracking pixel loaded
3. **Link Clicked**: User clicked phishing link
4. **Data Submitted**: User entered credentials
5. **Reported**: User reported as phishing (positive!)

## Files Created

### Backend
- `apps/api/src/models/awareness.py` - SQLAlchemy models
- `apps/api/src/schemas/awareness.py` - Pydantic schemas
- `apps/api/src/services/training_service.py` - Business logic
- `apps/api/src/api/v1/training.py` - API endpoints
- `apps/api/alembic/versions/i9j0k1l2m3n4_add_awareness_tables.py` - Migration

### Frontend
- `apps/web/app/(dashboard)/training/page.tsx` - Catalog & My Learning
- `apps/web/app/(dashboard)/training/[id]/page.tsx` - Course detail
- `apps/web/app/(dashboard)/training/[id]/module/[moduleId]/page.tsx` - Module viewer
- `apps/web/lib/api-client.ts` - trainingAPI functions

### Translations
- EN/DE translations added to `apps/web/i18n/translations.ts`

## Testing

```bash
# Run backend tests
cd apps/api
pytest tests/test_training.py -v

# Run migration
alembic upgrade head

# Start development server
uvicorn src.main:app --reload
```

## Security Considerations

1. **Phishing Campaigns**: Only accessible to admin users
2. **Quiz Answers**: Never exposed in frontend until submission
3. **Tracking Links**: Use secure tokens, not user IDs
4. **Certificate Generation**: Server-side only, with verification
5. **Progress Data**: User can only update their own progress
