from types import SimpleNamespace

import pytest

from providers.base import ProviderRequest
from providers.openai_compatible import OpenAICompatibleProvider


pytestmark = pytest.mark.unit


class FakeCompletions:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="译文"))],
            usage=SimpleNamespace(total_tokens=123),
        )


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class FakeOpenAIModule:
    last_client = None

    @classmethod
    def OpenAI(cls, **kwargs):
        cls.last_client = FakeClient(**kwargs)
        return cls.last_client


def test_create_client_passes_base_url_and_timeout():
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        model="demo-model",
        base_url="http://127.0.0.1:1234/v1",
        timeout_seconds="45",
        openai_module=FakeOpenAIModule,
    )

    client = provider.create_client()

    assert client.kwargs["api_key"] == "test-key"
    assert client.kwargs["base_url"] == "http://127.0.0.1:1234/v1"
    assert client.kwargs["timeout"] == 45.0


def test_translate_passes_request_timeout_and_returns_tokens():
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        model="default-model",
        timeout_seconds=30,
        openai_module=FakeOpenAIModule,
    )
    request = ProviderRequest(
        text="source",
        target_lang="中文",
        system_instruction="保持术语一致",
        model="request-model",
        timeout_seconds=12,
    )

    response = provider.translate(request)
    client = FakeOpenAIModule.last_client
    create_kwargs = client.completions.last_kwargs

    assert response.text == "译文"
    assert response.model == "request-model"
    assert response.tokens_used == 123
    assert create_kwargs["model"] == "request-model"
    assert create_kwargs["timeout"] == 12.0
    assert create_kwargs["messages"][0]["role"] == "system"
    assert "保持术语一致" in create_kwargs["messages"][0]["content"]
