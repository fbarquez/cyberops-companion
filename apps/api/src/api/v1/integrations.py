"""Integration Hub API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.integrations import IntegrationCategory, IntegrationStatus, IntegrationType
from src.schemas.integrations import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse, IntegrationListResponse,
    SyncLogListResponse, WebhookEventListResponse,
    IntegrationTemplateResponse,
    SecurityAwarenessMetricsResponse,
    TestConnectionRequest, TestConnectionResponse,
    ManualSyncRequest, ManualSyncResponse,
    IntegrationsDashboardStats
)
from src.services.integrations_service import IntegrationsService

router = APIRouter(prefix="/integrations")


# ============== Dashboard ==============

@router.get("/dashboard", response_model=IntegrationsDashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get integration dashboard statistics."""
    service = IntegrationsService(db)
    return await service.get_dashboard_stats()


# ============== Templates ==============

@router.get("/templates")
async def list_templates(
    category: Optional[IntegrationCategory] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List available integration templates."""
    service = IntegrationsService(db)
    templates = await service.get_templates(category)
    return [IntegrationTemplateResponse.model_validate(t) for t in templates]


@router.get("/templates/{integration_type}", response_model=IntegrationTemplateResponse)
async def get_template(
    integration_type: IntegrationType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific integration template."""
    service = IntegrationsService(db)
    template = await service.get_template(integration_type)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return IntegrationTemplateResponse.model_validate(template)


@router.post("/templates/seed")
async def seed_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed default integration templates."""
    service = IntegrationsService(db)
    await service.seed_templates()
    return {"message": "Templates seeded successfully"}


# ============== Integrations CRUD ==============

@router.post("", response_model=IntegrationResponse)
async def create_integration(
    data: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new integration."""
    service = IntegrationsService(db)
    integration = await service.create_integration(data, created_by=current_user.id)
    return IntegrationResponse.model_validate(integration)


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[IntegrationCategory] = None,
    status: Optional[IntegrationStatus] = None,
    is_enabled: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List integrations with filtering and pagination."""
    service = IntegrationsService(db)
    return await service.list_integrations(
        page=page,
        size=size,
        category=category,
        status=status,
        is_enabled=is_enabled,
        search=search,
    )


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an integration by ID."""
    service = IntegrationsService(db)
    integration = await service.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return IntegrationResponse.model_validate(integration)


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    data: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an integration."""
    service = IntegrationsService(db)
    integration = await service.update_integration(integration_id, data)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return IntegrationResponse.model_validate(integration)


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an integration."""
    service = IntegrationsService(db)
    success = await service.delete_integration(integration_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"message": "Integration deleted successfully"}


@router.post("/{integration_id}/enable", response_model=IntegrationResponse)
async def enable_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable an integration."""
    service = IntegrationsService(db)
    integration = await service.enable_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return IntegrationResponse.model_validate(integration)


@router.post("/{integration_id}/disable", response_model=IntegrationResponse)
async def disable_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable an integration."""
    service = IntegrationsService(db)
    integration = await service.disable_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return IntegrationResponse.model_validate(integration)


# ============== Test Connection ==============

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    data: TestConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test connection to an external platform."""
    service = IntegrationsService(db)
    return await service.test_connection(
        integration_type=data.integration_type,
        base_url=data.base_url,
        api_key=data.api_key,
        api_secret=data.api_secret,
        username=data.username,
        password=data.password,
        config=data.config,
    )


# ============== Sync Operations ==============

@router.post("/{integration_id}/sync", response_model=ManualSyncResponse)
async def trigger_sync(
    integration_id: str,
    data: Optional[ManualSyncRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a manual sync for an integration."""
    service = IntegrationsService(db)
    result = await service.trigger_sync(
        integration_id=integration_id,
        sync_type=data.sync_type if data else "incremental",
        triggered_by=current_user.id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Integration not found")
    return result


@router.get("/{integration_id}/sync-logs", response_model=SyncLogListResponse)
async def get_sync_logs(
    integration_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get sync logs for an integration."""
    service = IntegrationsService(db)
    return await service.get_sync_logs(integration_id, page, size)


# ============== Webhook Operations ==============

@router.post("/webhook/{webhook_path:path}")
async def receive_webhook(
    webhook_path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive webhook from external platform (no auth required)."""
    service = IntegrationsService(db)

    # Get request details
    headers = dict(request.headers)
    raw_body = await request.body()
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="ignore")}

    event = await service.process_webhook(
        webhook_path=webhook_path,
        headers=headers,
        payload=payload,
        raw_body=raw_body.decode("utf-8", errors="ignore"),
    )

    if not event:
        raise HTTPException(status_code=404, detail="Integration not found for webhook")

    return {"received": True, "event_id": event.id}


@router.get("/{integration_id}/webhooks", response_model=WebhookEventListResponse)
async def get_webhook_events(
    integration_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    processed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get webhook events for an integration."""
    service = IntegrationsService(db)
    return await service.get_webhook_events(integration_id, page, size, processed)


# ============== Security Awareness Metrics ==============

@router.get("/{integration_id}/awareness-metrics", response_model=SecurityAwarenessMetricsResponse)
async def get_awareness_metrics(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security awareness metrics for an integration."""
    service = IntegrationsService(db)
    metrics = await service.get_awareness_metrics(integration_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics found")
    return SecurityAwarenessMetricsResponse.model_validate(metrics)


@router.get("/awareness/aggregated")
async def get_aggregated_awareness_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated security awareness metrics from all integrations."""
    service = IntegrationsService(db)
    return await service.get_aggregated_awareness_metrics()
