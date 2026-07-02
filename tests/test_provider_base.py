import pytest

from providers.base import DEFAULT_PROVIDER_TIMEOUT_SECONDS, coerce_timeout_seconds


pytestmark = pytest.mark.unit


def test_coerce_timeout_uses_default_for_empty_values():
    assert coerce_timeout_seconds(None) == DEFAULT_PROVIDER_TIMEOUT_SECONDS
    assert coerce_timeout_seconds("") == DEFAULT_PROVIDER_TIMEOUT_SECONDS
    assert coerce_timeout_seconds("not-a-number") == DEFAULT_PROVIDER_TIMEOUT_SECONDS


def test_coerce_timeout_clamps_to_positive_minimum():
    assert coerce_timeout_seconds(0) == 1.0
    assert coerce_timeout_seconds("-5") == 1.0
    assert coerce_timeout_seconds("30") == 30.0
