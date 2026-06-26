#! python
# -*- coding: utf-8 -*-
"""Pure helpers for background translation worker loops.

These functions are intentionally free of tkinter and network calls.  They let
`book_translator_gui.pyw` move worker-loop decisions away from direct widget/Tk
variable reads before the full translation workflow is extracted into a larger
controller.
"""

from __future__ import annotations

from collections.abc import Sequence

from .translation_run_config import TranslationRunConfig


def clamp_start_index(start_index: int | None, total_segments: int) -> int:
    """Clamp a resume index into the valid segment range."""
    total = max(0, int(total_segments or 0))
    try:
        start = int(start_index or 0)
    except (TypeError, ValueError):
        start = 0
    return max(0, min(start, total))


def worker_count_for_run(config: TranslationRunConfig, total_segments: int, start_index: int = 0) -> int:
    """Return the safe worker count for a run snapshot.

    The GUI previously read `self.concurrency_var` inside the background thread.
    This helper consumes the immutable run config instead, so the future GUI
    worker can avoid Tk reads after the thread starts.
    """
    start = clamp_start_index(start_index, total_segments)
    remaining_segments = max(int(total_segments or 0) - start, 0)
    return max(1, min(config.concurrency, remaining_segments or 1))


def should_use_context(config: TranslationRunConfig, worker_count: int) -> bool:
    """Return whether previous-segment context should be used."""
    return config.use_context and worker_count == 1


def previous_segment_context(
    translated_segments: Sequence[str],
    index: int,
    *,
    use_context: bool,
) -> str | None:
    """Return previous translated segment text when it is safe as context."""
    if not use_context or index <= 0:
        return None
    if index - 1 >= len(translated_segments):
        return None

    previous = translated_segments[index - 1]
    if not previous or previous.startswith("["):
        return None
    return previous


def ensure_segment_slots(translated_segments: list[str], total_segments: int) -> list[str]:
    """Extend translated segment storage so direct index assignment is safe."""
    missing = max(0, int(total_segments or 0) - len(translated_segments))
    if missing:
        translated_segments.extend([""] * missing)
    return translated_segments


def progress_percent(completed_count: int, total_segments: int) -> float:
    """Compute progress percentage defensively."""
    total = max(1, int(total_segments or 0))
    completed = max(0, min(int(completed_count or 0), total))
    return (completed / total) * 100


def translated_text_snapshot(translated_segments: Sequence[str], end_index: int | None = None) -> str:
    """Join translated segments for UI/cache snapshots, skipping empty slots."""
    if end_index is None:
        segments = translated_segments
    else:
        segments = translated_segments[: max(0, int(end_index))]
    return "\n\n".join(segment for segment in segments if segment)
