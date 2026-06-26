#! python
# -*- coding: utf-8 -*-
"""Pure GUI translation lifecycle helpers.

These helpers isolate the state decisions that `book_translator_gui.pyw` currently
performs inline before and after a background translation worker run.  Keeping the
logic here makes the upcoming guarded workflow wiring smaller and testable:

- decide whether a GUI run should resume existing segment state or start fresh;
- translate a worker result into legacy GUI state fields;
- derive failed-segment records without touching tkinter widgets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .translation_worker_orchestrator import TranslationWorkerResult
from .translation_worker_runtime import progress_percent, translated_text_snapshot
from translation_review import build_failed_segments


FailedSegment = dict[str, Any]


@dataclass(frozen=True)
class GuiTranslationStartState:
    """State that the GUI should apply before starting a worker thread."""

    resume_from_index: int
    source_segments: list[str]
    translated_segments: list[str]
    failed_segments: list[FailedSegment]
    should_clear_translated_text: bool
    initial_progress: float
    resume_available: bool
    resume_requested: bool


@dataclass(frozen=True)
class GuiTranslationFinishState:
    """State that the GUI should apply after a worker thread returns."""

    source_segments: list[str]
    translated_segments: list[str]
    failed_segments: list[FailedSegment]
    translated_text: str
    progress: float
    status_message: str
    stopped: bool
    paused: bool
    should_call_completion_hook: bool
    should_clear_progress_cache: bool


def _copy_failed_segments(items: Sequence[Mapping[str, Any]] | None) -> list[FailedSegment]:
    return [dict(item) for item in (items or [])]


def plan_gui_translation_start(
    *,
    current_signature: str | None,
    cached_signature: str | None,
    source_segments: Sequence[str] | None,
    translated_segments: Sequence[str] | None,
    failed_segments: Sequence[Mapping[str, Any]] | None = None,
    resume_requested: bool = False,
) -> GuiTranslationStartState:
    """Return the segment state to apply before launching a GUI run.

    This mirrors the current `BookTranslatorGUI.start_translation()` branching but
    keeps the decision independent from message boxes or widgets.  The GUI can ask
    the user whether to resume, then pass that boolean here.
    """

    previous_sources = list(source_segments or [])
    previous_translations = list(translated_segments or [])
    resume_available = (
        cached_signature == current_signature
        and bool(previous_sources)
        and 0 < len(previous_translations) < len(previous_sources)
    )

    if resume_available and resume_requested:
        resume_from_index = len(previous_translations)
        aligned_translations = previous_translations[:resume_from_index]
        return GuiTranslationStartState(
            resume_from_index=resume_from_index,
            source_segments=previous_sources,
            translated_segments=aligned_translations,
            failed_segments=_copy_failed_segments(failed_segments),
            should_clear_translated_text=False,
            initial_progress=progress_percent(resume_from_index, len(previous_sources)),
            resume_available=True,
            resume_requested=True,
        )

    return GuiTranslationStartState(
        resume_from_index=0,
        source_segments=[],
        translated_segments=[],
        failed_segments=[],
        should_clear_translated_text=True,
        initial_progress=0.0,
        resume_available=resume_available,
        resume_requested=False,
    )


def finalize_gui_translation_result(
    result: TranslationWorkerResult,
    *,
    target_language: str = "中文",
) -> GuiTranslationFinishState:
    """Convert a worker result into legacy GUI state fields.

    The worker loop only returns pure state.  This helper derives the text snapshot,
    failed-segment list, completion status and cache-clearing decision so the GUI
    wiring can stay thin and guarded.
    """

    source_segments = list(result.source_segments)
    translated_segments = list(result.translated_segments)
    translated_text = result.final_text or translated_text_snapshot(translated_segments)
    failed_segments = build_failed_segments(
        source_segments,
        translated_segments,
        target_language,
    )
    failed_count = len(failed_segments)

    if result.paused:
        status_message = "已暂停，等待API恢复后可继续"
    elif result.stopped:
        status_message = "翻译已停止"
    elif failed_count:
        status_message = f"翻译完成，有 {failed_count} 段可能需要检查"
    else:
        status_message = "翻译完成!"

    total_segments = len(source_segments)
    progress = 100.0 if not result.stopped and not result.paused else progress_percent(
        result.completed_count,
        total_segments,
    )

    should_call_completion_hook = not result.stopped and not result.paused
    should_clear_progress_cache = should_call_completion_hook and failed_count == 0

    return GuiTranslationFinishState(
        source_segments=source_segments,
        translated_segments=translated_segments,
        failed_segments=failed_segments,
        translated_text=translated_text,
        progress=progress,
        status_message=status_message,
        stopped=result.stopped,
        paused=result.paused,
        should_call_completion_hook=should_call_completion_hook,
        should_clear_progress_cache=should_clear_progress_cache,
    )
