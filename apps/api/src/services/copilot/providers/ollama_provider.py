"""Ollama provider for local LLM inference."""

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


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for running local models.

    Supports models like:
    - qwen2.5:7b, qwen2.5:14b, qwen2.5:32b
    - llama3.1:8b, llama3.1:70b
    - mistral:7b
    - deepseek-coder:7b

    Setup:
        curl -fsSL https://ollama.ai/install.sh | sh
        ollama pull qwen2.5:7b
    """

    provider_type = CopilotProvider.OLLAMA
    default_model = "qwen2.5:7b"

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"

    async def generate(
        self,
        messages: List[CopilotMessage],
        system_prompt: Optional[str] = None,
    ) -> CopilotResponse:
        """Generate response using Ollama API."""
        start_time = time.time()

        try:
            formatted_messages = self._build_messages(messages, system_prompt)

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "stream": False,
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens,
                        },
                    },
                )

                if response.status_code != 200:
                    return CopilotResponse(
                        content="",
                        provider=self.provider_type,
                        model=self.model,
                        error=f"Ollama API error: {response.status_code} - {response.text}",
                    )

                data = response.json()
                latency_ms = (time.time() - start_time) * 1000

                return CopilotResponse(
                    content=data.get("message", {}).get("content", ""),
                    provider=self.provider_type,
                    model=self.model,
                    tokens_used=data.get("eval_count"),
                    latency_ms=latency_ms,
                )

        except httpx.ConnectError:
            return CopilotResponse(
                content="",
                provider=self.provider_type,
                model=self.model,
                error="Cannot connect to Ollama. Make sure Ollama is running: 'ollama serve'",
            )
        except Exception as e:
            return CopilotResponse(
                content="",
                provider=self.provider_type,
                model=self.model,
                error=f"Ollama error: {str(e)}",
            )

    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return False

                # Check if model is available
                data = response.json()
                available_models = [m.get("name", "") for m in data.get("models", [])]

                # Check for exact match or base name match
                model_base = self.model.split(":")[0]
                return any(
                    self.model in m or model_base in m
                    for m in available_models
                )

        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []
