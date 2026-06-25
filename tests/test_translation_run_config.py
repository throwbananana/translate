import pytest

from controllers.translation_run_config import (
    DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    TranslationRunConfig,
    coerce_translation_run_config,
)


pytestmark = pytest.mark.unit


def test_translation_run_config_style_prompt_and_context_mode():
    config = TranslationRunConfig(
        api_type="lm_studio",
        target_language="中文",
        style="日式轻小说 (Light Novel)",
        concurrency=1,
    )

    assert config.use_context is True
    assert config.style_prompt.startswith("风格要求：")
    assert "轻小说" in config.style_prompt


def test_translation_run_config_disables_context_for_parallel_runs():
    config = TranslationRunConfig(
        api_type="gemini",
        target_language="English",
        style="通俗小说 (Novel)",
        concurrency=4,
    )

    assert config.use_context is False


def test_coerce_translation_run_config_clamps_gui_values():
    config = coerce_translation_run_config(
        api_type="",
        target_language="",
        style="unknown",
        concurrency="0",
        segment_size="0",
        translation_delay="-1",
        provider_timeout_seconds="0",
    )

    assert config.api_type == "gemini"
    assert config.target_language == "中文"
    assert config.concurrency == 1
    assert config.segment_size == 1
    assert config.translation_delay == 0.0
    assert config.provider_timeout_seconds == 1.0
    assert config.style_prompt == ""


def test_coerce_translation_run_config_uses_default_timeout():
    config = coerce_translation_run_config(
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
    )

    assert config.provider_timeout_seconds == DEFAULT_PROVIDER_TIMEOUT_SECONDS
