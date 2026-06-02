#!/usr/bin/env python3
"""
Maximum Grok — Provider Telemetry v1.2
======================================
Lightweight, shared observability hook for all providers.

Every provider can (and should) call record_event() at key moments:
- operation_start
- operation_success (with latency_ms, payload_size)
- operation_error (with error_code)
- token_source, auth_method, etc.

Default implementation logs to stderr + can be extended to write to
a structured telemetry sink (Prometheus, OpenTelemetry, custom JSONL, etc.).

This data powers:
- Intelligent routing decisions in the Grok orchestrator
- Post-hoc debugging ("why did MicrosoftProvider take 4.2s on that query?")
- Health dashboards and Bullshit Olympics review

Grok Leads. Lattice Routes. Providers are observable.
"""

from __future__ import annotations
import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("provider_telemetry_v1.2")


class ProviderTelemetry:
    """
    Shared telemetry sink. Providers receive an instance (or use the global one).
    """

    def __init__(self, sink: Optional[Any] = None):
        """
        sink: optional object with .write(event: dict) method.
        If None, we only log and (optionally) append to a local JSONL file.
        """
        self.sink = sink
        self._jsonl_path = None  # Can be set later for persistent telemetry

    async def record_event(
        self,
        provider_name: str,
        kind: str,
        meta: Dict[str, Any]
    ) -> None:
        """
        Record a telemetry event from any provider.

        kind examples:
            "operation_start", "operation_success", "operation_error",
            "auth_refresh", "rate_limit_hit", "fallback_triggered"

        meta should contain useful context:
            latency_ms, error_code, token_source, payload_bytes, query_hash, etc.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider_name,
            "kind": kind,
            **meta
        }

        # Always log at INFO level for visibility in agent runs
        logger.info(f"TELEMETRY [{provider_name}] {kind}: {json.dumps(meta, default=str)[:300]}")

        # Optional: write to structured sink (future: Prometheus, OTEL, BigQuery, etc.)
        if self.sink and hasattr(self.sink, "write"):
            try:
                await self.sink.write(event) if hasattr(self.sink, "__await__") else self.sink.write(event)
            except Exception as e:
                logger.warning(f"Telemetry sink write failed: {e}")

        # Optional local JSONL persistence (can be enabled by setting path)
        if self._jsonl_path:
            try:
                with open(self._jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, default=str) + "\n")
            except Exception as e:
                logger.warning(f"Failed to append telemetry to {self._jsonl_path}: {e}")


# Global default instance — providers can import and use directly
default_telemetry = ProviderTelemetry()


async def record_event(provider_name: str, kind: str, meta: Dict[str, Any]) -> None:
    """Convenience wrapper around the global telemetry instance."""
    await default_telemetry.record_event(provider_name, kind, meta)
