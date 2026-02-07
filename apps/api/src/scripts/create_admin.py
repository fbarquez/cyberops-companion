#!/usr/bin/env python3
"""Create admin user with full enterprise access.

Usage:
    python -m src.scripts.create_admin

Or from docker:
    docker exec -it cyberops-companion-api python -m src.scripts.create_admin
"""
import asyncio
import sys
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_maker, init_db
from src.models.user import User, UserRole
from src.models.organization import Organization, OrganizationMember, OrgRole
from src.services.auth_service import AuthService


async def create_enterprise_admin(
    email: str = "admin@cyberops.local",
    password: str = "CyberOps2024!",
    full_name: str = "Enterprise Admin",
    org_name: str = "CyberOps Enterprise"
) -> dict:
    """Create enterprise admin user with full access.

    Returns:
        dict with user and organization details
    """
    await init_db()

    async with async_session_maker() as session:
        async with session.begin():
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User {email} already exists!")
                print(f"  ID: {existing_user.id}")
                print(f"  Role: {existing_user.role.value}")
                print(f"  Super Admin: {existing_user.is_super_admin}")
                return {"user": existing_user, "created": False}

            # Create organization first
            org_id = str(uuid4())
            organization = Organization(
                id=org_id,
                name=org_name,
                slug=org_name.lower().replace(" ", "-"),
                is_active=True,
                plan="enterprise",
                settings={
                    "features": {
                        "bsi_grundschutz": True,
                        "nis2_compliance": True,
                        "ai_copilot": True,
                        "attack_paths": True,
                        "threat_intelligence": True,
                        "vulnerability_management": True,
                        "risk_management": True,
                        "cmdb": True,
                        "tprm": True,
                        "bcm": True,
                        "iso27001": True,
                        "document_management": True,
                        "training": True,
                        "reporting": True,
                        "integrations": True,
                        "sso": True,
                        "api_access": True,
                        "audit_logs": True,
                        "custom_roles": True,
                        "multi_tenant": True,
                    },
                    "limits": {
                        "users": -1,  # unlimited
                        "incidents": -1,
                        "assets": -1,
                        "storage_gb": -1,
                    },
                    "branding": {
                        "logo_url": None,
                        "primary_color": "#6366f1",
                        "company_name": org_name,
                    }
                },
                created_at=datetime.utcnow(),
            )
            session.add(organization)

            # Create admin user
            user_id = str(uuid4())
            hashed_password = AuthService.hash_password(password)

            admin_user = User(
                id=user_id,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
                is_super_admin=True,  # Can access all tenants
                created_at=datetime.utcnow(),
                timezone="Europe/Berlin",
                language="en",
            )
            session.add(admin_user)

            # Link user to organization as owner
            membership = OrganizationMember(
                id=str(uuid4()),
                user_id=user_id,
                organization_id=org_id,
                org_role=OrgRole.OWNER,
                is_active=True,
                is_default=True,
                joined_at=datetime.utcnow(),
            )
            session.add(membership)

            await session.flush()

            print("\n" + "="*60)
            print("  ENTERPRISE ADMIN CREATED SUCCESSFULLY")
            print("="*60)
            print(f"\n  📧 Email:        {email}")
            print(f"  🔑 Password:     {password}")
            print(f"  👤 Name:         {full_name}")
            print(f"  🏢 Organization: {org_name}")
            print(f"  🆔 User ID:      {user_id}")
            print(f"  🏷️  Role:         ADMIN (Super Admin)")
            print(f"\n  ✅ All Enterprise features enabled:")
            print("     - BSI IT-Grundschutz 2023")
            print("     - NIS2 Compliance")
            print("     - AI Copilot")
            print("     - Attack Path Analysis")
            print("     - All other modules...")
            print("\n" + "="*60)
            print("  🌐 Login at: https://your-domain.com/login")
            print("="*60 + "\n")

            return {
                "user": admin_user,
                "organization": organization,
                "created": True,
            }


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Create enterprise admin user")
    parser.add_argument("--email", default="admin@cyberops.local", help="Admin email")
    parser.add_argument("--password", default="CyberOps2024!", help="Admin password")
    parser.add_argument("--name", default="Enterprise Admin", help="Full name")
    parser.add_argument("--org", default="CyberOps Enterprise", help="Organization name")

    args = parser.parse_args()

    await create_enterprise_admin(
        email=args.email,
        password=args.password,
        full_name=args.name,
        org_name=args.org,
    )


if __name__ == "__main__":
    asyncio.run(main())
