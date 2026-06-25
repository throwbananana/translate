#! python
# -*- coding: utf-8 -*-
"""Claude provider adapter."""

from __future__ import annotations

from typing import Any

from .base import ProviderRequest, ProviderResponse, coerce_timeout_seconds
from .errors import ProviderResponseError, ProviderTimeoutError


class ClaudeProvider:
    """Adapter for the Anthropic Claude SDK."""

    TIMEOUT_ERROR_NAMES = {"TimeoutError", "APITimeoutError", "ReadTimeout", "ConnectTimeout"}

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float | int | str | None = None,
        anthropic_module: Any = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = coerce_timeout_seconds(timeout_seconds)
        self._anthropic_module = anthropic_module

    def _load_anthropic_module(self):
        if self._anthropic_module is not None:
            return self._anthropic_module
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise ProviderResponseError("anthropic package is not installed") from exc
        return anthropic

    def create_client(self):
        anthropic_module = self._load_anthropic_module()
        return anthropic_module.Anthropic(api_key=self.api_key, timeout=self.timeout_seconds)

    def translate(self, request: ProviderRequest) -> ProviderResponse:
        client = self.create_client()
        model_name = request.model or self.model
        timeout = coerce_timeout_seconds(request.timeout_seconds or self.timeout_seconds)
        system_prompt = self._build_system_prompt(request)

        try:
            message = client.messages.create(
                model=model_name,
                max_tokens=request.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": request.text}],
                timeout=timeout,
            )
        except Exception as exc:
            if self._is_timeout_error(exc):
                raise ProviderTimeoutError(f"provider request timed out after {timeout:.1f}s") from exc
            raise

        text = self._extract_text(message)
        if not text:
            raise ProviderResponseError("provider returned an empty translation")
        return ProviderResponse(text=text, model=model_name, tokens_used=0)

    @staticmethod
    def _build_system_prompt(request: ProviderRequest) -> str:
        prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{request.target_lang}，保持原文的格式和段落结构。"
        if request.system_instruction:
            prompt = f"{request.system_instruction}{prompt}"
        return prompt

    @staticmethod
    def _extract_text(message: Any) -> str:
        try:
            return (message.content[0].text or "").strip()
        except (AttributeError, IndexError, TypeError):
            return ""

    @classmethod
    def _is_timeout_error(cls, exc: Exception) -> bool:
        names = {type(exc).__name__}
        for parent in type(exc).__mro__:
            names.add(parent.__name__)
        return bool(names & cls.TIMEOUT_ERROR_NAMES)
