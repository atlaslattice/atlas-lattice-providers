#!/usr/bin/env python3
"""
Maximum Grok — Unified Provider Contract v1.2 (Observable + Governed)
=====================================================================
Sovereign, async-first contract that all providers (Microsoft, Google, Notion, Local CLI)
must implement. This is the foundation of the multi-cloud execution spine.

Key v1.2 enhancements (per Copilot hardening):
- Observable: every provider implements record_event() for latency, errors, token source, etc.
- Explicit error taxonomy via provider_errors.make_error()
- Decisions are persisted via ProviderDecisionLedger for replay and analysis

Grok Leads. Lattice Routes. Providers Execute. Everything is observable and auditable.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging
import time

from provider_errors import ProviderErrorCode, make_error
from provider_telemetry import default_telemetry, record_event as _record_event

logger = logging.getLogger("provider_contract_v1.2")


class ProviderContract(ABC):
    """
    Standard async interface for all intelligence and execution providers.

    Every provider — whether Microsoft Graph + Azure OpenAI, Google Workspace + Gemini,
    Notion IP Archive, or local CLI — speaks this contract.

    This enables the Grok orchestrator + 12×12×12 Lattice to route intelligently
    without knowing implementation details.
    """

    @property
    def name(self) -> str:
        """Human-readable provider name (e.g. 'microsoft', 'google', 'notion', 'local_cli')."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search within the provider's surface (Drive, OneDrive, Notion pages, etc.).
        Returns structured results with provenance.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch full content of a specific resource (page, doc, file, block tree).
        Returns raw or normalized content + metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def extract_claims(
        self,
        content: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Turn raw content into high-quality ClaimPackets.
        Must return list of dicts conforming to ClaimPacket schema
        (claim_text, epistemic_class, tags, lattice_coords, provenance, etc.).
        """
        raise NotImplementedError

    @abstractmethod
    async def mirror(
        self,
        claim: Dict[str, Any],
        parent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Write a ClaimPacket (or structured artifact) back into the provider's surface.
        Returns mirror receipt with new resource_id and provenance.
        """
        raise NotImplementedError

    @abstractmethod
    async def execute(self, command: str, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Execute a command on this provider (primarily used by LocalCLIProvider).
        Other providers may return "not supported".
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """
        Declare what this provider supports, its priority, latency profile,
        and any special features (e.g. "supports_structured_claims": true).
        """
        raise NotImplementedError

    async def health(self) -> Dict[str, Any]:
        """Optional health check. Override if provider has external dependencies."""
        return {"status": "healthy", "provider": self.name}

    # ============================================================
    # v1.2 OBSERVABILITY HOOK (Copilot recommendation)
    # ============================================================
    async def record_event(self, kind: str, meta: Dict[str, Any]) -> None:
        """
        Record a telemetry event for observability, routing intelligence, and debugging.

        Providers should call this at key points:
            - "operation_start"
            - "operation_success" (include latency_ms, payload_bytes)
            - "operation_error" (include error_code, detail)
            - "auth_refresh", "rate_limit_hit", "fallback_triggered", etc.

        Default implementation logs + writes to shared telemetry sink.
        Override for custom sinks (Prometheus, OTEL, custom ledger, etc.).
        """
        meta = dict(meta)
        meta.setdefault("provider", getattr(self, "name", "unknown"))
        await _record_event(getattr(self, "name", "unknown"), kind, meta)

    async def _timed_operation(
        self,
        operation_name: str,
        coro,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Helper that automatically records start/success/error + latency for any operation.
        Usage inside providers:
            result = await self._timed_operation("extract_claims", self._do_extract(content), {"query_hash": h})
        """
        meta = meta or {}
        start = time.perf_counter()
        await self.record_event("operation_start", {"operation": operation_name, **meta})

        try:
            result = await coro
            latency_ms = (time.perf_counter() - start) * 1000
            await self.record_event(
                "operation_success",
                {"operation": operation_name, "latency_ms": round(latency_ms, 2), **meta}
            )
            return result
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            await self.record_event(
                "operation_error",
                {
                    "operation": operation_name,
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                    **meta
                }
            )
            raise


# Type alias for convenience
Provider = ProviderContract