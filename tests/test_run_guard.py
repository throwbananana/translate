import pytest

from controllers.run_guard import TranslationRunGuard


pytestmark = pytest.mark.unit


def test_run_guard_accepts_only_current_run():
    guard = TranslationRunGuard()

    first = guard.start_run()
    second = guard.start_run()

    assert guard.should_accept_result(first) is False
    assert guard.should_accept_result(second) is True


def test_run_guard_rejects_results_after_cancel():
    guard = TranslationRunGuard()
    run_id = guard.start_run()

    cancelled = guard.cancel_current()

    assert cancelled == run_id
    assert guard.is_current(run_id) is False
    assert guard.is_cancelled(run_id) is True
    assert guard.should_accept_result(run_id) is False


def test_run_guard_finishes_only_active_run():
    guard = TranslationRunGuard()
    first = guard.start_run()
    second = guard.start_run()

    assert guard.finish_run(first) is False
    assert guard.finish_run(second) is True
    assert guard.snapshot().is_active is False
