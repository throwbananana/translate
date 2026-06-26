#! python
# -*- coding: utf-8 -*-
"""Background translation worker orchestration without tkinter dependencies.

The GUI can call this module from a worker thread by injecting small callbacks
for splitting text, translating one segment, checking cancellation state, and
scheduling UI updates.  Keeping the loop here makes the behavior testable before
`book_translator_gui.pyw` is rewired.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import time

from .translation_run_config import TranslationRunConfig
from .translation_worker_runtime import (
    clamp_start_index,
    ensure_segment_slots,
    previous_segment_context,
    progress_percent,
    should_use_context,
    translated_text_snapshot,
    worker_count_for_run,
)


@dataclass(frozen=True)
class SegmentWorkResult:
    """Result for one translated segment."""

    index: int
    translated_text: str | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.translated_text is not None and not self.error


@dataclass(frozen=True)
class TranslationWorkerResult:
    """Final state returned by a worker loop."""

    source_segments: list[str]
    translated_segments: list[str]
    completed_count: int
    failed_count: int
    stopped: bool = False
    paused: bool = False
    final_text: str = ""


@dataclass
class TranslationWorkerEvents:
    """Optional callbacks emitted by the worker loop.

    UI callers should keep these callbacks tiny and use their own GUI-thread
    scheduler.  Unit tests can pass simple list appenders.
    """

    on_status: Callable[[str], None] | None = None
    on_progress: Callable[[float], None] | None = None
    on_snapshot: Callable[[str], None] | None = None
    on_segment_done: Callable[[SegmentWorkResult], None] | None = None
    on_error: Callable[[Exception], None] | None = None
    emitted_statuses: list[str] = field(default_factory=list)

    def status(self, message: str) -> None:
        self.emitted_statuses.append(message)
        if self.on_status:
            self.on_status(message)

    def progress(self, value: float) -> None:
        if self.on_progress:
            self.on_progress(value)

    def snapshot(self, text: str) -> None:
        if self.on_snapshot:
            self.on_snapshot(text)

    def segment_done(self, result: SegmentWorkResult) -> None:
        if self.on_segment_done:
            self.on_segment_done(result)

    def error(self, exc: Exception) -> None:
        if self.on_error:
            self.on_error(exc)


SplitText = Callable[[str, int], list[str]]
TranslateSegment = Callable[[int, str, str | None], str]
StateCheck = Callable[[], bool]


def _default_true() -> bool:
    return True


def _default_false() -> bool:
    return False


def run_translation_worker(
    *,
    text: str,
    config: TranslationRunConfig,
    split_text: SplitText,
    translate_segment: TranslateSegment,
    existing_translations: Sequence[str] | None = None,
    resume_from_index: int = 0,
    max_consecutive_failures: int = 3,
    is_active: StateCheck = _default_true,
    should_pause: StateCheck = _default_false,
    events: TranslationWorkerEvents | None = None,
    snapshot_every: int = 5,
) -> TranslationWorkerResult:
    """Run the translation worker loop using injected dependencies.

    This mirrors the existing GUI worker behavior while making key decisions from
    an immutable `TranslationRunConfig` instead of reading Tk variables from the
    background thread.
    """

    events = events or TranslationWorkerEvents()
    events.status("正在进行文本分段...")

    source_segments = split_text(text, config.segment_size)
    total_segments = len(source_segments)
    start_index = clamp_start_index(resume_from_index, total_segments)
    translated_segments = list(existing_translations or [])
    ensure_segment_slots(translated_segments, total_segments)

    worker_count = worker_count_for_run(config, total_segments, start_index)
    use_context = should_use_context(config, worker_count)
    completed_count = start_index
    consecutive_failures = 0
    paused = False
    stopped = False

    events.status(f"文本已分为 {total_segments} 段，准备开始翻译...")
    if start_index:
        events.progress(progress_percent(start_index, total_segments))
        events.status(f"继续翻译：从第 {start_index + 1} 段开始...")

    def process_segment(index: int) -> SegmentWorkResult | None:
        if not is_active() or should_pause():
            return None

        segment = source_segments[index]
        context = previous_segment_context(
            translated_segments,
            index,
            use_context=use_context,
        )
        try:
            return SegmentWorkResult(
                index=index,
                translated_text=translate_segment(index, segment, context),
            )
        except Exception as exc:  # pragma: no cover - exercised through public loop
            return SegmentWorkResult(index=index, error=str(exc))

    def apply_result(result: SegmentWorkResult) -> None:
        nonlocal completed_count, consecutive_failures, paused

        if result.success:
            translated_segments[result.index] = result.translated_text or ""
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            translated_segments[result.index] = (
                f"[翻译错误: {result.error}]\n{source_segments[result.index]}"
            )
            if consecutive_failures >= max_consecutive_failures:
                paused = True

        completed_count += 1
        events.segment_done(result)
        events.progress(progress_percent(completed_count, total_segments))
        events.status(f"正在翻译... {completed_count}/{total_segments} 段")

        if snapshot_every > 0 and completed_count % snapshot_every == 0:
            events.snapshot(translated_text_snapshot(translated_segments))

    try:
        if worker_count > 1:
            events.status(f"正在并发翻译 (线程数: {worker_count})...")
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = {
                    executor.submit(process_segment, index): index
                    for index in range(start_index, total_segments)
                }
                for future in as_completed(futures):
                    if not is_active() or should_pause() or paused:
                        executor.shutdown(wait=False, cancel_futures=True)
                        stopped = not is_active()
                        break
                    result = future.result()
                    if result is None:
                        stopped = not is_active()
                        break
                    apply_result(result)
        else:
            for index in range(start_index, total_segments):
                if not is_active() or should_pause() or paused:
                    stopped = not is_active()
                    break
                result = process_segment(index)
                if result is None:
                    stopped = not is_active()
                    break
                apply_result(result)
                if config.translation_delay:
                    time.sleep(config.translation_delay)
    except Exception as exc:
        events.error(exc)
        raise

    final_text = translated_text_snapshot(translated_segments)
    events.snapshot(final_text)

    failed_count = sum(
        1
        for segment in translated_segments
        if segment.startswith("[翻译错误") or segment.startswith("[未翻译")
    )

    if paused:
        events.status("已暂停，等待API恢复后可继续")
    elif stopped:
        events.status("翻译已停止")
    else:
        events.status(f"翻译完成，有 {failed_count} 段可能需要检查" if failed_count else "翻译完成!")

    return TranslationWorkerResult(
        source_segments=source_segments,
        translated_segments=translated_segments,
        completed_count=completed_count,
        failed_count=failed_count,
        stopped=stopped,
        paused=paused,
        final_text=final_text,
    )
