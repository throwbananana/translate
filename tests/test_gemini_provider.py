from types import SimpleNamespace

import pytest

from providers.base import ProviderRequest
from providers.errors import ProviderTimeoutError
from providers.gemini_provider import GeminiProvider


pytestmark = pytest.mark.unit


class FakeModel:
    last_prompt = None
    last_request_options = None

    def __init__(self, model_name):
        self.model_name = model_name

    def generate_content(self, prompt, request_options=None):
        FakeModel.last_prompt = prompt
        FakeModel.last_request_options = request_options
        return SimpleNamespace(text="Gemini 译文")


class FakeGenAI:
    configured_key = None
    last_model = None

    @staticmethod
    def configure(api_key):
        FakeGenAI.configured_key = api_key

    @staticmethod
    def GenerativeModel(model_name):
        FakeGenAI.last_model = FakeModel(model_name)
        return FakeGenAI.last_model


class TimeoutModel(FakeModel):
    def generate_content(self, prompt, request_options=None):
        class DeadlineExceeded(Exception):
            pass
        raise DeadlineExceeded("deadline exceeded")


class TimeoutGenAI(FakeGenAI):
    @staticmethod
    def GenerativeModel(model_name):
        return TimeoutModel(model_name)


def test_gemini_provider_passes_timeout_and_returns_text():
    provider = GeminiProvider(
        api_key="gemini-key",
        model="gemini-test",
        timeout_seconds=40,
        genai_module=FakeGenAI,
    )

    response = provider.translate(ProviderRequest(
        text="source",
        target_lang="中文",
        system_instruction="术语表：A=B\n",
        timeout_seconds=11,
    ))

    assert FakeGenAI.configured_key == "gemini-key"
    assert FakeGenAI.last_model.model_name == "gemini-test"
    assert FakeModel.last_request_options == {"timeout": 11.0}
    assert "术语表：A=B" in FakeModel.last_prompt
    assert response.text == "Gemini 译文"
    assert response.model == "gemini-test"


def test_gemini_provider_maps_timeout_errors():
    provider = GeminiProvider(
        api_key="gemini-key",
        model="gemini-test",
        timeout_seconds=5,
        genai_module=TimeoutGenAI,
    )

    with pytest.raises(ProviderTimeoutError):
        provider.translate(ProviderRequest(text="source", target_lang="中文"))
