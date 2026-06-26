#! python
# -*- coding: utf-8 -*-
"""High-level GUI translation session helpers.

This module is the last controller-side bridge before editing
`book_translator_gui.pyw`.  It combines guarded run creation, immutable config
snapshots and legacy resume/reset planning into one object that the GUI can store
on `self.current_guarded_run` or an equivalent field.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .gui_translation_adapter import (
    GuardedTranslationRun,
    cancel_guarded_translation_run,
    schedule_guarded_final_gui_update,
    start_guarded_translation_run,
)
from .gui_translation_lifecycle import GuiTranslationFinishState, GuiTranslationStartState, plan_gui_translation_start
from .run_guard import TranslationRunGuard

Scheduler = Callable[..., Any]
FinalStateCallback = Callable[[GuiTranslationFinishState], Any]


@dataclass(frozen=True)
class GuiTranslationSession:
    """A GUI-started translation session with immutable worker config."""

    guarded_run: GuardedTranslationRun
    start_state: GuiTranslationStartState

    @property
    def run_id(self) -> str:
        return self.guarded_run.run_id

    @property
    def config(self):
        return self.guarded_run.config


def start_gui_translation_session(
    guard: TranslationRunGuard,
    *,
    api_type: Any,
    target_language: Any,
    style: Any,
    concurrency: Any = 1,
    segment_size: Any = 800,
    use_memory: Any = True,
    use_glossary: Any = True,
    translation_delay: Any = 0.2,
    provider_timeout_seconds: Any = 90.0,
    current_signature: str | None = None,
    cached_signature: str | None = None,
    source_segments: Sequence[str] | None = None,
    translated_segments: Sequence[str] | None = None,
    failed_segments: Sequence[Mapping[str, Any]] | None = None,
    resume_requested: bool = False,
) -> GuiTranslationSession:
    """Start a guarded GUI translation session.

    All Tk-style values should be passed in from the GUI thread.  The returned
    session contains an immutable config snapshot plus a pure start-state plan,
    allowing the worker thread to avoid reading tkinter variables.
    """

    guarded_run = start_guarded_translation_run(
        guard,
        api_type=api_type,
        target_language=target_language,
        style=style,
        concurrency=concurrency,
        segment_size=segment_size,
        use_memory=use_memory,
        use_glossary=use_glossary,
        translation_delay=translation_delay,
        provider_timeout_seconds=provider_timeout_seconds,
    )
    start_state = plan_gui_translation_start(
        current_signature=current_signature,
        cached_signature=cached_signature,
        source_segments=source_segments,
        translated_segments=translated_segments,
        failed_segments=failed_segments,
        resume_requested=resume_requested,
    )
    return GuiTranslationSession(guarded_run=guarded_run, start_state=start_state)


def cancel_gui_translation_session(guard: TranslationRunGuard) -> str | None:
    """Cancel the currently active GUI translation session, if any."""
    return cancel_guarded_translation_run(guard)


def schedule_gui_translation_final_state(
    guard: TranslationRunGuard,
    session: GuiTranslationSession,
    scheduler: Scheduler,
    apply_final_state: FinalStateCallback,
    finish_state: GuiTranslationFinishState,
) -> Any:
    """Schedule final GUI state application and finish the session if accepted."""
    return schedule_guarded_final_gui_update(
        guard,
        session.run_id,
        scheduler,
        apply_final_state,
        finish_state,
    )
