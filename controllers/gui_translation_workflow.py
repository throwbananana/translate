#! python
# -*- coding: utf-8 -*-
"""GUI-facing adapter for the translation worker orchestrator.

This module is the final thin layer before wiring `book_translator_gui.pyw` to the
controller worker loop.  It composes four pieces that were previously separate:

- immutable `TranslationRunConfig` snapshots;
- `TranslationRunGuard` stale-run checks;
- `run_translation_worker(...)` orchestration and Tk-style scheduled UI events;
- lifecycle finalization that converts pure worker results back into GUI state.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .gui_translation_adapter import schedule_guarded_gui_update, should_apply_gui_update
from .gui_translation_lifecycle import GuiTranslationFinishState, finalize_gui_translation_result
from .run_guard import TranslationRunGuard
from .translation_run_config import TranslationRunConfig
from .translation_worker_orchestrator import (
    SegmentWorkResult,
    TranslationWorkerEvents,
    TranslationWorkerResult,
    run_translation_worker,
)

Scheduler = Callable[..., Any]
SplitText = Callable[[str, int], list[str]]
TranslateSegment = Callable[[int, str, str | None], str]
StateCheck = Callable[[], bool]
StatusCallback = Callable[[str], Any]
ProgressCallback = Callable[[float], Any]
SnapshotCallback = Callable[[str], Any]
SegmentDoneCallback = Callable[[SegmentWorkResult], Any]
ErrorCallback = Callable[[Exception], Any]


@dataclass(frozen=True)
class GuiTranslationWorkerCallbacks:
    """Callbacks supplied by `BookTranslatorGUI` when running a worker.

    The first group is used inside the worker thread.  UI callbacks are scheduled
    through the provided scheduler and guarded before execution.
    """

    split_text: SplitText
    translate_segment: TranslateSegment
    is_active: StateCheck
    should_pause: StateCheck
    set_status: StatusCallback
    set_progress: ProgressCallback
    update_snapshot: SnapshotCallback
    on_segment_done: SegmentDoneCallback | None = None
    on_error: ErrorCallback | None = None


def _guarded_active_check(
    guard: TranslationRunGuard,
    run_id: str | None,
    is_active: StateCheck,
) -> bool:
    """Return whether the current worker run should continue."""
    return is_active() and should_apply_gui_update(guard, run_id)


def build_guarded_translation_events(
    *,
    guard: TranslationRunGuard,
    run_id: str | None,
    scheduler: Scheduler,
    callbacks: GuiTranslationWorkerCallbacks,
) -> TranslationWorkerEvents:
    """Build worker events that schedule guarded GUI updates.

    `root.after(...)` callbacks can execute after a run has been stopped or a new
    run has started, so every scheduled event is checked again at execution time.
    """

    def schedule(callback: Callable[..., Any], *args: Any) -> Any:
        return schedule_guarded_gui_update(guard, run_id, scheduler, callback, *args)

    return TranslationWorkerEvents(
        on_status=lambda message: schedule(callbacks.set_status, message),
        on_progress=lambda value: schedule(callbacks.set_progress, value),
        on_snapshot=lambda text: schedule(callbacks.update_snapshot, text),
        on_segment_done=(
            None
            if callbacks.on_segment_done is None
            else lambda result: schedule(callbacks.on_segment_done, result)
        ),
        on_error=(
            None
            if callbacks.on_error is None
            else lambda exc: schedule(callbacks.on_error, exc)
        ),
    )


def run_guarded_gui_translation_worker(
    *,
    guard: TranslationRunGuard,
    run_id: str | None,
    scheduler: Scheduler,
    text: str,
    config: TranslationRunConfig,
    callbacks: GuiTranslationWorkerCallbacks,
    existing_translations: list[str] | None = None,
    resume_from_index: int = 0,
    max_consecutive_failures: int = 3,
    snapshot_every: int = 5,
) -> TranslationWorkerResult:
    """Run the translation worker with guarded GUI event scheduling."""

    events = build_guarded_translation_events(
        guard=guard,
        run_id=run_id,
        scheduler=scheduler,
        callbacks=callbacks,
    )

    return run_translation_worker(
        text=text,
        config=config,
        split_text=callbacks.split_text,
        translate_segment=callbacks.translate_segment,
        existing_translations=existing_translations,
        resume_from_index=resume_from_index,
        max_consecutive_failures=max_consecutive_failures,
        is_active=lambda: _guarded_active_check(guard, run_id, callbacks.is_active),
        should_pause=callbacks.should_pause,
        events=events,
        snapshot_every=snapshot_every,
    )


def run_guarded_gui_translation_lifecycle(
    *,
    guard: TranslationRunGuard,
    run_id: str | None,
    scheduler: Scheduler,
    text: str,
    config: TranslationRunConfig,
    callbacks: GuiTranslationWorkerCallbacks,
    existing_translations: list[str] | None = None,
    resume_from_index: int = 0,
    max_consecutive_failures: int = 3,
    snapshot_every: int = 5,
    target_language: str | None = None,
) -> GuiTranslationFinishState:
    """Run a guarded worker and return finalized GUI state.

    `book_translator_gui.pyw` can use this as its shortest migration path: the
    background thread calls this helper, then schedules one guarded callback that
    applies the returned `GuiTranslationFinishState` to widgets/state fields.
    """

    worker_result = run_guarded_gui_translation_worker(
        guard=guard,
        run_id=run_id,
        scheduler=scheduler,
        text=text,
        config=config,
        callbacks=callbacks,
        existing_translations=existing_translations,
        resume_from_index=resume_from_index,
        max_consecutive_failures=max_consecutive_failures,
        snapshot_every=snapshot_every,
    )
    return finalize_gui_translation_result(
        worker_result,
        target_language=target_language or config.target_language,
    )
