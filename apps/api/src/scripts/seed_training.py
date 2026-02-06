"""Seed script for Security Awareness & Training module."""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from src.config import settings


async def seed_training_data():
    """Seed training data for testing using raw SQL to avoid enum type mismatches."""

    # Create async engine
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get first organization
        result = await db.execute(sa.text("SELECT id, name FROM organizations LIMIT 1"))
        row = result.fetchone()

        if not row:
            print("No organization found. Please create one first.")
            return

        tenant_id = row[0]
        org_name = row[1]
        print(f"Using organization: {org_name} ({tenant_id})")

        # Check if courses already exist
        result = await db.execute(sa.text(
            "SELECT id FROM training_courses WHERE tenant_id = :tenant_id LIMIT 1"
        ), {"tenant_id": tenant_id})
        if result.fetchone():
            print("Training data already exists. Skipping seed.")
            return

        # ============================================================
        # Create Badges
        # ============================================================
        badges = [
            {"name": "First Steps", "description": "Complete your first training course",
             "category": "completion", "icon": "award", "color": "#10B981",
             "criteria": {"type": "courses_completed", "value": 1}, "points": 50},
            {"name": "Security Champion", "description": "Complete 5 security training courses",
             "category": "completion", "icon": "shield", "color": "#3B82F6",
             "criteria": {"type": "courses_completed", "value": 5}, "points": 200},
            {"name": "Quiz Master", "description": "Score 100% on any quiz",
             "category": "performance", "icon": "trophy", "color": "#F59E0B",
             "criteria": {"type": "quiz_score", "value": 100}, "points": 100},
            {"name": "Phishing Detective", "description": "Report 3 phishing simulations correctly",
             "category": "phishing", "icon": "search", "color": "#8B5CF6",
             "criteria": {"type": "phishing_reports", "value": 3}, "points": 150},
            {"name": "Learning Streak", "description": "Complete training for 7 consecutive days",
             "category": "streak", "icon": "flame", "color": "#EF4444",
             "criteria": {"type": "streak_days", "value": 7}, "points": 75},
        ]

        for b in badges:
            await db.execute(sa.text("""
                INSERT INTO training_badges (id, tenant_id, name, description, category, icon, color, criteria, points, is_rare, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :name, :description, CAST(:category AS badge_category_enum), :icon, :color, CAST(:criteria AS json), :points, false, true, NOW(), NOW())
            """), {
                "id": str(uuid4()), "tenant_id": tenant_id, "name": b["name"],
                "description": b["description"], "category": b["category"],
                "icon": b["icon"], "color": b["color"],
                "criteria": json.dumps(b["criteria"]), "points": b["points"]
            })
        print(f"Created {len(badges)} badges")

        # ============================================================
        # Course 1: Security Fundamentals
        # ============================================================
        course1_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_courses (
                id, tenant_id, course_code, title, description, short_description,
                category, difficulty, status, estimated_duration_minutes, passing_score,
                max_attempts, certificate_enabled, objectives, target_audience, tags,
                compliance_frameworks, control_references, mandatory_for, is_featured,
                is_deleted, published_at, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :course_code, :title, :description, :short_description,
                CAST(:category AS course_category_enum), CAST(:difficulty AS course_difficulty_enum),
                CAST(:status AS course_status_enum), :duration, :passing_score, :max_attempts,
                :certificate_enabled, CAST(:objectives AS json), CAST(:target_audience AS json), CAST(:tags AS json),
                CAST(:frameworks AS json), CAST(:controls AS json), CAST(:mandatory_for AS json), :is_featured,
                false, NOW(), NOW(), NOW()
            )
        """), {
            "id": course1_id, "tenant_id": tenant_id, "course_code": "SEC-001",
            "title": "Security Fundamentals",
            "description": "Learn the essential principles of information security. This course covers the CIA triad, common threats, and basic security practices every employee should know.",
            "short_description": "Essential security principles for all employees",
            "category": "security_fundamentals", "difficulty": "beginner", "status": "published",
            "duration": 45, "passing_score": 80, "max_attempts": 3, "certificate_enabled": True,
            "objectives": json.dumps([
                "Understand the CIA triad (Confidentiality, Integrity, Availability)",
                "Identify common security threats and attack vectors",
                "Apply basic security best practices in daily work",
                "Recognize social engineering attempts"
            ]),
            "target_audience": json.dumps(["all_employees"]),
            "tags": json.dumps(["security", "fundamentals", "beginner"]),
            "frameworks": json.dumps(["iso27001", "nis2"]),
            "controls": json.dumps(["A.6.3", "A.7.2.2"]),
            "mandatory_for": json.dumps(["all"]),
            "is_featured": True
        })

        # Course 1 Modules
        module1_1_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_modules (id, tenant_id, course_id, title, description, module_type, content, "order", estimated_duration_minutes, is_mandatory, requires_completion_to_proceed, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :course_id, :title, :description, CAST(:module_type AS module_type_enum), CAST(:content AS json), :order, :duration, :is_mandatory, true, true, NOW(), NOW())
        """), {
            "id": module1_1_id, "tenant_id": tenant_id, "course_id": course1_id,
            "title": "Introduction to Information Security",
            "description": "Overview of what information security is and why it matters.",
            "module_type": "text", "order": 0, "duration": 10, "is_mandatory": True,
            "content": json.dumps({
                "html": """<h2>Welcome to Information Security</h2>
<p>Information security is the practice of protecting information by mitigating information risks.</p>
<h3>Why Security Matters</h3>
<ul>
<li>Protects sensitive business data</li>
<li>Maintains customer trust</li>
<li>Ensures regulatory compliance</li>
<li>Prevents financial losses</li>
</ul>"""
            })
        })

        module1_2_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_modules (id, tenant_id, course_id, title, description, module_type, content, "order", estimated_duration_minutes, is_mandatory, requires_completion_to_proceed, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :course_id, :title, :description, CAST(:module_type AS module_type_enum), CAST(:content AS json), :order, :duration, :is_mandatory, true, true, NOW(), NOW())
        """), {
            "id": module1_2_id, "tenant_id": tenant_id, "course_id": course1_id,
            "title": "The CIA Triad",
            "description": "Learn about Confidentiality, Integrity, and Availability.",
            "module_type": "text", "order": 1, "duration": 15, "is_mandatory": True,
            "content": json.dumps({
                "html": """<h2>The CIA Triad</h2>
<h3>1. Confidentiality</h3>
<p>Ensuring that information is accessible only to those authorized to access it.</p>
<h3>2. Integrity</h3>
<p>Safeguarding the accuracy and completeness of information.</p>
<h3>3. Availability</h3>
<p>Ensuring that authorized users have access to information when required.</p>"""
            })
        })

        module1_3_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_modules (id, tenant_id, course_id, title, description, module_type, content, "order", estimated_duration_minutes, is_mandatory, requires_completion_to_proceed, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :course_id, :title, :description, CAST(:module_type AS module_type_enum), CAST(:content AS json), :order, :duration, :is_mandatory, true, true, NOW(), NOW())
        """), {
            "id": module1_3_id, "tenant_id": tenant_id, "course_id": course1_id,
            "title": "Common Security Threats",
            "description": "Overview of common security threats facing organizations.",
            "module_type": "text", "order": 2, "duration": 12, "is_mandatory": True,
            "content": json.dumps({
                "html": """<h2>Common Security Threats</h2>
<h3>Malware</h3>
<p>Malicious software: Viruses, Ransomware, Trojans, Spyware</p>
<h3>Phishing</h3>
<p>Fraudulent attempts to obtain sensitive information.</p>
<h3>Social Engineering</h3>
<p>Psychological manipulation to trick users into security mistakes.</p>"""
            })
        })

        # Quiz Module
        module1_4_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_modules (id, tenant_id, course_id, title, description, module_type, content, "order", estimated_duration_minutes, is_mandatory, requires_completion_to_proceed, is_active, created_at, updated_at)
            VALUES (:id, :tenant_id, :course_id, :title, :description, CAST(:module_type AS module_type_enum), NULL, :order, :duration, :is_mandatory, true, true, NOW(), NOW())
        """), {
            "id": module1_4_id, "tenant_id": tenant_id, "course_id": course1_id,
            "title": "Final Assessment",
            "description": "Complete this quiz to finish the course.",
            "module_type": "quiz", "order": 3, "duration": 15, "is_mandatory": True
        })

        # Quiz
        quiz1_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_quizzes (id, tenant_id, module_id, title, instructions, passing_score, time_limit_minutes, max_attempts, randomize_questions, randomize_answers, show_correct_answers, created_at, updated_at)
            VALUES (:id, :tenant_id, :module_id, :title, :instructions, :passing_score, :time_limit, :max_attempts, :randomize_q, :randomize_a, :show_correct, NOW(), NOW())
        """), {
            "id": quiz1_id, "tenant_id": tenant_id, "module_id": module1_4_id,
            "title": "Security Fundamentals Assessment",
            "instructions": "Test your knowledge of security fundamentals. You need 80% to pass.",
            "passing_score": 80, "time_limit": 15, "max_attempts": 3,
            "randomize_q": True, "randomize_a": True, "show_correct": True
        })

        # Quiz Questions
        questions = [
            {
                "text": "What does the 'C' in CIA triad stand for?",
                "type": "single_choice",
                "options": [
                    {"id": "a", "text": "Compliance", "is_correct": False},
                    {"id": "b", "text": "Confidentiality", "is_correct": True},
                    {"id": "c", "text": "Control", "is_correct": False},
                    {"id": "d", "text": "Continuity", "is_correct": False}
                ],
                "explanation": "Confidentiality ensures information is accessible only to authorized users.",
                "points": 1
            },
            {
                "text": "Which type of malware encrypts your files and demands payment?",
                "type": "single_choice",
                "options": [
                    {"id": "a", "text": "Virus", "is_correct": False},
                    {"id": "b", "text": "Trojan", "is_correct": False},
                    {"id": "c", "text": "Ransomware", "is_correct": True},
                    {"id": "d", "text": "Spyware", "is_correct": False}
                ],
                "explanation": "Ransomware encrypts files and demands a ransom payment.",
                "points": 1
            },
            {
                "text": "Phishing attacks can only occur through email.",
                "type": "true_false",
                "options": [
                    {"id": "a", "text": "True", "is_correct": False},
                    {"id": "b", "text": "False", "is_correct": True}
                ],
                "explanation": "Phishing can occur through email, SMS, phone calls, and other channels.",
                "points": 1
            },
            {
                "text": "Which of the following are components of the CIA triad?",
                "type": "multiple_choice",
                "options": [
                    {"id": "a", "text": "Confidentiality", "is_correct": True},
                    {"id": "b", "text": "Authentication", "is_correct": False},
                    {"id": "c", "text": "Integrity", "is_correct": True},
                    {"id": "d", "text": "Availability", "is_correct": True}
                ],
                "explanation": "The CIA triad consists of Confidentiality, Integrity, and Availability.",
                "points": 2
            },
            {
                "text": "What is social engineering?",
                "type": "single_choice",
                "options": [
                    {"id": "a", "text": "A type of software development", "is_correct": False},
                    {"id": "b", "text": "Psychological manipulation to trick users", "is_correct": True},
                    {"id": "c", "text": "A network protocol", "is_correct": False},
                    {"id": "d", "text": "A type of firewall", "is_correct": False}
                ],
                "explanation": "Social engineering manipulates people into divulging confidential information.",
                "points": 1
            }
        ]

        for idx, q in enumerate(questions):
            await db.execute(sa.text("""
                INSERT INTO quiz_questions (id, tenant_id, quiz_id, question_text, question_type, options, explanation, points, "order", created_at, updated_at)
                VALUES (:id, :tenant_id, :quiz_id, :question_text, CAST(:question_type AS question_type_enum), CAST(:options AS json), :explanation, :points, :order, NOW(), NOW())
            """), {
                "id": str(uuid4()), "tenant_id": tenant_id, "quiz_id": quiz1_id,
                "question_text": q["text"], "question_type": q["type"],
                "options": json.dumps(q["options"]), "explanation": q["explanation"],
                "points": q["points"], "order": idx
            })

        print(f"Created course: Security Fundamentals with 4 modules and {len(questions)} quiz questions")

        # ============================================================
        # Course 2: Phishing Awareness
        # ============================================================
        course2_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_courses (
                id, tenant_id, course_code, title, description, short_description,
                category, difficulty, status, estimated_duration_minutes, passing_score,
                max_attempts, certificate_enabled, objectives, target_audience, tags,
                compliance_frameworks, control_references, mandatory_for, is_featured,
                is_deleted, published_at, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :course_code, :title, :description, :short_description,
                CAST(:category AS course_category_enum), CAST(:difficulty AS course_difficulty_enum),
                CAST(:status AS course_status_enum), :duration, :passing_score, :max_attempts,
                :certificate_enabled, CAST(:objectives AS json), CAST(:target_audience AS json), CAST(:tags AS json),
                CAST(:frameworks AS json), CAST(:controls AS json), CAST(:mandatory_for AS json), :is_featured,
                false, NOW(), NOW(), NOW()
            )
        """), {
            "id": course2_id, "tenant_id": tenant_id, "course_code": "PHI-001",
            "title": "Phishing Awareness",
            "description": "Learn to identify and protect yourself from phishing attacks.",
            "short_description": "Protect yourself from phishing attacks",
            "category": "phishing_awareness", "difficulty": "beginner", "status": "published",
            "duration": 30, "passing_score": 80, "max_attempts": 3, "certificate_enabled": True,
            "objectives": json.dumps([
                "Recognize common phishing indicators",
                "Understand different types of phishing attacks",
                "Know how to report suspicious emails"
            ]),
            "target_audience": json.dumps(["all_employees"]),
            "tags": json.dumps(["phishing", "email", "security"]),
            "frameworks": json.dumps(["iso27001"]),
            "controls": json.dumps(["A.6.3"]),
            "mandatory_for": json.dumps(["all"]),
            "is_featured": True
        })

        # Course 2 Modules
        modules2 = [
            {"title": "What is Phishing?", "description": "Introduction to phishing attacks.",
             "content": {"html": "<h2>Understanding Phishing</h2><p>Phishing uses disguised communications as a weapon to steal credentials or install malware.</p>"},
             "order": 0, "duration": 8},
            {"title": "Identifying Phishing Emails", "description": "Learn the red flags.",
             "content": {"html": "<h2>Red Flags</h2><ul><li>Suspicious sender address</li><li>Urgent language</li><li>Suspicious links</li><li>Grammar errors</li></ul>"},
             "order": 1, "duration": 12},
            {"title": "How to Report Phishing", "description": "Proper reporting procedures.",
             "content": {"html": "<h2>Reporting</h2><ol><li>Don't click or reply</li><li>Report to IT Security</li><li>Delete the email</li></ol>"},
             "order": 2, "duration": 10}
        ]
        for m in modules2:
            await db.execute(sa.text("""
                INSERT INTO training_modules (id, tenant_id, course_id, title, description, module_type, content, "order", estimated_duration_minutes, is_mandatory, requires_completion_to_proceed, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :course_id, :title, :description, CAST(:module_type AS module_type_enum), CAST(:content AS json), :order, :duration, true, true, true, NOW(), NOW())
            """), {
                "id": str(uuid4()), "tenant_id": tenant_id, "course_id": course2_id,
                "title": m["title"], "description": m["description"], "module_type": "text",
                "content": json.dumps(m["content"]), "order": m["order"], "duration": m["duration"]
            })
        print(f"Created course: Phishing Awareness with {len(modules2)} modules")

        # ============================================================
        # Course 3: Password Security
        # ============================================================
        course3_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_courses (
                id, tenant_id, course_code, title, description, short_description,
                category, difficulty, status, estimated_duration_minutes, passing_score,
                max_attempts, certificate_enabled, objectives, target_audience, tags,
                compliance_frameworks, control_references, mandatory_for, is_featured,
                is_deleted, published_at, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :course_code, :title, :description, :short_description,
                CAST(:category AS course_category_enum), CAST(:difficulty AS course_difficulty_enum),
                CAST(:status AS course_status_enum), :duration, :passing_score, :max_attempts,
                :certificate_enabled, CAST(:objectives AS json), CAST(:target_audience AS json), CAST(:tags AS json),
                CAST(:frameworks AS json), CAST(:controls AS json), CAST(:mandatory_for AS json), :is_featured,
                false, NOW(), NOW(), NOW()
            )
        """), {
            "id": course3_id, "tenant_id": tenant_id, "course_code": "PWD-001",
            "title": "Password Security Best Practices",
            "description": "Master the art of creating and managing secure passwords.",
            "short_description": "Create and manage secure passwords",
            "category": "password_security", "difficulty": "beginner", "status": "published",
            "duration": 25, "passing_score": 80, "max_attempts": 3, "certificate_enabled": True,
            "objectives": json.dumps([
                "Create strong, unique passwords",
                "Understand and use password managers",
                "Enable multi-factor authentication"
            ]),
            "target_audience": json.dumps(["all_employees"]),
            "tags": json.dumps(["passwords", "authentication", "mfa"]),
            "frameworks": json.dumps(["iso27001", "nis2"]),
            "controls": json.dumps(["A.5.17", "A.8.5"]),
            "mandatory_for": json.dumps([]),
            "is_featured": False
        })

        # Course 3 Modules
        modules3 = [
            {"title": "Creating Strong Passwords", "description": "Characteristics of strong passwords.",
             "content": {"html": "<h2>Strong Passwords</h2><p>Use 12+ characters, mix letters/numbers/symbols, never use personal info.</p>"},
             "order": 0, "duration": 10},
            {"title": "Password Managers", "description": "How to use password managers.",
             "content": {"html": "<h2>Password Managers</h2><p>Store passwords securely in an encrypted vault. Recommended: 1Password, Bitwarden, LastPass.</p>"},
             "order": 1, "duration": 8},
            {"title": "Multi-Factor Authentication", "description": "Understanding MFA.",
             "content": {"html": "<h2>MFA</h2><p>Requires 2+ verification factors: something you know, have, or are.</p>"},
             "order": 2, "duration": 7}
        ]
        for m in modules3:
            await db.execute(sa.text("""
                INSERT INTO training_modules (id, tenant_id, course_id, title, description, module_type, content, "order", estimated_duration_minutes, is_mandatory, requires_completion_to_proceed, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :course_id, :title, :description, CAST(:module_type AS module_type_enum), CAST(:content AS json), :order, :duration, true, true, true, NOW(), NOW())
            """), {
                "id": str(uuid4()), "tenant_id": tenant_id, "course_id": course3_id,
                "title": m["title"], "description": m["description"], "module_type": "text",
                "content": json.dumps(m["content"]), "order": m["order"], "duration": m["duration"]
            })
        print(f"Created course: Password Security with {len(modules3)} modules")

        # ============================================================
        # Course 4: Data Protection
        # ============================================================
        course4_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_courses (
                id, tenant_id, course_code, title, description, short_description,
                category, difficulty, status, estimated_duration_minutes, passing_score,
                max_attempts, certificate_enabled, objectives, target_audience, tags,
                compliance_frameworks, control_references, mandatory_for, is_featured,
                is_deleted, published_at, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :course_code, :title, :description, :short_description,
                CAST(:category AS course_category_enum), CAST(:difficulty AS course_difficulty_enum),
                CAST(:status AS course_status_enum), :duration, :passing_score, :max_attempts,
                :certificate_enabled, CAST(:objectives AS json), CAST(:target_audience AS json), CAST(:tags AS json),
                CAST(:frameworks AS json), CAST(:controls AS json), CAST(:mandatory_for AS json), :is_featured,
                false, NOW(), NOW(), NOW()
            )
        """), {
            "id": course4_id, "tenant_id": tenant_id, "course_code": "DAT-001",
            "title": "Data Protection & Privacy",
            "description": "Understanding data classification and GDPR compliance.",
            "short_description": "Handle sensitive data responsibly",
            "category": "data_protection", "difficulty": "intermediate", "status": "published",
            "duration": 40, "passing_score": 80, "max_attempts": 3, "certificate_enabled": True,
            "objectives": json.dumps([
                "Classify data according to sensitivity",
                "Handle personal data per GDPR"
            ]),
            "target_audience": json.dumps(["all_employees", "managers"]),
            "tags": json.dumps(["gdpr", "privacy", "data protection"]),
            "frameworks": json.dumps(["iso27001", "gdpr"]),
            "controls": json.dumps(["A.5.12", "A.5.13"]),
            "mandatory_for": json.dumps(["hr", "finance"]),
            "is_featured": False
        })
        print(f"Created course: Data Protection & Privacy")

        # ============================================================
        # Course 5: Incident Response
        # ============================================================
        course5_id = str(uuid4())
        await db.execute(sa.text("""
            INSERT INTO training_courses (
                id, tenant_id, course_code, title, description, short_description,
                category, difficulty, status, estimated_duration_minutes, passing_score,
                max_attempts, certificate_enabled, objectives, target_audience, tags,
                compliance_frameworks, control_references, mandatory_for, is_featured,
                is_deleted, published_at, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :course_code, :title, :description, :short_description,
                CAST(:category AS course_category_enum), CAST(:difficulty AS course_difficulty_enum),
                CAST(:status AS course_status_enum), :duration, :passing_score, :max_attempts,
                :certificate_enabled, CAST(:objectives AS json), CAST(:target_audience AS json), CAST(:tags AS json),
                CAST(:frameworks AS json), CAST(:controls AS json), CAST(:mandatory_for AS json), :is_featured,
                false, NOW(), NOW(), NOW()
            )
        """), {
            "id": course5_id, "tenant_id": tenant_id, "course_code": "INC-001",
            "title": "Incident Response Fundamentals",
            "description": "Learn how to identify, report, and respond to security incidents.",
            "short_description": "Respond effectively to security incidents",
            "category": "incident_response", "difficulty": "advanced", "status": "published",
            "duration": 60, "passing_score": 85, "max_attempts": 2, "certificate_enabled": True,
            "objectives": json.dumps([
                "Understand the incident response lifecycle",
                "Identify and classify security incidents",
                "Follow proper incident reporting procedures"
            ]),
            "target_audience": json.dumps(["it_staff", "security_team"]),
            "tags": json.dumps(["incident response", "security operations"]),
            "frameworks": json.dumps(["iso27001", "nis2"]),
            "controls": json.dumps(["A.5.24", "A.5.25"]),
            "mandatory_for": json.dumps(["security"]),
            "is_featured": False
        })
        print(f"Created course: Incident Response Fundamentals")

        # Commit all changes
        await db.commit()

        print("\n" + "="*50)
        print("Training seed completed successfully!")
        print("="*50)
        print(f"\nCreated:")
        print(f"  - 5 Badges")
        print(f"  - 5 Training Courses")
        print(f"  - 10 Training Modules")
        print(f"  - 1 Quiz with 5 Questions")
        print(f"\nYou can now test the training module at /training")


if __name__ == "__main__":
    asyncio.run(seed_training_data())
