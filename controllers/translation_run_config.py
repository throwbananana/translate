#! python
# -*- coding: utf-8 -*-
"""Pure translation-run configuration helpers.

This module is intentionally independent from tkinter.  A GUI caller should
create a :class:`TranslationRunConfig` on the main thread before starting a
background translation worker, then pass this immutable snapshot into the
worker.  That keeps worker code from reading Tk variables directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


DEFAULT_SEGMENT_SIZE = 800
DEFAULT_TRANSLATION_DELAY = 0.2
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 90.0

STYLE_PROMPTS: Mapping[str, str] = {
    "直译 (Literal)": "请进行精准直译，严格保留原文的句子结构和语气，不要过度意译。",
    "通俗小说 (Novel)": "请采用通俗小说的笔法，用词生动、流畅，注重情节的连贯性和人物语气的自然，符合目标语言读者的阅读习惯。",
    "日式轻小说 (Light Novel)": "请采用日式轻小说译法，语气轻快自然，保留角色台词的个性、吐槽感、心理独白和章节节奏；专有名词、人名、称呼、拟声词与口癖应前后一致，避免过度文言化或学术化。",
    "学术专业 (Academic)": "请采用学术风格，用词严谨、专业，句式规范，确保术语准确，适合学术研究或专业人士阅读。",
    "武侠/古风 (Wuxia)": "请采用中国古典武侠或古风小说的笔触，用词典雅、古朴，半文半白，注重意境的渲染。",
    "新闻/媒体 (News)": "请采用新闻报道的风格，客观、简练、信息传达准确，符合新闻媒体的规范。",
}


@dataclass(frozen=True)
class TranslationRunConfig:
    """Immutable configuration snapshot for one translation run."""

    api_type: str
    target_language: str
    style: str
    concurrency: int = 1
    segment_size: int = DEFAULT_SEGMENT_SIZE
    use_memory: bool = True
    use_glossary: bool = True
    translation_delay: float = DEFAULT_TRANSLATION_DELAY
    provider_timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS

    @property
    def use_context(self) -> bool:
        """Only serial translation can safely use previous-segment context."""
        return self.concurrency == 1

    @property
    def style_prompt(self) -> str:
        """Return the prompt fragment for the configured translation style."""
        style_guide = STYLE_PROMPTS.get(self.style, "")
        return f"风格要求：{style_guide}" if style_guide else ""


def coerce_translation_run_config(
    *,
    api_type: str,
    target_language: str,
    style: str,
    concurrency: int | str | float = 1,
    segment_size: int | str | float = DEFAULT_SEGMENT_SIZE,
    use_memory: bool = True,
    use_glossary: bool = True,
    translation_delay: float | str = DEFAULT_TRANSLATION_DELAY,
    provider_timeout_seconds: float | str = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
) -> TranslationRunConfig:
    """Build a safe immutable run config from GUI/user supplied values.

    The function clamps numeric fields so callers do not have to duplicate
    defensive parsing around Tk variables.
    """

    safe_concurrency = max(1, int(float(concurrency or 1)))
    safe_segment_size = max(1, int(float(segment_size or DEFAULT_SEGMENT_SIZE)))
    safe_delay = max(0.0, float(translation_delay or 0.0))
    safe_timeout = max(1.0, float(provider_timeout_seconds or DEFAULT_PROVIDER_TIMEOUT_SECONDS))

    return TranslationRunConfig(
        api_type=str(api_type or "gemini"),
        target_language=str(target_language or "中文"),
        style=str(style or ""),
        concurrency=safe_concurrency,
        segment_size=safe_segment_size,
        use_memory=bool(use_memory),
        use_glossary=bool(use_glossary),
        translation_delay=safe_delay,
        provider_timeout_seconds=safe_timeout,
    )
