#! python
# -*- coding: utf-8 -*-
"""Batch queue controller helpers.

The GUI currently owns most batch workflow state.  This module provides a small
pure-Python controller that can be adopted incrementally: normalize persisted
queue entries, find the next runnable task, update task status, and serialize
back to dictionaries for `batch_tasks.json`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .batch_task import BatchTaskRecord, BatchTaskStatus, normalize_batch_queue, normalize_batch_task


@dataclass(frozen=True)
class BatchQueueSnapshot:
    total: int
    pending: int
    loading: int
    translating: int
    exporting: int
    done: int
    failed: int
    cancelled: int

    @property
    def completed(self) -> int:
        return self.done + self.failed + self.cancelled

    @property
    def active(self) -> int:
        return self.loading + self.translating + self.exporting

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.completed)


class BatchController:
    """Immutable-style helper for batch queue transitions."""

    def __init__(self, queue: Iterable[Mapping[str, Any] | str | Path | BatchTaskRecord] = ()) -> None:
        self.queue = [self._normalize(item) for item in queue]

    @staticmethod
    def _normalize(item: Mapping[str, Any] | str | Path | BatchTaskRecord) -> BatchTaskRecord:
        if isinstance(item, BatchTaskRecord):
            return item
        return normalize_batch_task(item)

    @classmethod
    def from_legacy_queue(cls, raw_queue: list[Mapping[str, Any] | str | Path]) -> "BatchController":
        return cls(normalize_batch_queue(raw_queue))

    def to_legacy_queue(self) -> list[dict[str, str]]:
        return [task.to_dict() for task in self.queue]

    def snapshot(self) -> BatchQueueSnapshot:
        counts = {status: 0 for status in BatchTaskStatus}
        for task in self.queue:
            counts[task.status] += 1
        return BatchQueueSnapshot(
            total=len(self.queue),
            pending=counts[BatchTaskStatus.PENDING],
            loading=counts[BatchTaskStatus.LOADING],
            translating=counts[BatchTaskStatus.TRANSLATING],
            exporting=counts[BatchTaskStatus.EXPORTING],
            done=counts[BatchTaskStatus.DONE],
            failed=counts[BatchTaskStatus.FAILED],
            cancelled=counts[BatchTaskStatus.CANCELLED],
        )

    def next_runnable_task(self, *, include_failed: bool = False) -> BatchTaskRecord | None:
        allowed = {BatchTaskStatus.PENDING}
        if include_failed:
            allowed.add(BatchTaskStatus.FAILED)
        for task in self.queue:
            if task.status in allowed:
                return task
        return None

    def replace_task(self, path: str, replacement: BatchTaskRecord) -> "BatchController":
        replaced = False
        next_queue: list[BatchTaskRecord] = []
        for task in self.queue:
            if task.path == path:
                next_queue.append(replacement)
                replaced = True
            else:
                next_queue.append(task)
        if not replaced:
            raise ValueError(f"Batch task not found: {path}")
        return BatchController(next_queue)

    def update_status(
        self,
        path: str,
        status: BatchTaskStatus | str,
        *,
        error: str | None = None,
        output_path: str | None = None,
        timestamp: str | None = None,
    ) -> "BatchController":
        task = self.get_task(path)
        return self.replace_task(
            path,
            task.with_status(status, error=error, output_path=output_path, timestamp=timestamp),
        )

    def get_task(self, path: str) -> BatchTaskRecord:
        for task in self.queue:
            if task.path == path:
                return task
        raise ValueError(f"Batch task not found: {path}")

    def add_tasks(self, paths: Iterable[str | Path]) -> "BatchController":
        existing_paths = {task.path for task in self.queue}
        next_queue = list(self.queue)
        for path in paths:
            normalized_path = str(path)
            if normalized_path not in existing_paths:
                next_queue.append(BatchTaskRecord(path=normalized_path))
                existing_paths.add(normalized_path)
        return BatchController(next_queue)

    def cancel_pending(self, *, timestamp: str | None = None) -> "BatchController":
        next_queue = []
        for task in self.queue:
            if task.status in {BatchTaskStatus.PENDING, BatchTaskStatus.LOADING, BatchTaskStatus.TRANSLATING, BatchTaskStatus.EXPORTING}:
                next_queue.append(task.with_status(BatchTaskStatus.CANCELLED, timestamp=timestamp))
            else:
                next_queue.append(task)
        return BatchController(next_queue)


def should_load_batch_file_silently(*, batch_mode: bool, task: BatchTaskRecord | None = None) -> bool:
    """Return whether file-loading UI should suppress success message boxes."""
    return bool(batch_mode or task is not None)
