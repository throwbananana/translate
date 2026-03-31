#! python
# -*- coding: utf-8 -*-
"""手工测试：Gemini 最小翻译烟雾验证。"""

from _common import create_gemini_engine


TEST_TEXT = """
Hello, this is a test.
I want to translate this text to Chinese.
This is a simple test of the translation functionality.
"""


def main():
    print("正在执行 Gemini API 最小翻译烟雾测试...")
    print(f"原文:\n{TEST_TEXT}\n")

    engine = create_gemini_engine()
    result = engine.translate(
        TEST_TEXT,
        "中文",
        provider="gemini",
        use_memory=False,
        use_glossary=False,
    )

    if not result.success:
        raise RuntimeError(f"翻译失败: {result.error}")

    print("译文:")
    print(result.translated_text)
    print("\n翻译成功。")


if __name__ == "__main__":
    main()
