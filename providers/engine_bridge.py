#! python
# -*- coding: utf-8 -*-
"""Bridge helpers between TranslationEngine and provider adapters.

The existing `translation_engine.py` methods currently return `(translated_text,
model_name)` tuples.  This module keeps that return shape while delegating the
actual OpenAI-compatible call to adapters.  It lets the engine migrate one method
at a time without duplicating provider defaults or timeout handling.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import ProviderRequest
from .openai_compatible_factory import (
    build_custom_local_provider,
    build_openai_compatible_provider,
)


def build_translation_system_instruction(target_lang: str, glossary_prompt: str = "") -> str:
    """Build the standard system instruction used by current engine providers."""
    system_prompt = f"你是一个专业的翻译助手，请将用户提供的文本翻译成{target_lang}，保持原文的格式和段落结构。"
    if glossary_prompt:
        return f"{glossary_prompt}{system_prompt}"
    return system_prompt


def translate_with_openai_compatible_config(
    *,
    provider_name: str,
    config: Any,
    text: str,
    target_lang: str,
    glossary_prompt: str = "",
    openai_module: Any = None,
) -> tuple[str, str]:
    """Translate using an APIConfig-like OpenAI-compatible provider config."""
    provider = build_openai_compatible_provider(
        provider_name,
        config,
        openai_module=openai_module,
    )
    request = ProviderRequest(
        text=text,
        target_lang=target_lang,
        system_instruction=build_translation_system_instruction(target_lang, glossary_prompt),
        model=provider.model,
        temperature=getattr(config, "temperature", 0.2) if not isinstance(config, Mapping) else config.get("temperature", 0.2),
        max_tokens=getattr(config, "max_tokens", 4096) if not isinstance(config, Mapping) else config.get("max_tokens", 4096),
        timeout_seconds=provider.timeout_seconds,
    )
    response = provider.translate(request)
    return response.text, response.model


def translate_with_custom_local_config(
    *,
    model_key: str,
    config: Mapping[str, Any],
    text: str,
    target_lang: str,
    glossary_prompt: str = "",
    openai_module: Any = None,
) -> tuple[str, str]:
    """Translate using a custom local model config dict."""
    provider = build_custom_local_provider(
        model_key,
        config,
        openai_module=openai_module,
    )
    request = ProviderRequest(
        text=text,
        target_lang=target_lang,
        system_instruction=build_translation_system_instruction(target_lang, glossary_prompt),
        model=provider.model,
        temperature=float(config.get("temperature", 0.2)),
        max_tokens=int(config.get("max_tokens", 4096)),
        timeout_seconds=provider.timeout_seconds,
    )
    response = provider.translate(request)
    return response.text, response.model
