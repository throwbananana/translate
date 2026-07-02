import pytest

import translation_engine
from translation_engine import APIConfig, APIProvider, TranslationEngine, create_engine_with_config
from providers.base import ProviderResponse


pytestmark = pytest.mark.unit

DUMMY_KEY = "unit" + "-test"


def test_api_config_accepts_timeout_seconds():
    config = APIConfig(
        provider=APIProvider.OPENAI,
        api_key=DUMMY_KEY,  # pragma: allowlist secret
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
            api_key=DUMMY_KEY,  # pragma: allowlist secret
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
        api_key=DUMMY_KEY,  # pragma: allowlist secret
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
        APIConfig(provider=APIProvider.DEEPSEEK, api_key=DUMMY_KEY, model=""),  # pragma: allowlist secret
    )
    engine.add_api_config(
        "lm_studio",
        APIConfig(provider=APIProvider.LM_STUDIO, api_key="", model="local-model"),  # pragma: allowlist secret
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


def test_browser_model_path_uses_browser_provider(monkeypatch):
    calls = []

    class FakeBrowserProvider:
        def __init__(self, model_key, config):
            self.model_key = model_key
            self.config = config
            self.model = config["display_name"]

        @classmethod
        def from_config(cls, model_key, config):
            calls.append(("from_config", model_key, config))
            return cls(model_key, config)

        def translate(self, request):
            calls.append(("translate", request.text, request.target_lang, request.system_instruction))
            return ProviderResponse(text="网页译文", model=self.model)

        def close(self):
            calls.append(("close", self.model_key))

    monkeypatch.setattr(translation_engine, "PLAYWRIGHT_SUPPORT", True)
    monkeypatch.setattr(translation_engine, "BrowserAutomationProvider", FakeBrowserProvider)

    engine = TranslationEngine()
    engine.add_browser_model(
        "deepseek-web",
        {
            "display_name": "DeepSeek Web",
            "start_url": "https://chat.deepseek.com/",
            "prompt_selector": "textarea",
            "response_selector": ".markdown",
        },
    )

    translated, model = engine._translate_with_browser_model("source", "中文", "deepseek-web", "术语表")

    assert translated == "网页译文"
    assert model == "DeepSeek Web"
    assert calls[0][0] == "from_config"
    assert calls[1] == ("translate", "source", "中文", "术语表")


def test_create_engine_with_config_reads_timeout_seconds(monkeypatch):
    monkeypatch.setattr(translation_engine, "OPENAI_SUPPORT", True)

    engine = create_engine_with_config({
        "api_configs": {
            "openai": {
                "api_key": DUMMY_KEY,  # pragma: allowlist secret
                "model": "gpt-test",
                "timeout_seconds": 44,
            }
        }
    })

    assert engine.api_configs["openai"].timeout_seconds == 44


def test_create_engine_with_config_reads_browser_models(monkeypatch):
    monkeypatch.setattr(translation_engine, "PLAYWRIGHT_SUPPORT", True)

    engine = create_engine_with_config({
        "browser_models": {
            "gemini-web": {
                "display_name": "Gemini Web",
                "start_url": "https://gemini.google.com/app",
                "prompt_selector": "textarea",
                "response_selector": ".markdown",
            }
        }
    })

    assert "gemini-web" in engine.browser_models
    assert engine.fallback_provider == "gemini-web"
