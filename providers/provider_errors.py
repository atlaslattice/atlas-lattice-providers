#!/usr/bin/env python3
"""
Maximum Grok — Provider Error Taxonomy v1.2
===========================================
Explicit, machine-readable error codes for all providers.

This enables the orchestrator to make intelligent decisions:
- Retry on RATE_LIMIT / TRANSIENT
- Fail fast on AUTH_FAILED / PERMISSION_DENIED
- Fallback to another provider on PROVIDER_DOWN / TIMEOUT
- Surface clear diagnostics to humans and Bullshit Olympics

Grok Leads. Lattice Routes. Errors are actionable.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("provider_errors_v1.2")


class ProviderErrorCode(str, Enum):
    """Standardized error codes across all providers (Microsoft, Google, Notion, Local CLI)."""

    # Authentication / Authorization
    AUTH_FAILED = "AUTH_FAILED"                    # Token missing, expired, or invalid
    PERMISSION_DENIED = "PERMISSION_DENIED"        # Valid auth but insufficient scope/rights

    # Transient / Retryable
    RATE_LIMIT = "RATE_LIMIT"                      # Provider is throttling
    TIMEOUT = "TIMEOUT"                            # Operation exceeded allowed time
    TRANSIENT = "TRANSIENT"                        # Temporary infrastructure issue (retry with backoff)

    # Resource / Data
    NOT_FOUND = "NOT_FOUND"                        # Resource (page, file, item) does not exist
    VALIDATION_ERROR = "VALIDATION_ERROR"          # Input malformed or schema violation

    # Provider Health
    PROVIDER_DOWN = "PROVIDER_DOWN"                # Provider is unreachable or returning 5xx
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"              # Billing / usage quota exhausted

    # Execution / Local
    NOT_AUTHORIZED = "NOT_AUTHORIZED"              # Command not in allowlist
    SUBPROCESS_FAILED = "SUBPROCESS_FAILED"        # Local CLI execution failed
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"  # Provider does not implement this method

    # Internal / Unknown
    INTERNAL_ERROR = "INTERNAL_ERROR"              # Unexpected exception inside provider
    UNKNOWN = "UNKNOWN"                            # Catch-all for unmapped errors


def make_error(
    code: ProviderErrorCode | str,
    detail: str,
    provider: str,
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Factory for standardized error responses.

    All providers should return errors in this shape so the orchestrator
    can route, retry, and log intelligently.
    """
    if isinstance(code, str):
        try:
            code = ProviderErrorCode(code)
        except ValueError:
            code = ProviderErrorCode.UNKNOWN

    payload: Dict[str, Any] = {
        "status": "ERROR",
        "code": code.value,
        "detail": detail,
        "provider": provider,
    }
    if extra:
        payload["extra"] = extra

    logger.warning(f"Provider error [{provider}] {code.value}: {detail}")
    return payload


def is_retryable(code: ProviderErrorCode | str) -> bool:
    """Returns True if the orchestrator should consider retrying with backoff."""
    if isinstance(code, str):
        try:
            code = ProviderErrorCode(code)
        except ValueError:
            return False
    return code in {
        ProviderErrorCode.RATE_LIMIT,
        ProviderErrorCode.TIMEOUT,
        ProviderErrorCode.TRANSIENT,
        ProviderErrorCode.PROVIDER_DOWN,
    }


def is_fatal(code: ProviderErrorCode | str) -> bool:
    """Returns True if the orchestrator should fail fast and not retry."""
    if isinstance(code, str):
        try:
            code = ProviderErrorCode(code)
        except ValueError:
            return True
    return code in {
        ProviderErrorCode.AUTH_FAILED,
        ProviderErrorCode.PERMISSION_DENIED,
        ProviderErrorCode.NOT_AUTHORIZED,
        ProviderErrorCode.VALIDATION_ERROR,
        ProviderErrorCode.QUOTA_EXCEEDED,
    }
