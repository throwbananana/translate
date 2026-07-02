"""Provider adapter layer.

Adapters in this package isolate third-party SDK calls from `translation_engine.py`.
They should expose small, testable classes with explicit timeout handling.
"""

from .base import ProviderRequest, ProviderResponse
from .claude_provider import ClaudeProvider
from .engine_bridge import (
    build_translation_system_instruction,
    translate_with_custom_local_config,
    translate_with_openai_compatible_config,
)
from .errors import (
    ProviderAuthError,
    ProviderError,
    ProviderQuotaError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from .gemini_provider import GeminiProvider
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
    "GeminiProvider",
    "ClaudeProvider",
    "build_openai_compatible_provider",
    "build_custom_local_provider",
    "build_translation_system_instruction",
    "translate_with_openai_compatible_config",
    "translate_with_custom_local_config",
]
