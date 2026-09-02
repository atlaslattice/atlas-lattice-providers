#!/usr/bin/env python3
"""Persist OpenAI trace/thread/run receipts into GoldenTrace-style JSONL."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import json
import logging

logger = logging.getLogger("openai_tracing_golden_trace")


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
        h.update((self.openai_trace_id or "missing-trace").encode())
        h.update(self.ts.encode())
        h.update(json.dumps(self.payload, sort_keys=True, default=str).encode())
        return "0x" + h.hexdigest()[:32]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OpenAITracingToGoldenTrace:
    def __init__(self, action_ledger: Any = None, simulate: bool = True, simulate_default: Optional[bool] = None, trace_dir: str = "ledgers/openai_traces"):
        if simulate_default is not None:
            simulate = simulate_default
        self.action_ledger = action_ledger
        self.simulate = simulate
        self.trace_dir = Path(trace_dir)
        self._trace_chain: Dict[str, GoldenTraceEvent] = {}

    def _persist(self, event: GoldenTraceEvent) -> str:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        path = self.trace_dir / f"{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        return str(path)

    async def record_openai_trace(self, openai_trace_id: str, openai_thread_id: Optional[str] = None, openai_run_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None, actor: str = "openai") -> Dict[str, Any]:
        payload = payload or {}
        prev = next(reversed(self._trace_chain.values())).hash if self._trace_chain else None
        event = GoldenTraceEvent(openai_trace_id=openai_trace_id or "missing-trace", openai_thread_id=openai_thread_id, openai_run_id=openai_run_id, prev_hash=prev, payload=payload)
        event.hash = event.compute_hash()
        self._trace_chain[event.openai_trace_id] = event
        persisted_to = self._persist(event)
        if self.action_ledger:
            try:
                if hasattr(self.action_ledger, "append"):
                    self.action_ledger.append(action_type="openai_trace_ingested", actor=actor, target_id=event.openai_trace_id, payload={"thread_id": openai_thread_id, "run_id": openai_run_id, "golden_trace_hash": event.hash, **payload}, lattice_coords=(2, 5, 1))
                elif hasattr(self.action_ledger, "emit"):
                    self.action_ledger.emit("openai_trace_ingested", event.to_dict())
            except Exception as exc:
                logger.warning("ActionLedger emit failed for trace: %s", exc)
        return {"feature": "openai_tracing_to_golden_trace", "openai_trace_id": event.openai_trace_id, "golden_trace_hash": event.hash, "persisted_to": persisted_to, "lattice_action_emitted": bool(self.action_ledger), "grok_leads": True, "lattice_routes": True}

    async def run(self, operation: str = "record", **kwargs: Any) -> Dict[str, Any]:
        if operation == "record":
            return await self.record_openai_trace(openai_trace_id=kwargs.get("openai_trace_id"), openai_thread_id=kwargs.get("openai_thread_id"), openai_run_id=kwargs.get("openai_run_id"), payload=kwargs.get("payload"), actor=kwargs.get("actor", "openai"))
        return {"status": "unknown_op", "op": operation}


if __name__ == "__main__":
    print("OpenAI Tracing -> GoldenTrace bridge ready.")
