"""
MiMo LLM Client — OpenAI-compatible client for Xiaomi MiMo API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://token-plan-sgp.xiaomimimo.com/v1"
DEFAULT_MODEL = "MiMo-v2.5-pro"


@dataclass
class LLMResponse:
    """Structured LLM response."""

    content: str
    model: str
    usage: Optional[Any] = None
    raw: Optional[dict] = None


class MiMoClient:
    """
    Async client for Xiaomi MiMo API (OpenAI-compatible).
    Supports chat completions with streaming and non-streaming modes.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._total_tokens = 0
        self._request_count = 0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request to MiMo API."""
        client = await self._get_client()

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs,
        }

        self._request_count += 1
        logger.debug(
            f"MiMo request #{self._request_count}: "
            f"model={payload['model']}, messages={len(messages)}"
        )

        try:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            if usage:
                self._total_tokens += usage.get("total_tokens", 0)

            return LLMResponse(
                content=content,
                model=data.get("model", payload["model"]),
                usage=usage,
                raw=data,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"MiMo API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"MiMo client error: {e}")
            raise

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_requests": self._request_count,
            "total_tokens": self._total_tokens,
            "base_url": self.base_url,
            "default_model": self.default_model,
        }

    async def __aenter__(self) -> MiMoClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
