"""API v1 router aggregating all endpoints."""
from fastapi import APIRouter

from src.api.v1 import auth, sso, incidents, evidence, checklists, decisions, compliance, tools, threats, vulnerabilities, risks, cmdb, soc, tprm, integrations, reporting, notifications, user_management, attachments, analytics, audit, organizations, iso27001, bcm, attack_paths, documents, training

api_router = APIRouter()

# Include all routers
api_router.include_router(organizations.router, tags=["Organizations"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(sso.router, tags=["SSO Authentication"])
api_router.include_router(audit.router, tags=["Audit"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(evidence.router, tags=["Evidence"])
api_router.include_router(checklists.router, tags=["Checklists"])
api_router.include_router(decisions.router, tags=["Decisions"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(threats.router, prefix="/threats", tags=["Threat Intelligence"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerability Management"])
api_router.include_router(risks.router, tags=["Risk Management"])
api_router.include_router(cmdb.router, tags=["CMDB"])
api_router.include_router(soc.router, tags=["SOC"])
api_router.include_router(tprm.router, tags=["Third-Party Risk Management"])
api_router.include_router(integrations.router, tags=["Integrations"])
api_router.include_router(reporting.router, tags=["Reporting"])
api_router.include_router(notifications.router, tags=["Notifications"])
api_router.include_router(user_management.router, tags=["User Management"])
api_router.include_router(attachments.router, tags=["Attachments"])
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(iso27001.router, tags=["ISO 27001:2022 Compliance"])
api_router.include_router(bcm.router, tags=["Business Continuity Management"])
api_router.include_router(attack_paths.router, tags=["Attack Path Analysis"])
api_router.include_router(documents.router, tags=["Document & Policy Management"])
api_router.include_router(training.router, tags=["Security Awareness & Training"])
