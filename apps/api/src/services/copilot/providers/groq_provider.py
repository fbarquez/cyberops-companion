"""Groq provider for fast LLM inference."""

import httpx
import time
from typing import List, Optional

from ..base import (
    BaseLLMProvider,
    CopilotMessage,
    CopilotResponse,
    CopilotProvider,
    ProviderConfig,
)


class GroqProvider(BaseLLMProvider):
    """
    Groq provider for ultra-fast inference.

    Free tier available with generous limits.

    Get API key: https://console.groq.com/keys

    Models:
    - llama-3.1-8b-instant (fast, good quality)
    - llama-3.1-70b-versatile (better quality)
    - mixtral-8x7b-32768 (good for long context)
    - gemma2-9b-it (Google's Gemma)
    """

    provider_type = CopilotProvider.GROQ
    default_model = "llama-3.1-8b-instant"
    api_base = "https://api.groq.com/openai/v1"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Groq requires an API key. Get one at: https://console.groq.com/keys")
        self.api_key = config.api_key

    async def generate(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> CopilotResponse:
        """Generate response using Groq API (OpenAI-compatible)."""
        start_time = time.time()

        try:
            formatted_messages = self._build_messages(messages, system_prompt)

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                    },
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    return CopilotResponse(
                        content="",
                        provider=self.provider_type,
                        model=self.model,
                        error=f"Groq API error: {error_msg}",
                    )

                data = response.json()
                latency_ms = (time.time() - start_time) * 1000

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens")

                return CopilotResponse(
                    content=content,
                    provider=self.provider_type,
                    model=self.model,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                )

        except httpx.TimeoutException:
            return CopilotResponse(
                content="",
                provider=self.provider_type,
                model=self.model,
                error="Request timed out",
            )
        except Exception as e:
            return CopilotResponse(
                content="",
                provider=self.provider_type,
                model=self.model,
                error=f"Groq error: {str(e)}",
            )

    async def health_check(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_base}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False
