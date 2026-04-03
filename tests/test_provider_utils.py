import pytest

from provider_utils import (
    choose_fallback_provider,
    list_ready_builtin_providers,
    provider_error_message,
    provider_ready,
    validate_builtin_provider,
    validate_custom_local_model,
)


pytestmark = pytest.mark.unit


def test_lm_studio_is_ready_without_api_key():
    api_configs = {
        "lm_studio": {
            "api_key": "",
            "base_url": "http://127.0.0.1:1234/v1",
            "model": "qwen",
        }
    }
    support_flags = {"openai": True}

    assert provider_ready("lm_studio", api_configs=api_configs, support_flags=support_flags) is True
    assert "lm_studio" in list_ready_builtin_providers(api_configs, support_flags)


def test_builtin_provider_reports_missing_fields():
    ready, reason = validate_builtin_provider(
        "custom",
        {"api_key": "", "base_url": "http://127.0.0.1:8000/v1", "model": ""},
        support_flags={"requests": True},
    )

    assert ready is False
    assert "api_key" in reason
    assert "model" in reason


def test_custom_local_model_requires_base_url_and_model_id():
    ready, reason = validate_custom_local_model(
        "local-qwen",
        {"base_url": "", "model_id": ""},
        support_flags={"openai": True},
    )

    assert ready is False
    assert "base_url" in reason
    assert "model_id" in reason


def test_choose_fallback_provider_prefers_lm_studio():
    api_configs = {
        "openai": {"api_key": "sk-test", "model": "gpt-4o-mini", "base_url": ""},
        "lm_studio": {"api_key": "", "base_url": "http://127.0.0.1:1234/v1", "model": "qwen"},
    }
    custom_local_models = {
        "local-qwen": {"base_url": "http://127.0.0.1:8000/v1", "model_id": "qwen"}
    }
    support_flags = {"openai": True}

    assert choose_fallback_provider(api_configs, custom_local_models, support_flags) == "lm_studio"


def test_provider_error_message_for_missing_dependency():
    message = provider_error_message(
        "openai",
        api_configs={"openai": {"api_key": "sk-test", "model": "gpt-4o-mini"}},
        support_flags={"openai": False},
    )

    assert "缺少 openai 库" in message
