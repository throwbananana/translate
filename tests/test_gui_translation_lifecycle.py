import pytest

from controllers.gui_translation_lifecycle import (
    finalize_gui_translation_result,
    plan_gui_translation_start,
)
from controllers.translation_worker_orchestrator import TranslationWorkerResult


pytestmark = pytest.mark.unit


def test_plan_gui_translation_start_resumes_aligned_segments_when_requested():
    state = plan_gui_translation_start(
        current_signature="same",
        cached_signature="same",
        source_segments=["a", "b", "c"],
        translated_segments=["A", "B"],
        failed_segments=[{"index": 1, "source": "b", "last_error": "old"}],
        resume_requested=True,
    )

    assert state.resume_available is True
    assert state.resume_requested is True
    assert state.resume_from_index == 2
    assert state.source_segments == ["a", "b", "c"]
    assert state.translated_segments == ["A", "B"]
    assert state.failed_segments == [{"index": 1, "source": "b", "last_error": "old"}]
    assert state.should_clear_translated_text is False
    assert state.initial_progress == pytest.approx(66.6666666667)


def test_plan_gui_translation_start_resets_when_resume_declined():
    state = plan_gui_translation_start(
        current_signature="same",
        cached_signature="same",
        source_segments=["a", "b", "c"],
        translated_segments=["A", "B"],
        resume_requested=False,
    )

    assert state.resume_available is True
    assert state.resume_requested is False
    assert state.resume_from_index == 0
    assert state.source_segments == []
    assert state.translated_segments == []
    assert state.failed_segments == []
    assert state.should_clear_translated_text is True
    assert state.initial_progress == 0


def test_plan_gui_translation_start_resets_when_signatures_do_not_match():
    state = plan_gui_translation_start(
        current_signature="new",
        cached_signature="old",
        source_segments=["a", "b", "c"],
        translated_segments=["A", "B"],
        resume_requested=True,
    )

    assert state.resume_available is False
    assert state.resume_requested is False
    assert state.resume_from_index == 0
    assert state.should_clear_translated_text is True


def test_finalize_gui_translation_result_marks_success_ready_for_completion_and_cache_clear():
    result = TranslationWorkerResult(
        source_segments=["hello world source", "another world source"],
        translated_segments=["你好，世界。", "另一个世界。"],
        completed_count=2,
        failed_count=0,
        final_text="你好，世界。\n\n另一个世界。",
    )

    state = finalize_gui_translation_result(result, target_language="中文")

    assert state.translated_text == "你好，世界。\n\n另一个世界。"
    assert state.failed_segments == []
    assert state.progress == 100
    assert state.status_message == "翻译完成!"
    assert state.should_call_completion_hook is True
    assert state.should_clear_progress_cache is True


def test_finalize_gui_translation_result_builds_failed_segments_for_incomplete_items():
    result = TranslationWorkerResult(
        source_segments=["This is a long enough source sentence for checking.", "world source"],
        translated_segments=["[翻译错误: timeout]", "世界译文。"],
        completed_count=2,
        failed_count=1,
        final_text="[翻译错误: timeout]\n\n世界译文。",
    )

    state = finalize_gui_translation_result(result, target_language="中文")

    assert state.failed_segments == [
        {
            "index": 0,
            "source": "This is a long enough source sentence for checking.",
            "last_error": "[翻译错误: timeout]",
        }
    ]
    assert state.status_message == "翻译完成，有 1 段可能需要检查"
    assert state.should_call_completion_hook is True
    assert state.should_clear_progress_cache is False


def test_finalize_gui_translation_result_keeps_stopped_run_from_completion_hook():
    result = TranslationWorkerResult(
        source_segments=["a", "b", "c", "d"],
        translated_segments=["A", "", "", ""],
        completed_count=1,
        failed_count=0,
        stopped=True,
        final_text="A",
    )

    state = finalize_gui_translation_result(result, target_language="英文")

    assert state.stopped is True
    assert state.paused is False
    assert state.progress == 25
    assert state.status_message == "翻译已停止"
    assert state.should_call_completion_hook is False
    assert state.should_clear_progress_cache is False


def test_finalize_gui_translation_result_keeps_paused_run_from_completion_hook():
    result = TranslationWorkerResult(
        source_segments=["a", "b"],
        translated_segments=["[翻译错误: timeout]", ""],
        completed_count=1,
        failed_count=1,
        paused=True,
        final_text="[翻译错误: timeout]",
    )

    state = finalize_gui_translation_result(result, target_language="中文")

    assert state.stopped is False
    assert state.paused is True
    assert state.progress == 50
    assert state.status_message == "已暂停，等待API恢复后可继续"
    assert state.should_call_completion_hook is False
    assert state.should_clear_progress_cache is False
