"""Base classes and data models for AI Copilot providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class CopilotProvider(str, Enum):
    """Supported AI providers."""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class CopilotMessage:
    """A message in the conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class CopilotResponse:
    """Response from the AI provider."""
    content: str
    provider: CopilotProvider
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    provider: CopilotProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 180  # Increased for local models that need time to load
    extra_params: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    provider_type: CopilotProvider
    default_model: str

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.model = config.model or self.default_model

    @abstractmethod
    async def generate(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> CopilotResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass

    def _build_messages(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Build message list with optional system prompt."""
        result = []

        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

        for msg in messages:
            result.append(msg.to_dict())

        return result


# Default system prompts for different use cases
SYSTEM_PROMPTS = {
    "general": """You are an AI assistant for CyberOps Companion, a cybersecurity operations platform.
You help security teams with:
- Incident analysis and response
- Compliance with BSI IT-Grundschutz and NIS2 Directive
- Vulnerability management
- Risk assessment
- Security operations

Respond in the same language as the user's question.
Be concise, professional, and actionable.""",

    "incident_analysis": """You are a senior incident response analyst.
Analyze security incidents and provide:
1. Executive summary
2. Indicators of Compromise (IOCs)
3. Attack vector analysis
4. Containment recommendations
5. Remediation steps
6. Lessons learned

Be thorough but concise. Use bullet points.""",

    "compliance_advisor": """You are a compliance expert specializing in:
- EU NIS2 Directive
- BSI IT-Grundschutz
- ISO 27001

Help users understand requirements, identify gaps, and implement controls.
Provide practical, actionable advice.
Reference specific articles/controls when relevant.""",

    "report_generator": """You are a technical writer for cybersecurity.
Generate professional reports that are:
- Clear and well-structured
- Executive-friendly summaries
- Technical details for practitioners
- Actionable recommendations

Use markdown formatting.""",

    "vulnerability_advisor": """You are a vulnerability management specialist.
Help prioritize and remediate vulnerabilities based on:
- CVSS scores
- Exploitability (EPSS, KEV)
- Business context
- Available patches

Provide specific remediation guidance.""",
}
