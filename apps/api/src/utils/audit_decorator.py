"""Audit logging decorator for automatic action tracking."""
import functools
import uuid
from typing import Callable, Optional, Any
from fastapi import Request

from src.services.audit_service import AuditService


def audit_log(
    action: str,
    resource_type: str,
    get_resource_id: Optional[Callable[..., str]] = None,
    get_resource_name: Optional[Callable[..., str]] = None,
    get_description: Optional[Callable[..., str]] = None,
    include_request_body: bool = False,
    include_response: bool = False,
):
    """Decorator to automatically log API actions to the audit trail.

    Args:
        action: The action type (create, update, delete, etc.)
        resource_type: Type of resource being acted upon
        get_resource_id: Optional function to extract resource ID from kwargs/result
        get_resource_name: Optional function to extract resource name from kwargs/result
        get_description: Optional function to generate description from kwargs/result
        include_request_body: Whether to include request body in new_values
        include_response: Whether to include response in new_values

    Usage:
        @router.post("")
        @audit_log(action="create", resource_type="incident")
        async def create_incident(...):
            ...

        @router.patch("/{incident_id}")
        @audit_log(
            action="update",
            resource_type="incident",
            get_resource_id=lambda kwargs, result: kwargs.get("incident_id")
        )
        async def update_incident(incident_id: str, ...):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract common parameters from kwargs
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request: Optional[Request] = kwargs.get("request")

            # Generate request ID for correlation
            request_id = str(uuid.uuid4())[:8]

            # Extract request info
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent", "")[:500]

            # Capture old values for updates (if applicable)
            old_values = None

            # Execute the actual function
            result = None
            error_message = None
            success = True

            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # Only log if we have a database session
                if db:
                    try:
                        audit_service = AuditService(db)

                        # Extract resource ID
                        resource_id = None
                        if get_resource_id:
                            try:
                                resource_id = get_resource_id(kwargs, result)
                            except Exception:
                                pass
                        elif "incident_id" in kwargs:
                            resource_id = kwargs["incident_id"]
                        elif "id" in kwargs:
                            resource_id = kwargs["id"]
                        elif result and hasattr(result, "id"):
                            resource_id = result.id
                        elif result and isinstance(result, dict) and "id" in result:
                            resource_id = result["id"]

                        # Extract resource name
                        resource_name = None
                        if get_resource_name:
                            try:
                                resource_name = get_resource_name(kwargs, result)
                            except Exception:
                                pass
                        elif result and hasattr(result, "title"):
                            resource_name = result.title
                        elif result and hasattr(result, "name"):
                            resource_name = result.name
                        elif result and isinstance(result, dict):
                            resource_name = result.get("title") or result.get("name")

                        # Generate description
                        description = None
                        if get_description:
                            try:
                                description = get_description(kwargs, result)
                            except Exception:
                                pass
                        else:
                            user_name = current_user.full_name if current_user else "Unknown"
                            if action == "create":
                                description = f"{user_name} created {resource_type}"
                            elif action == "update":
                                description = f"{user_name} updated {resource_type}"
                            elif action == "delete":
                                description = f"{user_name} deleted {resource_type}"
                            else:
                                description = f"{user_name} performed {action} on {resource_type}"

                            if resource_name:
                                description += f": {resource_name}"

                        # Prepare new_values
                        new_values = None
                        if include_response and result:
                            if hasattr(result, "model_dump"):
                                new_values = result.model_dump()
                            elif hasattr(result, "__dict__"):
                                new_values = {
                                    k: v for k, v in result.__dict__.items()
                                    if not k.startswith("_")
                                }
                            elif isinstance(result, dict):
                                new_values = result

                        await audit_service.log_action(
                            user_id=current_user.id if current_user else None,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            resource_name=resource_name,
                            description=description,
                            old_values=old_values,
                            new_values=new_values,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            request_id=request_id,
                            success=success,
                            error_message=error_message,
                        )
                    except Exception:
                        # Don't let audit logging failure affect the API response
                        pass

            return result

        return wrapper
    return decorator


def log_auth_action(
    action: str,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Helper function to log authentication actions.

    This is a simpler function (not a decorator) for logging auth events
    from within auth service methods.

    Args:
        action: The auth action (login, logout, login_failed, etc.)
        user_id: ID of the user
        email: Email of the user (useful for failed logins)
        success: Whether the action succeeded
        error_message: Error message if action failed
        ip_address: Client IP address
        user_agent: Client user agent
    """
    async def _log(db):
        audit_service = AuditService(db)

        description = None
        if action == "login":
            description = f"User logged in: {email}"
        elif action == "logout":
            description = f"User logged out: {email}"
        elif action == "login_failed":
            description = f"Login failed for: {email}"
        elif action == "password_change":
            description = f"Password changed for: {email}"
        else:
            description = f"Auth action {action} for: {email}"

        await audit_service.log_action(
            user_id=user_id,
            action=action,
            resource_type="session",
            resource_name=email,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

    return _log
