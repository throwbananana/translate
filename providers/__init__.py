"""Provider adapter layer.

Adapters in this package isolate third-party SDK calls from `translation_engine.py`.
They should expose small, testable classes with explicit timeout handling.
"""

from .base import ProviderRequest, ProviderResponse
from .errors import (
    ProviderAuthError,
    ProviderError,
    ProviderQuotaError,
    ProviderResponseError,
    ProviderTimeoutError,
)

__all__ = [
    "ProviderRequest",
    "ProviderResponse",
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderQuotaError",
    "ProviderAuthError",
    "ProviderResponseError",
]
