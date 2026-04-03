import pytest

import translation_engine as te
from translation_engine import APIProvider, create_engine_with_config, provider_enum_for_name


pytestmark = pytest.mark.unit


def test_provider_enum_for_name_maps_builtin_providers():
    assert provider_enum_for_name("gemini") is APIProvider.GEMINI
    assert provider_enum_for_name("lm_studio") is APIProvider.LM_STUDIO
    assert provider_enum_for_name("custom") is APIProvider.CUSTOM
    assert provider_enum_for_name("local-qwen") is None


def test_create_engine_with_config_keeps_lm_studio_and_custom_local(monkeypatch):
    monkeypatch.setattr(te, "GEMINI_SUPPORT", True)
    monkeypatch.setattr(te, "OPENAI_SUPPORT", True)
    monkeypatch.setattr(te, "CLAUDE_SUPPORT", True)
    monkeypatch.setattr(te, "REQUESTS_SUPPORT", True)

    config = {
        "api_configs": {
            "gemini": {"api_key": "gm-test", "model": "gemini-2.5-flash"},
            "openai": {"api_key": "sk-openai", "model": "gpt-4o-mini"},
            "lm_studio": {
                "api_key": "",
                "base_url": "http://127.0.0.1:1234/v1",
                "model": "qwen2.5-7b",
            },
            "custom": {
                "api_key": "",
                "base_url": "http://127.0.0.1:8000/v1",
                "model": "chat-model",
            },
        },
        "custom_local_models": {
            "local-qwen": {
                "display_name": "Local Qwen",
                "base_url": "http://127.0.0.1:8001/v1",
                "model_id": "qwen/local",
                "api_key": "",
            }
        },
    }

    engine = create_engine_with_config(config)

    assert set(engine.api_configs) == {"gemini", "openai", "lm_studio"}
    assert engine.api_configs["lm_studio"].provider is APIProvider.LM_STUDIO
    assert engine.api_configs["lm_studio"].api_key == ""
    assert "custom" not in engine.api_configs

    assert "local-qwen" in engine.custom_local_models
    assert engine.custom_local_models["local-qwen"]["api_key"] == "lm-studio"
    assert engine.fallback_provider == "lm_studio"


def test_create_engine_with_config_skips_invalid_custom_local_model(monkeypatch):
    monkeypatch.setattr(te, "OPENAI_SUPPORT", True)

    engine = create_engine_with_config(
        {
            "custom_local_models": {
                "broken-local": {
                    "display_name": "Broken Local",
                    "base_url": "http://127.0.0.1:8001/v1",
                    "model_id": "",
                }
            }
        }
    )

    assert engine.custom_local_models == {}
    assert engine.fallback_provider is None
