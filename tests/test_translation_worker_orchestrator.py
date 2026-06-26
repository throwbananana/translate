import pytest

from controllers.translation_run_config import coerce_translation_run_config
from controllers.translation_worker_orchestrator import (
    TranslationWorkerEvents,
    run_translation_worker,
)


pytestmark = pytest.mark.unit


def _config(concurrency=1, delay=0):
    return coerce_translation_run_config(
        api_type="openai",
        target_language="中文",
        style="直译 (Literal)",
        concurrency=concurrency,
        translation_delay=delay,
    )


def _split(text, max_length):
    assert max_length >= 1
    return text.split("|") if text else []


def test_run_translation_worker_uses_previous_context_in_serial_mode():
    contexts = []

    def translate(index, segment, context):
        contexts.append(context)
        return f"{segment}-译"

    result = run_translation_worker(
        text="a|b|c",
        config=_config(concurrency=1),
        split_text=_split,
        translate_segment=translate,
        snapshot_every=1,
    )

    assert contexts == [None, "a-译", "b-译"]
    assert result.final_text == "a-译\n\nb-译\n\nc-译"
    assert result.completed_count == 3
    assert result.failed_count == 0
    assert result.paused is False


def test_run_translation_worker_does_not_use_context_in_parallel_mode():
    contexts = []

    def translate(index, segment, context):
        contexts.append(context)
        return f"{index}:{segment}"

    result = run_translation_worker(
        text="a|b|c|d",
        config=_config(concurrency=4),
        split_text=_split,
        translate_segment=translate,
    )

    assert all(context is None for context in contexts)
    assert sorted(result.translated_segments) == ["0:a", "1:b", "2:c", "3:d"]


def test_run_translation_worker_resumes_from_existing_translation_slots():
    seen = []

    def translate(index, segment, context):
        seen.append((index, context))
        return f"{segment}-new"

    result = run_translation_worker(
        text="a|b|c",
        config=_config(concurrency=1),
        split_text=_split,
        translate_segment=translate,
        existing_translations=["a-old"],
        resume_from_index=1,
    )

    assert seen == [(1, "a-old"), (2, "b-new")]
    assert result.translated_segments == ["a-old", "b-new", "c-new"]


def test_run_translation_worker_pauses_after_consecutive_failures():
    def translate(index, segment, context):
        raise RuntimeError(f"boom-{index}")

    statuses = []
    result = run_translation_worker(
        text="a|b|c",
        config=_config(concurrency=1),
        split_text=_split,
        translate_segment=translate,
        max_consecutive_failures=2,
        events=TranslationWorkerEvents(on_status=statuses.append),
    )

    assert result.paused is True
    assert result.completed_count == 2
    assert result.translated_segments[0].startswith("[翻译错误: boom-0]")
    assert statuses[-1] == "已暂停，等待API恢复后可继续"


def test_run_translation_worker_stops_when_active_check_turns_false():
    calls = 0

    def is_active():
        nonlocal calls
        calls += 1
        return calls < 4

    def translate(index, segment, context):
        return segment

    result = run_translation_worker(
        text="a|b|c|d",
        config=_config(concurrency=1),
        split_text=_split,
        translate_segment=translate,
        is_active=is_active,
    )

    assert result.stopped is True
    assert result.completed_count < 4


def test_run_translation_worker_emits_progress_and_snapshots():
    progress = []
    snapshots = []

    result = run_translation_worker(
        text="a|b",
        config=_config(concurrency=1),
        split_text=_split,
        translate_segment=lambda index, segment, context: segment.upper(),
        events=TranslationWorkerEvents(
            on_progress=progress.append,
            on_snapshot=snapshots.append,
        ),
        snapshot_every=1,
    )

    assert progress[-1] == 100
    assert snapshots[-1] == result.final_text == "A\n\nB"
