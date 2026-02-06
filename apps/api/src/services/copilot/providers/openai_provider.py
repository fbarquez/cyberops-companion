"""OpenAI provider."""

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


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider.

    Requires paid API key: https://platform.openai.com/api-keys

    Models:
    - gpt-4o-mini (cheap, fast)
    - gpt-4o (capable)
    - gpt-4-turbo (most capable)
    """

    provider_type = CopilotProvider.OPENAI
    default_model = "gpt-4o-mini"
    api_base = "https://api.openai.com/v1"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("OpenAI requires an API key")
        self.api_key = config.api_key

    async def generate(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> CopilotResponse:
        """Generate response using OpenAI API."""
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
                        error=f"OpenAI API error: {error_msg}",
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
                error=f"OpenAI error: {str(e)}",
            )

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_base}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False
