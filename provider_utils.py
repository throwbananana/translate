#! python
# -*- coding: utf-8 -*-
"""
Provider 配置校验工具。

统一 GUI 与翻译引擎对 provider 就绪状态的判断规则，避免多处维护不一致。
"""

from typing import Dict, List, Optional, Tuple


BUILTIN_PROVIDER_ORDER = (
    "gemini",
    "openai",
    "claude",
    "deepseek",
    "lm_studio",
    "custom",
)


def _normalize_support_flags(support_flags: Optional[Dict[str, bool]] = None) -> Dict[str, bool]:
    flags = {
        "gemini": True,
        "openai": True,
        "claude": True,
        "requests": True,
    }
    if support_flags:
        flags.update(support_flags)
    return flags


def _missing_fields(config: Optional[Dict[str, str]], field_names: List[str]) -> List[str]:
    config = config or {}
    return [field_name for field_name in field_names if not str(config.get(field_name, "")).strip()]


def validate_builtin_provider(
    provider_name: str,
    config: Optional[Dict[str, str]],
    support_flags: Optional[Dict[str, bool]] = None,
) -> Tuple[bool, str]:
    """校验内置 provider 是否可用。"""
    flags = _normalize_support_flags(support_flags)
    config = config or {}

    if provider_name == "gemini":
        if not flags["gemini"]:
            return False, "缺少 google-generativeai 库，无法使用 Gemini"
        missing = _missing_fields(config, ["api_key", "model"])
        if missing:
            return False, f"Gemini 缺少必要配置: {', '.join(missing)}"
        return True, ""

    if provider_name == "openai":
        if not flags["openai"]:
            return False, "缺少 openai 库，无法使用 OpenAI"
        missing = _missing_fields(config, ["api_key", "model"])
        if missing:
            return False, f"OpenAI 缺少必要配置: {', '.join(missing)}"
        return True, ""

    if provider_name == "claude":
        if not flags["claude"]:
            return False, "缺少 anthropic 库，无法使用 Claude"
        missing = _missing_fields(config, ["api_key", "model"])
        if missing:
            return False, f"Claude 缺少必要配置: {', '.join(missing)}"
        return True, ""

    if provider_name == "deepseek":
        if not flags["openai"]:
            return False, "缺少 openai 库，无法使用 DeepSeek"
        missing = _missing_fields(config, ["api_key", "model"])
        if missing:
            return False, f"DeepSeek 缺少必要配置: {', '.join(missing)}"
        return True, ""

    if provider_name == "lm_studio":
        if not flags["openai"]:
            return False, "缺少 openai 库，无法连接 LM Studio"
        missing = _missing_fields(config, ["base_url", "model"])
        if missing:
            return False, f"LM Studio 缺少必要配置: {', '.join(missing)}"
        return True, ""

    if provider_name == "custom":
        if not flags["requests"]:
            return False, "缺少 requests 库，无法使用自定义 API"
        missing = _missing_fields(config, ["api_key", "base_url", "model"])
        if missing:
            return False, f"自定义 API 缺少必要配置: {', '.join(missing)}"
        return True, ""

    return False, f"未知内置 provider: {provider_name}"


def validate_custom_local_model(
    model_name: str,
    config: Optional[Dict[str, str]],
    support_flags: Optional[Dict[str, bool]] = None,
) -> Tuple[bool, str]:
    """校验自定义本地模型是否可用。"""
    flags = _normalize_support_flags(support_flags)
    config = config or {}

    if not flags["openai"]:
        return False, "缺少 openai 库，无法调用本地模型"

    missing = _missing_fields(config, ["base_url", "model_id"])
    if missing:
        return False, f"本地模型 {model_name} 缺少必要配置: {', '.join(missing)}"

    return True, ""


def provider_ready(
    provider_name: str,
    api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    custom_local_models: Optional[Dict[str, Dict[str, str]]] = None,
    support_flags: Optional[Dict[str, bool]] = None,
) -> bool:
    """统一判断 provider 是否可用。"""
    api_configs = api_configs or {}
    custom_local_models = custom_local_models or {}

    if provider_name in custom_local_models:
        return validate_custom_local_model(
            provider_name, custom_local_models.get(provider_name), support_flags
        )[0]

    return validate_builtin_provider(provider_name, api_configs.get(provider_name), support_flags)[0]


def provider_error_message(
    provider_name: str,
    api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    custom_local_models: Optional[Dict[str, Dict[str, str]]] = None,
    support_flags: Optional[Dict[str, bool]] = None,
) -> str:
    """获取 provider 当前不可用的具体原因。"""
    api_configs = api_configs or {}
    custom_local_models = custom_local_models or {}

    if provider_name in custom_local_models:
        return validate_custom_local_model(
            provider_name, custom_local_models.get(provider_name), support_flags
        )[1]

    return validate_builtin_provider(provider_name, api_configs.get(provider_name), support_flags)[1]


def list_ready_builtin_providers(
    api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    support_flags: Optional[Dict[str, bool]] = None,
) -> List[str]:
    """返回当前可用的内置 provider 列表。"""
    api_configs = api_configs or {}
    ready = []

    for provider_name in BUILTIN_PROVIDER_ORDER:
        if provider_ready(provider_name, api_configs=api_configs, support_flags=support_flags):
            ready.append(provider_name)

    return ready


def list_ready_custom_local_models(
    custom_local_models: Optional[Dict[str, Dict[str, str]]] = None,
    support_flags: Optional[Dict[str, bool]] = None,
) -> List[str]:
    """返回当前可用的自定义本地模型列表。"""
    custom_local_models = custom_local_models or {}
    ready = []

    for provider_name in custom_local_models:
        if provider_ready(
            provider_name,
            custom_local_models=custom_local_models,
            support_flags=support_flags,
        ):
            ready.append(provider_name)

    return ready


def choose_fallback_provider(
    api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    custom_local_models: Optional[Dict[str, Dict[str, str]]] = None,
    support_flags: Optional[Dict[str, bool]] = None,
) -> Optional[str]:
    """按约定优先级选择一个可用回退 provider。"""
    api_configs = api_configs or {}
    custom_local_models = custom_local_models or {}

    if provider_ready("lm_studio", api_configs=api_configs, support_flags=support_flags):
        return "lm_studio"

    for provider_name in list_ready_custom_local_models(custom_local_models, support_flags=support_flags):
        return provider_name

    for provider_name in ("deepseek", "openai", "gemini", "claude", "custom"):
        if provider_ready(provider_name, api_configs=api_configs, support_flags=support_flags):
            return provider_name

    return None
