#! python
# -*- coding: utf-8 -*-
"""GUI-facing helpers for translation run orchestration.

This module is the narrow bridge that `book_translator_gui.pyw` can adopt before
its translation workflow is fully moved into a controller.  It keeps Tk reads on
the GUI thread, produces immutable worker config snapshots, and centralizes the
stale-run guard check used before writing worker results back to widgets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .run_guard import TranslationRunGuard
from .translation_run_config import TranslationRunConfig, coerce_translation_run_config


@dataclass(frozen=True)
class GuardedTranslationRun:
    """One GUI-started translation run."""

    run_id: str
    config: TranslationRunConfig


def _read_widget_value(value_or_var: Any, default: Any = None) -> Any:
    """Read a plain value or a Tk-style variable without importing tkinter."""
    if hasattr(value_or_var, "get"):
        try:
            return value_or_var.get()
        except Exception:
            return default
    return default if value_or_var is None else value_or_var


def build_run_config_from_gui_state(
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
) -> TranslationRunConfig:
    """Build a safe immutable run config from GUI/Tk variable values."""
    return coerce_translation_run_config(
        api_type=_read_widget_value(api_type, "gemini"),
        target_language=_read_widget_value(target_language, "中文"),
        style=_read_widget_value(style, ""),
        concurrency=_read_widget_value(concurrency, 1),
        segment_size=_read_widget_value(segment_size, 800),
        use_memory=bool(_read_widget_value(use_memory, True)),
        use_glossary=bool(_read_widget_value(use_glossary, True)),
        translation_delay=_read_widget_value(translation_delay, 0.2),
        provider_timeout_seconds=_read_widget_value(provider_timeout_seconds, 90.0),
    )


def start_guarded_translation_run(
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
) -> GuardedTranslationRun:
    """Start a guarded run and return the run id plus immutable config."""
    run_config = build_run_config_from_gui_state(
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
    run_id = guard.start_run()
    return GuardedTranslationRun(run_id=run_id, config=run_config)


def should_apply_gui_update(guard: TranslationRunGuard, run_id: str | None) -> bool:
    """Return whether a worker result should still be written to the GUI."""
    return guard.should_accept_result(run_id)


def guarded_gui_update(
    guard: TranslationRunGuard,
    run_id: str | None,
    update_callback: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> bool:
    """Run an update callback only when the worker result is still current."""
    if not should_apply_gui_update(guard, run_id):
        return False
    update_callback(*args, **kwargs)
    return True


def cancel_guarded_translation_run(guard: TranslationRunGuard) -> str | None:
    """Cancel the active run and return the cancelled id, if any."""
    return guard.cancel_current()
