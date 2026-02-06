"""API endpoints for AI Copilot."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.models.user import User
from src.config import settings
from src.services.copilot import CopilotService, CopilotProvider

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


# --- Pydantic Models ---

class ChatMessage(BaseModel):
    """A message in chat history."""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for general chat."""
    message: str = Field(..., description="User's message")
    history: Optional[List[ChatMessage]] = Field(default=None, description="Previous messages")
    context: Optional[str] = Field(default=None, description="Additional context")


class IncidentAnalysisRequest(BaseModel):
    """Request for incident analysis."""
    incident_id: Optional[str] = None
    incident_data: Optional[Dict[str, Any]] = None
    include_timeline: bool = True


class ComplianceControlRequest(BaseModel):
    """Request for compliance control explanation."""
    framework: str = Field(..., description="Framework: BSI, NIS2, ISO27001")
    control_id: str = Field(..., description="Control identifier")
    control_title: str = Field(..., description="Control title")
    control_description: Optional[str] = None
    current_status: Optional[str] = None


class ComplianceReportRequest(BaseModel):
    """Request for compliance report generation."""
    framework: str
    compliance_data: Dict[str, Any]
    report_type: str = Field(default="executive", description="executive or detailed")


class VulnerabilityPrioritizationRequest(BaseModel):
    """Request for vulnerability prioritization."""
    vulnerabilities: List[Dict[str, Any]]
    context: Optional[str] = None


class GapRemediationRequest(BaseModel):
    """Request for gap remediation suggestions."""
    framework: str
    gap: Dict[str, Any]


class CopilotResponse(BaseModel):
    """Response from AI Copilot."""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    provider: Optional[str] = None
    model: Optional[str] = None
    message: str


class ProvidersResponse(BaseModel):
    """Available providers response."""
    configured_provider: Optional[str] = None
    configured_model: Optional[str] = None
    available_providers: List[Dict[str, Any]]


# --- Helper Functions ---

def get_copilot_service() -> Optional[CopilotService]:
    """Get the copilot service from settings."""
    return CopilotService.from_settings(settings)


def _response_to_dict(response) -> Dict[str, Any]:
    """Convert CopilotResponse to dict."""
    return {
        "content": response.content,
        "provider": response.provider.value if hasattr(response.provider, 'value') else str(response.provider),
        "model": response.model,
        "tokens_used": response.tokens_used,
        "latency_ms": response.latency_ms,
        "error": response.error,
    }


# --- Endpoints ---

@router.get("/health", response_model=HealthResponse)
async def copilot_health(
    current_user: User = Depends(get_current_user),
):
    """
    Check if AI Copilot is available and healthy.

    If no provider is configured, tries to auto-detect Ollama.
    """
    service = get_copilot_service()

    # Try to auto-detect Ollama if service exists but might need detection
    if service and getattr(service, '_auto_detect', False):
        detected_model = await CopilotService.detect_ollama(
            getattr(service, '_ollama_url', 'http://localhost:11434')
        )
        if detected_model:
            return HealthResponse(
                status="healthy",
                provider="ollama",
                model=detected_model,
                message=f"Auto-detected Ollama with model: {detected_model}",
            )
        else:
            return HealthResponse(
                status="not_configured",
                provider=None,
                model=None,
                message="No AI provider configured. Install Ollama or configure a cloud provider.",
            )

    if not service:
        # Try auto-detect Ollama as fallback
        detected_model = await CopilotService.detect_ollama()
        if detected_model:
            return HealthResponse(
                status="healthy",
                provider="ollama",
                model=detected_model,
                message=f"Auto-detected Ollama with model: {detected_model}",
            )

        return HealthResponse(
            status="not_configured",
            provider=None,
            model=None,
            message="No AI provider configured. Install Ollama or set COPILOT_PROVIDER.",
        )

    health = await service.health_check()
    return HealthResponse(**health)


@router.get("/detect-ollama")
async def detect_ollama(
    current_user: User = Depends(get_current_user),
):
    """
    Detect if Ollama is running locally and list available models.
    """
    ollama_url = settings.OLLAMA_URL if hasattr(settings, 'OLLAMA_URL') else "http://localhost:11434"

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {
                    "available": True,
                    "url": ollama_url,
                    "models": models,
                    "recommended": await CopilotService.detect_ollama(ollama_url),
                }
    except Exception as e:
        pass

    return {
        "available": False,
        "url": ollama_url,
        "models": [],
        "recommended": None,
        "install_instructions": "curl -fsSL https://ollama.ai/install.sh | sh && ollama pull qwen2.5:7b",
    }


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """List available AI providers and current configuration."""
    service = get_copilot_service()

    available = [
        {
            "id": "ollama",
            "name": "Ollama (Local)",
            "description": "Run models locally. Free, private.",
            "models": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "mistral:7b"],
            "free": True,
            "setup": "Install Ollama and run: ollama pull qwen2.5:7b",
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "description": "Google's AI. Generous free tier.",
            "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
            "free": True,
            "setup": "Get API key at: https://aistudio.google.com/apikey",
        },
        {
            "id": "groq",
            "name": "Groq",
            "description": "Ultra-fast inference. Free tier available.",
            "models": ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
            "free": True,
            "setup": "Get API key at: https://console.groq.com/keys",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "GPT models. Paid.",
            "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            "free": False,
            "setup": "Get API key at: https://platform.openai.com/api-keys",
        },
        {
            "id": "anthropic",
            "name": "Anthropic (Claude)",
            "description": "Claude models. Paid.",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
            "free": False,
            "setup": "Get API key at: https://console.anthropic.com/",
        },
    ]

    return ProvidersResponse(
        configured_provider=service.config.provider.value if service else None,
        configured_model=service.provider.model if service and service.provider else None,
        available_providers=available,
    )


@router.post("/chat", response_model=CopilotResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    General chat with the AI Copilot.

    Send a message and optionally include conversation history.
    """
    service = get_copilot_service()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot is not configured. Set COPILOT_PROVIDER environment variable.",
        )

    history = None
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]

    response = await service.chat(
        message=request.message,
        history=history,
        context=request.context,
    )

    return CopilotResponse(**_response_to_dict(response))


@router.post("/analyze-incident", response_model=CopilotResponse)
async def analyze_incident(
    request: IncidentAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a security incident.

    Provide either incident_id to fetch from database, or incident_data directly.
    """
    service = get_copilot_service()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot is not configured",
        )

    incident_data = request.incident_data

    # If incident_id provided, fetch from database
    if request.incident_id and not incident_data:
        from src.services.incident_service import IncidentService
        incident_service = IncidentService(db)
        incident = await incident_service.get_incident(request.incident_id, current_user.tenant_id)

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )

        incident_data = {
            "id": str(incident.id),
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value if incident.severity else None,
            "status": incident.status.value if incident.status else None,
            "incident_type": incident.incident_type,
            "created_at": str(incident.created_at),
            "timeline": incident.timeline or [],
            "affected_systems": incident.affected_systems or [],
        }

    if not incident_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either incident_id or incident_data must be provided",
        )

    response = await service.analyze_incident(
        incident=incident_data,
        include_timeline=request.include_timeline,
    )

    return CopilotResponse(**_response_to_dict(response))


@router.post("/explain-control", response_model=CopilotResponse)
async def explain_compliance_control(
    request: ComplianceControlRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Explain a compliance control and how to implement it.

    Supports BSI IT-Grundschutz, NIS2, and ISO 27001 frameworks.
    """
    service = get_copilot_service()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot is not configured",
        )

    response = await service.explain_compliance_control(
        framework=request.framework,
        control_id=request.control_id,
        control_title=request.control_title,
        control_description=request.control_description,
        current_status=request.current_status,
    )

    return CopilotResponse(**_response_to_dict(response))


@router.post("/generate-report", response_model=CopilotResponse)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a compliance report.

    Provide compliance data and get a formatted report.
    """
    service = get_copilot_service()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot is not configured",
        )

    response = await service.generate_compliance_report(
        framework=request.framework,
        compliance_data=request.compliance_data,
        report_type=request.report_type,
    )

    return CopilotResponse(**_response_to_dict(response))


@router.post("/prioritize-vulnerabilities", response_model=CopilotResponse)
async def prioritize_vulnerabilities(
    request: VulnerabilityPrioritizationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Prioritize vulnerabilities based on risk.

    Provide a list of vulnerabilities to get prioritization recommendations.
    """
    service = get_copilot_service()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot is not configured",
        )

    response = await service.prioritize_vulnerabilities(
        vulnerabilities=request.vulnerabilities,
        context=request.context,
    )

    return CopilotResponse(**_response_to_dict(response))


@router.post("/suggest-remediation", response_model=CopilotResponse)
async def suggest_gap_remediation(
    request: GapRemediationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Suggest remediation steps for a compliance gap.
    """
    service = get_copilot_service()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Copilot is not configured",
        )

    response = await service.suggest_gap_remediation(
        framework=request.framework,
        gap=request.gap,
    )

    return CopilotResponse(**_response_to_dict(response))
