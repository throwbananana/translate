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
from .openai_compatible import OpenAICompatibleProvider
from .openai_compatible_factory import (
    build_custom_local_provider,
    build_openai_compatible_provider,
)

__all__ = [
    "ProviderRequest",
    "ProviderResponse",
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderQuotaError",
    "ProviderAuthError",
    "ProviderResponseError",
    "OpenAICompatibleProvider",
    "build_openai_compatible_provider",
    "build_custom_local_provider",
]
