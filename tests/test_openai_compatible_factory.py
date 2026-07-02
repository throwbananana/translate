from types import SimpleNamespace

import pytest

from providers.base import DEFAULT_PROVIDER_TIMEOUT_SECONDS
from providers.openai_compatible_factory import (
    build_custom_local_provider,
    build_openai_compatible_provider,
)


pytestmark = pytest.mark.unit

DUMMY_KEY = "unit" + "-test"


def test_build_openai_compatible_provider_uses_deepseek_defaults():
    config = SimpleNamespace(api_key=DUMMY_KEY, model="", base_url="", timeout_seconds=33)  # pragma: allowlist secret

    provider = build_openai_compatible_provider("deepseek", config)

    assert provider.api_key == DUMMY_KEY  # pragma: allowlist secret
    assert provider.model == "deepseek-chat"
    assert provider.base_url == "https://api.deepseek.com/v1"
    assert provider.timeout_seconds == 33.0


def test_build_openai_compatible_provider_uses_lm_studio_defaults():
    config = SimpleNamespace(api_key="", model="local-model", base_url="")  # pragma: allowlist secret

    provider = build_openai_compatible_provider("lm_studio", config)

    assert provider.api_key == "lm-studio"  # pragma: allowlist secret
    assert provider.model == "local-model"
    assert provider.base_url == "http://127.0.0.1:1234/v1"
    assert provider.timeout_seconds == DEFAULT_PROVIDER_TIMEOUT_SECONDS


def test_build_openai_compatible_provider_accepts_mapping_config():
    provider = build_openai_compatible_provider(
        "openai",
        {
            "api_key": DUMMY_KEY,  # pragma: allowlist secret
            "model": "gpt-test",
            "base_url": "https://example.test/v1",
            "timeout": 22,
        },
    )

    assert provider.api_key == DUMMY_KEY  # pragma: allowlist secret
    assert provider.model == "gpt-test"
    assert provider.base_url == "https://example.test/v1"
    assert provider.timeout_seconds == 22.0


def test_build_custom_local_provider_uses_model_id_and_lm_studio_key():
    provider = build_custom_local_provider(
        "my-local-model",
        {
            "model_id": "qwen-local",
            "base_url": "http://127.0.0.1:1234/v1",
        },
    )

    assert provider.api_key == "lm-studio"  # pragma: allowlist secret
    assert provider.model == "qwen-local"
    assert provider.base_url == "http://127.0.0.1:1234/v1"
