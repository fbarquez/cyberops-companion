"""Audit logging endpoints."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import io

from src.api.deps import DBSession, CurrentUser, AdminUser
from src.services.audit_service import AuditService
from src.schemas.audit import (
    ActivityLogResponse,
    ActivityLogDetailResponse,
    ActivityLogListResponse,
    AuditStatsResponse,
    AuditExportRequest,
)


router = APIRouter(prefix="/audit")


@router.get("/logs", response_model=ActivityLogListResponse)
async def list_audit_logs(
    db: DBSession,
    current_user: CurrentUser,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    action_category: Optional[str] = Query(None, description="Filter by action category"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    search: Optional[str] = Query(None, description="Search in description and resource_name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
):
    """List audit logs with filtering and pagination.

    Requires authentication. Non-admin users can only see their own logs.
    """
    audit_service = AuditService(db)

    # Non-admin users can only see their own logs
    if current_user.role.value not in ["admin", "manager"]:
        user_id = current_user.id

    logs, total = await audit_service.list_logs(
        user_id=user_id,
        action=action,
        action_category=action_category,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        success=success,
        severity=severity,
        search=search,
        page=page,
        size=size,
    )

    # Calculate pages
    pages = (total + size - 1) // size if total > 0 else 1

    return ActivityLogListResponse(
        items=[ActivityLogResponse(**log) for log in logs],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/logs/{log_id}", response_model=ActivityLogDetailResponse)
async def get_audit_log(
    log_id: str,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get a single audit log entry with full details.

    Requires authentication. Non-admin users can only see their own logs.
    """
    audit_service = AuditService(db)
    log = await audit_service.get_log(log_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    # Non-admin users can only see their own logs
    if current_user.role.value not in ["admin", "manager"]:
        if log["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    return ActivityLogDetailResponse(**log)


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    db: DBSession,
    current_user: AdminUser,
):
    """Get audit statistics.

    Requires admin role.
    """
    audit_service = AuditService(db)
    return await audit_service.get_stats()


@router.post("/export")
async def export_audit_logs(
    request: AuditExportRequest,
    db: DBSession,
    current_user: AdminUser,
):
    """Export audit logs to CSV or JSON format.

    Requires admin role.
    """
    audit_service = AuditService(db)

    content, content_type, count = await audit_service.export_logs(
        format=request.format,
        user_id=request.user_id,
        action=request.action,
        resource_type=request.resource_type,
        start_date=request.start_date,
        end_date=request.end_date,
        severity=request.severity,
    )

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    extension = "json" if request.format == "json" else "csv"
    filename = f"audit_logs_{timestamp}.{extension}"

    # Return as streaming response for download
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(count),
        },
    )


@router.get("/actions")
async def get_audit_actions(current_user: CurrentUser):
    """Get list of available audit actions for filtering."""
    return {
        "actions": [
            {"value": "login", "label": "Login", "category": "auth"},
            {"value": "logout", "label": "Logout", "category": "auth"},
            {"value": "login_failed", "label": "Login Failed", "category": "auth"},
            {"value": "password_change", "label": "Password Change", "category": "auth"},
            {"value": "create", "label": "Create", "category": "crud"},
            {"value": "read", "label": "Read", "category": "crud"},
            {"value": "update", "label": "Update", "category": "crud"},
            {"value": "delete", "label": "Delete", "category": "crud"},
            {"value": "export", "label": "Export", "category": "data"},
            {"value": "import", "label": "Import", "category": "data"},
            {"value": "assign", "label": "Assign", "category": "crud"},
            {"value": "escalate", "label": "Escalate", "category": "crud"},
            {"value": "status_change", "label": "Status Change", "category": "crud"},
            {"value": "role_change", "label": "Role Change", "category": "crud"},
            {"value": "config_change", "label": "Config Change", "category": "system"},
        ],
        "categories": [
            {"value": "auth", "label": "Authentication"},
            {"value": "crud", "label": "CRUD Operations"},
            {"value": "data", "label": "Data Operations"},
            {"value": "system", "label": "System"},
        ],
        "resource_types": [
            {"value": "incident", "label": "Incident"},
            {"value": "alert", "label": "Alert"},
            {"value": "user", "label": "User"},
            {"value": "team", "label": "Team"},
            {"value": "role", "label": "Role"},
            {"value": "vulnerability", "label": "Vulnerability"},
            {"value": "risk", "label": "Risk"},
            {"value": "asset", "label": "Asset"},
            {"value": "report", "label": "Report"},
            {"value": "playbook", "label": "Playbook"},
            {"value": "case", "label": "Case"},
            {"value": "ioc", "label": "IOC"},
            {"value": "setting", "label": "Setting"},
            {"value": "api_key", "label": "API Key"},
            {"value": "session", "label": "Session"},
        ],
        "severities": [
            {"value": "info", "label": "Info"},
            {"value": "warning", "label": "Warning"},
            {"value": "critical", "label": "Critical"},
        ],
    }
