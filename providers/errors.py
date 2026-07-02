#! python
# -*- coding: utf-8 -*-
"""Structured provider adapter errors."""

from __future__ import annotations


class ProviderError(Exception):
    """Base class for provider adapter errors."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderQuotaError(ProviderError):
    """Raised when quota or rate limit errors are detected."""


class ProviderAuthError(ProviderError):
    """Raised when credentials are invalid or missing."""


class ProviderResponseError(ProviderError):
    """Raised when the provider response is malformed or empty."""
