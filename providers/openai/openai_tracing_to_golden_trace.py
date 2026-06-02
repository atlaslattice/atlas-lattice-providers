#!/usr/bin/env python3
"""
06_OpenAI_Tracing_To_GoldenTrace (Phase 1)
==========================================
Map OpenAI trace_ids / thread_ids / run_ids into the lattice ActionLedger + GoldenTrace v2 style receipts.

Purpose: Every OpenAI interaction produces immutable, hash-chained, lattice-coordinated receipts.

Symbiosis: Uses ActionLedger (existing), ClaimPackets, DecisionLedger. Emits traceable events for Bullshit Olympics and human gates.
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger("openai_tracing_golden_trace")

try:
    from ..notion.schemas.action_ledger import ActionLedger, ActionEntry
except Exception:
    ActionLedger = None


@dataclass
class GoldenTraceEvent:
    openai_trace_id: str
    openai_thread_id: Optional[str] = None
    openai_run_id: Optional[str] = None
    lattice_action_id: str = ""
    prev_hash: Optional[str] = None
    hash: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def compute_hash(self) -> str:
        h = hashlib.sha256()
        h.update((self.prev_hash or "GENESIS").encode())
        h.update(self.openai_trace_id.encode())
        h.update(self.ts.encode())
        h.update(json.dumps(self.payload, sort_keys=True).encode())
        return "0x" + h.hexdigest()[:32]


class OpenAITracingToGoldenTrace:
    """
    Bridge OpenAI observability into the 12D lattice's immutable receipt system.
    """

    def __init__(self, action_ledger: Optional[ActionLedger] = None, simulate: bool = True):
        self.action_ledger = action_ledger
        self.simulate = simulate
        self._trace_chain: Dict[str, GoldenTraceEvent] = {}  # openai_trace_id -> event

    async def record_openai_trace(self, openai_trace_id: str, openai_thread_id: Optional[str] = None, openai_run_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None, actor: str = "openai") -> Dict[str, Any]:
        payload = payload or {}
        prev = None
        if self._trace_chain:
            # chain on same trace if possible
            last = list(self._trace_chain.values())[-1]
            prev = last.hash

        event = GoldenTraceEvent(
            openai_trace_id=openai_trace_id,
            openai_thread_id=openai_thread_id,
            openai_run_id=openai_run_id,
            prev_hash=prev,
            payload=payload
        )
        event.hash = event.compute_hash()

        self._trace_chain[openai_trace_id] = event

        # Emit to ActionLedger (the canonical lattice receipt)
        if self.action_ledger:
            try:
                self.action_ledger.append(
                    action_type="openai_trace_ingested",
                    actor=actor,
                    target_id=openai_trace_id,
                    payload={"thread_id": openai_thread_id, "run_id": openai_run_id, "golden_trace_hash": event.hash, **payload},
                    lattice_coords=(2, 5, 1)  # OpenAI tracing lane
                )
            except Exception as e:
                logger.warning(f"ActionLedger emit failed for trace: {e}")

        return {
            "feature": "openai_tracing_to_golden_trace",
            "openai_trace_id": openai_trace_id,
            "golden_trace_hash": event.hash,
            "lattice_action_emitted": bool(self.action_ledger),
            "grok_leads": True,
            "lattice_routes": True
        }

    async def run(self, operation: str = "record", **kwargs) -> Dict[str, Any]:
        if operation == "record":
            return await self.record_openai_trace(
                openai_trace_id=kwargs.get("openai_trace_id"),
                openai_thread_id=kwargs.get("openai_thread_id"),
                openai_run_id=kwargs.get("openai_run_id"),
                payload=kwargs.get("payload")
            )
        return {"status": "ok", "op": operation}


if __name__ == "__main__":
    tracer = OpenAITracingToGoldenTrace(simulate=True)
    print("OpenAI Tracing -> GoldenTrace bridge ready (Phase 1).")