import pytest

from controllers.gui_translation_lifecycle import GuiTranslationFinishState
from controllers.gui_translation_session import (
    cancel_gui_translation_session,
    schedule_gui_translation_final_state,
    start_gui_translation_session,
)
from controllers.run_guard import TranslationRunGuard


pytestmark = pytest.mark.unit


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeScheduler:
    def __init__(self):
        self.callbacks = []

    def after(self, delay, callback):
        assert delay == 0
        self.callbacks.append(callback)
        return f"after-{len(self.callbacks)}"


def _finish_state():
    return GuiTranslationFinishState(
        source_segments=["hello"],
        translated_segments=["你好"],
        failed_segments=[],
        translated_text="你好",
        progress=100,
        status_message="翻译完成!",
        stopped=False,
        paused=False,
        should_call_completion_hook=True,
        should_clear_progress_cache=True,
    )


def test_start_gui_translation_session_snapshots_config_and_resume_state():
    guard = TranslationRunGuard()

    session = start_gui_translation_session(
        guard,
        api_type=FakeVar("openai"),
        target_language=FakeVar("中文"),
        style=FakeVar("日式轻小说 (Light Novel)"),
        concurrency=FakeVar("2"),
        current_signature="same",
        cached_signature="same",
        source_segments=["a", "b", "c"],
        translated_segments=["A", "B"],
        failed_segments=[{"index": 1, "source": "b", "last_error": "old"}],
        resume_requested=True,
    )

    assert session.run_id
    assert guard.should_accept_result(session.run_id) is True
    assert session.config.api_type == "openai"
    assert session.config.target_language == "中文"
    assert session.config.style == "日式轻小说 (Light Novel)"
    assert session.config.concurrency == 2
    assert session.start_state.resume_from_index == 2
    assert session.start_state.translated_segments == ["A", "B"]
    assert session.start_state.failed_segments == [
        {"index": 1, "source": "b", "last_error": "old"}
    ]
    assert session.start_state.should_clear_translated_text is False


def test_start_gui_translation_session_resets_when_resume_not_requested():
    guard = TranslationRunGuard()

    session = start_gui_translation_session(
        guard,
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
        current_signature="same",
        cached_signature="same",
        source_segments=["a", "b", "c"],
        translated_segments=["A", "B"],
        resume_requested=False,
    )

    assert session.start_state.resume_available is True
    assert session.start_state.resume_requested is False
    assert session.start_state.resume_from_index == 0
    assert session.start_state.translated_segments == []
    assert session.start_state.should_clear_translated_text is True


def test_cancel_gui_translation_session_cancels_current_run():
    guard = TranslationRunGuard()
    session = start_gui_translation_session(
        guard,
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
    )

    cancelled = cancel_gui_translation_session(guard)

    assert cancelled == session.run_id
    assert guard.should_accept_result(session.run_id) is False
    assert guard.snapshot().is_active is False


def test_schedule_gui_translation_final_state_applies_state_and_finishes_run():
    guard = TranslationRunGuard()
    scheduler = FakeScheduler()
    applied = []
    session = start_gui_translation_session(
        guard,
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
    )
    finish_state = _finish_state()

    token = schedule_gui_translation_final_state(
        guard,
        session,
        scheduler.after,
        applied.append,
        finish_state,
    )

    assert token == "after-1"
    assert guard.should_accept_result(session.run_id) is True
    scheduler.callbacks[0]()

    assert applied == [finish_state]
    assert guard.should_accept_result(session.run_id) is False
    assert guard.snapshot().is_active is False


def test_schedule_gui_translation_final_state_skips_after_cancel():
    guard = TranslationRunGuard()
    scheduler = FakeScheduler()
    applied = []
    session = start_gui_translation_session(
        guard,
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
    )

    schedule_gui_translation_final_state(
        guard,
        session,
        scheduler.after,
        applied.append,
        _finish_state(),
    )
    cancel_gui_translation_session(guard)
    scheduler.callbacks[0]()

    assert applied == []
    assert guard.should_accept_result(session.run_id) is False
    assert guard.snapshot().is_active is False
