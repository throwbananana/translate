#! python
# -*- coding: utf-8 -*-
"""Factory helpers for OpenAI-compatible provider adapters.

These helpers form the bridge from existing engine config objects/dicts to the
new adapter layer.  They are intentionally small and GUI-free so
`translation_engine.py` can adopt them incrementally.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import DEFAULT_PROVIDER_TIMEOUT_SECONDS
from .openai_compatible import OpenAICompatibleProvider


DEFAULT_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "lm_studio": "http://127.0.0.1:1234/v1",
}

DEFAULT_API_KEYS = {
    "lm_studio": "lm-studio",
}

DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
}


def _get_attr_or_key(config: Any, key: str, default: Any = "") -> Any:
    if isinstance(config, Mapping):
        return config.get(key, default)
    return getattr(config, key, default)


def _timeout_from_config(config: Any) -> float:
    return (
        _get_attr_or_key(config, "timeout_seconds", None)
        or _get_attr_or_key(config, "timeout", None)
        or DEFAULT_PROVIDER_TIMEOUT_SECONDS
    )


def build_openai_compatible_provider(
    provider_name: str,
    config: Any,
    *,
    openai_module: Any = None,
) -> OpenAICompatibleProvider:
    """Build an adapter from an existing APIConfig-like object."""
    api_key = _get_attr_or_key(config, "api_key", "") or DEFAULT_API_KEYS.get(provider_name, "")
    model = _get_attr_or_key(config, "model", "") or DEFAULT_MODELS.get(provider_name, "")
    base_url = _get_attr_or_key(config, "base_url", "") or DEFAULT_BASE_URLS.get(provider_name, "")

    return OpenAICompatibleProvider(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout_seconds=_timeout_from_config(config),
        openai_module=openai_module,
    )


def build_custom_local_provider(
    model_key: str,
    config: Mapping[str, Any],
    *,
    openai_module: Any = None,
) -> OpenAICompatibleProvider:
    """Build an adapter from the custom-local-model config dict."""
    model = config.get("model_id") or config.get("model") or model_key
    return OpenAICompatibleProvider(
        api_key=config.get("api_key") or "lm-studio",
        model=model,
        base_url=config.get("base_url", ""),
        timeout_seconds=config.get("timeout_seconds") or config.get("timeout") or DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        openai_module=openai_module,
    )
