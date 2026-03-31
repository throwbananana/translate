#! python
# -*- coding: utf-8 -*-
"""手工测试：对仓库样例文件做真实翻译。"""

import time
from pathlib import Path

from file_processor import FileProcessor

from _common import OUTPUT_DIR, create_gemini_engine, resolve_repo_path


def run_file(file_path: Path, take_segments: int, output_name: str):
    if not file_path.exists():
        print(f"[跳过] 文件不存在: {file_path}")
        return

    processor = FileProcessor()
    engine = create_gemini_engine()

    content = file_path.read_text(encoding="utf-8")
    segments = processor.split_text_into_segments(content, max_length=500)
    selected_segments = segments[:take_segments]

    print(f"[加载] {file_path.name} | 共 {len(content):,} 字符 | 分段 {len(segments)}")
    print(f"[测试] 仅翻译前 {len(selected_segments)} 段")

    translated_segments = []
    for idx, segment in enumerate(selected_segments, 1):
        print(f"[翻译] 段落 {idx}/{len(selected_segments)}...", end=" ", flush=True)
        result = engine.translate(
            segment,
            "中文",
            provider="gemini",
            use_memory=False,
            use_glossary=False,
        )
        if result.success:
            translated_segments.append(result.translated_text)
            print(f"完成 ({len(result.translated_text)} 字符)")
        else:
            translated_segments.append(f"[翻译错误: {result.error}]\n{segment}")
            print(f"失败: {result.error}")
        time.sleep(0.5)

    output_path = OUTPUT_DIR / output_name
    output_path.write_text("\n\n".join(translated_segments), encoding="utf-8")
    print(f"[保存] 已写出: {output_path}")


def main():
    print("=" * 70)
    print("书籍翻译工具 - 实际翻译手工测试")
    print("=" * 70)

    run_file(resolve_repo_path("sample_book.txt"), 3, "sample_book_翻译测试.txt")
    run_file(resolve_repo_path("test_50k.txt"), 2, "test_50k_翻译测试.txt")


if __name__ == "__main__":
    main()
