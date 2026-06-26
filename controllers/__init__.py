"""Controller-layer helpers for workflow orchestration.

The GUI should remain responsible for widget composition and event routing, while
controllers hold pure state/configuration helpers that can be tested without
creating Tk windows.
"""

from .batch_controller import BatchController, BatchQueueSnapshot, should_load_batch_file_silently
from .gui_translation_adapter import (
    GuardedTranslationRun,
    build_run_config_from_gui_state,
    cancel_guarded_translation_run,
    guarded_gui_update,
    should_apply_gui_update,
    start_guarded_translation_run,
)
from .gui_translation_lifecycle import (
    GuiTranslationFinishState,
    GuiTranslationStartState,
    finalize_gui_translation_result,
    plan_gui_translation_start,
)
from .gui_translation_workflow import (
    GuiTranslationWorkerCallbacks,
    build_guarded_translation_events,
    run_guarded_gui_translation_worker,
)
from .run_guard import TranslationRunGuard
from .translation_run_config import TranslationRunConfig, coerce_translation_run_config
from .translation_worker_orchestrator import (
    SegmentWorkResult,
    TranslationWorkerEvents,
    TranslationWorkerResult,
    run_translation_worker,
)
from .translation_worker_runtime import (
    clamp_start_index,
    ensure_segment_slots,
    previous_segment_context,
    progress_percent,
    should_use_context,
    translated_text_snapshot,
    worker_count_for_run,
)

__all__ = [
    "TranslationRunConfig",
    "TranslationRunGuard",
    "GuardedTranslationRun",
    "BatchController",
    "BatchQueueSnapshot",
    "SegmentWorkResult",
    "TranslationWorkerEvents",
    "TranslationWorkerResult",
    "GuiTranslationWorkerCallbacks",
    "GuiTranslationStartState",
    "GuiTranslationFinishState",
    "run_translation_worker",
    "build_guarded_translation_events",
    "run_guarded_gui_translation_worker",
    "coerce_translation_run_config",
    "build_run_config_from_gui_state",
    "start_guarded_translation_run",
    "should_apply_gui_update",
    "guarded_gui_update",
    "cancel_guarded_translation_run",
    "plan_gui_translation_start",
    "finalize_gui_translation_result",
    "should_load_batch_file_silently",
    "clamp_start_index",
    "worker_count_for_run",
    "should_use_context",
    "previous_segment_context",
    "ensure_segment_slots",
    "progress_percent",
    "translated_text_snapshot",
]
