#! python
# -*- coding: utf-8 -*-
"""Gemini provider adapter."""

from __future__ import annotations

from typing import Any

from .base import ProviderRequest, ProviderResponse, coerce_timeout_seconds
from .errors import ProviderResponseError, ProviderTimeoutError


class GeminiProvider:
    """Adapter for `google.generativeai` style clients."""

    TIMEOUT_ERROR_NAMES = {"TimeoutError", "DeadlineExceeded", "ServiceUnavailable"}

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float | int | str | None = None,
        genai_module: Any = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = coerce_timeout_seconds(timeout_seconds)
        self._genai_module = genai_module

    def _load_genai_module(self):
        if self._genai_module is not None:
            return self._genai_module
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ProviderResponseError("google-generativeai package is not installed") from exc
        return genai

    def translate(self, request: ProviderRequest) -> ProviderResponse:
        genai = self._load_genai_module()
        timeout = coerce_timeout_seconds(request.timeout_seconds or self.timeout_seconds)
        model_name = request.model or self.model
        prompt = self._build_prompt(request)

        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                request_options={"timeout": timeout},
            )
        except Exception as exc:
            if self._is_timeout_error(exc):
                raise ProviderTimeoutError(f"provider request timed out after {timeout:.1f}s") from exc
            raise

        text = getattr(response, "text", "") or ""
        text = text.strip()
        if not text:
            raise ProviderResponseError("provider returned an empty translation")
        return ProviderResponse(text=text, model=model_name, tokens_used=0)

    @staticmethod
    def _build_prompt(request: ProviderRequest) -> str:
        base_prompt = f"请将以下文本翻译成{request.target_lang}，保持原文的格式和段落结构。只输出翻译结果，不要添加任何解释。"
        if request.system_instruction:
            base_prompt = f"{request.system_instruction}{base_prompt}"
        return f"{base_prompt}\n\n{request.text}"

    @classmethod
    def _is_timeout_error(cls, exc: Exception) -> bool:
        names = {type(exc).__name__}
        for parent in type(exc).__mro__:
            names.add(parent.__name__)
        return bool(names & cls.TIMEOUT_ERROR_NAMES)
