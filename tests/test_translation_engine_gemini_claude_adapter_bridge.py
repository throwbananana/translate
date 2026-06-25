import pytest

import translation_engine
from providers.base import ProviderResponse
from translation_engine import APIConfig, APIProvider, TranslationEngine


pytestmark = pytest.mark.unit

DUMMY_API_KEY = "unit" + "-test"


class FakeGeminiProvider:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def translate(self, request):
        self.__class__.calls.append((self.kwargs, request))
        return ProviderResponse(text="Gemini bridge text", model=request.model)


class FakeClaudeProvider:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def translate(self, request):
        self.__class__.calls.append((self.kwargs, request))
        return ProviderResponse(text="Claude bridge text", model=request.model)


def test_gemini_path_uses_provider_adapter(monkeypatch):
    FakeGeminiProvider.calls = []
    monkeypatch.setattr(translation_engine, "GEMINI_SUPPORT", True)
    monkeypatch.setattr(translation_engine, "GeminiProvider", FakeGeminiProvider)

    engine = TranslationEngine()
    config = APIConfig(
        provider=APIProvider.GEMINI,
        api_key=DUMMY_API_KEY,
        model="gemini-test",
        temperature=0.4,
        max_tokens=1234,
        timeout_seconds=17,
    )
    engine.add_api_config("gemini", config)

    translated, model = engine._translate_with_gemini("source", "中文", "术语表：A=B\n")

    provider_kwargs, request = FakeGeminiProvider.calls[0]
    assert translated == "Gemini bridge text"
    assert model == "gemini-test"
    assert provider_kwargs == {
        "api_key": DUMMY_API_KEY,
        "model": "gemini-test",
        "timeout_seconds": 17,
    }
    assert request.text == "source"
    assert request.target_lang == "中文"
    assert request.system_instruction == "术语表：A=B\n"
    assert request.temperature == 0.4
    assert request.max_tokens == 1234
    assert request.timeout_seconds == 17


def test_claude_path_uses_provider_adapter(monkeypatch):
    FakeClaudeProvider.calls = []
    monkeypatch.setattr(translation_engine, "CLAUDE_SUPPORT", True)
    monkeypatch.setattr(translation_engine, "ClaudeProvider", FakeClaudeProvider)

    engine = TranslationEngine()
    config = APIConfig(
        provider=APIProvider.CLAUDE,
        api_key=DUMMY_API_KEY,
        model="claude-test",
        temperature=0.1,
        max_tokens=2222,
        timeout_seconds=25,
    )
    engine.add_api_config("claude", config)

    translated, model = engine._translate_with_claude("source", "English", "风格要求：直译\n")

    provider_kwargs, request = FakeClaudeProvider.calls[0]
    assert translated == "Claude bridge text"
    assert model == "claude-test"
    assert provider_kwargs == {
        "api_key": DUMMY_API_KEY,
        "model": "claude-test",
        "timeout_seconds": 25,
    }
    assert request.text == "source"
    assert request.target_lang == "English"
    assert request.system_instruction == "风格要求：直译\n"
    assert request.temperature == 0.1
    assert request.max_tokens == 2222
    assert request.timeout_seconds == 25
