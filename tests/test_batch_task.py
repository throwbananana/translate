import pytest

from controllers.batch_task import (
    BatchTaskRecord,
    BatchTaskStatus,
    normalize_batch_queue,
    normalize_batch_task,
)


pytestmark = pytest.mark.unit


def test_normalize_legacy_string_task():
    task = normalize_batch_task("books/demo.epub")

    assert task.path == "books/demo.epub"
    assert task.filename == "demo.epub"
    assert task.status == BatchTaskStatus.PENDING
    assert task.can_resume is True


def test_normalize_legacy_dict_task_with_file_path_alias():
    task = normalize_batch_task({"file_path": "demo.txt", "status": "translating"})

    assert task.path == "demo.txt"
    assert task.status == BatchTaskStatus.TRANSLATING


def test_normalize_unknown_status_falls_back_to_pending():
    task = normalize_batch_task({"path": "demo.txt", "status": "unknown"})

    assert task.status == BatchTaskStatus.PENDING


def test_task_transitions_record_timestamps_and_terminal_state():
    task = BatchTaskRecord(path="demo.txt")

    loading = task.with_status(BatchTaskStatus.LOADING, timestamp="2026-01-01T00:00:00+00:00")
    done = loading.with_status(
        BatchTaskStatus.DONE,
        output_path="out/demo.txt",
        timestamp="2026-01-01T00:05:00+00:00",
    )

    assert loading.started_at == "2026-01-01T00:00:00+00:00"
    assert done.finished_at == "2026-01-01T00:05:00+00:00"
    assert done.output_path == "out/demo.txt"
    assert done.is_terminal is True
    assert done.can_resume is False


def test_failed_task_can_resume_with_error_reason():
    task = BatchTaskRecord(path="demo.pdf").with_status(
        BatchTaskStatus.FAILED,
        error="OCR dependency missing",
        timestamp="2026-01-01T00:00:00+00:00",
    )

    assert task.is_terminal is True
    assert task.can_resume is True
    assert task.error == "OCR dependency missing"


def test_normalize_batch_queue():
    queue = normalize_batch_queue([
        "a.txt",
        {"filepath": "b.epub", "status": "done"},
    ])

    assert [task.path for task in queue] == ["a.txt", "b.epub"]
    assert queue[1].status == BatchTaskStatus.DONE
