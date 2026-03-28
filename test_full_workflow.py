#! python
# -*- coding: utf-8 -*-
"""完整翻译工作流测试。

默认运行离线、可重复的 smoke test。
若需要真实调用 Gemini，请设置：
    TRANSLATE_LIVE_TEST=1
    GOOGLE_API_KEY=<your key>
"""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path

TEST_TEXT = """Chapter 1: Introduction

This is a test book for translation.
We want to see how well the translation works.

Chapter 2: Testing

The translation tool should be able to handle multiple paragraphs.
It should preserve the formatting and structure of the original text.

This is another paragraph to test the segmentation functionality."""


def split_text_into_segments(text: str, max_length: int = 500) -> list[str]:
    """将文本分割成段落（复制自主程序的基础逻辑）。"""
    paragraphs = re.split(r"\n\s*\n", text)
    segments: list[str] = []
    current_segment = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if not current_segment:
            current_segment = para
            continue

        if len(current_segment) + len(para) + 2 <= max_length:
            current_segment += "\n\n" + para
        else:
            segments.append(current_segment)
            current_segment = para

    if current_segment:
        segments.append(current_segment)

    return segments


def build_translation_prompt(segment: str) -> str:
    return f"请将以下文本翻译成中文，保持原文的格式和段落结构:\n\n{segment}"


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


class FakeModel:
    """离线测试替身，保证测试可重复、可断言。"""

    def generate_content(self, prompt: str) -> FakeResponse:
        source_text = prompt.split("\n\n", 1)[1]
        translated = "[FAKE-ZH]\n" + source_text.replace("Chapter", "章节")
        return FakeResponse(translated)


def get_model():
    live_mode = os.getenv("TRANSLATE_LIVE_TEST") == "1"
    api_key = os.getenv("GOOGLE_API_KEY")

    if not live_mode:
        return FakeModel(), False

    if not api_key:
        raise RuntimeError("已启用实时测试，但缺少 GOOGLE_API_KEY 环境变量。")

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash"), True


def translate_segments(model, segments: list[str]) -> list[str]:
    translated_segments: list[str] = []
    for segment in segments:
        prompt = build_translation_prompt(segment)
        response = model.generate_content(prompt)
        translated_segments.append(response.text)
    return translated_segments


class TestFullWorkflow(unittest.TestCase):
    def test_offline_workflow_creates_translated_file(self) -> None:
        model = FakeModel()
        segments = split_text_into_segments(TEST_TEXT, max_length=100)
        self.assertGreater(len(segments), 1)

        translated_segments = translate_segments(model, segments)
        translated_text = "\n\n".join(translated_segments)

        self.assertIn("[FAKE-ZH]", translated_text)
        self.assertIn("章节 1", translated_text)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_book_translated.txt"
            output_file.write_text(translated_text, encoding="utf-8")

            self.assertTrue(output_file.exists())
            self.assertEqual(output_file.read_text(encoding="utf-8"), translated_text)

    @unittest.skipUnless(os.getenv("TRANSLATE_LIVE_TEST") == "1", "未启用实时 Gemini 集成测试")
    def test_live_gemini_translation_when_explicitly_enabled(self) -> None:
        model, is_live = get_model()
        self.assertTrue(is_live)

        segments = split_text_into_segments("Hello world\n\nThis is a test.", max_length=50)
        translated_segments = translate_segments(model, segments)
        translated_text = "\n\n".join(translated_segments)

        self.assertTrue(translated_text.strip())
        self.assertGreater(len(translated_text), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
