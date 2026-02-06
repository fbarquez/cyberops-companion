"""Main Copilot Service - Orchestrates AI providers for cybersecurity assistance."""

import logging
import httpx
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    BaseLLMProvider,
    CopilotMessage,
    CopilotResponse,
    CopilotProvider,
    ProviderConfig,
    MessageRole,
    SYSTEM_PROMPTS,
)
from .providers import (
    OllamaProvider,
    GeminiProvider,
    GroqProvider,
    OpenAIProvider,
    AnthropicProvider,
)

logger = logging.getLogger(__name__)


# Default Ollama URL
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"


class CopilotService:
    """
    AI Copilot service for cybersecurity operations.

    Supports multiple providers:
    - Ollama (local, free)
    - Gemini (Google, free tier)
    - Groq (fast, free tier)
    - OpenAI (paid)
    - Anthropic (paid)
    """

    PROVIDER_CLASSES = {
        CopilotProvider.OLLAMA: OllamaProvider,
        CopilotProvider.GEMINI: GeminiProvider,
        CopilotProvider.GROQ: GroqProvider,
        CopilotProvider.OPENAI: OpenAIProvider,
        CopilotProvider.ANTHROPIC: AnthropicProvider,
    }

    def __init__(self, config: ProviderConfig):
        """Initialize with a specific provider configuration."""
        self.config = config
        self.provider = self._create_provider(config)

    def _create_provider(self, config: ProviderConfig) -> Optional[BaseLLMProvider]:
        """Create the appropriate provider based on configuration."""
        provider_class = self.PROVIDER_CLASSES.get(config.provider)
        if not provider_class:
            logger.warning(f"Unknown provider: {config.provider}")
            return None

        try:
            return provider_class(config)
        except Exception as e:
            logger.error(f"Failed to create provider {config.provider}: {e}")
            return None

    @classmethod
    async def detect_ollama(cls, url: str = DEFAULT_OLLAMA_URL) -> Optional[str]:
        """
        Check if Ollama is running and return the best available model.

        Returns model name if Ollama is available, None otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]

                    if not models:
                        return None

                    # Prefer these models in order
                    preferred = ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5", "llama3.1:8b", "llama3.1", "mistral:7b", "mistral"]
                    for pref in preferred:
                        for model in models:
                            if pref in model:
                                return model

                    # Return first available model
                    return models[0]
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")

        return None

    @classmethod
    def from_settings(cls, settings: Any) -> Optional["CopilotService"]:
        """
        Create CopilotService from application settings.

        Expected settings attributes:
        - COPILOT_PROVIDER: str (ollama, gemini, groq, openai, anthropic)
        - COPILOT_MODEL: str (optional, provider-specific)
        - OLLAMA_URL: str (for Ollama)
        - GOOGLE_API_KEY: str (for Gemini)
        - GROQ_API_KEY: str (for Groq)
        - OPENAI_API_KEY: str (for OpenAI)
        - ANTHROPIC_API_KEY: str (for Anthropic)
        """
        provider_name = getattr(settings, "COPILOT_PROVIDER", None) or ""
        provider_name = provider_name.strip().lower()

        # If no provider configured, we'll try auto-detection later
        if not provider_name:
            logger.info("No COPILOT_PROVIDER configured, will try auto-detect Ollama")
            # Return a service that will auto-detect on first use
            return cls._create_auto_detect_service(settings)

        try:
            provider = CopilotProvider(provider_name)
        except ValueError:
            logger.error(f"Invalid COPILOT_PROVIDER: {provider_name}")
            return None

        # Build config based on provider
        config = ProviderConfig(provider=provider)

        if provider == CopilotProvider.OLLAMA:
            config.base_url = getattr(settings, "OLLAMA_URL", DEFAULT_OLLAMA_URL)
            config.model = getattr(settings, "COPILOT_MODEL", None) or DEFAULT_OLLAMA_MODEL

        elif provider == CopilotProvider.GEMINI:
            config.api_key = getattr(settings, "GOOGLE_API_KEY", None)
            if not config.api_key:
                logger.warning("GOOGLE_API_KEY not set for Gemini provider")
                return None
            config.model = getattr(settings, "COPILOT_MODEL", None) or "gemini-1.5-flash"

        elif provider == CopilotProvider.GROQ:
            config.api_key = getattr(settings, "GROQ_API_KEY", None)
            if not config.api_key:
                logger.warning("GROQ_API_KEY not set for Groq provider")
                return None
            config.model = getattr(settings, "COPILOT_MODEL", None) or "llama-3.1-8b-instant"

        elif provider == CopilotProvider.OPENAI:
            config.api_key = getattr(settings, "OPENAI_API_KEY", None)
            if not config.api_key:
                logger.warning("OPENAI_API_KEY not set for OpenAI provider")
                return None
            config.model = getattr(settings, "COPILOT_MODEL", None) or "gpt-4o-mini"

        elif provider == CopilotProvider.ANTHROPIC:
            config.api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
            if not config.api_key:
                logger.warning("ANTHROPIC_API_KEY not set for Anthropic provider")
                return None
            config.model = getattr(settings, "COPILOT_MODEL", None) or "claude-3-5-sonnet-20241022"

        return cls(config)

    @classmethod
    def _create_auto_detect_service(cls, settings: Any) -> "CopilotService":
        """Create a service that will auto-detect Ollama."""
        ollama_url = getattr(settings, "OLLAMA_URL", DEFAULT_OLLAMA_URL)
        config = ProviderConfig(
            provider=CopilotProvider.OLLAMA,
            base_url=ollama_url,
            model=DEFAULT_OLLAMA_MODEL,
        )
        service = cls(config)
        service._auto_detect = True
        service._ollama_url = ollama_url
        return service

    @classmethod
    def from_user_settings(
        cls,
        user_settings: Dict[str, Any],
        fallback_settings: Any
    ) -> Optional["CopilotService"]:
        """
        Create CopilotService from user-specific settings with fallback to server settings.

        This enables the hybrid model where users can override the default provider.

        Args:
            user_settings: User's copilot preferences from database
            fallback_settings: Server-level settings to fall back to
        """
        # If user has configured their own provider, use it
        if user_settings and user_settings.get("provider"):
            provider_name = user_settings.get("provider", "").lower()

            try:
                provider = CopilotProvider(provider_name)
            except ValueError:
                logger.warning(f"Invalid user provider: {provider_name}, falling back to server")
                return cls.from_settings(fallback_settings)

            config = ProviderConfig(
                provider=provider,
                api_key=user_settings.get("api_key"),
                base_url=user_settings.get("base_url", DEFAULT_OLLAMA_URL),
                model=user_settings.get("model"),
            )

            return cls(config)

        # Fall back to server settings
        return cls.from_settings(fallback_settings)

    @property
    def is_available(self) -> bool:
        """Check if the copilot is configured and available."""
        return self.provider is not None

    async def health_check(self) -> Dict[str, Any]:
        """Check if the AI provider is healthy."""
        if not self.provider:
            return {
                "status": "disabled",
                "provider": None,
                "model": None,
                "message": "Copilot not configured",
            }

        is_healthy = await self.provider.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "provider": self.config.provider.value,
            "model": self.provider.model,
            "message": "Provider is available" if is_healthy else "Provider is not responding",
        }

    async def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None,
    ) -> CopilotResponse:
        """
        General chat with the AI copilot.

        Args:
            message: User's message
            history: Previous messages [{"role": "user/assistant", "content": "..."}]
            context: Additional context about current page/data
        """
        if not self.provider:
            return CopilotResponse(
                content="",
                provider=CopilotProvider.OLLAMA,
                model="none",
                error="Copilot is not configured. Please set COPILOT_PROVIDER in your environment.",
            )

        messages = []

        # Add history
        if history:
            for h in history:
                role = MessageRole.USER if h.get("role") == "user" else MessageRole.ASSISTANT
                messages.append(CopilotMessage(role=role, content=h.get("content", "")))

        # Add current message
        messages.append(CopilotMessage(role=MessageRole.USER, content=message))

        # Build system prompt with context
        system_prompt = SYSTEM_PROMPTS["general"]
        if context:
            system_prompt += f"\n\nCurrent context:\n{context}"

        return await self.provider.generate(messages, system_prompt)

    async def analyze_incident(
        self,
        incident: Dict[str, Any],
        include_timeline: bool = True,
    ) -> CopilotResponse:
        """
        Analyze a security incident and provide recommendations.

        Args:
            incident: Incident data dict
            include_timeline: Whether to include timeline in analysis
        """
        if not self.provider:
            return CopilotResponse(
                content="",
                provider=CopilotProvider.OLLAMA,
                model="none",
                error="Copilot is not configured",
            )

        # Build incident context
        context = f"""
## Incident Details

- **ID:** {incident.get('id', 'N/A')}
- **Title:** {incident.get('title', 'N/A')}
- **Severity:** {incident.get('severity', 'N/A')}
- **Status:** {incident.get('status', 'N/A')}
- **Type:** {incident.get('incident_type', 'N/A')}
- **Created:** {incident.get('created_at', 'N/A')}

## Description
{incident.get('description', 'No description provided')}
"""

        if include_timeline and incident.get('timeline'):
            context += "\n## Timeline\n"
            for event in incident.get('timeline', []):
                context += f"- [{event.get('timestamp', '')}] {event.get('action', '')}: {event.get('description', '')}\n"

        if incident.get('affected_systems'):
            context += f"\n## Affected Systems\n{', '.join(incident.get('affected_systems', []))}"

        message = CopilotMessage(
            role=MessageRole.USER,
            content=f"Analyze this security incident and provide recommendations:\n\n{context}",
        )

        return await self.provider.generate([message], SYSTEM_PROMPTS["incident_analysis"])

    async def explain_compliance_control(
        self,
        framework: str,
        control_id: str,
        control_title: str,
        control_description: Optional[str] = None,
        current_status: Optional[str] = None,
    ) -> CopilotResponse:
        """
        Explain a compliance control and how to implement it.

        Args:
            framework: Framework name (BSI, NIS2, ISO27001)
            control_id: Control identifier
            control_title: Control title
            control_description: Control description
            current_status: Current implementation status
        """
        if not self.provider:
            return CopilotResponse(
                content="",
                provider=CopilotProvider.OLLAMA,
                model="none",
                error="Copilot is not configured",
            )

        context = f"""
## Compliance Control

- **Framework:** {framework}
- **Control ID:** {control_id}
- **Title:** {control_title}
"""

        if control_description:
            context += f"\n**Description:** {control_description}"

        if current_status:
            context += f"\n**Current Status:** {current_status}"

        prompt = f"""
{context}

Please explain:
1. What this control requires
2. Why it's important
3. Step-by-step implementation guide
4. Common evidence/documentation needed
5. Potential challenges and solutions
"""

        message = CopilotMessage(role=MessageRole.USER, content=prompt)
        return await self.provider.generate([message], SYSTEM_PROMPTS["compliance_advisor"])

    async def generate_compliance_report(
        self,
        framework: str,
        compliance_data: Dict[str, Any],
        report_type: str = "executive",
    ) -> CopilotResponse:
        """
        Generate a compliance report.

        Args:
            framework: Framework name
            compliance_data: Compliance status data
            report_type: "executive" or "detailed"
        """
        if not self.provider:
            return CopilotResponse(
                content="",
                provider=CopilotProvider.OLLAMA,
                model="none",
                error="Copilot is not configured",
            )

        context = f"""
## Compliance Report Request

- **Framework:** {framework}
- **Report Type:** {report_type}
- **Overall Score:** {compliance_data.get('overall_score', 'N/A')}%
- **Total Controls:** {compliance_data.get('total_controls', 'N/A')}
- **Compliant:** {compliance_data.get('compliant_count', 'N/A')}
- **Gaps:** {compliance_data.get('gaps_count', 'N/A')}

## Status by Category
"""

        for category, data in compliance_data.get('categories', {}).items():
            context += f"- **{category}:** {data.get('score', 0)}% ({data.get('compliant', 0)}/{data.get('total', 0)})\n"

        if compliance_data.get('critical_gaps'):
            context += "\n## Critical Gaps\n"
            for gap in compliance_data.get('critical_gaps', []):
                context += f"- {gap.get('control_id', '')}: {gap.get('title', '')}\n"

        prompt = f"""
{context}

Generate a professional {report_type} compliance report in markdown format.

{"Include: Executive summary, key findings, risk assessment, and top recommendations." if report_type == "executive" else "Include: Detailed findings for each category, specific gaps, remediation steps, and timeline recommendations."}
"""

        message = CopilotMessage(role=MessageRole.USER, content=prompt)
        return await self.provider.generate([message], SYSTEM_PROMPTS["report_generator"])

    async def prioritize_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> CopilotResponse:
        """
        Prioritize vulnerabilities based on risk.

        Args:
            vulnerabilities: List of vulnerability data
            context: Additional context about the environment
        """
        if not self.provider:
            return CopilotResponse(
                content="",
                provider=CopilotProvider.OLLAMA,
                model="none",
                error="Copilot is not configured",
            )

        vuln_context = "## Vulnerabilities to Prioritize\n\n"
        for vuln in vulnerabilities[:20]:  # Limit to 20
            vuln_context += f"""
### {vuln.get('cve_id', 'Unknown')}
- **CVSS:** {vuln.get('cvss_score', 'N/A')}
- **Severity:** {vuln.get('severity', 'N/A')}
- **EPSS:** {vuln.get('epss_score', 'N/A')}
- **KEV:** {'Yes' if vuln.get('is_kev') else 'No'}
- **Affected:** {vuln.get('affected_systems', 'N/A')}
- **Description:** {vuln.get('description', 'N/A')[:200]}...
"""

        if context:
            vuln_context += f"\n## Environment Context\n{context}"

        prompt = f"""
{vuln_context}

Analyze and prioritize these vulnerabilities. For each, provide:
1. Priority ranking (Critical/High/Medium/Low)
2. Reasoning for the priority
3. Recommended remediation approach
4. Estimated effort

Focus on exploitability, business impact, and available patches.
"""

        message = CopilotMessage(role=MessageRole.USER, content=prompt)
        return await self.provider.generate([message], SYSTEM_PROMPTS["vulnerability_advisor"])

    async def suggest_gap_remediation(
        self,
        framework: str,
        gap: Dict[str, Any],
    ) -> CopilotResponse:
        """
        Suggest remediation steps for a compliance gap.

        Args:
            framework: Framework name
            gap: Gap details
        """
        if not self.provider:
            return CopilotResponse(
                content="",
                provider=CopilotProvider.OLLAMA,
                model="none",
                error="Copilot is not configured",
            )

        prompt = f"""
## Compliance Gap Remediation

- **Framework:** {framework}
- **Control ID:** {gap.get('control_id', 'N/A')}
- **Control Title:** {gap.get('title', 'N/A')}
- **Current Status:** {gap.get('status', 'Not Implemented')}
- **Implementation Level:** {gap.get('implementation_level', 0)}%

**Gap Description:** {gap.get('gap_description', 'No description')}

Please provide:
1. Step-by-step remediation plan
2. Required resources (people, tools, budget estimate)
3. Timeline estimate
4. Quick wins vs long-term improvements
5. Evidence needed to demonstrate compliance
6. Common pitfalls to avoid
"""

        message = CopilotMessage(role=MessageRole.USER, content=prompt)
        return await self.provider.generate([message], SYSTEM_PROMPTS["compliance_advisor"])
