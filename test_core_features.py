#! python
# -*- coding: utf-8 -*-
"""核心功能自动化测试（断言版）。"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

PREVIEW_LIMIT = 10_000


def get_character_count(filepath: Path) -> int:
    """按主程序的思路，优先按 UTF-8 文本字符数计算。"""
    try:
        return len(filepath.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return filepath.stat().st_size


def get_display_mode(char_count: int, preview_limit: int = PREVIEW_LIMIT) -> str:
    return "预览模式" if char_count > preview_limit else "完整显示"


def read_for_display(filepath: Path, preview_limit: int = PREVIEW_LIMIT) -> dict:
    content = filepath.read_text(encoding="utf-8")
    char_count = len(content)
    is_large = char_count > preview_limit
    preview_text = content[:preview_limit] if is_large else content
    return {
        "content": content,
        "char_count": char_count,
        "display_chars": len(preview_text),
        "mode": "预览" if is_large else "完整",
    }


def split_text_into_segments(text: str, max_length: int = 500) -> list[str]:
    """将文本按段落聚合切分，保持与主程序一致的基本策略。"""
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


def simulate_preview_toggle(content: str, preview_limit: int = PREVIEW_LIMIT) -> dict:
    char_count = len(content)
    is_large = char_count > preview_limit

    if not is_large:
        return {
            "mode": "完整显示（无需切换）",
            "button_enabled": False,
            "preview_chars": char_count,
            "full_chars": char_count,
        }

    return {
        "mode": "预览模式（可切换）",
        "button_enabled": True,
        "preview_chars": preview_limit,
        "full_chars": char_count,
    }


def generate_export_filename(original_file: str) -> str:
    if original_file:
        return f"{Path(original_file).stem}_中文译文.txt"
    return "译文.txt"


class TestCoreFeatures(unittest.TestCase):
    def test_display_mode_threshold(self) -> None:
        self.assertEqual(get_display_mode(1_000), "完整显示")
        self.assertEqual(get_display_mode(10_000), "完整显示")
        self.assertEqual(get_display_mode(10_001), "预览模式")

    def test_text_reading_uses_preview_for_large_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "large.txt"
            file_path.write_text("a" * 12_345, encoding="utf-8")

            result = read_for_display(file_path)

        self.assertEqual(result["char_count"], 12_345)
        self.assertEqual(result["display_chars"], PREVIEW_LIMIT)
        self.assertEqual(result["mode"], "预览")

    def test_get_character_count_prefers_text_length(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "utf8.txt"
            file_path.write_text("你好\n世界", encoding="utf-8")
            self.assertEqual(get_character_count(file_path), len("你好\n世界"))

    def test_split_text_into_segments_preserves_all_nonempty_paragraphs(self) -> None:
        text = "第一段\n\n第二段\n\n\n第三段"
        segments = split_text_into_segments(text, max_length=8)
        recovered = "\n\n".join(segments)
        self.assertEqual(recovered, "第一段\n\n第二段\n\n第三段")

    def test_split_text_merges_when_within_limit(self) -> None:
        text = "Alpha\n\nBeta\n\nGamma"
        segments = split_text_into_segments(text, max_length=20)
        self.assertEqual(segments, ["Alpha\n\nBeta\n\nGamma"])

    def test_preview_toggle_state(self) -> None:
        small = simulate_preview_toggle("x" * 200)
        large = simulate_preview_toggle("x" * 12_000)

        self.assertFalse(small["button_enabled"])
        self.assertTrue(large["button_enabled"])
        self.assertEqual(large["preview_chars"], PREVIEW_LIMIT)
        self.assertEqual(large["full_chars"], 12_000)

    def test_generate_export_filename(self) -> None:
        self.assertEqual(generate_export_filename("sample_book.txt"), "sample_book_中文译文.txt")
        self.assertEqual(generate_export_filename("document.pdf"), "document_中文译文.txt")
        self.assertEqual(generate_export_filename(""), "译文.txt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
