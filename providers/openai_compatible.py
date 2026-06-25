#! python
# -*- coding: utf-8 -*-
"""OpenAI-compatible provider adapter.

This adapter is intended for OpenAI, DeepSeek, LM Studio and custom OpenAI-style
HTTP endpoints.  It centralizes timeout handling and response normalization so
`translation_engine.py` can eventually delegate provider calls here.
"""

from __future__ import annotations

from typing import Any

from .base import ProviderRequest, ProviderResponse, coerce_timeout_seconds
from .errors import ProviderResponseError, ProviderTimeoutError


class OpenAICompatibleProvider:
    """Adapter for SDKs exposing `OpenAI(...).chat.completions.create(...)`."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "",
        timeout_seconds: float | int | str | None = None,
        openai_module: Any = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout_seconds = coerce_timeout_seconds(timeout_seconds)
        self._openai_module = openai_module

    def _load_openai_module(self):
        if self._openai_module is not None:
            return self._openai_module

        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise ProviderResponseError("openai package is not installed") from exc
        return openai

    def create_client(self):
        """Create an OpenAI-compatible SDK client with an explicit timeout."""
        openai_module = self._load_openai_module()
        kwargs = {
            "api_key": self.api_key,
            "timeout": self.timeout_seconds,
        }
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return openai_module.OpenAI(**kwargs)

    def translate(self, request: ProviderRequest) -> ProviderResponse:
        """Translate text and return a normalized response."""
        client = self.create_client()
        model = request.model or self.model
        timeout = coerce_timeout_seconds(request.timeout_seconds or self.timeout_seconds)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt(request)},
                    {"role": "user", "content": request.text},
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                timeout=timeout,
            )
        except TimeoutError as exc:
            raise ProviderTimeoutError(f"provider request timed out after {timeout:.1f}s") from exc

        translated_text = self._extract_text(response)
        if not translated_text:
            raise ProviderResponseError("provider returned an empty translation")

        tokens_used = self._extract_total_tokens(response)
        return ProviderResponse(text=translated_text, model=model, tokens_used=tokens_used)

    @staticmethod
    def _build_system_prompt(request: ProviderRequest) -> str:
        prompt = f"请将以下文本翻译成{request.target_lang}。"
        if request.system_instruction:
            prompt += "\n\n" + request.system_instruction
        return prompt

    @staticmethod
    def _extract_text(response: Any) -> str:
        try:
            return (response.choices[0].message.content or "").strip()
        except (AttributeError, IndexError, TypeError):
            return ""

    @staticmethod
    def _extract_total_tokens(response: Any) -> int:
        usage = getattr(response, "usage", None)
        total_tokens = getattr(usage, "total_tokens", 0)
        try:
            return int(total_tokens or 0)
        except (TypeError, ValueError):
            return 0
