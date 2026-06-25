#! python
# -*- coding: utf-8 -*-
"""Batch task state helpers.

The current GUI stores batch tasks as dictionaries.  This module provides a small
validated record type and transition helpers so the batch workflow can be moved
out of the GUI incrementally without breaking existing persisted queues.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class BatchTaskStatus(str, Enum):
    PENDING = "pending"
    LOADING = "loading"
    TRANSLATING = "translating"
    EXPORTING = "exporting"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = {
    BatchTaskStatus.DONE,
    BatchTaskStatus.FAILED,
    BatchTaskStatus.CANCELLED,
}

RESUMABLE_STATUSES = {
    BatchTaskStatus.PENDING,
    BatchTaskStatus.LOADING,
    BatchTaskStatus.TRANSLATING,
    BatchTaskStatus.EXPORTING,
    BatchTaskStatus.FAILED,
}


def utc_now_iso() -> str:
    """Return a compact UTC timestamp for persisted task metadata."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class BatchTaskRecord:
    path: str
    status: BatchTaskStatus = BatchTaskStatus.PENDING
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    output_path: str = ""

    @property
    def filename(self) -> str:
        return Path(self.path).name

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def can_resume(self) -> bool:
        return self.status in RESUMABLE_STATUSES and self.status != BatchTaskStatus.DONE

    def to_dict(self) -> dict[str, str]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def with_status(
        self,
        status: BatchTaskStatus | str,
        *,
        error: str | None = None,
        output_path: str | None = None,
        timestamp: str | None = None,
    ) -> "BatchTaskRecord":
        next_status = BatchTaskStatus(status)
        now = timestamp or utc_now_iso()
        started_at = self.started_at
        if next_status != BatchTaskStatus.PENDING and not started_at:
            started_at = now

        finished_at = self.finished_at
        if next_status in TERMINAL_STATUSES:
            finished_at = now

        return BatchTaskRecord(
            path=self.path,
            status=next_status,
            error=self.error if error is None else error,
            started_at=started_at,
            finished_at=finished_at,
            output_path=self.output_path if output_path is None else output_path,
        )


def normalize_batch_task(raw: Mapping[str, Any] | str | Path) -> BatchTaskRecord:
    """Normalize legacy queue entries into a validated task record."""
    if isinstance(raw, (str, Path)):
        return BatchTaskRecord(path=str(raw))

    path = str(raw.get("path") or raw.get("file_path") or raw.get("filepath") or "")
    if not path:
        raise ValueError("Batch task is missing a file path")

    raw_status = raw.get("status") or BatchTaskStatus.PENDING.value
    try:
        status = BatchTaskStatus(str(raw_status))
    except ValueError:
        status = BatchTaskStatus.PENDING

    return BatchTaskRecord(
        path=path,
        status=status,
        error=str(raw.get("error") or ""),
        started_at=str(raw.get("started_at") or ""),
        finished_at=str(raw.get("finished_at") or ""),
        output_path=str(raw.get("output_path") or ""),
    )


def normalize_batch_queue(raw_queue: list[Mapping[str, Any] | str | Path]) -> list[BatchTaskRecord]:
    """Normalize an entire persisted batch queue."""
    return [normalize_batch_task(item) for item in raw_queue]
