"""Security Awareness & Training service."""
import hashlib
import math
import secrets
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from src.models.awareness import (
    TrainingCourse, TrainingModule, Quiz, QuizQuestion,
    TrainingEnrollment, ModuleProgress, QuizAttempt,
    PhishingTemplate, PhishingCampaign, PhishingTarget,
    Badge, UserBadge, TrainingStats,
    CourseCategory, CourseDifficulty, CourseStatus, ModuleType, QuestionType,
    EnrollmentStatus, CampaignStatus, PhishingResult, BadgeCategory
)
from src.schemas.awareness import (
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse, CourseCatalogItem, CourseCatalogResponse,
    ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse, ModuleContentResponse,
    QuizCreate, QuizUpdate, QuizResponse, QuizDetailResponse, QuizStudentView, QuizStartResponse,
    QuizQuestionCreate, QuizQuestionStudentView, QuizAnswer, QuizAttemptResponse, QuizResultQuestion,
    EnrollmentCreate, BulkEnrollmentRequest, EnrollmentResponse, EnrollmentListResponse,
    MyLearningItem, MyLearningResponse, ModuleProgressUpdate, ModuleProgressResponse,
    PhishingTemplateCreate, PhishingTemplateUpdate, PhishingTemplateResponse, PhishingTemplateListResponse,
    PhishingCampaignCreate, PhishingCampaignUpdate, PhishingCampaignResponse, PhishingCampaignListResponse,
    PhishingTargetResponse, PhishingCampaignResultsResponse,
    BadgeCreate, BadgeUpdate, BadgeResponse, BadgeListResponse, UserBadgeResponse, UserBadgesResponse,
    TrainingStatsResponse, LeaderboardEntry, LeaderboardResponse,
    TrainingDashboardStats, CourseComplianceReport, DepartmentComplianceReport
)
from src.services.base_service import TenantAwareService

logger = logging.getLogger(__name__)


class TrainingService(TenantAwareService[TrainingCourse]):
    """Service for Security Awareness & Training operations."""

    model_class = TrainingCourse

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.db = db

    # ============================================================================
    # Course Code Generation
    # ============================================================================

    async def generate_course_code(self, category: CourseCategory) -> str:
        """Generate unique course code based on category."""
        prefix_map = {
            CourseCategory.SECURITY_FUNDAMENTALS: "SEC",
            CourseCategory.PHISHING_AWARENESS: "PHI",
            CourseCategory.DATA_PROTECTION: "DAT",
            CourseCategory.PASSWORD_SECURITY: "PWD",
            CourseCategory.SOCIAL_ENGINEERING: "SOC",
            CourseCategory.COMPLIANCE: "CMP",
            CourseCategory.INCIDENT_RESPONSE: "INC",
            CourseCategory.PHYSICAL_SECURITY: "PHY",
            CourseCategory.MOBILE_SECURITY: "MOB",
            CourseCategory.CLOUD_SECURITY: "CLD",
            CourseCategory.PRIVACY: "PRV",
            CourseCategory.CUSTOM: "CUS",
        }
        prefix = prefix_map.get(category, "TRN")

        result = await self.db.execute(
            select(func.count(TrainingCourse.id)).where(
                TrainingCourse.course_code.like(f"{prefix}-%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}-{count + 1:03d}"

    # ============================================================================
    # Course CRUD
    # ============================================================================

    async def create_course(
        self,
        data: CourseCreate,
        created_by: str,
    ) -> TrainingCourse:
        """Create a new training course."""
        course_code = await self.generate_course_code(data.category)

        course = TrainingCourse(
            course_code=course_code,
            title=data.title,
            description=data.description,
            short_description=data.short_description,
            category=data.category,
            difficulty=data.difficulty or CourseDifficulty.BEGINNER,
            status=CourseStatus.DRAFT,
            estimated_duration_minutes=data.estimated_duration_minutes or 30,
            passing_score=data.passing_score or 80,
            max_attempts=data.max_attempts or 3,
            certificate_enabled=data.certificate_enabled if data.certificate_enabled is not None else True,
            thumbnail_url=data.thumbnail_url,
            objectives=data.objectives or [],
            target_audience=data.target_audience or [],
            tags=data.tags or [],
            compliance_frameworks=data.compliance_frameworks or [],
            control_references=data.control_references or [],
            mandatory_for=data.mandatory_for or [],
            recurrence_days=data.recurrence_days,
            deadline_days=data.deadline_days,
            created_by=created_by,
        )

        self._set_tenant_on_create(course)
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)

        logger.info(f"Created course {course_code}: {data.title}")
        return course

    async def get_course(self, course_id: str) -> Optional[TrainingCourse]:
        """Get course by ID or course_code."""
        query = self._base_query().where(
            and_(
                or_(TrainingCourse.id == course_id, TrainingCourse.course_code == course_id),
                TrainingCourse.is_deleted == False
            )
        ).options(
            selectinload(TrainingCourse.modules),
            selectinload(TrainingCourse.enrollments)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_course(
        self,
        course_id: str,
        data: CourseUpdate,
    ) -> Optional[TrainingCourse]:
        """Update a course."""
        course = await self.get_course(course_id)
        if not course:
            return None

        # Only allow updates if course is in draft status
        if course.status == CourseStatus.PUBLISHED and data.status != CourseStatus.ARCHIVED:
            # Create new version instead of direct edit for published courses
            pass

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(course, field):
                setattr(course, field, value)

        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def delete_course(self, course_id: str) -> bool:
        """Soft delete a course."""
        course = await self.get_course(course_id)
        if not course:
            return False

        course.is_deleted = True
        course.deleted_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def publish_course(
        self,
        course_id: str,
        published_by: str,
    ) -> Optional[TrainingCourse]:
        """Publish a course making it available for enrollment."""
        course = await self.get_course(course_id)
        if not course:
            return None

        # Validate course has at least one module
        if not course.modules or len([m for m in course.modules if m.is_active]) == 0:
            raise ValueError("Course must have at least one active module before publishing")

        course.status = CourseStatus.PUBLISHED
        course.published_at = datetime.utcnow()
        course.published_by = published_by

        await self.db.commit()
        await self.db.refresh(course)

        logger.info(f"Published course {course.course_code}")
        return course

    async def list_courses(
        self,
        page: int = 1,
        size: int = 20,
        category: Optional[CourseCategory] = None,
        difficulty: Optional[CourseDifficulty] = None,
        status: Optional[CourseStatus] = None,
        search: Optional[str] = None,
    ) -> CourseListResponse:
        """List courses with filters."""
        query = self._base_query().where(TrainingCourse.is_deleted == False)

        if category:
            query = query.where(TrainingCourse.category == category)
        if difficulty:
            query = query.where(TrainingCourse.difficulty == difficulty)
        if status:
            query = query.where(TrainingCourse.status == status)
        if search:
            search_filter = or_(
                TrainingCourse.title.ilike(f"%{search}%"),
                TrainingCourse.course_code.ilike(f"%{search}%"),
                TrainingCourse.description.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get page
        query = query.order_by(desc(TrainingCourse.created_at))
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        courses = result.scalars().all()

        items = []
        for course in courses:
            response = CourseResponse.model_validate(course)
            response.modules_count = len([m for m in course.modules if m.is_active]) if course.modules else 0
            response.enrolled_count = len(course.enrollments) if course.enrollments else 0
            items.append(response)

        return CourseListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if size > 0 else 0
        )

    async def get_course_catalog(
        self,
        user_id: str,
        page: int = 1,
        size: int = 20,
        category: Optional[CourseCategory] = None,
    ) -> CourseCatalogResponse:
        """Get course catalog with user enrollment status."""
        query = self._base_query().where(
            and_(
                TrainingCourse.is_deleted == False,
                TrainingCourse.status == CourseStatus.PUBLISHED
            )
        )

        if category:
            query = query.where(TrainingCourse.category == category)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get page
        query = query.order_by(
            desc(TrainingCourse.is_featured),
            desc(TrainingCourse.created_at)
        )
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        courses = result.scalars().all()

        # Get user enrollments
        enrollment_query = select(TrainingEnrollment).where(
            and_(
                TrainingEnrollment.user_id == user_id,
                TrainingEnrollment.course_id.in_([c.id for c in courses])
            )
        )
        enrollment_result = await self.db.execute(enrollment_query)
        enrollments = {e.course_id: e for e in enrollment_result.scalars().all()}

        items = []
        for course in courses:
            enrollment = enrollments.get(course.id)
            item = CourseCatalogItem(
                id=course.id,
                course_code=course.course_code,
                title=course.title,
                short_description=course.short_description,
                category=course.category,
                difficulty=course.difficulty,
                estimated_duration_minutes=course.estimated_duration_minutes,
                thumbnail_url=course.thumbnail_url,
                is_featured=course.is_featured,
                modules_count=len([m for m in course.modules if m.is_active]) if course.modules else 0,
                enrolled_count=len(course.enrollments) if course.enrollments else 0,
                average_score=None,
                user_enrollment_status=enrollment.status if enrollment else None,
                user_progress_percent=enrollment.progress_percent if enrollment else None,
            )
            items.append(item)

        # Get category counts
        category_query = select(
            TrainingCourse.category,
            func.count(TrainingCourse.id)
        ).where(
            and_(
                TrainingCourse.is_deleted == False,
                TrainingCourse.status == CourseStatus.PUBLISHED
            )
        ).group_by(TrainingCourse.category)
        category_result = await self.db.execute(category_query)
        categories = [{"category": cat.value, "count": count} for cat, count in category_result.all()]

        return CourseCatalogResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if size > 0 else 0,
            categories=categories
        )

    # ============================================================================
    # Module CRUD
    # ============================================================================

    async def create_module(
        self,
        data: ModuleCreate,
    ) -> TrainingModule:
        """Create a new training module."""
        # Get max order for this course
        order_query = select(func.max(TrainingModule.order)).where(
            TrainingModule.course_id == data.course_id
        )
        result = await self.db.execute(order_query)
        max_order = result.scalar() or 0

        module = TrainingModule(
            course_id=data.course_id,
            title=data.title,
            description=data.description,
            module_type=data.module_type,
            content=data.content,
            order=data.order if data.order is not None else max_order + 1,
            estimated_duration_minutes=data.estimated_duration_minutes or 10,
            is_mandatory=data.is_mandatory if data.is_mandatory is not None else True,
            requires_completion_to_proceed=data.requires_completion_to_proceed if data.requires_completion_to_proceed is not None else True,
            attachment_id=data.attachment_id,
        )

        self._set_tenant_on_create(module)
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)

        # Update course duration
        await self._update_course_duration(data.course_id)

        logger.info(f"Created module for course {data.course_id}: {data.title}")
        return module

    async def get_module(self, module_id: str) -> Optional[TrainingModule]:
        """Get module by ID."""
        query = select(TrainingModule).where(TrainingModule.id == module_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_module(
        self,
        module_id: str,
        data: ModuleUpdate,
    ) -> Optional[TrainingModule]:
        """Update a module."""
        module = await self.get_module(module_id)
        if not module:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(module, field):
                setattr(module, field, value)

        await self.db.commit()
        await self.db.refresh(module)

        # Update course duration if duration changed
        if 'estimated_duration_minutes' in update_data:
            await self._update_course_duration(module.course_id)

        return module

    async def delete_module(self, module_id: str) -> bool:
        """Delete a module (hard delete for draft courses)."""
        module = await self.get_module(module_id)
        if not module:
            return False

        course_id = module.course_id
        await self.db.delete(module)
        await self.db.commit()

        # Update course duration
        await self._update_course_duration(course_id)

        return True

    async def list_modules(
        self,
        course_id: str,
        user_id: Optional[str] = None,
    ) -> ModuleListResponse:
        """List modules for a course with optional user progress."""
        query = select(TrainingModule).where(
            and_(
                TrainingModule.course_id == course_id,
                TrainingModule.is_active == True
            )
        ).order_by(TrainingModule.order)

        result = await self.db.execute(query)
        modules = result.scalars().all()

        # Get user progress if user_id provided
        progress_map = {}
        if user_id:
            progress_query = select(ModuleProgress).where(
                and_(
                    ModuleProgress.module_id.in_([m.id for m in modules]),
                    ModuleProgress.user_id == user_id
                )
            )
            progress_result = await self.db.execute(progress_query)
            progress_map = {p.module_id: p for p in progress_result.scalars().all()}

        items = []
        for module in modules:
            response = ModuleResponse.model_validate(module)
            response.has_quiz = module.module_type == ModuleType.QUIZ

            if user_id and module.id in progress_map:
                progress = progress_map[module.id]
                response.user_completed = progress.is_completed
                response.user_progress_percent = progress.completion_percent

            items.append(response)

        return ModuleListResponse(items=items, total=len(items))

    async def _update_course_duration(self, course_id: str) -> None:
        """Update course total duration based on modules."""
        query = select(func.sum(TrainingModule.estimated_duration_minutes)).where(
            and_(
                TrainingModule.course_id == course_id,
                TrainingModule.is_active == True
            )
        )
        result = await self.db.execute(query)
        total_duration = result.scalar() or 0

        update_query = select(TrainingCourse).where(TrainingCourse.id == course_id)
        course_result = await self.db.execute(update_query)
        course = course_result.scalar_one_or_none()
        if course:
            course.estimated_duration_minutes = total_duration
            await self.db.commit()

    # ============================================================================
    # Quiz Management
    # ============================================================================

    async def create_quiz(
        self,
        data: QuizCreate,
    ) -> Quiz:
        """Create a quiz for a module."""
        quiz = Quiz(
            module_id=data.module_id,
            title=data.title,
            instructions=data.instructions,
            time_limit_minutes=data.time_limit_minutes,
            passing_score=data.passing_score or 80,
            randomize_questions=data.randomize_questions if data.randomize_questions is not None else True,
            randomize_answers=data.randomize_answers if data.randomize_answers is not None else True,
            show_correct_answers=data.show_correct_answers if data.show_correct_answers is not None else True,
            max_attempts=data.max_attempts or 3,
        )

        self._set_tenant_on_create(quiz)
        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz)

        # Add questions if provided
        if data.questions:
            for i, q_data in enumerate(data.questions):
                await self.add_question(quiz.id, q_data, order=i)

        logger.info(f"Created quiz for module {data.module_id}: {data.title}")
        return quiz

    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID with questions."""
        query = select(Quiz).where(Quiz.id == quiz_id).options(
            selectinload(Quiz.questions)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_quiz_by_module(self, module_id: str) -> Optional[Quiz]:
        """Get quiz by module ID."""
        query = select(Quiz).where(Quiz.module_id == module_id).options(
            selectinload(Quiz.questions)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_question(
        self,
        quiz_id: str,
        data: QuizQuestionCreate,
        order: Optional[int] = None,
    ) -> QuizQuestion:
        """Add a question to a quiz."""
        if order is None:
            order_query = select(func.max(QuizQuestion.order)).where(
                QuizQuestion.quiz_id == quiz_id
            )
            result = await self.db.execute(order_query)
            order = (result.scalar() or 0) + 1

        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=data.question_text,
            question_type=data.question_type,
            options=[opt.model_dump() for opt in data.options],
            matching_data=data.matching_data,
            explanation=data.explanation,
            points=data.points or 1,
            order=order,
        )

        self._set_tenant_on_create(question)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)

        return question

    async def start_quiz_attempt(
        self,
        quiz_id: str,
        user_id: str,
        enrollment_id: Optional[str] = None,
    ) -> QuizStartResponse:
        """Start a new quiz attempt."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")

        # Check attempts remaining
        attempts_query = select(func.count(QuizAttempt.id)).where(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id
            )
        )
        result = await self.db.execute(attempts_query)
        attempt_count = result.scalar() or 0

        if attempt_count >= quiz.max_attempts:
            raise ValueError("Maximum attempts reached")

        # Create attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            enrollment_id=enrollment_id,
            attempt_number=attempt_count + 1,
            started_at=datetime.utcnow(),
        )

        self._set_tenant_on_create(attempt)
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)

        # Prepare questions (randomized if needed)
        questions = list(quiz.questions)
        if quiz.randomize_questions:
            import random
            random.shuffle(questions)

        student_questions = []
        for q in questions:
            options = q.options.copy()
            if quiz.randomize_answers:
                import random
                random.shuffle(options)
            # Remove is_correct from options
            sanitized_options = [{"id": opt["id"], "text": opt["text"]} for opt in options]
            student_questions.append(QuizQuestionStudentView(
                id=q.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=sanitized_options,
                points=q.points,
                order=q.order,
            ))

        return QuizStartResponse(
            attempt_id=attempt.id,
            quiz_id=quiz_id,
            started_at=attempt.started_at,
            time_limit_minutes=quiz.time_limit_minutes,
            questions=student_questions,
        )

    async def submit_quiz_attempt(
        self,
        attempt_id: str,
        answers: List[QuizAnswer],
    ) -> QuizAttemptResponse:
        """Submit quiz answers and calculate score."""
        attempt_query = select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        result = await self.db.execute(attempt_query)
        attempt = result.scalar_one_or_none()

        if not attempt:
            raise ValueError("Attempt not found")
        if attempt.completed_at:
            raise ValueError("Attempt already completed")

        quiz = await self.get_quiz(attempt.quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")

        # Build question map
        question_map = {q.id: q for q in quiz.questions}

        # Calculate score
        points_earned = 0
        points_possible = 0
        results = []

        for answer in answers:
            question = question_map.get(answer.question_id)
            if not question:
                continue

            points_possible += question.points

            # Find correct answers
            correct_ids = [opt["id"] for opt in question.options if opt.get("is_correct")]
            is_correct = set(answer.selected_options) == set(correct_ids)

            if is_correct:
                points_earned += question.points

            results.append({
                "question_id": answer.question_id,
                "selected": answer.selected_options,
                "correct": correct_ids,
                "is_correct": is_correct,
            })

        # Calculate percentage
        score = (points_earned / points_possible * 100) if points_possible > 0 else 0
        passed = score >= quiz.passing_score

        # Update attempt
        attempt.score = score
        attempt.points_earned = points_earned
        attempt.points_possible = points_possible
        attempt.passed = passed
        attempt.answers = results
        attempt.completed_at = datetime.utcnow()
        attempt.time_taken_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())

        await self.db.commit()
        await self.db.refresh(attempt)

        # Update enrollment progress if applicable
        if attempt.enrollment_id:
            await self._update_enrollment_quiz_score(attempt.enrollment_id, score)

        # Check for badges
        await self._check_quiz_badges(attempt.user_id, attempt)

        # Build response
        response = QuizAttemptResponse.model_validate(attempt)

        if quiz.show_correct_answers:
            response.results = [
                QuizResultQuestion(
                    question_id=r["question_id"],
                    question_text=question_map[r["question_id"]].question_text,
                    selected_answer=r["selected"],
                    correct_answer=r["correct"],
                    is_correct=r["is_correct"],
                    points_earned=question_map[r["question_id"]].points if r["is_correct"] else 0,
                    points_possible=question_map[r["question_id"]].points,
                    explanation=question_map[r["question_id"]].explanation,
                )
                for r in results
            ]

        return response

    # ============================================================================
    # Enrollment & Progress
    # ============================================================================

    async def enroll_user(
        self,
        course_id: str,
        user_id: str,
        deadline: Optional[date] = None,
        assigned_by: Optional[str] = None,
        assignment_reason: Optional[str] = None,
    ) -> TrainingEnrollment:
        """Enroll a user in a course."""
        # Check if already enrolled
        existing_query = select(TrainingEnrollment).where(
            and_(
                TrainingEnrollment.course_id == course_id,
                TrainingEnrollment.user_id == user_id,
                TrainingEnrollment.status.notin_([EnrollmentStatus.EXPIRED, EnrollmentStatus.DROPPED])
            )
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise ValueError("User is already enrolled in this course")

        # Get course for module count
        course = await self.get_course(course_id)
        if not course:
            raise ValueError("Course not found")

        total_modules = len([m for m in course.modules if m.is_active]) if course.modules else 0

        # Calculate deadline if not provided
        if not deadline and course.deadline_days:
            deadline = date.today() + timedelta(days=course.deadline_days)

        enrollment = TrainingEnrollment(
            course_id=course_id,
            user_id=user_id,
            status=EnrollmentStatus.ENROLLED,
            progress_percent=0.0,
            modules_completed=0,
            total_modules=total_modules,
            enrolled_at=datetime.utcnow(),
            deadline=deadline,
            assigned_by=assigned_by,
            assignment_reason=assignment_reason,
        )

        self._set_tenant_on_create(enrollment)
        self.db.add(enrollment)
        await self.db.commit()
        await self.db.refresh(enrollment)

        logger.info(f"Enrolled user {user_id} in course {course_id}")
        return enrollment

    async def bulk_enroll(
        self,
        data: BulkEnrollmentRequest,
        assigned_by: str,
    ) -> List[TrainingEnrollment]:
        """Bulk enroll multiple users in a course."""
        enrollments = []
        for user_id in data.user_ids:
            try:
                enrollment = await self.enroll_user(
                    course_id=data.course_id,
                    user_id=user_id,
                    deadline=data.deadline,
                    assigned_by=assigned_by,
                    assignment_reason=data.assignment_reason,
                )
                enrollments.append(enrollment)
            except ValueError as e:
                logger.warning(f"Could not enroll user {user_id}: {e}")
                continue

        return enrollments

    async def get_enrollment(
        self,
        enrollment_id: str,
    ) -> Optional[TrainingEnrollment]:
        """Get enrollment by ID."""
        query = select(TrainingEnrollment).where(TrainingEnrollment.id == enrollment_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_enrollment(
        self,
        course_id: str,
        user_id: str,
    ) -> Optional[TrainingEnrollment]:
        """Get user's enrollment in a course."""
        query = select(TrainingEnrollment).where(
            and_(
                TrainingEnrollment.course_id == course_id,
                TrainingEnrollment.user_id == user_id,
                TrainingEnrollment.status.notin_([EnrollmentStatus.EXPIRED, EnrollmentStatus.DROPPED])
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_module_progress(
        self,
        enrollment_id: str,
        module_id: str,
        user_id: str,
        data: ModuleProgressUpdate,
    ) -> ModuleProgress:
        """Update user's progress on a module."""
        # Get or create progress record
        query = select(ModuleProgress).where(
            and_(
                ModuleProgress.enrollment_id == enrollment_id,
                ModuleProgress.module_id == module_id,
                ModuleProgress.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        progress = result.scalar_one_or_none()

        if not progress:
            progress = ModuleProgress(
                enrollment_id=enrollment_id,
                module_id=module_id,
                user_id=user_id,
                started_at=datetime.utcnow(),
            )
            self._set_tenant_on_create(progress)
            self.db.add(progress)

        # Update fields
        if data.completion_percent is not None:
            progress.completion_percent = data.completion_percent
        if data.time_spent_seconds is not None:
            progress.time_spent_seconds += data.time_spent_seconds
        if data.last_position_seconds is not None:
            progress.last_position_seconds = data.last_position_seconds
        if data.is_completed is not None and data.is_completed and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            progress.completion_percent = 100.0

        await self.db.commit()
        await self.db.refresh(progress)

        # Update enrollment progress
        await self._update_enrollment_progress(enrollment_id)

        return progress

    async def complete_module(
        self,
        enrollment_id: str,
        module_id: str,
        user_id: str,
    ) -> ModuleProgress:
        """Mark a module as completed."""
        return await self.update_module_progress(
            enrollment_id=enrollment_id,
            module_id=module_id,
            user_id=user_id,
            data=ModuleProgressUpdate(is_completed=True),
        )

    async def _update_enrollment_progress(self, enrollment_id: str) -> None:
        """Update enrollment progress based on module completions."""
        enrollment = await self.get_enrollment(enrollment_id)
        if not enrollment:
            return

        # Count completed modules
        completed_query = select(func.count(ModuleProgress.id)).where(
            and_(
                ModuleProgress.enrollment_id == enrollment_id,
                ModuleProgress.is_completed == True
            )
        )
        result = await self.db.execute(completed_query)
        completed_count = result.scalar() or 0

        enrollment.modules_completed = completed_count
        enrollment.progress_percent = (completed_count / enrollment.total_modules * 100) if enrollment.total_modules > 0 else 0
        enrollment.last_activity_at = datetime.utcnow()

        # Update status
        if enrollment.status == EnrollmentStatus.ENROLLED and completed_count > 0:
            enrollment.status = EnrollmentStatus.IN_PROGRESS
            enrollment.started_at = datetime.utcnow()

        if completed_count >= enrollment.total_modules:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
            # Check for completion badges
            await self._check_completion_badges(enrollment)

        await self.db.commit()

    async def _update_enrollment_quiz_score(self, enrollment_id: str, score: float) -> None:
        """Update enrollment quiz scores."""
        enrollment = await self.get_enrollment(enrollment_id)
        if not enrollment:
            return

        # Get all quiz attempts for this enrollment
        attempts_query = select(QuizAttempt).where(
            and_(
                QuizAttempt.enrollment_id == enrollment_id,
                QuizAttempt.completed_at.isnot(None)
            )
        )
        result = await self.db.execute(attempts_query)
        attempts = result.scalars().all()

        if attempts:
            scores = [a.score for a in attempts]
            enrollment.highest_quiz_score = max(scores)
            enrollment.average_quiz_score = sum(scores) / len(scores)
            await self.db.commit()

    async def get_my_learning(self, user_id: str) -> MyLearningResponse:
        """Get user's learning dashboard."""
        query = select(TrainingEnrollment).where(
            and_(
                TrainingEnrollment.user_id == user_id,
                TrainingEnrollment.status.notin_([EnrollmentStatus.DROPPED])
            )
        ).options(selectinload(TrainingEnrollment.course))

        result = await self.db.execute(query)
        enrollments = result.scalars().all()

        in_progress = []
        completed = []
        assigned = []
        overdue_count = 0
        due_soon_count = 0
        today = date.today()
        week_from_now = today + timedelta(days=7)

        for e in enrollments:
            course = e.course
            item = MyLearningItem(
                enrollment_id=e.id,
                course_id=e.course_id,
                course_code=course.course_code if course else "",
                course_title=course.title if course else "",
                course_category=course.category if course else CourseCategory.CUSTOM,
                course_difficulty=course.difficulty if course else CourseDifficulty.BEGINNER,
                thumbnail_url=course.thumbnail_url if course else None,
                status=e.status,
                progress_percent=e.progress_percent,
                modules_completed=e.modules_completed,
                total_modules=e.total_modules,
                deadline=e.deadline,
                is_overdue=e.deadline < today if e.deadline else False,
                last_activity_at=e.last_activity_at,
            )

            if e.status == EnrollmentStatus.COMPLETED:
                completed.append(item)
            elif e.status == EnrollmentStatus.IN_PROGRESS:
                in_progress.append(item)
                if e.deadline and e.deadline < today:
                    overdue_count += 1
                elif e.deadline and e.deadline <= week_from_now:
                    due_soon_count += 1
            else:
                assigned.append(item)
                if e.deadline and e.deadline < today:
                    overdue_count += 1
                elif e.deadline and e.deadline <= week_from_now:
                    due_soon_count += 1

        return MyLearningResponse(
            in_progress=in_progress,
            completed=completed,
            assigned=assigned,
            overdue=overdue_count,
            due_soon=due_soon_count,
        )

    # ============================================================================
    # Phishing Campaign Management
    # ============================================================================

    async def create_phishing_template(
        self,
        data: PhishingTemplateCreate,
        created_by: str,
    ) -> PhishingTemplate:
        """Create a phishing email template."""
        template = PhishingTemplate(
            name=data.name,
            description=data.description,
            category=data.category,
            subject=data.subject,
            sender_name=data.sender_name,
            sender_email=data.sender_email,
            body_html=data.body_html,
            body_text=data.body_text,
            landing_page_html=data.landing_page_html,
            landing_page_url=data.landing_page_url,
            difficulty=data.difficulty or "medium",
            red_flags=data.red_flags or [],
            created_by=created_by,
        )

        self._set_tenant_on_create(template)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(f"Created phishing template: {data.name}")
        return template

    async def list_phishing_templates(
        self,
        page: int = 1,
        size: int = 20,
        category: Optional[str] = None,
        active_only: bool = True,
    ) -> PhishingTemplateListResponse:
        """List phishing templates."""
        query = select(PhishingTemplate)

        if active_only:
            query = query.where(PhishingTemplate.is_active == True)
        if category:
            query = query.where(PhishingTemplate.category == category)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get page
        query = query.order_by(desc(PhishingTemplate.created_at))
        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        templates = result.scalars().all()

        items = [PhishingTemplateResponse.model_validate(t) for t in templates]

        return PhishingTemplateListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if size > 0 else 0
        )

    async def create_phishing_campaign(
        self,
        data: PhishingCampaignCreate,
        created_by: str,
    ) -> PhishingCampaign:
        """Create a phishing simulation campaign."""
        campaign = PhishingCampaign(
            template_id=data.template_id,
            name=data.name,
            description=data.description,
            status=CampaignStatus.DRAFT,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            target_departments=data.target_departments or [],
            target_user_ids=data.target_user_ids or [],
            exclude_user_ids=data.exclude_user_ids or [],
            send_window_start_hour=data.send_window_start_hour or 9,
            send_window_end_hour=data.send_window_end_hour or 17,
            randomize_send_time=data.randomize_send_time if data.randomize_send_time is not None else True,
            training_course_id=data.training_course_id,
            auto_enroll_on_fail=data.auto_enroll_on_fail if data.auto_enroll_on_fail is not None else True,
            created_by=created_by,
        )

        self._set_tenant_on_create(campaign)
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(f"Created phishing campaign: {data.name}")
        return campaign

    async def get_phishing_campaign(
        self,
        campaign_id: str,
    ) -> Optional[PhishingCampaign]:
        """Get campaign by ID."""
        query = select(PhishingCampaign).where(PhishingCampaign.id == campaign_id).options(
            selectinload(PhishingCampaign.template),
            selectinload(PhishingCampaign.targets)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def launch_phishing_campaign(
        self,
        campaign_id: str,
        user_ids: List[str],
    ) -> PhishingCampaign:
        """Launch a phishing campaign and create targets."""
        campaign = await self.get_phishing_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValueError("Campaign already launched")

        # Create targets
        for user_id in user_ids:
            if user_id in campaign.exclude_user_ids:
                continue

            tracking_id = secrets.token_urlsafe(32)
            target = PhishingTarget(
                campaign_id=campaign_id,
                user_id=user_id,
                tracking_id=tracking_id,
                result=PhishingResult.PENDING,
            )
            self._set_tenant_on_create(target)
            self.db.add(target)

        campaign.status = CampaignStatus.ACTIVE
        campaign.actual_start = datetime.utcnow()
        campaign.total_targets = len(user_ids)

        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(f"Launched phishing campaign {campaign_id} with {len(user_ids)} targets")
        return campaign

    async def track_phishing_event(
        self,
        tracking_id: str,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        submitted_data: Optional[dict] = None,
    ) -> Optional[PhishingTarget]:
        """Track a phishing event (open, click, submit)."""
        query = select(PhishingTarget).where(PhishingTarget.tracking_id == tracking_id)
        result = await self.db.execute(query)
        target = result.scalar_one_or_none()

        if not target:
            return None

        now = datetime.utcnow()
        target.ip_address = ip_address
        target.user_agent = user_agent

        if event_type == "open" and not target.email_opened_at:
            target.email_opened_at = now
            target.result = PhishingResult.OPENED
        elif event_type == "click" and not target.link_clicked_at:
            target.link_clicked_at = now
            target.result = PhishingResult.CLICKED
        elif event_type == "submit" and not target.credentials_submitted_at:
            target.credentials_submitted_at = now
            target.submitted_data = submitted_data
            target.result = PhishingResult.CLICKED
        elif event_type == "report" and not target.reported_at:
            target.reported_at = now
            target.result = PhishingResult.REPORTED

        await self.db.commit()
        await self.db.refresh(target)

        # Update campaign stats
        await self._update_campaign_stats(target.campaign_id)

        return target

    async def _update_campaign_stats(self, campaign_id: str) -> None:
        """Update campaign statistics."""
        campaign = await self.get_phishing_campaign(campaign_id)
        if not campaign:
            return

        sent_query = select(func.count(PhishingTarget.id)).where(
            and_(
                PhishingTarget.campaign_id == campaign_id,
                PhishingTarget.email_sent_at.isnot(None)
            )
        )
        opened_query = select(func.count(PhishingTarget.id)).where(
            and_(
                PhishingTarget.campaign_id == campaign_id,
                PhishingTarget.email_opened_at.isnot(None)
            )
        )
        clicked_query = select(func.count(PhishingTarget.id)).where(
            and_(
                PhishingTarget.campaign_id == campaign_id,
                PhishingTarget.link_clicked_at.isnot(None)
            )
        )
        reported_query = select(func.count(PhishingTarget.id)).where(
            and_(
                PhishingTarget.campaign_id == campaign_id,
                PhishingTarget.reported_at.isnot(None)
            )
        )

        sent_result = await self.db.execute(sent_query)
        opened_result = await self.db.execute(opened_query)
        clicked_result = await self.db.execute(clicked_query)
        reported_result = await self.db.execute(reported_query)

        campaign.emails_sent = sent_result.scalar() or 0
        campaign.emails_opened = opened_result.scalar() or 0
        campaign.links_clicked = clicked_result.scalar() or 0
        campaign.reported_count = reported_result.scalar() or 0

        await self.db.commit()

    # ============================================================================
    # Gamification
    # ============================================================================

    async def create_badge(
        self,
        data: BadgeCreate,
    ) -> Badge:
        """Create a badge definition."""
        badge = Badge(
            name=data.name,
            description=data.description,
            category=data.category,
            icon=data.icon or "award",
            color=data.color or "gold",
            criteria=data.criteria,
            points=data.points or 10,
            is_rare=data.is_rare or False,
        )

        self._set_tenant_on_create(badge)
        self.db.add(badge)
        await self.db.commit()
        await self.db.refresh(badge)

        return badge

    async def list_badges(self, active_only: bool = True) -> BadgeListResponse:
        """List all badges."""
        query = select(Badge)
        if active_only:
            query = query.where(Badge.is_active == True)

        result = await self.db.execute(query)
        badges = result.scalars().all()

        items = [BadgeResponse.model_validate(b) for b in badges]

        return BadgeListResponse(items=items, total=len(items))

    async def award_badge(
        self,
        user_id: str,
        badge_id: str,
        earned_for: Optional[str] = None,
    ) -> UserBadge:
        """Award a badge to a user."""
        # Check if already earned
        existing_query = select(UserBadge).where(
            and_(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge_id
            )
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise ValueError("User already has this badge")

        user_badge = UserBadge(
            badge_id=badge_id,
            user_id=user_id,
            earned_at=datetime.utcnow(),
            earned_for=earned_for,
        )

        self._set_tenant_on_create(user_badge)
        self.db.add(user_badge)

        # Update user stats
        await self._update_user_stats_badges(user_id)

        await self.db.commit()
        await self.db.refresh(user_badge)

        logger.info(f"Awarded badge {badge_id} to user {user_id}")
        return user_badge

    async def get_user_badges(self, user_id: str) -> UserBadgesResponse:
        """Get all badges earned by a user."""
        query = select(UserBadge).where(UserBadge.user_id == user_id).options(
            selectinload(UserBadge.badge)
        )
        result = await self.db.execute(query)
        user_badges = result.scalars().all()

        items = []
        total_points = 0
        for ub in user_badges:
            badge = ub.badge
            items.append(UserBadgeResponse(
                id=ub.id,
                badge_id=ub.badge_id,
                user_id=ub.user_id,
                earned_at=ub.earned_at,
                earned_for=ub.earned_for,
                badge_name=badge.name,
                badge_description=badge.description,
                badge_category=badge.category,
                badge_icon=badge.icon,
                badge_color=badge.color,
                badge_points=badge.points,
                badge_is_rare=badge.is_rare,
            ))
            total_points += badge.points

        return UserBadgesResponse(items=items, total=len(items), total_points=total_points)

    async def _check_completion_badges(self, enrollment: TrainingEnrollment) -> None:
        """Check and award badges for course completion."""
        # Award "Course Completed" type badges
        badges_query = select(Badge).where(
            and_(
                Badge.category == BadgeCategory.COMPLETION,
                Badge.is_active == True
            )
        )
        result = await self.db.execute(badges_query)
        badges = result.scalars().all()

        for badge in badges:
            criteria = badge.criteria
            if criteria.get("type") == "course_completed":
                # Check if this is for any course or specific course
                if "course_id" in criteria and criteria["course_id"] != enrollment.course_id:
                    continue

                try:
                    await self.award_badge(
                        user_id=enrollment.user_id,
                        badge_id=badge.id,
                        earned_for=f"Completed course: {enrollment.course_id}",
                    )
                except ValueError:
                    pass  # Already has badge

    async def _check_quiz_badges(self, user_id: str, attempt: QuizAttempt) -> None:
        """Check and award badges for quiz performance."""
        if attempt.score == 100:
            # Perfect score badge
            badges_query = select(Badge).where(
                and_(
                    Badge.category == BadgeCategory.PERFORMANCE,
                    Badge.is_active == True,
                    Badge.criteria.contains({"type": "perfect_quiz"})
                )
            )
            result = await self.db.execute(badges_query)
            badges = result.scalars().all()

            for badge in badges:
                try:
                    await self.award_badge(
                        user_id=user_id,
                        badge_id=badge.id,
                        earned_for=f"Perfect score on quiz: {attempt.quiz_id}",
                    )
                except ValueError:
                    pass

    async def _update_user_stats_badges(self, user_id: str) -> None:
        """Update user stats badge count."""
        count_query = select(func.count(UserBadge.id)).where(UserBadge.user_id == user_id)
        result = await self.db.execute(count_query)
        badge_count = result.scalar() or 0

        stats = await self.get_or_create_user_stats(user_id)
        stats.badges_earned = badge_count
        await self.db.commit()

    # ============================================================================
    # Leaderboard & Stats
    # ============================================================================

    async def get_or_create_user_stats(self, user_id: str) -> TrainingStats:
        """Get or create training stats for a user."""
        query = select(TrainingStats).where(TrainingStats.user_id == user_id)
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = TrainingStats(user_id=user_id)
            self._set_tenant_on_create(stats)
            self.db.add(stats)
            await self.db.commit()
            await self.db.refresh(stats)

        return stats

    async def update_user_stats(self, user_id: str) -> TrainingStats:
        """Recalculate user training stats."""
        stats = await self.get_or_create_user_stats(user_id)

        # Count enrollments
        completed_query = select(func.count(TrainingEnrollment.id)).where(
            and_(
                TrainingEnrollment.user_id == user_id,
                TrainingEnrollment.status == EnrollmentStatus.COMPLETED
            )
        )
        in_progress_query = select(func.count(TrainingEnrollment.id)).where(
            and_(
                TrainingEnrollment.user_id == user_id,
                TrainingEnrollment.status == EnrollmentStatus.IN_PROGRESS
            )
        )

        completed_result = await self.db.execute(completed_query)
        in_progress_result = await self.db.execute(in_progress_query)

        stats.courses_completed = completed_result.scalar() or 0
        stats.courses_in_progress = in_progress_result.scalar() or 0

        # Count modules completed
        modules_query = select(func.count(ModuleProgress.id)).where(
            and_(
                ModuleProgress.user_id == user_id,
                ModuleProgress.is_completed == True
            )
        )
        modules_result = await self.db.execute(modules_query)
        stats.modules_completed = modules_result.scalar() or 0

        # Count passed quizzes and average score
        quizzes_query = select(QuizAttempt).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.completed_at.isnot(None),
                QuizAttempt.passed == True
            )
        )
        quizzes_result = await self.db.execute(quizzes_query)
        passed_quizzes = quizzes_result.scalars().all()
        stats.quizzes_passed = len(passed_quizzes)

        # Calculate average score from all attempts
        all_attempts_query = select(QuizAttempt.score).where(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.completed_at.isnot(None)
            )
        )
        all_attempts_result = await self.db.execute(all_attempts_query)
        all_scores = [row[0] for row in all_attempts_result.all()]
        stats.average_quiz_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

        # Total training time
        time_query = select(func.sum(ModuleProgress.time_spent_seconds)).where(
            ModuleProgress.user_id == user_id
        )
        time_result = await self.db.execute(time_query)
        total_seconds = time_result.scalar() or 0
        stats.total_training_time_minutes = total_seconds // 60

        # Calculate points
        stats.total_points = (
            stats.courses_completed * 100 +
            stats.quizzes_passed * 50 +
            stats.modules_completed * 10
        )

        # Phishing stats
        phishing_query = select(PhishingTarget).where(PhishingTarget.user_id == user_id)
        phishing_result = await self.db.execute(phishing_query)
        phishing_targets = phishing_result.scalars().all()

        stats.phishing_tests_received = len(phishing_targets)
        stats.phishing_emails_reported = len([t for t in phishing_targets if t.reported_at])
        stats.phishing_links_clicked = len([t for t in phishing_targets if t.link_clicked_at])

        # Badges
        badges_query = select(func.count(UserBadge.id)).where(UserBadge.user_id == user_id)
        badges_result = await self.db.execute(badges_query)
        stats.badges_earned = badges_result.scalar() or 0

        # Update last activity
        stats.last_activity_date = date.today()
        stats.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(stats)

        return stats

    async def get_leaderboard(
        self,
        period: str = "all_time",
        limit: int = 10,
        current_user_id: Optional[str] = None,
    ) -> LeaderboardResponse:
        """Get training leaderboard."""
        query = select(TrainingStats).order_by(desc(TrainingStats.total_points)).limit(limit)

        result = await self.db.execute(query)
        stats_list = result.scalars().all()

        entries = []
        for rank, stats in enumerate(stats_list, 1):
            entries.append(LeaderboardEntry(
                rank=rank,
                user_id=stats.user_id,
                user_name=f"User {stats.user_id[:8]}",  # Would be replaced with actual user name
                user_avatar=None,
                department=None,
                total_points=stats.total_points,
                courses_completed=stats.courses_completed,
                badges_earned=stats.badges_earned,
                current_streak_days=stats.current_streak_days,
            ))

        total_query = select(func.count(TrainingStats.id))
        total_result = await self.db.execute(total_query)
        total_users = total_result.scalar() or 0

        # Get current user rank if not in top
        current_user_rank = None
        current_user_points = None
        if current_user_id:
            user_stats = await self.get_or_create_user_stats(current_user_id)
            current_user_points = user_stats.total_points

            rank_query = select(func.count(TrainingStats.id)).where(
                TrainingStats.total_points > user_stats.total_points
            )
            rank_result = await self.db.execute(rank_query)
            current_user_rank = (rank_result.scalar() or 0) + 1

        return LeaderboardResponse(
            entries=entries,
            total_users=total_users,
            period=period,
            current_user_rank=current_user_rank,
            current_user_points=current_user_points,
        )

    # ============================================================================
    # Dashboard Stats
    # ============================================================================

    async def get_dashboard_stats(self, user_id: str) -> TrainingDashboardStats:
        """Get training dashboard statistics."""
        # Course stats
        courses_query = select(TrainingCourse).where(TrainingCourse.is_deleted == False)
        courses_result = await self.db.execute(courses_query)
        courses = courses_result.scalars().all()

        total_courses = len(courses)
        published_courses = len([c for c in courses if c.status == CourseStatus.PUBLISHED])
        draft_courses = len([c for c in courses if c.status == CourseStatus.DRAFT])

        category_counts = {}
        for c in courses:
            cat = c.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Enrollment stats
        enrollments_query = select(TrainingEnrollment)
        enrollments_result = await self.db.execute(enrollments_query)
        enrollments = enrollments_result.scalars().all()

        total_enrollments = len(enrollments)
        in_progress = len([e for e in enrollments if e.status == EnrollmentStatus.IN_PROGRESS])
        completed = len([e for e in enrollments if e.status == EnrollmentStatus.COMPLETED])
        overdue = len([e for e in enrollments if e.deadline and e.deadline < date.today() and e.status not in [EnrollmentStatus.COMPLETED, EnrollmentStatus.DROPPED]])

        completion_rate = (completed / total_enrollments * 100) if total_enrollments > 0 else 0

        # Average quiz score
        quiz_scores_query = select(func.avg(QuizAttempt.score)).where(QuizAttempt.completed_at.isnot(None))
        quiz_result = await self.db.execute(quiz_scores_query)
        avg_quiz_score = quiz_result.scalar() or 0

        # User-specific stats
        my_query = select(TrainingEnrollment).where(TrainingEnrollment.user_id == user_id)
        my_result = await self.db.execute(my_query)
        my_enrollments = my_result.scalars().all()

        my_in_progress = len([e for e in my_enrollments if e.status == EnrollmentStatus.IN_PROGRESS])
        my_completed = len([e for e in my_enrollments if e.status == EnrollmentStatus.COMPLETED])
        my_pending = len([e for e in my_enrollments if e.status == EnrollmentStatus.ENROLLED])
        my_overdue = len([e for e in my_enrollments if e.deadline and e.deadline < date.today() and e.status not in [EnrollmentStatus.COMPLETED, EnrollmentStatus.DROPPED]])

        # Phishing stats
        campaigns_query = select(PhishingCampaign)
        campaigns_result = await self.db.execute(campaigns_query)
        campaigns = campaigns_result.scalars().all()

        active_campaigns = len([c for c in campaigns if c.status == CampaignStatus.ACTIVE])
        completed_campaigns = len([c for c in campaigns if c.status == CampaignStatus.COMPLETED])

        # Calculate overall click and report rates
        total_sent = sum(c.emails_sent for c in campaigns if c.emails_sent > 0)
        total_clicked = sum(c.links_clicked for c in campaigns)
        total_reported = sum(c.reported_count for c in campaigns)

        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        report_rate = (total_reported / total_sent * 100) if total_sent > 0 else 0

        # User gamification
        user_stats = await self.get_or_create_user_stats(user_id)

        return TrainingDashboardStats(
            total_courses=total_courses,
            published_courses=published_courses,
            draft_courses=draft_courses,
            courses_by_category=category_counts,
            total_enrollments=total_enrollments,
            enrollments_in_progress=in_progress,
            enrollments_completed=completed,
            enrollments_overdue=overdue,
            completion_rate=completion_rate,
            average_quiz_score=avg_quiz_score,
            my_courses_in_progress=my_in_progress,
            my_courses_completed=my_completed,
            my_pending_assignments=my_pending,
            my_overdue_assignments=my_overdue,
            active_campaigns=active_campaigns,
            completed_campaigns=completed_campaigns,
            overall_phishing_click_rate=click_rate,
            overall_phishing_report_rate=report_rate,
            my_total_points=user_stats.total_points,
            my_rank=user_stats.rank,
            my_badges=user_stats.badges_earned,
        )
