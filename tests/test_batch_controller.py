import pytest

from controllers.batch_controller import BatchController, should_load_batch_file_silently
from controllers.batch_task import BatchTaskStatus


pytestmark = pytest.mark.unit


def test_batch_controller_normalizes_legacy_queue_and_snapshots_counts():
    controller = BatchController.from_legacy_queue([
        "a.txt",
        {"path": "b.txt", "status": "done"},
        {"file_path": "c.txt", "status": "failed", "error": "network"},
    ])

    snapshot = controller.snapshot()

    assert snapshot.total == 3
    assert snapshot.pending == 1
    assert snapshot.done == 1
    assert snapshot.failed == 1
    assert snapshot.completed == 2
    assert snapshot.remaining == 1


def test_next_runnable_task_defaults_to_pending_only():
    controller = BatchController.from_legacy_queue([
        {"path": "a.txt", "status": "failed"},
        {"path": "b.txt", "status": "pending"},
    ])

    assert controller.next_runnable_task().path == "b.txt"
    assert controller.next_runnable_task(include_failed=True).path == "a.txt"


def test_update_status_returns_new_controller_and_preserves_original():
    controller = BatchController.from_legacy_queue(["a.txt"])

    updated = controller.update_status(
        "a.txt",
        BatchTaskStatus.DONE,
        output_path="out/a.txt",
        timestamp="2026-01-01T00:00:00+00:00",
    )

    assert controller.get_task("a.txt").status == BatchTaskStatus.PENDING
    assert updated.get_task("a.txt").status == BatchTaskStatus.DONE
    assert updated.get_task("a.txt").output_path == "out/a.txt"


def test_add_tasks_deduplicates_paths():
    controller = BatchController.from_legacy_queue(["a.txt"])

    updated = controller.add_tasks(["a.txt", "b.txt"])

    assert [task.path for task in updated.queue] == ["a.txt", "b.txt"]


def test_cancel_pending_only_cancels_active_or_pending_tasks():
    controller = BatchController.from_legacy_queue([
        {"path": "a.txt", "status": "pending"},
        {"path": "b.txt", "status": "translating"},
        {"path": "c.txt", "status": "done"},
        {"path": "d.txt", "status": "failed"},
    ])

    updated = controller.cancel_pending(timestamp="2026-01-01T00:00:00+00:00")

    assert updated.get_task("a.txt").status == BatchTaskStatus.CANCELLED
    assert updated.get_task("b.txt").status == BatchTaskStatus.CANCELLED
    assert updated.get_task("c.txt").status == BatchTaskStatus.DONE
    assert updated.get_task("d.txt").status == BatchTaskStatus.FAILED


def test_to_legacy_queue_round_trips_dicts():
    controller = BatchController.from_legacy_queue(["a.txt"])

    data = controller.update_status("a.txt", "loading", timestamp="2026-01-01T00:00:00+00:00").to_legacy_queue()

    assert data == [
        {
            "path": "a.txt",
            "status": "loading",
            "error": "",
            "started_at": "2026-01-01T00:00:00+00:00",
            "finished_at": "",
            "output_path": "",
        }
    ]


def test_should_load_batch_file_silently():
    controller = BatchController.from_legacy_queue(["a.txt"])
    task = controller.next_runnable_task()

    assert should_load_batch_file_silently(batch_mode=True) is True
    assert should_load_batch_file_silently(batch_mode=False, task=task) is True
    assert should_load_batch_file_silently(batch_mode=False, task=None) is False
