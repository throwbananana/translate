#! python
# -*- coding: utf-8 -*-
"""Thread-safe guards for background translation runs.

The GUI can use this helper to assign an id to each translation run.  Background
workers should carry that id and ask the guard before writing results back.  When
the user stops translation, late results from already-started API calls can then
be ignored instead of being written into the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading
import uuid


@dataclass(frozen=True)
class TranslationRunSnapshot:
    """Public immutable view of the current run state."""

    run_id: str | None
    is_active: bool
    is_cancelled: bool


class TranslationRunGuard:
    """Track the active translation run and reject stale worker results."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active_run_id: str | None = None
        self._cancelled_run_ids: set[str] = set()

    def start_run(self) -> str:
        """Start a new run and return its unique run id."""
        with self._lock:
            run_id = uuid.uuid4().hex
            self._active_run_id = run_id
            self._cancelled_run_ids.discard(run_id)
            return run_id

    def cancel_current(self) -> str | None:
        """Cancel the current run and return the cancelled run id, if any."""
        with self._lock:
            run_id = self._active_run_id
            if run_id is not None:
                self._cancelled_run_ids.add(run_id)
                self._active_run_id = None
            return run_id

    def finish_run(self, run_id: str) -> bool:
        """Mark a run as finished if it is still the active run."""
        with self._lock:
            if self._active_run_id != run_id:
                return False
            self._active_run_id = None
            self._cancelled_run_ids.discard(run_id)
            return True

    def is_current(self, run_id: str | None) -> bool:
        """Return whether the run id still represents the active run."""
        with self._lock:
            return bool(run_id) and self._active_run_id == run_id

    def is_cancelled(self, run_id: str | None) -> bool:
        """Return whether the run id has been explicitly cancelled."""
        with self._lock:
            return bool(run_id) and run_id in self._cancelled_run_ids

    def should_accept_result(self, run_id: str | None) -> bool:
        """Return True only when a worker result may still be applied."""
        with self._lock:
            return self.is_current(run_id) and not self.is_cancelled(run_id)

    def snapshot(self) -> TranslationRunSnapshot:
        """Return an immutable snapshot for diagnostics or tests."""
        with self._lock:
            run_id = self._active_run_id
            return TranslationRunSnapshot(
                run_id=run_id,
                is_active=run_id is not None,
                is_cancelled=bool(run_id and run_id in self._cancelled_run_ids),
            )
