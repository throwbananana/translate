import pytest

from controllers.translation_run_config import coerce_translation_run_config
from controllers.translation_worker_runtime import (
    clamp_start_index,
    ensure_segment_slots,
    previous_segment_context,
    progress_percent,
    should_use_context,
    translated_text_snapshot,
    worker_count_for_run,
)


pytestmark = pytest.mark.unit


def _config(concurrency=1):
    return coerce_translation_run_config(
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
        concurrency=concurrency,
    )


def test_clamp_start_index_keeps_resume_index_in_range():
    assert clamp_start_index(None, 5) == 0
    assert clamp_start_index(-3, 5) == 0
    assert clamp_start_index(2, 5) == 2
    assert clamp_start_index(99, 5) == 5


def test_worker_count_for_run_uses_config_snapshot_not_tk_state():
    config = _config(concurrency=8)

    assert worker_count_for_run(config, total_segments=10, start_index=0) == 8
    assert worker_count_for_run(config, total_segments=10, start_index=7) == 3
    assert worker_count_for_run(config, total_segments=0, start_index=0) == 1


def test_should_use_context_only_for_single_worker_runs():
    assert should_use_context(_config(concurrency=1), worker_count=1) is True
    assert should_use_context(_config(concurrency=3), worker_count=3) is False


def test_previous_segment_context_skips_missing_empty_or_error_segments():
    translated = ["第一段译文", "", "[翻译错误: timeout]"]

    assert previous_segment_context(translated, 1, use_context=True) == "第一段译文"
    assert previous_segment_context(translated, 2, use_context=True) is None
    assert previous_segment_context(translated, 3, use_context=True) is None
    assert previous_segment_context(translated, 1, use_context=False) is None
    assert previous_segment_context(translated, 9, use_context=True) is None


def test_ensure_segment_slots_extends_without_dropping_existing_translations():
    translated = ["a"]

    result = ensure_segment_slots(translated, 3)

    assert result is translated
    assert translated == ["a", "", ""]


def test_progress_percent_is_defensive():
    assert progress_percent(0, 0) == 0
    assert progress_percent(2, 4) == 50
    assert progress_percent(99, 4) == 100


def test_translated_text_snapshot_skips_empty_slots():
    translated = ["第一段", "", "第三段"]

    assert translated_text_snapshot(translated) == "第一段\n\n第三段"
    assert translated_text_snapshot(translated, end_index=2) == "第一段"
