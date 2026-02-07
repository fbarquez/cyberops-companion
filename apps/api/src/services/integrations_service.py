"""Integration Hub service."""
import math
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.integrations import (
    Integration, IntegrationSyncLog, WebhookEvent,
    IntegrationTemplate, SecurityAwarenessMetrics,
    IntegrationType, IntegrationCategory, IntegrationStatus,
    SyncDirection, SyncFrequency
)
from src.schemas.integrations import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse, IntegrationListResponse,
    SyncLogResponse, SyncLogListResponse,
    WebhookEventResponse, WebhookEventListResponse,
    IntegrationTemplateResponse,
    SecurityAwarenessMetricsResponse,
    TestConnectionResponse, ManualSyncResponse,
    IntegrationsDashboardStats
)


class IntegrationsService:
    """Service for managing integrations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== Integration CRUD ==============

    async def create_integration(
        self, data: IntegrationCreate, created_by: Optional[str] = None
    ) -> Integration:
        """Create a new integration."""
        # Generate webhook URL and secret
        webhook_secret = secrets.token_urlsafe(32)
        webhook_url = f"/api/v1/integrations/webhook/{secrets.token_urlsafe(16)}"

        integration = Integration(
            name=data.name,
            description=data.description,
            integration_type=data.integration_type,
            category=data.category,
            base_url=data.base_url,
            api_key=data.api_key,
            api_secret=data.api_secret,
            username=data.username,
            password=data.password,
            config=data.config,
            sync_direction=data.sync_direction,
            sync_frequency=data.sync_frequency,
            data_mappings=data.data_mappings,
            sync_filters=data.sync_filters,
            webhook_secret=webhook_secret,
            webhook_url=webhook_url,
            created_by=created_by,
        )

        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def get_integration(self, integration_id: str) -> Optional[Integration]:
        """Get integration by ID."""
        result = await self.db.execute(
            select(Integration).where(Integration.id == integration_id)
        )
        return result.scalar_one_or_none()

    async def list_integrations(
        self,
        page: int = 1,
        size: int = 20,
        category: Optional[IntegrationCategory] = None,
        status: Optional[IntegrationStatus] = None,
        is_enabled: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> IntegrationListResponse:
        """List integrations with filtering and pagination."""
        query = select(Integration)

        if category:
            query = query.where(Integration.category == category)
        if status:
            query = query.where(Integration.status == status)
        if is_enabled is not None:
            query = query.where(Integration.is_enabled == is_enabled)
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Integration.name.ilike(search_filter),
                    Integration.description.ilike(search_filter),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(Integration.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        integrations = result.scalars().all()

        return IntegrationListResponse(
            items=[IntegrationResponse.model_validate(i) for i in integrations],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    async def update_integration(
        self, integration_id: str, data: IntegrationUpdate
    ) -> Optional[Integration]:
        """Update an integration."""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(integration, field, value)

        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration."""
        integration = await self.get_integration(integration_id)
        if not integration:
            return False

        await self.db.delete(integration)
        await self.db.commit()
        return True

    async def enable_integration(self, integration_id: str) -> Optional[Integration]:
        """Enable an integration."""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        integration.is_enabled = True
        integration.status = IntegrationStatus.ACTIVE

        # Calculate next sync time
        integration.next_sync_at = self._calculate_next_sync(integration.sync_frequency)

        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def disable_integration(self, integration_id: str) -> Optional[Integration]:
        """Disable an integration."""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        integration.is_enabled = False
        integration.status = IntegrationStatus.INACTIVE
        integration.next_sync_at = None

        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    def _calculate_next_sync(self, frequency: SyncFrequency) -> datetime:
        """Calculate next sync time based on frequency."""
        now = datetime.utcnow()
        intervals = {
            SyncFrequency.EVERY_5_MIN: timedelta(minutes=5),
            SyncFrequency.EVERY_15_MIN: timedelta(minutes=15),
            SyncFrequency.EVERY_30_MIN: timedelta(minutes=30),
            SyncFrequency.HOURLY: timedelta(hours=1),
            SyncFrequency.EVERY_6_HOURS: timedelta(hours=6),
            SyncFrequency.DAILY: timedelta(days=1),
            SyncFrequency.WEEKLY: timedelta(weeks=1),
        }
        return now + intervals.get(frequency, timedelta(hours=1))

    # ============== Test Connection ==============

    async def test_connection(
        self,
        integration_type: IntegrationType,
        base_url: Optional[str],
        api_key: Optional[str],
        api_secret: Optional[str],
        username: Optional[str],
        password: Optional[str],
        config: Optional[Dict[str, Any]],
    ) -> TestConnectionResponse:
        """Test connection to an external platform."""
        # This is a placeholder - actual implementation would make HTTP calls
        # to the external platform's API to verify credentials

        start_time = datetime.utcnow()

        try:
            # Simulate connection test based on integration type
            # In production, this would make actual API calls
            if not base_url and integration_type not in [
                IntegrationType.VIRUSTOTAL,
                IntegrationType.OTX,
            ]:
                return TestConnectionResponse(
                    success=False,
                    message="Base URL is required",
                    details=None,
                    response_time_ms=0,
                )

            if not api_key and not (username and password):
                return TestConnectionResponse(
                    success=False,
                    message="API key or username/password is required",
                    details=None,
                    response_time_ms=0,
                )

            # Simulate successful connection
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            return TestConnectionResponse(
                success=True,
                message=f"Successfully connected to {integration_type.value}",
                details={
                    "platform": integration_type.value,
                    "api_version": "v1",
                },
                response_time_ms=int(elapsed),
            )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return TestConnectionResponse(
                success=False,
                message=f"Connection failed: {str(e)}",
                details=None,
                response_time_ms=int(elapsed),
            )

    async def test_integration_connection(
        self, integration: Integration
    ) -> TestConnectionResponse:
        """Test connection for an existing integration using saved credentials."""
        start_time = datetime.utcnow()

        try:
            # Check if this is a scanner integration
            scanner_types = {
                IntegrationType.NESSUS: "nessus",
                IntegrationType.OPENVAS: "openvas",
                IntegrationType.QUALYS: "qualys",
            }

            if integration.integration_type in scanner_types:
                # Use real scanner adapter for connection test
                from src.integrations.scanners import (
                    get_scanner_adapter,
                    ScannerConfig,
                )
                from src.integrations.scanners.exceptions import (
                    ScannerError,
                    ScannerConnectionError,
                    ScannerAuthenticationError,
                )

                adapter = None
                try:
                    config = ScannerConfig.from_integration(integration)
                    adapter = get_scanner_adapter(config)

                    # Test the connection
                    await adapter.test_connection()

                    elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

                    # Update integration health status
                    integration.last_health_check = datetime.utcnow()
                    integration.health_status = "ok"
                    integration.error_message = None
                    integration.consecutive_failures = 0
                    await self.db.commit()

                    return TestConnectionResponse(
                        success=True,
                        message=f"Successfully connected to {integration.integration_type.value}",
                        details={
                            "platform": integration.integration_type.value,
                            "scanner_type": scanner_types[integration.integration_type],
                            "base_url": integration.base_url,
                        },
                        response_time_ms=int(elapsed),
                    )

                except ScannerAuthenticationError as e:
                    elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
                    integration.last_health_check = datetime.utcnow()
                    integration.health_status = "down"
                    integration.error_message = str(e)
                    integration.consecutive_failures += 1
                    await self.db.commit()

                    return TestConnectionResponse(
                        success=False,
                        message=f"Authentication failed: {str(e)}",
                        details={"error_type": "authentication"},
                        response_time_ms=int(elapsed),
                    )

                except ScannerConnectionError as e:
                    elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
                    integration.last_health_check = datetime.utcnow()
                    integration.health_status = "down"
                    integration.error_message = str(e)
                    integration.consecutive_failures += 1
                    await self.db.commit()

                    return TestConnectionResponse(
                        success=False,
                        message=f"Connection failed: {str(e)}",
                        details={"error_type": "connection"},
                        response_time_ms=int(elapsed),
                    )

                except ScannerError as e:
                    elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
                    integration.last_health_check = datetime.utcnow()
                    integration.health_status = "degraded"
                    integration.error_message = str(e)
                    integration.consecutive_failures += 1
                    await self.db.commit()

                    return TestConnectionResponse(
                        success=False,
                        message=f"Scanner error: {str(e)}",
                        details={"error_type": "scanner_error"},
                        response_time_ms=int(elapsed),
                    )

                finally:
                    if adapter:
                        await adapter.close()

            else:
                # For non-scanner integrations, use basic HTTP test
                return await self.test_connection(
                    integration_type=integration.integration_type,
                    base_url=integration.base_url,
                    api_key=integration.api_key,
                    api_secret=integration.api_secret,
                    username=integration.username,
                    password=integration.password,
                    config=integration.config,
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return TestConnectionResponse(
                success=False,
                message=f"Connection test failed: {str(e)}",
                details=None,
                response_time_ms=int(elapsed),
            )

    # ============== Sync Operations ==============

    async def trigger_sync(
        self,
        integration_id: str,
        sync_type: str = "incremental",
        triggered_by: Optional[str] = None,
    ) -> Optional[ManualSyncResponse]:
        """Trigger a manual sync for an integration."""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        # Create sync log
        sync_log = IntegrationSyncLog(
            integration_id=integration_id,
            sync_type=sync_type,
            direction=integration.sync_direction,
            triggered_by=triggered_by or "manual",
        )
        self.db.add(sync_log)
        await self.db.commit()
        await self.db.refresh(sync_log)

        # In production, this would queue the sync job
        # For now, simulate immediate completion
        sync_log.status = "success"
        sync_log.completed_at = datetime.utcnow()
        sync_log.duration_seconds = 1
        sync_log.records_fetched = 0
        sync_log.records_created = 0
        sync_log.records_updated = 0

        integration.last_sync_at = datetime.utcnow()
        integration.next_sync_at = self._calculate_next_sync(integration.sync_frequency)

        await self.db.commit()

        return ManualSyncResponse(
            sync_log_id=sync_log.id,
            status="success",
            message=f"Sync triggered for {integration.name}",
        )

    async def get_sync_logs(
        self,
        integration_id: str,
        page: int = 1,
        size: int = 20,
    ) -> SyncLogListResponse:
        """Get sync logs for an integration."""
        query = select(IntegrationSyncLog).where(
            IntegrationSyncLog.integration_id == integration_id
        )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(IntegrationSyncLog.started_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return SyncLogListResponse(
            items=[SyncLogResponse.model_validate(l) for l in logs],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    # ============== Webhook Operations ==============

    async def process_webhook(
        self,
        webhook_path: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        raw_body: str,
    ) -> Optional[WebhookEvent]:
        """Process incoming webhook event."""
        # Find integration by webhook URL
        result = await self.db.execute(
            select(Integration).where(
                Integration.webhook_url.contains(webhook_path)
            )
        )
        integration = result.scalar_one_or_none()

        if not integration:
            return None

        # Create webhook event
        event = WebhookEvent(
            integration_id=integration.id,
            event_type=payload.get("event_type") or payload.get("type"),
            event_id=payload.get("id") or payload.get("event_id"),
            headers=headers,
            payload=payload,
            raw_body=raw_body,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        # Process the webhook (in production, this would be async/queued)
        await self._process_webhook_event(event, integration)

        return event

    async def _process_webhook_event(
        self, event: WebhookEvent, integration: Integration
    ):
        """Process a webhook event and create corresponding entities."""
        try:
            # Map webhook data based on integration type
            # This is where we'd create alerts, incidents, etc. from webhook data

            event.processed = True
            event.processed_at = datetime.utcnow()
            event.processing_result = "success"

            await self.db.commit()

        except Exception as e:
            event.processed = True
            event.processed_at = datetime.utcnow()
            event.processing_result = "failed"
            event.processing_error = str(e)
            await self.db.commit()

    async def get_webhook_events(
        self,
        integration_id: str,
        page: int = 1,
        size: int = 20,
        processed: Optional[bool] = None,
    ) -> WebhookEventListResponse:
        """Get webhook events for an integration."""
        query = select(WebhookEvent).where(
            WebhookEvent.integration_id == integration_id
        )

        if processed is not None:
            query = query.where(WebhookEvent.processed == processed)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(WebhookEvent.received_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        events = result.scalars().all()

        return WebhookEventListResponse(
            items=[WebhookEventResponse.model_validate(e) for e in events],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    # ============== Templates ==============

    async def get_templates(
        self, category: Optional[IntegrationCategory] = None
    ) -> List[IntegrationTemplate]:
        """Get available integration templates."""
        query = select(IntegrationTemplate).where(IntegrationTemplate.is_active == True)

        if category:
            query = query.where(IntegrationTemplate.category == category)

        query = query.order_by(IntegrationTemplate.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_template(
        self, integration_type: IntegrationType
    ) -> Optional[IntegrationTemplate]:
        """Get a specific integration template."""
        result = await self.db.execute(
            select(IntegrationTemplate).where(
                IntegrationTemplate.integration_type == integration_type
            )
        )
        return result.scalar_one_or_none()

    async def seed_templates(self):
        """Seed default integration templates."""
        templates = [
            # Security Awareness
            {
                "integration_type": IntegrationType.KNOWBE4,
                "category": IntegrationCategory.SECURITY_AWARENESS,
                "name": "KnowBe4",
                "description": "Security awareness training and phishing simulation platform",
                "vendor": "KnowBe4",
                "documentation_url": "https://developer.knowbe4.com/",
                "supports_inbound": True,
                "supports_outbound": False,
                "supports_webhook": True,
                "supported_entities": ["training_metrics", "phishing_metrics", "users"],
                "auth_methods": ["api_key"],
                "config_schema": {
                    "type": "object",
                    "required": ["api_key"],
                    "properties": {
                        "api_key": {"type": "string", "title": "API Key"},
                        "region": {"type": "string", "title": "Region", "enum": ["us", "eu", "ca"], "default": "us"},
                    }
                },
            },
            {
                "integration_type": IntegrationType.GOPHISH,
                "category": IntegrationCategory.SECURITY_AWARENESS,
                "name": "GoPhish",
                "description": "Open-source phishing simulation framework",
                "vendor": "GoPhish",
                "documentation_url": "https://docs.getgophish.com/api-documentation/",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": True,
                "supported_entities": ["campaigns", "results", "users"],
                "auth_methods": ["api_key"],
                "config_schema": {
                    "type": "object",
                    "required": ["api_key", "base_url"],
                    "properties": {
                        "api_key": {"type": "string", "title": "API Key"},
                        "base_url": {"type": "string", "title": "GoPhish URL"},
                    }
                },
            },
            # SIEM
            {
                "integration_type": IntegrationType.SPLUNK,
                "category": IntegrationCategory.SIEM,
                "name": "Splunk",
                "description": "Enterprise SIEM and log management platform",
                "vendor": "Splunk",
                "documentation_url": "https://docs.splunk.com/Documentation/Splunk/latest/RESTAPI",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": True,
                "supported_entities": ["alerts", "events", "searches"],
                "auth_methods": ["api_key", "basic"],
                "config_schema": {
                    "type": "object",
                    "required": ["base_url"],
                    "properties": {
                        "base_url": {"type": "string", "title": "Splunk URL"},
                        "token": {"type": "string", "title": "HEC Token"},
                        "username": {"type": "string", "title": "Username"},
                        "password": {"type": "string", "title": "Password"},
                    }
                },
            },
            {
                "integration_type": IntegrationType.ELASTIC,
                "category": IntegrationCategory.SIEM,
                "name": "Elastic Security",
                "description": "Elastic SIEM and security analytics",
                "vendor": "Elastic",
                "documentation_url": "https://www.elastic.co/guide/en/elasticsearch/reference/current/rest-apis.html",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": False,
                "supported_entities": ["alerts", "events", "detections"],
                "auth_methods": ["api_key", "basic"],
            },
            # EDR
            {
                "integration_type": IntegrationType.CROWDSTRIKE,
                "category": IntegrationCategory.EDR_XDR,
                "name": "CrowdStrike Falcon",
                "description": "Endpoint detection and response platform",
                "vendor": "CrowdStrike",
                "documentation_url": "https://falcon.crowdstrike.com/documentation",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": True,
                "supported_entities": ["detections", "incidents", "devices", "iocs"],
                "auth_methods": ["oauth2"],
                "config_schema": {
                    "type": "object",
                    "required": ["client_id", "client_secret"],
                    "properties": {
                        "client_id": {"type": "string", "title": "Client ID"},
                        "client_secret": {"type": "string", "title": "Client Secret"},
                        "base_url": {"type": "string", "title": "API Base URL", "default": "https://api.crowdstrike.com"},
                    }
                },
            },
            {
                "integration_type": IntegrationType.DEFENDER,
                "category": IntegrationCategory.EDR_XDR,
                "name": "Microsoft Defender",
                "description": "Microsoft Defender for Endpoint",
                "vendor": "Microsoft",
                "documentation_url": "https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": True,
                "supported_entities": ["alerts", "incidents", "devices", "vulnerabilities"],
                "auth_methods": ["oauth2"],
            },
            # Ticketing
            {
                "integration_type": IntegrationType.JIRA,
                "category": IntegrationCategory.TICKETING,
                "name": "Jira",
                "description": "Atlassian Jira for issue tracking",
                "vendor": "Atlassian",
                "documentation_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": True,
                "supported_entities": ["issues", "projects", "comments"],
                "auth_methods": ["api_key", "oauth2"],
                "config_schema": {
                    "type": "object",
                    "required": ["base_url", "email", "api_token"],
                    "properties": {
                        "base_url": {"type": "string", "title": "Jira URL"},
                        "email": {"type": "string", "title": "Email"},
                        "api_token": {"type": "string", "title": "API Token"},
                        "project_key": {"type": "string", "title": "Default Project Key"},
                    }
                },
            },
            {
                "integration_type": IntegrationType.SERVICENOW,
                "category": IntegrationCategory.TICKETING,
                "name": "ServiceNow",
                "description": "ServiceNow ITSM platform",
                "vendor": "ServiceNow",
                "documentation_url": "https://developer.servicenow.com/dev.do",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": True,
                "supported_entities": ["incidents", "changes", "cmdb"],
                "auth_methods": ["basic", "oauth2"],
            },
            # Threat Intelligence
            {
                "integration_type": IntegrationType.MISP,
                "category": IntegrationCategory.THREAT_INTEL,
                "name": "MISP",
                "description": "Open-source threat intelligence platform",
                "vendor": "MISP Project",
                "documentation_url": "https://www.misp-project.org/documentation/",
                "supports_inbound": True,
                "supports_outbound": True,
                "supports_webhook": False,
                "supported_entities": ["events", "attributes", "galaxies"],
                "auth_methods": ["api_key"],
                "config_schema": {
                    "type": "object",
                    "required": ["base_url", "api_key"],
                    "properties": {
                        "base_url": {"type": "string", "title": "MISP URL"},
                        "api_key": {"type": "string", "title": "API Key"},
                        "verify_ssl": {"type": "boolean", "title": "Verify SSL", "default": True},
                    }
                },
            },
            {
                "integration_type": IntegrationType.VIRUSTOTAL,
                "category": IntegrationCategory.THREAT_INTEL,
                "name": "VirusTotal",
                "description": "File and URL analysis service",
                "vendor": "Google",
                "documentation_url": "https://developers.virustotal.com/reference",
                "supports_inbound": True,
                "supports_outbound": False,
                "supports_webhook": False,
                "supported_entities": ["files", "urls", "domains", "ips"],
                "auth_methods": ["api_key"],
                "config_schema": {
                    "type": "object",
                    "required": ["api_key"],
                    "properties": {
                        "api_key": {"type": "string", "title": "API Key"},
                    }
                },
            },
            # Vulnerability
            {
                "integration_type": IntegrationType.NESSUS,
                "category": IntegrationCategory.VULNERABILITY,
                "name": "Tenable Nessus",
                "description": "Vulnerability assessment scanner",
                "vendor": "Tenable",
                "documentation_url": "https://docs.tenable.com/nessus/api",
                "supports_inbound": True,
                "supports_outbound": False,
                "supports_webhook": False,
                "supported_entities": ["scans", "vulnerabilities", "assets"],
                "auth_methods": ["api_key"],
            },
            {
                "integration_type": IntegrationType.QUALYS,
                "category": IntegrationCategory.VULNERABILITY,
                "name": "Qualys",
                "description": "Cloud security and compliance platform",
                "vendor": "Qualys",
                "documentation_url": "https://www.qualys.com/docs/qualys-api-vmpc-user-guide.pdf",
                "supports_inbound": True,
                "supports_outbound": False,
                "supports_webhook": False,
                "supported_entities": ["scans", "vulnerabilities", "assets"],
                "auth_methods": ["basic"],
            },
        ]

        for template_data in templates:
            # Check if template already exists
            existing = await self.get_template(template_data["integration_type"])
            if not existing:
                template = IntegrationTemplate(**template_data)
                self.db.add(template)

        await self.db.commit()

    # ============== Security Awareness Metrics ==============

    async def get_awareness_metrics(
        self, integration_id: str
    ) -> Optional[SecurityAwarenessMetrics]:
        """Get latest security awareness metrics for an integration."""
        result = await self.db.execute(
            select(SecurityAwarenessMetrics)
            .where(SecurityAwarenessMetrics.integration_id == integration_id)
            .order_by(SecurityAwarenessMetrics.period_end.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_aggregated_awareness_metrics(self) -> Dict[str, Any]:
        """Get aggregated security awareness metrics from all integrations."""
        # Get all awareness integrations
        result = await self.db.execute(
            select(Integration).where(
                and_(
                    Integration.category == IntegrationCategory.SECURITY_AWARENESS,
                    Integration.is_enabled == True,
                )
            )
        )
        integrations = result.scalars().all()

        if not integrations:
            return {}

        total_users = 0
        total_completed = 0
        total_phishing_sent = 0
        total_phishing_clicked = 0
        total_score_sum = 0
        score_count = 0

        for integration in integrations:
            metrics = await self.get_awareness_metrics(integration.id)
            if metrics:
                total_users += metrics.total_users
                total_completed += metrics.training_completed
                total_phishing_sent += metrics.phishing_emails_sent
                total_phishing_clicked += metrics.phishing_clicked
                if metrics.average_score:
                    total_score_sum += metrics.average_score * metrics.total_users
                    score_count += metrics.total_users

        return {
            "total_users": total_users,
            "training_completion_rate": round(total_completed / total_users * 100) if total_users > 0 else 0,
            "average_score": round(total_score_sum / score_count) if score_count > 0 else 0,
            "phishing_click_rate": round(total_phishing_clicked / total_phishing_sent * 100) if total_phishing_sent > 0 else 0,
            "integrations_count": len(integrations),
        }

    # ============== Dashboard Stats ==============

    async def get_dashboard_stats(self) -> IntegrationsDashboardStats:
        """Get dashboard statistics."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Integration counts
        total_integrations = (await self.db.execute(
            select(func.count(Integration.id))
        )).scalar() or 0

        active_integrations = (await self.db.execute(
            select(func.count(Integration.id)).where(
                Integration.is_enabled == True
            )
        )).scalar() or 0

        integrations_with_errors = (await self.db.execute(
            select(func.count(Integration.id)).where(
                Integration.status == IntegrationStatus.ERROR
            )
        )).scalar() or 0

        # By category
        by_category = {}
        for category in IntegrationCategory:
            count = (await self.db.execute(
                select(func.count(Integration.id)).where(
                    Integration.category == category
                )
            )).scalar() or 0
            if count > 0:
                by_category[category.value] = count

        # By status
        by_status = {}
        for status in IntegrationStatus:
            count = (await self.db.execute(
                select(func.count(Integration.id)).where(
                    Integration.status == status
                )
            )).scalar() or 0
            if count > 0:
                by_status[status.value] = count

        # Sync stats today
        total_syncs_today = (await self.db.execute(
            select(func.count(IntegrationSyncLog.id)).where(
                IntegrationSyncLog.started_at >= today_start
            )
        )).scalar() or 0

        successful_syncs_today = (await self.db.execute(
            select(func.count(IntegrationSyncLog.id)).where(
                and_(
                    IntegrationSyncLog.started_at >= today_start,
                    IntegrationSyncLog.status == "success"
                )
            )
        )).scalar() or 0

        failed_syncs_today = (await self.db.execute(
            select(func.count(IntegrationSyncLog.id)).where(
                and_(
                    IntegrationSyncLog.started_at >= today_start,
                    IntegrationSyncLog.status == "failed"
                )
            )
        )).scalar() or 0

        records_synced_today = (await self.db.execute(
            select(func.sum(IntegrationSyncLog.records_created + IntegrationSyncLog.records_updated)).where(
                IntegrationSyncLog.started_at >= today_start
            )
        )).scalar() or 0

        # Webhook stats today
        webhooks_received_today = (await self.db.execute(
            select(func.count(WebhookEvent.id)).where(
                WebhookEvent.received_at >= today_start
            )
        )).scalar() or 0

        webhooks_processed_today = (await self.db.execute(
            select(func.count(WebhookEvent.id)).where(
                and_(
                    WebhookEvent.received_at >= today_start,
                    WebhookEvent.processing_result == "success"
                )
            )
        )).scalar() or 0

        webhooks_failed_today = (await self.db.execute(
            select(func.count(WebhookEvent.id)).where(
                and_(
                    WebhookEvent.received_at >= today_start,
                    WebhookEvent.processing_result == "failed"
                )
            )
        )).scalar() or 0

        # Awareness metrics
        awareness_metrics = await self.get_aggregated_awareness_metrics()

        return IntegrationsDashboardStats(
            total_integrations=total_integrations,
            active_integrations=active_integrations,
            integrations_with_errors=integrations_with_errors,
            integrations_by_category=by_category,
            integrations_by_status=by_status,
            total_syncs_today=total_syncs_today,
            successful_syncs_today=successful_syncs_today,
            failed_syncs_today=failed_syncs_today,
            records_synced_today=records_synced_today,
            webhooks_received_today=webhooks_received_today,
            webhooks_processed_today=webhooks_processed_today,
            webhooks_failed_today=webhooks_failed_today,
            awareness_metrics=awareness_metrics if awareness_metrics else None,
        )
