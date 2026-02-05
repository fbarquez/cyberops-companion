"""Audit logging service for tracking user actions."""
import csv
import io
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User
from src.models.user_management import ActivityLog
from src.schemas.audit import (
    ActivityLogResponse,
    ActivityLogDetailResponse,
    AuditStatsResponse,
    AuditLogFilter,
)


# Action to severity mapping
ACTION_SEVERITY = {
    # Critical actions
    "login_failed": "warning",
    "password_change": "warning",
    "delete": "warning",
    "role_change": "warning",
    "config_change": "critical",
    "bulk_delete": "critical",
    "export": "info",
    "import": "warning",
    # Default
    "create": "info",
    "update": "info",
    "read": "info",
    "login": "info",
    "logout": "info",
}

# Action to category mapping
ACTION_CATEGORY = {
    "login": "auth",
    "logout": "auth",
    "login_failed": "auth",
    "password_change": "auth",
    "create": "crud",
    "read": "crud",
    "update": "crud",
    "delete": "crud",
    "export": "data",
    "import": "data",
    "bulk_delete": "data",
    "assign": "crud",
    "escalate": "crud",
    "status_change": "crud",
    "role_change": "crud",
    "config_change": "system",
}


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changes_summary: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: Optional[str] = None,
        action_category: Optional[str] = None,
    ) -> ActivityLog:
        """Log an action to the audit trail.

        Args:
            user_id: ID of the user performing the action
            action: The action being performed (create, update, delete, etc.)
            resource_type: Type of resource being acted upon
            resource_id: ID of the specific resource
            resource_name: Human-readable name of the resource
            description: Description of the action
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            changes_summary: Human-readable summary of changes
            ip_address: IP address of the client
            user_agent: User agent string
            request_id: Request correlation ID
            success: Whether the action succeeded
            error_message: Error message if action failed
            severity: Severity level (info, warning, critical)
            action_category: Category of action (auth, crud, system, data)

        Returns:
            The created ActivityLog entry
        """
        # Filter out sensitive data from old_values and new_values
        if old_values:
            old_values = self._filter_sensitive_data(old_values)
        if new_values:
            new_values = self._filter_sensitive_data(new_values)

        # Auto-determine severity if not provided
        if severity is None:
            severity = ACTION_SEVERITY.get(action, "info")
            # Failures are always at least warning
            if not success and severity == "info":
                severity = "warning"

        # Auto-determine category if not provided
        if action_category is None:
            action_category = ACTION_CATEGORY.get(action, "crud")

        # Generate changes_summary if not provided but we have old/new values
        if changes_summary is None and old_values and new_values:
            changes_summary = self._generate_changes_summary(old_values, new_values)

        log = ActivityLog(
            user_id=user_id,
            action=action,
            action_category=action_category,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            old_values=old_values,
            new_values=new_values,
            changes_summary=changes_summary,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message,
            severity=severity,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out sensitive fields from data.

        Args:
            data: Dictionary that may contain sensitive data

        Returns:
            Dictionary with sensitive fields masked
        """
        sensitive_fields = {
            "password", "password_hash", "hashed_password",
            "token", "access_token", "refresh_token", "api_key",
            "secret", "key_hash", "token_hash",
            "credit_card", "ssn", "social_security",
        }

        filtered = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields:
                filtered[key] = "[REDACTED]"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value

        return filtered

    def _generate_changes_summary(
        self,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any]
    ) -> str:
        """Generate a human-readable summary of changes.

        Args:
            old_values: Previous values
            new_values: New values

        Returns:
            Human-readable changes summary
        """
        changes = []
        all_keys = set(old_values.keys()) | set(new_values.keys())

        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)

            if old_val != new_val:
                if old_val is None:
                    changes.append(f"Set {key} to '{new_val}'")
                elif new_val is None:
                    changes.append(f"Removed {key}")
                else:
                    changes.append(f"Changed {key} from '{old_val}' to '{new_val}'")

        return "; ".join(changes) if changes else "No changes"

    async def list_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        action_category: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        severity: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List audit logs with filtering and pagination.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            action_category: Filter by action category
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            success: Filter by success status
            severity: Filter by severity level
            search: Search in description and resource_name
            page: Page number (1-indexed)
            size: Page size

        Returns:
            Tuple of (list of log entries with user info, total count)
        """
        query = select(ActivityLog, User).outerjoin(
            User, ActivityLog.user_id == User.id
        )

        # Apply filters
        conditions = []

        if user_id:
            conditions.append(ActivityLog.user_id == user_id)
        if action:
            conditions.append(ActivityLog.action == action)
        if action_category:
            conditions.append(ActivityLog.action_category == action_category)
        if resource_type:
            conditions.append(ActivityLog.resource_type == resource_type)
        if resource_id:
            conditions.append(ActivityLog.resource_id == resource_id)
        if start_date:
            conditions.append(ActivityLog.created_at >= start_date)
        if end_date:
            conditions.append(ActivityLog.created_at <= end_date)
        if success is not None:
            conditions.append(ActivityLog.success == success)
        if severity:
            conditions.append(ActivityLog.severity == severity)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    ActivityLog.description.ilike(search_term),
                    ActivityLog.resource_name.ilike(search_term),
                    ActivityLog.action.ilike(search_term),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(
            select(ActivityLog.id).where(and_(*conditions) if conditions else True).subquery()
        )
        total = await self.db.scalar(count_query) or 0

        # Order and paginate
        query = query.order_by(desc(ActivityLog.created_at))
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.fetchall()

        # Build response with user info
        logs = []
        for log, user in rows:
            log_dict = {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": user.full_name if user else None,
                "user_email": user.email if user else None,
                "action": log.action,
                "action_category": log.action_category,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "description": log.description,
                "changes_summary": log.changes_summary,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "request_id": log.request_id,
                "success": log.success,
                "error_message": log.error_message,
                "severity": log.severity,
                "created_at": log.created_at,
            }
            logs.append(log_dict)

        return logs, total

    async def get_log(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Get a single audit log entry by ID.

        Args:
            log_id: The ID of the log entry

        Returns:
            Log entry with user info and full values, or None if not found
        """
        query = select(ActivityLog, User).outerjoin(
            User, ActivityLog.user_id == User.id
        ).where(ActivityLog.id == log_id)

        result = await self.db.execute(query)
        row = result.first()

        if not row:
            return None

        log, user = row
        return {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": user.full_name if user else None,
            "user_email": user.email if user else None,
            "action": log.action,
            "action_category": log.action_category,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "resource_name": log.resource_name,
            "description": log.description,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "changes_summary": log.changes_summary,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_id": log.request_id,
            "success": log.success,
            "error_message": log.error_message,
            "severity": log.severity,
            "created_at": log.created_at,
        }

    async def get_stats(self) -> AuditStatsResponse:
        """Get audit statistics.

        Returns:
            Statistics about audit logs
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        # Total logs
        total_logs = await self.db.scalar(
            select(func.count()).select_from(ActivityLog)
        ) or 0

        # Logs today
        logs_today = await self.db.scalar(
            select(func.count()).where(ActivityLog.created_at >= today_start)
        ) or 0

        # Logs this week
        logs_this_week = await self.db.scalar(
            select(func.count()).where(ActivityLog.created_at >= week_start)
        ) or 0

        # Critical actions
        critical_actions = await self.db.scalar(
            select(func.count()).where(ActivityLog.severity == "critical")
        ) or 0

        # Failed actions
        failed_actions = await self.db.scalar(
            select(func.count()).where(ActivityLog.success == False)
        ) or 0

        # Active users today
        active_users_query = select(func.count(func.distinct(ActivityLog.user_id))).where(
            ActivityLog.created_at >= today_start
        )
        active_users_today = await self.db.scalar(active_users_query) or 0

        # Actions by type
        actions_query = select(
            ActivityLog.action, func.count()
        ).group_by(ActivityLog.action)
        actions_result = await self.db.execute(actions_query)
        actions_by_type = {action: count for action, count in actions_result.fetchall()}

        # Actions by resource
        resources_query = select(
            ActivityLog.resource_type, func.count()
        ).where(ActivityLog.resource_type.isnot(None)).group_by(ActivityLog.resource_type)
        resources_result = await self.db.execute(resources_query)
        actions_by_resource = {resource: count for resource, count in resources_result.fetchall()}

        # Actions by severity
        severity_query = select(
            ActivityLog.severity, func.count()
        ).group_by(ActivityLog.severity)
        severity_result = await self.db.execute(severity_query)
        actions_by_severity = {sev or "info": count for sev, count in severity_result.fetchall()}

        # Top users (by action count today)
        top_users_query = select(
            ActivityLog.user_id,
            User.full_name,
            User.email,
            func.count().label("action_count")
        ).outerjoin(User, ActivityLog.user_id == User.id).where(
            ActivityLog.created_at >= today_start
        ).group_by(
            ActivityLog.user_id, User.full_name, User.email
        ).order_by(desc("action_count")).limit(5)

        top_users_result = await self.db.execute(top_users_query)
        top_users = [
            {"user_id": uid, "name": name, "email": email, "action_count": count}
            for uid, name, email, count in top_users_result.fetchall()
        ]

        # Recent critical actions
        critical_query = select(ActivityLog, User).outerjoin(
            User, ActivityLog.user_id == User.id
        ).where(
            ActivityLog.severity == "critical"
        ).order_by(desc(ActivityLog.created_at)).limit(5)

        critical_result = await self.db.execute(critical_query)
        recent_critical = [
            ActivityLogResponse(
                id=log.id,
                user_id=log.user_id,
                user_name=user.full_name if user else None,
                user_email=user.email if user else None,
                action=log.action,
                action_category=log.action_category,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                resource_name=log.resource_name,
                description=log.description,
                changes_summary=log.changes_summary,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                request_id=log.request_id,
                success=log.success,
                error_message=log.error_message,
                severity=log.severity or "info",
                created_at=log.created_at,
            )
            for log, user in critical_result.fetchall()
        ]

        return AuditStatsResponse(
            total_logs=total_logs,
            logs_today=logs_today,
            logs_this_week=logs_this_week,
            critical_actions=critical_actions,
            failed_actions=failed_actions,
            active_users_today=active_users_today,
            actions_by_type=actions_by_type,
            actions_by_resource=actions_by_resource,
            actions_by_severity=actions_by_severity,
            top_users=top_users,
            recent_critical=recent_critical,
        )

    async def export_logs(
        self,
        format: str = "csv",
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[str] = None,
    ) -> tuple[bytes, str, int]:
        """Export audit logs to a file format.

        Args:
            format: Export format (csv or json)
            user_id: Filter by user ID
            action: Filter by action
            resource_type: Filter by resource type
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            severity: Filter by severity

        Returns:
            Tuple of (file content as bytes, content type, record count)
        """
        # Get all matching logs (no pagination for export)
        logs, total = await self.list_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            severity=severity,
            page=1,
            size=10000,  # Reasonable limit for export
        )

        if format == "json":
            # Convert datetime to ISO format for JSON serialization
            for log in logs:
                if log.get("created_at"):
                    log["created_at"] = log["created_at"].isoformat()

            content = json.dumps(logs, indent=2, default=str)
            return content.encode("utf-8"), "application/json", len(logs)

        else:  # CSV
            output = io.StringIO()
            fieldnames = [
                "id", "created_at", "user_id", "user_name", "user_email",
                "action", "action_category", "resource_type", "resource_id",
                "resource_name", "description", "changes_summary",
                "ip_address", "success", "severity", "error_message"
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for log in logs:
                # Format datetime
                if log.get("created_at"):
                    log["created_at"] = log["created_at"].isoformat()
                writer.writerow(log)

            content = output.getvalue()
            return content.encode("utf-8"), "text/csv", len(logs)
