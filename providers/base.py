#! python
# -*- coding: utf-8 -*-
"""Base data structures for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_PROVIDER_TIMEOUT_SECONDS = 90.0


@dataclass(frozen=True)
class ProviderRequest:
    """One provider translation request."""

    text: str
    target_lang: str
    system_instruction: str = ""
    model: str = ""
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ProviderResponse:
    """Normalized provider translation response."""

    text: str
    model: str
    tokens_used: int = 0


def coerce_timeout_seconds(value: float | int | str | None) -> float:
    """Coerce provider timeout values to a safe positive number."""
    if value is None or value == "":
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    return max(1.0, timeout)
