from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class BatchTranslationResult:
    translated_segments: List[str]
    completed_count: int
    consecutive_failures: int
    paused_due_to_failures: bool
    resume_from_index: int


class BatchTranslationExecutor:
    """将分段翻译循环从 GUI 中抽离，便于复用和测试。"""

    def __init__(
        self,
        source_segments: List[str],
        translated_segments: Optional[List[str]] = None,
        start_index: int = 0,
        max_workers: int = 1,
        max_consecutive_failures: int = 3,
        delay_seconds: float = 0.2,
        checkpoint_every: int = 5,
        use_context: bool = True,
        should_continue: Optional[Callable[[], bool]] = None,
        translate_segment: Optional[Callable[[int, str, Optional[str]], str]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_checkpoint: Optional[Callable[[List[str], int], None]] = None,
        on_error: Optional[Callable[[int, str], None]] = None,
    ):
        self.source_segments = source_segments
        self.translated_segments = list(translated_segments or [])
        self.start_index = max(0, start_index)
        self.total_segments = len(self.source_segments)
        self.max_workers = max(1, max_workers)
        self.max_consecutive_failures = max(1, max_consecutive_failures)
        self.delay_seconds = max(0.0, delay_seconds)
        self.checkpoint_every = max(1, checkpoint_every)
        self.use_context = use_context
        self.should_continue = should_continue or (lambda: True)
        self.translate_segment = translate_segment
        self.on_progress = on_progress
        self.on_checkpoint = on_checkpoint
        self.on_error = on_error

        self.consecutive_failures = 0
        self.paused_due_to_failures = False
        self.resume_from_index = self.start_index

        if len(self.translated_segments) < self.total_segments:
            self.translated_segments.extend([""] * (self.total_segments - len(self.translated_segments)))

    def _build_context(self, idx: int) -> Optional[str]:
        if not self.use_context or idx <= 0:
            return None
        prev_trans = self.translated_segments[idx - 1]
        if prev_trans and not prev_trans.startswith("["):
            return prev_trans
        return None

    def _translate_one(self, idx: int):
        if not self.should_continue() or self.paused_due_to_failures:
            return None
        if self.translate_segment is None:
            raise RuntimeError("translate_segment callback is required")

        segment = self.source_segments[idx]
        context = self._build_context(idx)
        try:
            result = self.translate_segment(idx, segment, context)
            return idx, result, None
        except Exception as exc:
            return idx, None, str(exc)

    def _record_outcome(self, idx: int, result: Optional[str], error: Optional[str]) -> None:
        if result:
            self.translated_segments[idx] = result
            self.consecutive_failures = 0
            return

        self.consecutive_failures += 1
        error_text = error or "未知错误"
        self.translated_segments[idx] = f"[翻译错误: {error_text}]\n{self.source_segments[idx]}"
        if self.on_error:
            self.on_error(idx, error_text)
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.paused_due_to_failures = True
            self.resume_from_index = idx

    def _notify_progress(self, completed_count: int) -> None:
        if self.on_progress:
            self.on_progress(completed_count, self.total_segments)
        if completed_count % self.checkpoint_every == 0 and self.on_checkpoint:
            self.on_checkpoint(self.translated_segments, completed_count)

    def _run_parallel(self) -> int:
        completed_count = self.start_index
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._translate_one, idx): idx
                for idx in range(self.start_index, self.total_segments)
            }
            for future in as_completed(futures):
                if not self.should_continue() or self.paused_due_to_failures:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                try:
                    outcome = future.result()
                except Exception as exc:
                    idx = futures[future]
                    outcome = (idx, None, str(exc))
                if outcome is None:
                    break
                idx, result, error = outcome
                self._record_outcome(idx, result, error)
                completed_count += 1
                self._notify_progress(completed_count)
        return completed_count

    def _run_sequential(self) -> int:
        completed_count = self.start_index
        for idx in range(self.start_index, self.total_segments):
            if not self.should_continue() or self.paused_due_to_failures:
                break
            outcome = self._translate_one(idx)
            if outcome is None:
                break
            _, result, error = outcome
            self._record_outcome(idx, result, error)
            completed_count += 1
            self._notify_progress(completed_count)
            if self.paused_due_to_failures:
                break
            if self.delay_seconds:
                time.sleep(self.delay_seconds)
        return completed_count

    def run(self) -> BatchTranslationResult:
        if self.total_segments == 0:
            return BatchTranslationResult(
                translated_segments=self.translated_segments,
                completed_count=0,
                consecutive_failures=0,
                paused_due_to_failures=False,
                resume_from_index=0,
            )

        if self.max_workers > 1:
            completed_count = self._run_parallel()
        else:
            completed_count = self._run_sequential()

        if not self.paused_due_to_failures and completed_count >= self.total_segments:
            self.resume_from_index = self.total_segments

        return BatchTranslationResult(
            translated_segments=self.translated_segments,
            completed_count=completed_count,
            consecutive_failures=self.consecutive_failures,
            paused_due_to_failures=self.paused_due_to_failures,
            resume_from_index=self.resume_from_index,
        )
