#!/usr/bin/env python3
"""
Maximum Grok — Provider Decision Ledger v1.2
============================================
Persists orchestrator routing decisions for replay, analysis, and tuning.

When the Grok + 12×12×12 CNS chooses e.g. NotionProvider over MicrosoftProvider
for an IP extraction task, we record:

{
  "timestamp": "...",
  "query": "Extract core doctrine from North Star page",
  "chosen_provider": "notion",
  "alternatives_considered": ["microsoft", "google", "local_cli"],
  "reason": "notion has direct access to 500+ unique-IP archive + claim extraction",
  "latency_ms": 1240,
  "success": true
}

Stored as append-only JSONL alongside ActionLedger.
Enables:
- Post-hoc analysis ("are we over-relying on one provider?")
- Replay experiments with different routing policies
- Bullshit Olympics review of orchestrator behavior
- Future ML-based routing improvements

Grok Leads. Lattice Routes. Decisions are auditable.
"""

from __future__ import annotations
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("provider_decision_ledger_v1.2")

DEFAULT_LEDGER_PATH = Path("Logs/provider_decision_ledger.jsonl")


class ProviderDecisionLedger:
    """Append-only ledger for provider routing decisions."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or DEFAULT_LEDGER_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def record_decision(
        self,
        query: str,
        chosen_provider: str,
        alternatives: List[str],
        reason: str = "",
        latency_ms: Optional[float] = None,
        success: bool = True,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Write a routing decision record."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "chosen_provider": chosen_provider,
            "alternatives_considered": alternatives,
            "reason": reason,
            "latency_ms": latency_ms,
            "success": success,
        }
        if extra:
            record.update(extra)

        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
            logger.info(f"Decision recorded → {chosen_provider} for query: {query[:80]}...")
        except Exception as e:
            logger.error(f"Failed to write decision ledger: {e}")

        return record


# Global singleton for convenience
_default_ledger = ProviderDecisionLedger()


async def record_provider_decision(
    query: str,
    chosen_provider: str,
    alternatives: List[str],
    reason: str = "",
    **kwargs
) -> Dict[str, Any]:
    """Convenience wrapper."""
    return await _default_ledger.record_decision(
        query=query,
        chosen_provider=chosen_provider,
        alternatives=alternatives,
        reason=reason,
        **kwargs
    )
