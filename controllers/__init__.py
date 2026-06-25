"""Controller-layer helpers for workflow orchestration.

The GUI should remain responsible for widget composition and event routing, while
controllers hold pure state/configuration helpers that can be tested without
creating Tk windows.
"""

from .gui_translation_adapter import (
    GuardedTranslationRun,
    build_run_config_from_gui_state,
    cancel_guarded_translation_run,
    guarded_gui_update,
    should_apply_gui_update,
    start_guarded_translation_run,
)
from .run_guard import TranslationRunGuard
from .translation_run_config import TranslationRunConfig, coerce_translation_run_config

__all__ = [
    "TranslationRunConfig",
    "TranslationRunGuard",
    "GuardedTranslationRun",
    "coerce_translation_run_config",
    "build_run_config_from_gui_state",
    "start_guarded_translation_run",
    "should_apply_gui_update",
    "guarded_gui_update",
    "cancel_guarded_translation_run",
]
