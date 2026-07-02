import pytest

from providers.browser_automation import (
    build_browser_translation_prompt,
    normalize_browser_model_config,
)
from providers.base import ProviderRequest


pytestmark = pytest.mark.unit


def test_browser_model_config_merges_preset_defaults():
    config = normalize_browser_model_config(
        "deepseek-web",
        {
            "preset": "deepseek_web",
            "display_name": "DeepSeek Web",
            "headless": "true",
        },
    )

    assert config["start_url"] == "https://chat.deepseek.com/"
    assert config["display_name"] == "DeepSeek Web"
    assert config["headless"] is True
    assert config["user_data_dir"].endswith("deepseek-web")


def test_legacy_gptinstant_preset_migrates_to_chatgpt_defaults():
    config = normalize_browser_model_config(
        "gpt-web",
        {
            "preset": "gptinstant_web",
            "display_name": "GPTInstant 网页端",
            "start_url": "https://gptinstant.com/",
        },
    )

    assert config["preset"] == "chatgpt_web"
    assert config["display_name"] == "ChatGPT 网页端"
    assert config["start_url"] == "https://chatgpt.com/"
    assert config["prompt_selector"] == "#prompt-textarea"
    assert "send-button" in config["submit_selector"]


def test_gemini_preset_does_not_match_hidden_quill_clipboard():
    config = normalize_browser_model_config("gemini-web", {"preset": "gemini_web"})

    assert "ql-clipboard" not in config["prompt_selector"]
    assert "div[contenteditable='true'], textarea" not in config["prompt_selector"]
    assert "textarea" in config["prompt_selector"]
    assert ".ql-editor" in config["prompt_selector"]


def test_browser_translation_prompt_includes_style_and_plain_output_rule():
    prompt = build_browser_translation_prompt(
        ProviderRequest(
            text="Hello",
            target_lang="中文",
            system_instruction="风格要求：自然流畅",
        )
    )

    assert "风格要求：自然流畅" in prompt
    assert "翻译成中文" in prompt
    assert "只输出翻译结果" in prompt
    assert prompt.endswith("Hello")
