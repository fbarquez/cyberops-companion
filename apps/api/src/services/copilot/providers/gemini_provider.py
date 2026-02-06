"""Google Gemini provider."""

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


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider.

    Free tier: 15 requests/minute, 1M tokens/day

    Get API key: https://aistudio.google.com/apikey

    Models:
    - gemini-1.5-flash (fast, free tier friendly)
    - gemini-1.5-pro (more capable)
    """

    provider_type = CopilotProvider.GEMINI
    default_model = "gemini-1.5-flash"
    api_base = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Gemini requires an API key. Get one at: https://aistudio.google.com/apikey")
        self.api_key = config.api_key

    async def generate(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> CopilotResponse:
        """Generate response using Gemini API."""
        start_time = time.time()

        try:
            # Convert messages to Gemini format
            contents = []

            # Add system instruction if provided
            system_instruction = None
            if system_prompt:
                system_instruction = {"parts": [{"text": system_prompt}]}

            for msg in messages:
                role = "user" if msg.role == MessageRole.USER else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

            request_body = {
                "contents": contents,
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens,
                },
            }

            if system_instruction:
                request_body["systemInstruction"] = system_instruction

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json=request_body,
                )

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    return CopilotResponse(
                        content="",
                        provider=self.provider_type,
                        model=self.model,
                        error=f"Gemini API error: {error_msg}",
                    )

                data = response.json()
                latency_ms = (time.time() - start_time) * 1000

                # Extract response text
                candidates = data.get("candidates", [])
                if not candidates:
                    return CopilotResponse(
                        content="",
                        provider=self.provider_type,
                        model=self.model,
                        error="No response generated",
                    )

                content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

                # Get token count if available
                usage = data.get("usageMetadata", {})
                tokens_used = usage.get("totalTokenCount")

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
                error=f"Gemini error: {str(e)}",
            )

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_base}/models/{self.model}",
                    params={"key": self.api_key},
                )
                return response.status_code == 200
        except Exception:
            return False
