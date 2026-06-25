import pytest

import translation_engine
from translation_engine import APIConfig, APIProvider, TranslationEngine, create_engine_with_config


pytestmark = pytest.mark.unit

DUMMY_API_KEY = "unit" + "-test"


def test_api_config_accepts_timeout_seconds():
    config = APIConfig(
        provider=APIProvider.OPENAI,
        api_key=DUMMY_API_KEY,
        model="gpt-test",
        timeout_seconds=12,
    )

    assert config.timeout_seconds == 12


def test_engine_serializes_timeout_seconds():
    engine = TranslationEngine()
    engine.add_api_config(
        "openai",
        APIConfig(
            provider=APIProvider.OPENAI,
            api_key=DUMMY_API_KEY,
            model="gpt-test",
            timeout_seconds=21,
        ),
    )

    serialized = engine._serialize_api_configs()

    assert serialized["openai"]["timeout_seconds"] == 21


def test_openai_path_uses_engine_bridge(monkeypatch):
    calls = []

    def fake_bridge(**kwargs):
        calls.append(kwargs)
        return "译文", "bridge-model"

    monkeypatch.setattr(translation_engine, "OPENAI_SUPPORT", True)
    monkeypatch.setattr(translation_engine, "translate_with_openai_compatible_config", fake_bridge)

    engine = TranslationEngine()
    config = APIConfig(
        provider=APIProvider.OPENAI,
        api_key=DUMMY_API_KEY,
        model="gpt-test",
        timeout_seconds=30,
    )
    engine.add_api_config("openai", config)

    translated, model = engine._translate_with_openai("source", "中文", "术语表：A=B\n")

    assert translated == "译文"
    assert model == "bridge-model"
    assert calls[0]["provider_name"] == "openai"
    assert calls[0]["config"] is config
    assert calls[0]["glossary_prompt"] == "术语表：A=B\n"


def test_deepseek_and_lm_studio_paths_use_engine_bridge(monkeypatch):
    provider_names = []

    def fake_bridge(**kwargs):
        provider_names.append(kwargs["provider_name"])
        return "译文", kwargs["provider_name"]

    monkeypatch.setattr(translation_engine, "OPENAI_SUPPORT", True)
    monkeypatch.setattr(translation_engine, "translate_with_openai_compatible_config", fake_bridge)

    engine = TranslationEngine()
    engine.add_api_config(
        "deepseek",
        APIConfig(provider=APIProvider.DEEPSEEK, api_key=DUMMY_API_KEY, model=""),
    )
    engine.add_api_config(
        "lm_studio",
        APIConfig(provider=APIProvider.LM_STUDIO, api_key="", model="local-model"),
    )

    assert engine._translate_with_deepseek("source", "中文") == ("译文", "deepseek")
    assert engine._translate_with_lm_studio("source", "中文") == ("译文", "lm_studio")
    assert provider_names == ["deepseek", "lm_studio"]


def test_custom_local_path_uses_engine_bridge(monkeypatch):
    calls = []

    def fake_custom_bridge(**kwargs):
        calls.append(kwargs)
        return "本地译文", "local-model"

    monkeypatch.setattr(translation_engine, "OPENAI_SUPPORT", True)
    monkeypatch.setattr(translation_engine, "translate_with_custom_local_config", fake_custom_bridge)

    engine = TranslationEngine()
    engine.custom_local_models["local"] = {
        "display_name": "Local",
        "base_url": "http://127.0.0.1:1234/v1",
        "model_id": "local-model",
        "timeout_seconds": 18,
    }

    translated, model = engine._translate_with_custom_local("source", "中文", "local")

    assert translated == "本地译文"
    assert model == "local-model"
    assert calls[0]["model_key"] == "local"
    assert calls[0]["config"] is engine.custom_local_models["local"]


def test_create_engine_with_config_reads_timeout_seconds(monkeypatch):
    monkeypatch.setattr(translation_engine, "OPENAI_SUPPORT", True)

    engine = create_engine_with_config({
        "api_configs": {
            "openai": {
                "api_key": DUMMY_API_KEY,
                "model": "gpt-test",
                "timeout_seconds": 44,
            }
        }
    })

    assert engine.api_configs["openai"].timeout_seconds == 44
