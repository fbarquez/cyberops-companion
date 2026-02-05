"""add_awareness_tables

Create tables for Security Awareness & Training module.
Enables training courses, modules, quizzes, phishing simulations,
gamification, and compliance tracking.

Tables:
- training_courses (Course catalog)
- training_modules (Lessons within courses)
- training_quizzes (Assessment quizzes)
- quiz_questions (Quiz questions)
- training_enrollments (User enrollments)
- module_progress (Per-module progress)
- quiz_attempts (Quiz attempt history)
- phishing_templates (Email templates)
- phishing_campaigns (Simulation campaigns)
- phishing_targets (Campaign targets/results)
- training_badges (Badge definitions)
- user_badges (Earned badges)
- training_stats (Aggregated stats for leaderboard)

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-02-05 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, Sequence[str], None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE course_category_enum AS ENUM (
                'security_fundamentals', 'phishing_awareness', 'data_protection',
                'password_security', 'social_engineering', 'compliance',
                'incident_response', 'physical_security', 'mobile_security',
                'cloud_security', 'privacy', 'custom'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE course_difficulty_enum AS ENUM ('beginner', 'intermediate', 'advanced');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE course_status_enum AS ENUM ('draft', 'published', 'archived');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE module_type_enum AS ENUM ('video', 'text', 'interactive', 'quiz', 'document', 'external_link');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE question_type_enum AS ENUM ('single_choice', 'multiple_choice', 'true_false', 'matching');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE enrollment_status_enum AS ENUM ('enrolled', 'in_progress', 'completed', 'expired', 'dropped');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE campaign_status_enum AS ENUM ('draft', 'scheduled', 'active', 'completed', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE phishing_result_enum AS ENUM ('pending', 'delivered', 'opened', 'clicked', 'reported', 'no_action');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE badge_category_enum AS ENUM ('completion', 'streak', 'performance', 'phishing', 'milestone', 'special');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create training_courses table
    op.create_table(
        'training_courses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_code', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('category', postgresql.ENUM('security_fundamentals', 'phishing_awareness', 'data_protection',
                'password_security', 'social_engineering', 'compliance', 'incident_response', 'physical_security',
                'mobile_security', 'cloud_security', 'privacy', 'custom', name='course_category_enum', create_type=False), nullable=False),
        sa.Column('difficulty', postgresql.ENUM('beginner', 'intermediate', 'advanced', name='course_difficulty_enum', create_type=False), default='beginner'),
        sa.Column('status', postgresql.ENUM('draft', 'published', 'archived', name='course_status_enum', create_type=False), default='draft'),
        sa.Column('estimated_duration_minutes', sa.Integer, default=30),
        sa.Column('passing_score', sa.Integer, default=80),
        sa.Column('max_attempts', sa.Integer, default=3),
        sa.Column('certificate_enabled', sa.Boolean, default=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('objectives', sa.JSON, default=[]),
        sa.Column('target_audience', sa.JSON, default=[]),
        sa.Column('tags', sa.JSON, default=[]),
        sa.Column('compliance_frameworks', sa.JSON, default=[]),
        sa.Column('control_references', sa.JSON, default=[]),
        sa.Column('mandatory_for', sa.JSON, default=[]),
        sa.Column('recurrence_days', sa.Integer, nullable=True),
        sa.Column('deadline_days', sa.Integer, nullable=True),
        sa.Column('published_at', sa.DateTime, nullable=True),
        sa.Column('published_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_training_courses_tenant_id', 'training_courses', ['tenant_id'])
    op.create_index('ix_training_courses_course_code', 'training_courses', ['course_code'])
    op.create_index('ix_training_courses_category', 'training_courses', ['category'])
    op.create_index('ix_training_courses_status', 'training_courses', ['status'])

    # Create course_prerequisites association table
    op.create_table(
        'course_prerequisites',
        sa.Column('course_id', sa.String(36), sa.ForeignKey('training_courses.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('prerequisite_id', sa.String(36), sa.ForeignKey('training_courses.id', ondelete='CASCADE'), primary_key=True),
    )

    # Create training_modules table
    op.create_table(
        'training_modules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('training_courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('module_type', postgresql.ENUM('video', 'text', 'interactive', 'quiz', 'document', 'external_link', name='module_type_enum', create_type=False), nullable=False),
        sa.Column('content', sa.JSON, nullable=True),
        sa.Column('order', sa.Integer, default=0),
        sa.Column('estimated_duration_minutes', sa.Integer, default=10),
        sa.Column('is_mandatory', sa.Boolean, default=True),
        sa.Column('requires_completion_to_proceed', sa.Boolean, default=True),
        sa.Column('attachment_id', sa.String(36), sa.ForeignKey('attachments.id'), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_training_modules_tenant_id', 'training_modules', ['tenant_id'])
    op.create_index('ix_training_modules_course_id', 'training_modules', ['course_id'])

    # Create training_quizzes table
    op.create_table(
        'training_quizzes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', sa.String(36), sa.ForeignKey('training_modules.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('instructions', sa.Text, nullable=True),
        sa.Column('time_limit_minutes', sa.Integer, nullable=True),
        sa.Column('passing_score', sa.Integer, default=80),
        sa.Column('randomize_questions', sa.Boolean, default=True),
        sa.Column('randomize_answers', sa.Boolean, default=True),
        sa.Column('show_correct_answers', sa.Boolean, default=True),
        sa.Column('max_attempts', sa.Integer, default=3),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_training_quizzes_tenant_id', 'training_quizzes', ['tenant_id'])
    op.create_index('ix_training_quizzes_module_id', 'training_quizzes', ['module_id'])

    # Create quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quiz_id', sa.String(36), sa.ForeignKey('training_quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('question_type', postgresql.ENUM('single_choice', 'multiple_choice', 'true_false', 'matching', name='question_type_enum', create_type=False), default='single_choice'),
        sa.Column('options', sa.JSON, default=[]),
        sa.Column('matching_data', sa.JSON, nullable=True),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('points', sa.Integer, default=1),
        sa.Column('order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_quiz_questions_tenant_id', 'quiz_questions', ['tenant_id'])
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'])

    # Create training_enrollments table
    op.create_table(
        'training_enrollments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('training_courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', postgresql.ENUM('enrolled', 'in_progress', 'completed', 'expired', 'dropped', name='enrollment_status_enum', create_type=False), default='enrolled'),
        sa.Column('progress_percent', sa.Float, default=0.0),
        sa.Column('modules_completed', sa.Integer, default=0),
        sa.Column('total_modules', sa.Integer, default=0),
        sa.Column('highest_quiz_score', sa.Float, nullable=True),
        sa.Column('average_quiz_score', sa.Float, nullable=True),
        sa.Column('enrolled_at', sa.DateTime, default=sa.func.now()),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('deadline', sa.Date, nullable=True),
        sa.Column('last_activity_at', sa.DateTime, nullable=True),
        sa.Column('certificate_issued', sa.Boolean, default=False),
        sa.Column('certificate_url', sa.String(500), nullable=True),
        sa.Column('assigned_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assignment_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_training_enrollments_tenant_id', 'training_enrollments', ['tenant_id'])
    op.create_index('ix_training_enrollments_course_id', 'training_enrollments', ['course_id'])
    op.create_index('ix_training_enrollments_user_id', 'training_enrollments', ['user_id'])
    op.create_index('ix_training_enrollments_status', 'training_enrollments', ['status'])

    # Create module_progress table
    op.create_table(
        'module_progress',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enrollment_id', sa.String(36), sa.ForeignKey('training_enrollments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', sa.String(36), sa.ForeignKey('training_modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_completed', sa.Boolean, default=False),
        sa.Column('completion_percent', sa.Float, default=0.0),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('time_spent_seconds', sa.Integer, default=0),
        sa.Column('last_position_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_module_progress_tenant_id', 'module_progress', ['tenant_id'])
    op.create_index('ix_module_progress_enrollment_id', 'module_progress', ['enrollment_id'])
    op.create_index('ix_module_progress_module_id', 'module_progress', ['module_id'])

    # Create quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quiz_id', sa.String(36), sa.ForeignKey('training_quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enrollment_id', sa.String(36), sa.ForeignKey('training_enrollments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('attempt_number', sa.Integer, default=1),
        sa.Column('score', sa.Float, default=0.0),
        sa.Column('points_earned', sa.Integer, default=0),
        sa.Column('points_possible', sa.Integer, default=0),
        sa.Column('passed', sa.Boolean, default=False),
        sa.Column('answers', sa.JSON, default=[]),
        sa.Column('started_at', sa.DateTime, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('time_taken_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_quiz_attempts_tenant_id', 'quiz_attempts', ['tenant_id'])
    op.create_index('ix_quiz_attempts_quiz_id', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])

    # Create phishing_templates table
    op.create_table(
        'phishing_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('sender_name', sa.String(255), nullable=False),
        sa.Column('sender_email', sa.String(255), nullable=False),
        sa.Column('body_html', sa.Text, nullable=False),
        sa.Column('body_text', sa.Text, nullable=True),
        sa.Column('landing_page_html', sa.Text, nullable=True),
        sa.Column('landing_page_url', sa.String(500), nullable=True),
        sa.Column('difficulty', sa.String(50), default='medium'),
        sa.Column('red_flags', sa.JSON, default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_phishing_templates_tenant_id', 'phishing_templates', ['tenant_id'])

    # Create phishing_campaigns table
    op.create_table(
        'phishing_campaigns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', sa.String(36), sa.ForeignKey('phishing_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'scheduled', 'active', 'completed', 'cancelled', name='campaign_status_enum', create_type=False), default='draft'),
        sa.Column('scheduled_start', sa.DateTime, nullable=True),
        sa.Column('scheduled_end', sa.DateTime, nullable=True),
        sa.Column('actual_start', sa.DateTime, nullable=True),
        sa.Column('actual_end', sa.DateTime, nullable=True),
        sa.Column('target_departments', sa.JSON, default=[]),
        sa.Column('target_user_ids', sa.JSON, default=[]),
        sa.Column('exclude_user_ids', sa.JSON, default=[]),
        sa.Column('send_window_start_hour', sa.Integer, default=9),
        sa.Column('send_window_end_hour', sa.Integer, default=17),
        sa.Column('randomize_send_time', sa.Boolean, default=True),
        sa.Column('total_targets', sa.Integer, default=0),
        sa.Column('emails_sent', sa.Integer, default=0),
        sa.Column('emails_opened', sa.Integer, default=0),
        sa.Column('links_clicked', sa.Integer, default=0),
        sa.Column('credentials_submitted', sa.Integer, default=0),
        sa.Column('reported_count', sa.Integer, default=0),
        sa.Column('training_course_id', sa.String(36), sa.ForeignKey('training_courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('auto_enroll_on_fail', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_phishing_campaigns_tenant_id', 'phishing_campaigns', ['tenant_id'])
    op.create_index('ix_phishing_campaigns_status', 'phishing_campaigns', ['status'])

    # Create phishing_targets table
    op.create_table(
        'phishing_targets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('campaign_id', sa.String(36), sa.ForeignKey('phishing_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tracking_id', sa.String(64), nullable=False, unique=True),
        sa.Column('result', postgresql.ENUM('pending', 'delivered', 'opened', 'clicked', 'reported', 'no_action', name='phishing_result_enum', create_type=False), default='pending'),
        sa.Column('email_sent_at', sa.DateTime, nullable=True),
        sa.Column('email_opened_at', sa.DateTime, nullable=True),
        sa.Column('link_clicked_at', sa.DateTime, nullable=True),
        sa.Column('credentials_submitted_at', sa.DateTime, nullable=True),
        sa.Column('reported_at', sa.DateTime, nullable=True),
        sa.Column('submitted_data', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('training_assigned', sa.Boolean, default=False),
        sa.Column('training_enrollment_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_phishing_targets_tenant_id', 'phishing_targets', ['tenant_id'])
    op.create_index('ix_phishing_targets_campaign_id', 'phishing_targets', ['campaign_id'])
    op.create_index('ix_phishing_targets_tracking_id', 'phishing_targets', ['tracking_id'])
    op.create_index('ix_phishing_targets_result', 'phishing_targets', ['result'])

    # Create training_badges table
    op.create_table(
        'training_badges',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('category', postgresql.ENUM('completion', 'streak', 'performance', 'phishing', 'milestone', 'special', name='badge_category_enum', create_type=False), nullable=False),
        sa.Column('icon', sa.String(50), default='award'),
        sa.Column('color', sa.String(50), default='gold'),
        sa.Column('criteria', sa.JSON, default={}),
        sa.Column('points', sa.Integer, default=10),
        sa.Column('is_rare', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_training_badges_tenant_id', 'training_badges', ['tenant_id'])

    # Create user_badges table
    op.create_table(
        'user_badges',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', sa.String(36), sa.ForeignKey('training_badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('earned_at', sa.DateTime, default=sa.func.now()),
        sa.Column('earned_for', sa.String(255), nullable=True),
        sa.Column('notified', sa.Boolean, default=False),
    )
    op.create_index('ix_user_badges_tenant_id', 'user_badges', ['tenant_id'])
    op.create_index('ix_user_badges_badge_id', 'user_badges', ['badge_id'])
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])

    # Create training_stats table
    op.create_table(
        'training_stats',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('courses_completed', sa.Integer, default=0),
        sa.Column('courses_in_progress', sa.Integer, default=0),
        sa.Column('modules_completed', sa.Integer, default=0),
        sa.Column('quizzes_passed', sa.Integer, default=0),
        sa.Column('total_points', sa.Integer, default=0),
        sa.Column('average_quiz_score', sa.Float, default=0.0),
        sa.Column('total_training_time_minutes', sa.Integer, default=0),
        sa.Column('current_streak_days', sa.Integer, default=0),
        sa.Column('longest_streak_days', sa.Integer, default=0),
        sa.Column('last_activity_date', sa.Date, nullable=True),
        sa.Column('phishing_tests_received', sa.Integer, default=0),
        sa.Column('phishing_emails_reported', sa.Integer, default=0),
        sa.Column('phishing_links_clicked', sa.Integer, default=0),
        sa.Column('badges_earned', sa.Integer, default=0),
        sa.Column('rank', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_training_stats_tenant_id', 'training_stats', ['tenant_id'])
    op.create_index('ix_training_stats_user_id', 'training_stats', ['user_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('training_stats')
    op.drop_table('user_badges')
    op.drop_table('training_badges')
    op.drop_table('phishing_targets')
    op.drop_table('phishing_campaigns')
    op.drop_table('phishing_templates')
    op.drop_table('quiz_attempts')
    op.drop_table('module_progress')
    op.drop_table('training_enrollments')
    op.drop_table('quiz_questions')
    op.drop_table('training_quizzes')
    op.drop_table('training_modules')
    op.drop_table('course_prerequisites')
    op.drop_table('training_courses')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS badge_category_enum")
    op.execute("DROP TYPE IF EXISTS phishing_result_enum")
    op.execute("DROP TYPE IF EXISTS campaign_status_enum")
    op.execute("DROP TYPE IF EXISTS enrollment_status_enum")
    op.execute("DROP TYPE IF EXISTS question_type_enum")
    op.execute("DROP TYPE IF EXISTS module_type_enum")
    op.execute("DROP TYPE IF EXISTS course_status_enum")
    op.execute("DROP TYPE IF EXISTS course_difficulty_enum")
    op.execute("DROP TYPE IF EXISTS course_category_enum")
