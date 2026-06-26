import pytest

from controllers.gui_translation_workflow import (
    GuiTranslationWorkerCallbacks,
    run_guarded_gui_translation_worker,
)
from controllers.run_guard import TranslationRunGuard
from controllers.translation_run_config import coerce_translation_run_config


pytestmark = pytest.mark.unit


class FakeScheduler:
    def __init__(self):
        self.callbacks = []

    def after(self, delay, callback):
        assert delay == 0
        self.callbacks.append(callback)
        return len(self.callbacks)

    def drain(self):
        callbacks = list(self.callbacks)
        self.callbacks.clear()
        for callback in callbacks:
            callback()


def _config(concurrency=1):
    return coerce_translation_run_config(
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
        concurrency=concurrency,
    )


def _callbacks(statuses, progress, snapshots):
    return GuiTranslationWorkerCallbacks(
        split_text=lambda text, max_length: text.split("|"),
        translate_segment=lambda index, segment, context: segment.upper(),
        is_active=lambda: True,
        should_pause=lambda: False,
        set_status=statuses.append,
        set_progress=progress.append,
        update_snapshot=snapshots.append,
    )


def test_guarded_gui_translation_worker_schedules_ui_updates_for_current_run():
    guard = TranslationRunGuard()
    run_id = guard.start_run()
    scheduler = FakeScheduler()
    statuses = []
    progress = []
    snapshots = []

    result = run_guarded_gui_translation_worker(
        guard=guard,
        run_id=run_id,
        scheduler=scheduler.after,
        text="a|b",
        config=_config(),
        callbacks=_callbacks(statuses, progress, snapshots),
        snapshot_every=1,
    )
    scheduler.drain()

    assert result.final_text == "A\n\nB"
    assert statuses[-1] == "翻译完成!"
    assert progress[-1] == 100
    assert snapshots[-1] == "A\n\nB"


def test_guarded_gui_translation_worker_skips_queued_ui_updates_after_cancel():
    guard = TranslationRunGuard()
    run_id = guard.start_run()
    scheduler = FakeScheduler()
    statuses = []
    progress = []
    snapshots = []

    run_guarded_gui_translation_worker(
        guard=guard,
        run_id=run_id,
        scheduler=scheduler.after,
        text="a|b",
        config=_config(),
        callbacks=_callbacks(statuses, progress, snapshots),
        snapshot_every=1,
    )
    guard.cancel_run(run_id)
    scheduler.drain()

    assert statuses == []
    assert progress == []
    assert snapshots == []


def test_guarded_gui_translation_worker_stops_when_run_is_stale():
    guard = TranslationRunGuard()
    stale_run_id = guard.start_run()
    guard.start_run()  # supersede the stale run before work begins
    scheduler = FakeScheduler()
    statuses = []
    progress = []
    snapshots = []

    result = run_guarded_gui_translation_worker(
        guard=guard,
        run_id=stale_run_id,
        scheduler=scheduler.after,
        text="a|b|c",
        config=_config(),
        callbacks=_callbacks(statuses, progress, snapshots),
    )
    scheduler.drain()

    assert result.stopped is True
    assert result.completed_count == 0
    assert statuses == []
    assert progress == []
    assert snapshots == []
