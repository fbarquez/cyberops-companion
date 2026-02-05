"""Security Awareness & Training API endpoints."""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.awareness import (
    CourseCategory, CourseDifficulty, CourseStatus,
    CampaignStatus, BadgeCategory
)
from src.schemas.awareness import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    CourseCatalogResponse,
    ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse, ModuleContentResponse,
    QuizCreate, QuizUpdate, QuizResponse, QuizDetailResponse,
    QuizStudentView, QuizStartResponse, QuizSubmitRequest, QuizAttemptResponse,
    QuizQuestionCreate, QuizQuestionResponse,
    EnrollmentCreate, BulkEnrollmentRequest, EnrollmentResponse, EnrollmentListResponse,
    MyLearningResponse, ModuleProgressUpdate, ModuleProgressResponse,
    PhishingTemplateCreate, PhishingTemplateUpdate, PhishingTemplateResponse, PhishingTemplateListResponse,
    PhishingCampaignCreate, PhishingCampaignUpdate, PhishingCampaignResponse, PhishingCampaignListResponse,
    PhishingCampaignResultsResponse,
    BadgeCreate, BadgeUpdate, BadgeResponse, BadgeListResponse, UserBadgesResponse,
    TrainingStatsResponse, LeaderboardResponse,
    TrainingDashboardStats,
)
from src.services.training_service import TrainingService

router = APIRouter(prefix="/training")


# ============================================================================
# Dashboard
# ============================================================================

@router.get("/dashboard", response_model=TrainingDashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get training dashboard statistics."""
    service = TrainingService(db)
    return await service.get_dashboard_stats(user_id=current_user.id)


@router.get("/stats", response_model=TrainingDashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias for dashboard stats."""
    service = TrainingService(db)
    return await service.get_dashboard_stats(user_id=current_user.id)


# ============================================================================
# Course CRUD
# ============================================================================

@router.post("/courses", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new training course."""
    service = TrainingService(db)
    course = await service.create_course(data, created_by=current_user.id)
    return CourseResponse.model_validate(course)


@router.get("/courses", response_model=CourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[CourseCategory] = None,
    difficulty: Optional[CourseDifficulty] = None,
    status: Optional[CourseStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List training courses with filtering."""
    service = TrainingService(db)
    return await service.list_courses(
        page=page,
        size=size,
        category=category,
        difficulty=difficulty,
        status=status,
        search=search,
    )


@router.get("/catalog", response_model=CourseCatalogResponse)
async def get_course_catalog(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[CourseCategory] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get course catalog with user enrollment status."""
    service = TrainingService(db)
    return await service.get_course_catalog(
        user_id=current_user.id,
        page=page,
        size=size,
        category=category,
    )


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a training course by ID."""
    service = TrainingService(db)
    course = await service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse.model_validate(course)


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a training course."""
    service = TrainingService(db)
    course = await service.update_course(course_id, data)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse.model_validate(course)


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a training course."""
    service = TrainingService(db)
    success = await service.delete_course(course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}


@router.post("/courses/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publish a course making it available for enrollment."""
    service = TrainingService(db)
    try:
        course = await service.publish_course(course_id, published_by=current_user.id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return CourseResponse.model_validate(course)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Module CRUD
# ============================================================================

@router.post("/modules", response_model=ModuleResponse)
async def create_module(
    data: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new training module."""
    service = TrainingService(db)
    module = await service.create_module(data)
    return ModuleResponse.model_validate(module)


@router.get("/courses/{course_id}/modules", response_model=ModuleListResponse)
async def list_course_modules(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List modules for a course with user progress."""
    service = TrainingService(db)
    return await service.list_modules(course_id, user_id=current_user.id)


@router.get("/modules/{module_id}", response_model=ModuleContentResponse)
async def get_module(
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a training module with content."""
    service = TrainingService(db)
    module = await service.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    response = ModuleContentResponse.model_validate(module)
    response.content_data = module.content
    return response


@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: str,
    data: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a training module."""
    service = TrainingService(db)
    module = await service.update_module(module_id, data)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return ModuleResponse.model_validate(module)


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a training module."""
    service = TrainingService(db)
    success = await service.delete_module(module_id)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"message": "Module deleted successfully"}


# ============================================================================
# Quiz Management
# ============================================================================

@router.post("/quizzes", response_model=QuizResponse)
async def create_quiz(
    data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a quiz for a module."""
    service = TrainingService(db)
    quiz = await service.create_quiz(data)
    return QuizResponse.model_validate(quiz)


@router.get("/quizzes/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz(
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a quiz with questions (admin view)."""
    service = TrainingService(db)
    quiz = await service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return QuizDetailResponse.model_validate(quiz)


@router.get("/modules/{module_id}/quiz", response_model=QuizDetailResponse)
async def get_module_quiz(
    module_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get quiz for a module."""
    service = TrainingService(db)
    quiz = await service.get_quiz_by_module(module_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this module")
    return QuizDetailResponse.model_validate(quiz)


@router.post("/quizzes/{quiz_id}/questions", response_model=QuizQuestionResponse)
async def add_question(
    quiz_id: str,
    data: QuizQuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a question to a quiz."""
    service = TrainingService(db)
    question = await service.add_question(quiz_id, data)
    return QuizQuestionResponse.model_validate(question)


@router.post("/quizzes/{quiz_id}/start", response_model=QuizStartResponse)
async def start_quiz_attempt(
    quiz_id: str,
    enrollment_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new quiz attempt."""
    service = TrainingService(db)
    try:
        return await service.start_quiz_attempt(
            quiz_id=quiz_id,
            user_id=current_user.id,
            enrollment_id=enrollment_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quizzes/attempts/{attempt_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(
    attempt_id: str,
    data: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit quiz answers and get results."""
    service = TrainingService(db)
    try:
        return await service.submit_quiz_attempt(attempt_id, data.answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Enrollment & Progress
# ============================================================================

@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_in_course(
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll current user in a course."""
    service = TrainingService(db)
    try:
        enrollment = await service.enroll_user(
            course_id=data.course_id,
            user_id=current_user.id,
            deadline=data.deadline,
            assignment_reason=data.assignment_reason,
        )
        return EnrollmentResponse.model_validate(enrollment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/courses/{course_id}/enroll", response_model=EnrollmentResponse)
async def enroll_user_in_course(
    course_id: str,
    user_id: Optional[str] = None,
    deadline: Optional[date] = None,
    assignment_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll a user in a course (admin can specify user_id)."""
    service = TrainingService(db)
    try:
        enrollment = await service.enroll_user(
            course_id=course_id,
            user_id=user_id or current_user.id,
            deadline=deadline,
            assigned_by=current_user.id if user_id else None,
            assignment_reason=assignment_reason,
        )
        return EnrollmentResponse.model_validate(enrollment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-enroll", response_model=List[EnrollmentResponse])
async def bulk_enroll_users(
    data: BulkEnrollmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk enroll multiple users in a course."""
    service = TrainingService(db)
    enrollments = await service.bulk_enroll(data, assigned_by=current_user.id)
    return [EnrollmentResponse.model_validate(e) for e in enrollments]


@router.get("/my-learning", response_model=MyLearningResponse)
async def get_my_learning(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's learning dashboard."""
    service = TrainingService(db)
    return await service.get_my_learning(user_id=current_user.id)


@router.post("/modules/{module_id}/progress", response_model=ModuleProgressResponse)
async def update_module_progress(
    module_id: str,
    data: ModuleProgressUpdate,
    enrollment_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update progress on a module."""
    service = TrainingService(db)
    progress = await service.update_module_progress(
        enrollment_id=enrollment_id,
        module_id=module_id,
        user_id=current_user.id,
        data=data,
    )
    return ModuleProgressResponse.model_validate(progress)


@router.post("/modules/{module_id}/complete", response_model=ModuleProgressResponse)
async def complete_module(
    module_id: str,
    enrollment_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a module as completed."""
    service = TrainingService(db)
    progress = await service.complete_module(
        enrollment_id=enrollment_id,
        module_id=module_id,
        user_id=current_user.id,
    )
    return ModuleProgressResponse.model_validate(progress)


# ============================================================================
# Phishing Campaigns
# ============================================================================

phishing_router = APIRouter(prefix="/phishing")


@phishing_router.post("/templates", response_model=PhishingTemplateResponse)
async def create_phishing_template(
    data: PhishingTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a phishing email template."""
    service = TrainingService(db)
    template = await service.create_phishing_template(data, created_by=current_user.id)
    return PhishingTemplateResponse.model_validate(template)


@phishing_router.get("/templates", response_model=PhishingTemplateListResponse)
async def list_phishing_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List phishing templates."""
    service = TrainingService(db)
    return await service.list_phishing_templates(
        page=page,
        size=size,
        category=category,
        active_only=active_only,
    )


@phishing_router.post("/campaigns", response_model=PhishingCampaignResponse)
async def create_phishing_campaign(
    data: PhishingCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a phishing simulation campaign."""
    service = TrainingService(db)
    campaign = await service.create_phishing_campaign(data, created_by=current_user.id)
    return PhishingCampaignResponse.model_validate(campaign)


@phishing_router.get("/campaigns/{campaign_id}", response_model=PhishingCampaignResponse)
async def get_phishing_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a phishing campaign."""
    service = TrainingService(db)
    campaign = await service.get_phishing_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return PhishingCampaignResponse.model_validate(campaign)


@phishing_router.post("/campaigns/{campaign_id}/launch", response_model=PhishingCampaignResponse)
async def launch_phishing_campaign(
    campaign_id: str,
    user_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Launch a phishing campaign."""
    service = TrainingService(db)
    try:
        campaign = await service.launch_phishing_campaign(campaign_id, user_ids)
        return PhishingCampaignResponse.model_validate(campaign)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@phishing_router.get("/campaigns/{campaign_id}/results", response_model=PhishingCampaignResultsResponse)
async def get_campaign_results(
    campaign_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get phishing campaign results."""
    service = TrainingService(db)
    campaign = await service.get_phishing_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Build response with targets
    from src.schemas.awareness import PhishingTargetResponse
    targets = [PhishingTargetResponse.model_validate(t) for t in campaign.targets]

    # Paginate
    total = len(targets)
    start = (page - 1) * size
    end = start + size
    paginated_targets = targets[start:end]

    # Count by status
    results_by_status = {}
    for t in campaign.targets:
        status = t.result.value if t.result else "pending"
        results_by_status[status] = results_by_status.get(status, 0) + 1

    return PhishingCampaignResultsResponse(
        campaign=PhishingCampaignResponse.model_validate(campaign),
        targets=paginated_targets,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        results_by_status=results_by_status,
    )


@phishing_router.get("/track/{tracking_id}")
async def track_phishing_event(
    tracking_id: str,
    event: str = Query(..., description="Event type: open, click, submit, report"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Track a phishing event (used by email tracking pixels and links)."""
    service = TrainingService(db)

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    target = await service.track_phishing_event(
        tracking_id=tracking_id,
        event_type=event,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Return tracking pixel or redirect
    if event == "open":
        # Return 1x1 transparent pixel
        from fastapi.responses import Response
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        return Response(content=pixel, media_type="image/gif")

    return {"tracked": True}


# ============================================================================
# Badges & Gamification
# ============================================================================

@router.post("/badges", response_model=BadgeResponse)
async def create_badge(
    data: BadgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a badge definition."""
    service = TrainingService(db)
    badge = await service.create_badge(data)
    return BadgeResponse.model_validate(badge)


@router.get("/badges", response_model=BadgeListResponse)
async def list_badges(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all badges."""
    service = TrainingService(db)
    return await service.list_badges(active_only=active_only)


@router.get("/my-badges", response_model=UserBadgesResponse)
async def get_my_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's earned badges."""
    service = TrainingService(db)
    return await service.get_user_badges(user_id=current_user.id)


@router.get("/users/{user_id}/badges", response_model=UserBadgesResponse)
async def get_user_badges(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a user's earned badges."""
    service = TrainingService(db)
    return await service.get_user_badges(user_id=user_id)


# ============================================================================
# Leaderboard & Stats
# ============================================================================

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    period: str = Query("all_time", description="Period: all_time, monthly, weekly"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get training leaderboard."""
    service = TrainingService(db)
    return await service.get_leaderboard(
        period=period,
        limit=limit,
        current_user_id=current_user.id,
    )


@router.get("/my-stats", response_model=TrainingStatsResponse)
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's training statistics."""
    service = TrainingService(db)
    stats = await service.update_user_stats(user_id=current_user.id)
    return TrainingStatsResponse.model_validate(stats)


@router.get("/users/{user_id}/stats", response_model=TrainingStatsResponse)
async def get_user_stats(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a user's training statistics."""
    service = TrainingService(db)
    stats = await service.update_user_stats(user_id=user_id)
    return TrainingStatsResponse.model_validate(stats)


# Include phishing router
router.include_router(phishing_router)
