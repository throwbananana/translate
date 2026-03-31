#! python
# -*- coding: utf-8 -*-
"""手工测试：创建测试书籍并跑完整翻译工作流。"""

import time

from file_processor import FileProcessor

from _common import OUTPUT_DIR, create_gemini_engine


TEST_TEXT = """Chapter 1: Introduction

This is a test book for translation.
We want to see how well the translation works.

Chapter 2: Testing

The translation tool should be able to handle multiple paragraphs.
It should preserve the formatting and structure of the original text.

This is another paragraph to test the segmentation functionality."""


def main():
    processor = FileProcessor()
    engine = create_gemini_engine()

    test_file = OUTPUT_DIR / "test_book.txt"
    test_file.write_text(TEST_TEXT, encoding="utf-8")

    print("=" * 60)
    print("测试完整翻译工作流")
    print("=" * 60)
    print(f"\n1. 已创建测试文件: {test_file}")
    print(f"   字符数: {len(TEST_TEXT)}")

    segments = processor.split_text_into_segments(TEST_TEXT, max_length=100)
    print(f"\n2. 文本已分割成 {len(segments)} 段")

    print("\n3. 开始翻译...")
    translated_segments = []
    for idx, segment in enumerate(segments, 1):
        print(f"   翻译段落 {idx}/{len(segments)}...", end=" ", flush=True)
        result = engine.translate(
            segment,
            "中文",
            provider="gemini",
            use_memory=False,
            use_glossary=False,
        )
        if result.success:
            translated_segments.append(result.translated_text)
            print("完成")
        else:
            translated_segments.append(f"[翻译错误: {result.error}]\n{segment}")
            print(f"失败: {result.error}")
        time.sleep(0.5)

    translated_text = "\n\n".join(translated_segments)
    output_file = OUTPUT_DIR / "test_book_translated.txt"
    output_file.write_text(translated_text, encoding="utf-8")

    print(f"\n4. 翻译完成！译文长度: {len(translated_text)} 字符")
    print(f"\n5. 译文已保存到: {output_file}")


if __name__ == "__main__":
    main()
