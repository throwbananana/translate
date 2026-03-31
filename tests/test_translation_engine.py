import pytest

import translation_engine as te
from translation_engine import APIConfig, APIProvider, TranslationEngine


pytestmark = pytest.mark.unit


def test_get_available_providers_filters_incomplete_configs(monkeypatch):
    monkeypatch.setattr(te, "OPENAI_SUPPORT", True)
    monkeypatch.setattr(te, "REQUESTS_SUPPORT", True)

    engine = TranslationEngine()
    engine.add_api_config(
        "openai",
        APIConfig(provider=APIProvider.OPENAI, api_key="", model="gpt-4o-mini"),
    )
    engine.add_api_config(
        "custom",
        APIConfig(provider=APIProvider.CUSTOM, api_key="", model="", base_url="http://127.0.0.1:8000/v1"),
    )
    engine.add_api_config(
        "lm_studio",
        APIConfig(provider=APIProvider.LM_STUDIO, api_key="lm-studio", model="qwen", base_url="http://127.0.0.1:1234/v1"),
    )

    assert engine.get_available_providers() == ["lm_studio"]


def test_translate_returns_clear_error_for_unconfigured_provider(monkeypatch):
    monkeypatch.setattr(te, "OPENAI_SUPPORT", True)

    engine = TranslationEngine()
    result = engine.translate("hello", "中文", provider="openai", use_memory=False, use_glossary=False)

    assert result.success is False
    assert "未配置完成" in result.error or "不可用" in result.error
