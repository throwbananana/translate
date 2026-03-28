# -*- coding: utf-8 -*-
"""Utilities for resolving and validating retry API selections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


BUILTIN_API_NAME_MAP = {
    "Gemini API": "gemini",
    "OpenAI API": "openai",
    "Claude API": "claude",
    "DeepSeek API": "deepseek",
    "本地 LM Studio": "lm_studio",
    "自定义API": "custom",
}


def map_api_name_to_key(
    api_name: Optional[str],
    custom_local_models: Optional[Dict[str, Dict[str, Any]]] = None,
    default: str = "gemini",
) -> str:
    """Map a user-facing API label to the runtime provider key."""
    if not api_name:
        return default

    custom_local_models = custom_local_models or {}
    if api_name.startswith("[本地] "):
        display_name = api_name[5:]
        for key, config in custom_local_models.items():
            if config.get("display_name") == display_name:
                return key

    return BUILTIN_API_NAME_MAP.get(api_name, default)


def choose_retry_api_name(
    api_names: Iterable[str],
    current_retry: Optional[str],
    translation_api_name: Optional[str],
) -> Optional[str]:
    """Choose a stable retry API selection when available options change."""
    api_names = list(api_names)
    if not api_names:
        return current_retry
    if current_retry in api_names:
        return current_retry

    preferred_retry = "本地 LM Studio" if "本地 LM Studio" in api_names else translation_api_name
    if preferred_retry in api_names:
        return preferred_retry

    return api_names[0]


@dataclass
class RetryAPIValidationResult:
    api_name: str
    api_type: str
    is_ready: bool
    error_message: str = ""
    open_api_config: bool = False
    edit_local_model: bool = False
    requires_user_action: bool = False


def validate_retry_api_selection(
    api_name: Optional[str],
    api_configs: Dict[str, Dict[str, Any]],
    custom_local_models: Dict[str, Dict[str, Any]],
    openai_support: bool,
) -> RetryAPIValidationResult:
    """Validate whether the selected retry API can be used immediately."""
    api_type = map_api_name_to_key(api_name, custom_local_models)

    if api_type in custom_local_models:
        config = custom_local_models[api_type]
        if not config.get("base_url") or not config.get("model_id"):
            return RetryAPIValidationResult(
                api_name=api_name or "",
                api_type=api_type,
                is_ready=False,
                error_message="请先配置本地模型的 Base URL 和 Model ID",
                edit_local_model=True,
                requires_user_action=True,
            )
        if not openai_support:
            return RetryAPIValidationResult(
                api_name=api_name or "",
                api_type=api_type,
                is_ready=False,
                error_message="缺少 openai 库，无法调用本地模型",
            )
        return RetryAPIValidationResult(api_name=api_name or "", api_type=api_type, is_ready=True)

    config = api_configs.get(api_type, {})
    if api_type == "custom" and not config.get("base_url"):
        return RetryAPIValidationResult(
            api_name=api_name or "",
            api_type=api_type,
            is_ready=False,
            error_message="请先配置自定义API的 Base URL",
            open_api_config=True,
            requires_user_action=True,
        )

    if api_type in {"gemini", "openai", "custom", "lm_studio"} and not config.get("api_key"):
        return RetryAPIValidationResult(
            api_name=api_name or "",
            api_type=api_type,
            is_ready=False,
            error_message="请先配置API Key",
            open_api_config=True,
            requires_user_action=True,
        )

    if api_type == "lm_studio" and not openai_support:
        return RetryAPIValidationResult(
            api_name=api_name or "",
            api_type=api_type,
            is_ready=False,
            error_message="缺少 openai 库，无法调用本地LM Studio",
        )

    return RetryAPIValidationResult(api_name=api_name or "", api_type=api_type, is_ready=True)
