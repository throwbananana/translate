from types import SimpleNamespace

import pytest

from providers.engine_bridge import (
    build_translation_system_instruction,
    translate_with_custom_local_config,
    translate_with_openai_compatible_config,
)


pytestmark = pytest.mark.unit

DUMMY_API_KEY = "unit" + "-test"


class FakeCompletions:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="桥接译文"))],
            usage=SimpleNamespace(total_tokens=10),
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


def test_build_translation_system_instruction_keeps_glossary_prefix():
    prompt = build_translation_system_instruction("中文", "术语表：A=B\n")

    assert prompt.startswith("术语表：A=B")
    assert "翻译成中文" in prompt
    assert "格式和段落结构" in prompt


def test_translate_with_openai_compatible_config_returns_engine_tuple_shape():
    config = SimpleNamespace(
        api_key=DUMMY_API_KEY,
        model="gpt-test",
        base_url="https://example.test/v1",
        temperature=0.3,
        max_tokens=1024,
        timeout_seconds=17,
    )

    translated, model = translate_with_openai_compatible_config(
        provider_name="openai",
        config=config,
        text="source text",
        target_lang="中文",
        glossary_prompt="术语表：A=B\n",
        openai_module=FakeOpenAIModule,
    )
    client = FakeOpenAIModule.last_client
    create_kwargs = client.completions.last_kwargs

    assert translated == "桥接译文"
    assert model == "gpt-test"
    assert client.kwargs["timeout"] == 17.0
    assert create_kwargs["timeout"] == 17.0
    assert create_kwargs["temperature"] == 0.3
    assert create_kwargs["max_tokens"] == 1024
    assert "术语表：A=B" in create_kwargs["messages"][0]["content"]


def test_translate_with_custom_local_config_returns_engine_tuple_shape():
    translated, model = translate_with_custom_local_config(
        model_key="local-key",
        config={
            "model_id": "qwen-local",
            "base_url": "http://127.0.0.1:1234/v1",
            "timeout_seconds": 9,
        },
        text="source text",
        target_lang="中文",
        openai_module=FakeOpenAIModule,
    )
    client = FakeOpenAIModule.last_client

    assert translated == "桥接译文"
    assert model == "qwen-local"
    assert client.kwargs["api_key"] == "lm-studio"
    assert client.kwargs["base_url"] == "http://127.0.0.1:1234/v1"
    assert client.kwargs["timeout"] == 9.0
