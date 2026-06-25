from types import SimpleNamespace

import pytest

from providers.base import ProviderRequest
from providers.claude_provider import ClaudeProvider
from providers.errors import ProviderTimeoutError


pytestmark = pytest.mark.unit


class FakeMessages:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text="Claude 译文")])


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.messages = FakeMessages()


class FakeAnthropicModule:
    last_client = None

    @classmethod
    def Anthropic(cls, **kwargs):
        cls.last_client = FakeClient(**kwargs)
        return cls.last_client


class TimeoutMessages:
    def create(self, **kwargs):
        class APITimeoutError(Exception):
            pass
        raise APITimeoutError("timed out")


class TimeoutClient(FakeClient):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.messages = TimeoutMessages()


class TimeoutAnthropicModule:
    @classmethod
    def Anthropic(cls, **kwargs):
        return TimeoutClient(**kwargs)


def test_claude_provider_passes_timeout_and_returns_text():
    provider = ClaudeProvider(
        api_key="claude-key",
        model="claude-test",
        timeout_seconds=40,
        anthropic_module=FakeAnthropicModule,
    )

    response = provider.translate(ProviderRequest(
        text="source",
        target_lang="中文",
        system_instruction="术语表：A=B\n",
        max_tokens=2048,
        timeout_seconds=12,
    ))
    client = FakeAnthropicModule.last_client
    create_kwargs = client.messages.last_kwargs

    assert client.kwargs["api_key"] == "claude-key"
    assert client.kwargs["timeout"] == 40.0
    assert create_kwargs["timeout"] == 12.0
    assert create_kwargs["model"] == "claude-test"
    assert create_kwargs["max_tokens"] == 2048
    assert "术语表：A=B" in create_kwargs["system"]
    assert response.text == "Claude 译文"


def test_claude_provider_maps_timeout_errors():
    provider = ClaudeProvider(
        api_key="claude-key",
        model="claude-test",
        timeout_seconds=5,
        anthropic_module=TimeoutAnthropicModule,
    )

    with pytest.raises(ProviderTimeoutError):
        provider.translate(ProviderRequest(text="source", target_lang="中文"))
