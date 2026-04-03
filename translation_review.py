#! python
# -*- coding: utf-8 -*-
"""
失败段落复核与修正逻辑。
"""

import re
from typing import Callable, Dict, List, Tuple


def _contains_any(text: str, keywords: List[str]) -> bool:
    normalized = (text or "").lower()
    return any(keyword in normalized for keyword in keywords)


def is_translation_incomplete(translated: str, source: str, target_language: str = "中文") -> bool:
    """检测译文是否为空、异常、语言方向错误或明显不完整。"""
    target = (target_language or "").lower()
    target_is_chinese = _contains_any(target, ["中文", "汉语", "chinese", "zh"])
    target_is_english = _contains_any(target, ["英文", "英语", "english", "en"])

    if not translated or not translated.strip():
        return True

    normalized = translated.strip()
    if normalized.startswith("[翻译错误") or normalized.startswith("[未翻译") or normalized.startswith("[待手动翻译"):
        return True

    if len(normalized) < 5:
        return True
    if normalized == (source or "").strip():
        return True

    min_length_ratio = 0.2 if target_is_chinese else 0.15
    if len(source or "") > 50 and len(normalized) < len(source) * min_length_ratio:
        return True

    def count_chars(text: str, pattern: str) -> int:
        return len(re.findall(pattern, text))

    chinese_chars = count_chars(normalized, r"[\u4e00-\u9fff]")
    latin_chars = count_chars(normalized, r"[A-Za-z]")
    japanese_chars = count_chars(normalized, r"[\u3040-\u30ff\u31f0-\u31ff]")
    total_chars = len(re.findall(r"\S", normalized)) or 1

    chinese_ratio = chinese_chars / total_chars
    latin_ratio = latin_chars / total_chars
    japanese_ratio = japanese_chars / total_chars

    source_has_latin = bool(re.search(r"[A-Za-z]", source or ""))
    source_has_japanese = bool(re.search(r"[\u3040-\u30ff\u31f0-\u31ff]", source or ""))

    if target_is_chinese:
        if source_has_latin and chinese_ratio < 0.2:
            return True
        if source_has_japanese and chinese_ratio < 0.2:
            return True
        if chinese_ratio < 0.15 and (latin_ratio > 0.35 or japanese_ratio > 0.2):
            return True
        if latin_ratio > 0.6 or japanese_ratio > 0.3:
            return True
    elif target_is_english:
        if chinese_ratio > 0.3 and chinese_ratio > latin_ratio:
            return True
        if latin_ratio < 0.15 and len(source or "") > 50:
            return True
    else:
        if chinese_ratio > 0.6 and target_language:
            return True

    return False


def build_failed_segments(
    source_segments: List[str],
    translated_segments: List[str],
    target_language: str = "中文",
) -> List[Dict[str, str]]:
    """根据当前分段构建失败段落列表。"""
    failed = []

    for idx, (source, translated) in enumerate(zip(source_segments, translated_segments)):
        if not is_translation_incomplete(translated, source, target_language):
            continue

        failed.append({
            "index": idx,
            "source": source,
            "last_error": translated,
        })

    return failed


def verify_and_retry_segments(
    source_segments: List[str],
    translated_segments: List[str],
    retry_callback: Callable[[str, int], str],
    target_language: str = "中文",
) -> Tuple[List[str], List[Dict[str, str]]]:
    """检查不完整译文，并尝试自动重试一次。"""
    updated_segments = list(translated_segments)
    failed = []

    for idx, source in enumerate(source_segments):
        translated = updated_segments[idx] if idx < len(updated_segments) else ""
        if not is_translation_incomplete(translated, source, target_language):
            continue

        try:
            retry_text = retry_callback(source, idx)
        except Exception as exc:
            retry_text = f"[翻译错误: {exc}]"

        if is_translation_incomplete(retry_text, source, target_language):
            updated_segments[idx] = f"[待手动翻译 - 段 {idx + 1}]"
            failed.append({
                "index": idx,
                "source": source,
                "last_error": translated,
            })
        else:
            updated_segments[idx] = retry_text

    return updated_segments, failed


def apply_manual_translation(
    translated_segments: List[str],
    failed_segments: List[Dict[str, str]],
    selected_failed_index: int,
    manual_text: str,
) -> Tuple[List[str], List[Dict[str, str]], Dict[str, str]]:
    """应用人工修正并移除对应失败项。"""
    if selected_failed_index < 0 or selected_failed_index >= len(failed_segments):
        raise IndexError("失败段落索引无效")

    normalized_manual = (manual_text or "").strip()
    if not normalized_manual:
        raise ValueError("手动翻译内容不能为空")

    info = failed_segments[selected_failed_index]
    updated_translated_segments = list(translated_segments)
    updated_failed_segments = list(failed_segments)

    updated_translated_segments[info["index"]] = normalized_manual
    updated_failed_segments.pop(selected_failed_index)

    return updated_translated_segments, updated_failed_segments, info
