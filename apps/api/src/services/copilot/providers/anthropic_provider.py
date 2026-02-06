"""Anthropic (Claude) provider."""

import httpx
import time
from typing import List, Optional

from ..base import (
    BaseLLMProvider,
    CopilotMessage,
    CopilotResponse,
    CopilotProvider,
    ProviderConfig,
    MessageRole,
)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic (Claude) provider.

    Requires paid API key: https://console.anthropic.com/

    Models:
    - claude-3-5-sonnet-20241022 (balanced)
    - claude-3-5-haiku-20241022 (fast, cheap)
    - claude-3-opus-20240229 (most capable)
    """

    provider_type = CopilotProvider.ANTHROPIC
    default_model = "claude-3-5-sonnet-20241022"
    api_base = "https://api.anthropic.com/v1"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Anthropic requires an API key")
        self.api_key = config.api_key

    async def generate(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> CopilotResponse:
        """Generate response using Anthropic API."""
        start_time = time.time()

        try:
            # Anthropic uses a different format - system is separate
            formatted_messages = []
            for msg in messages:
                if msg.role != MessageRole.SYSTEM:
                    formatted_messages.append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant",
                        "content": msg.content,
                    })

            request_body = {
                "model": self.model,
                "messages": formatted_messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            if system_prompt:
                request_body["system"] = system_prompt

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    return CopilotResponse(
                        content="",
                        provider=self.provider_type,
                        model=self.model,
                        error=f"Anthropic API error: {error_msg}",
                    )

                data = response.json()
                latency_ms = (time.time() - start_time) * 1000

                # Extract content from response
                content_blocks = data.get("content", [])
                content = ""
                for block in content_blocks:
                    if block.get("type") == "text":
                        content += block.get("text", "")

                usage = data.get("usage", {})
                tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

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
                error=f"Anthropic error: {str(e)}",
            )

    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible with a minimal request."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 10,
                    },
                )
                return response.status_code == 200
        except Exception:
            return False
