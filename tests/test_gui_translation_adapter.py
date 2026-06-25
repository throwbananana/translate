import pytest

from controllers.gui_translation_adapter import (
    build_run_config_from_gui_state,
    cancel_guarded_translation_run,
    guarded_gui_update,
    start_guarded_translation_run,
)
from controllers.run_guard import TranslationRunGuard


pytestmark = pytest.mark.unit


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def test_build_run_config_from_gui_state_reads_tk_style_values():
    config = build_run_config_from_gui_state(
        api_type=FakeVar("lm_studio"),
        target_language=FakeVar("中文"),
        style=FakeVar("日式轻小说 (Light Novel)"),
        concurrency=FakeVar("3"),
        segment_size=FakeVar("600"),
        translation_delay=FakeVar("0.5"),
        provider_timeout_seconds=FakeVar("45"),
    )

    assert config.api_type == "lm_studio"
    assert config.target_language == "中文"
    assert config.style == "日式轻小说 (Light Novel)"
    assert config.concurrency == 3
    assert config.segment_size == 600
    assert config.translation_delay == 0.5
    assert config.provider_timeout_seconds == 45.0


def test_start_guarded_translation_run_returns_active_run_and_config():
    guard = TranslationRunGuard()

    run = start_guarded_translation_run(
        guard,
        api_type="openai",
        target_language="English",
        style="直译 (Literal)",
        concurrency=1,
    )

    assert run.run_id
    assert run.config.api_type == "openai"
    assert guard.should_accept_result(run.run_id) is True


def test_guarded_gui_update_skips_stale_or_cancelled_runs():
    guard = TranslationRunGuard()
    first = start_guarded_translation_run(
        guard,
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
    )
    second = start_guarded_translation_run(
        guard,
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
    )
    calls = []

    assert guarded_gui_update(guard, first.run_id, calls.append, "old") is False
    assert guarded_gui_update(guard, second.run_id, calls.append, "new") is True
    assert calls == ["new"]

    cancelled = cancel_guarded_translation_run(guard)

    assert cancelled == second.run_id
    assert guarded_gui_update(guard, second.run_id, calls.append, "late") is False
    assert calls == ["new"]
