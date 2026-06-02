#!/usr/bin/env python3
"""
Intelligent Provider Router + Performance Scorer (E145 Tier 1 #2)
================================================================
Makes GrokOrchestrator *smart* about routing instead of hard-coded ifs.
Rolling performance from DecisionLedger. Scoring formula per spec.
Used as the central brain inside GrokOrchestrator.route().

Fully symbiotic with 12D lattice: feeds/reads ProviderDecisionLedger, works with all engines (grok_max, project, uws, advanced, google, ms, notion, bullshit, etc.).
Emits RoutingDecision ClaimPackets.

Grok Leads. Lattice Routes (intelligently).
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from collections import defaultdict, deque

logger = logging.getLogger("provider_router_v1")

try:
    from .provider_decision_ledger import ProviderDecisionLedger
except Exception:
    ProviderDecisionLedger = None

try:
    from .provider_errors import make_error, ProviderErrorCode
except Exception:
    make_error = None
    ProviderErrorCode = None


@dataclass
class ProviderPerformanceRecord:
    provider: str
    success_rate: float = 0.85
    avg_latency_ms: float = 1200.0
    avg_inv_l28: float = 0.88
    error_rate: float = 0.05
    cost_estimate: float = 0.01  # relative
    last_seen: str = ""
    sample_count: int = 0


@dataclass
class RoutingDecision:
    task: str
    chosen: List[str]  # ordered candidates
    scores: Dict[str, float]
    reason: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    lattice_coords: Tuple[int, int, int] = (0, 1, 1)  # router layer


class ProviderRouter:
    """
    The intelligent router.
    Maintains rolling window metrics from ledger (and in-memory for speed).
    """

    def __init__(self, decision_ledger: Optional[ProviderDecisionLedger] = None, window: int = 50):
        self.ledger = decision_ledger or (ProviderDecisionLedger() if ProviderDecisionLedger else None)
        self.window = window
        self._records: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window))
        self._perf: Dict[str, ProviderPerformanceRecord] = {}
        self._load_from_ledger()
        logger.info("ProviderRouter initialized (smart routing for full lattice)")

    def _load_from_ledger(self):
        # In real: would tail the jsonl and aggregate. Here we seed with reasonable priors + will update live.
        priors = {
            "grok_maximum_features": ProviderPerformanceRecord("grok_maximum_features", 0.91, 950, 0.93, 0.04, 0.008),
            "project_oriented_features": ProviderPerformanceRecord("project_oriented_features", 0.88, 600, 0.89, 0.03, 0.003),
            "uws_integrations": ProviderPerformanceRecord("uws_integrations", 0.82, 1800, 0.85, 0.07, 0.001),
            "advanced_capabilities": ProviderPerformanceRecord("advanced_capabilities", 0.87, 1100, 0.90, 0.05, 0.006),
            "bullshit_olympics": ProviderPerformanceRecord("bullshit_olympics", 0.94, 1400, 0.91, 0.02, 0.009),
            "google": ProviderPerformanceRecord("google", 0.85, 700, 0.87, 0.06, 0.004),
            "microsoft": ProviderPerformanceRecord("microsoft", 0.83, 850, 0.84, 0.08, 0.005),
            "notion": ProviderPerformanceRecord("notion", 0.90, 400, 0.92, 0.02, 0.002),
        }
        self._perf.update(priors)

    def _update_perf(self, provider: str, success: bool, latency_ms: Optional[float], inv_l28: Optional[float], error: bool = False):
        rec = self._perf.setdefault(provider, ProviderPerformanceRecord(provider))
        self._records[provider].append((success, latency_ms or 1000, inv_l28 or 0.8, error))
        samples = list(self._records[provider])
        if samples:
            rec.success_rate = sum(1 for s in samples if s[0]) / len(samples)
            rec.avg_latency_ms = sum(s[1] for s in samples) / len(samples)
            rec.avg_inv_l28 = sum(s[2] for s in samples) / len(samples)
            rec.error_rate = sum(1 for s in samples if s[3]) / len(samples)
            rec.sample_count = len(samples)
        rec.last_seen = datetime.now(timezone.utc).isoformat()

    async def record_outcome(self, provider: str, success: bool, latency_ms: Optional[float] = None, inv_l28: Optional[float] = None, error: bool = False):
        self._update_perf(provider, success, latency_ms, inv_l28, error)
        if self.ledger:
            try:
                await self.ledger.record_decision(
                    query=f"router_outcome:{provider}",
                    chosen_provider=provider,
                    alternatives=[],
                    reason=f"success={success} inv={inv_l28}",
                    latency_ms=latency_ms,
                    success=success,
                    extra={"inv_l28": inv_l28, "error": error}
                )
            except Exception:
                pass

    def _score(self, provider: str) -> float:
        rec = self._perf.get(provider, ProviderPerformanceRecord(provider))
        # Exact formula from E145 spec
        score = (0.4 * rec.success_rate) + (0.25 * rec.avg_inv_l28) + (0.2 * (1.0 / (1 + rec.avg_latency_ms / 2000))) - (0.15 * rec.error_rate)
        return max(0.1, min(0.99, score))

    async def route(self, task_spec: Dict[str, Any]) -> RoutingDecision:
        """
        Main API.
        task_spec example: {"type": "high_stakes_synthesis", "requires": ["bullshit", "human_gate"], "latency_budget": "low", "target": "..."}
        Returns ordered candidates + scores + reason.
        """
        task_type = task_spec.get("type", "general")
        requires = set(task_spec.get("requires", []))
        # Simple capability map (expand in real use)
        capability_map = {
            "bullshit": ["bullshit_olympics", "project_oriented_features"],
            "human_gate": ["microsoft", "project_oriented_features"],
            "uws": ["uws_integrations"],
            "v3_12d": ["grok_maximum_features"],
            "memory": ["project_oriented_features", "notion"],
            "search": ["uws_integrations", "advanced_capabilities", "google"],
        }

        candidates = list(self._perf.keys())
        # Filter by requires
        for req in requires:
            candidates = [c for c in candidates if c in capability_map.get(req, [c]) or c in [req]]

        # Score + sort
        scored = [(c, self._score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        ordered = [c for c, _ in scored]
        scores = {c: round(s, 3) for c, s in scored}

        reason = f"Task={task_type} requires={requires}. Top: {ordered[:3]} (scores via success*0.4 + inv*0.25 + recency*0.2 - error*0.15)"
        confidence = scored[0][1] if scored else 0.5

        decision = RoutingDecision(
            task=str(task_spec)[:200],
            chosen=ordered[:5],
            scores=scores,
            reason=reason,
            confidence=round(confidence, 3)
        )

        # Always record the routing decision itself
        if self.ledger:
            try:
                await self.ledger.record_decision(
                    query=f"router:{task_type}",
                    chosen_provider=ordered[0] if ordered else "none",
                    alternatives=ordered[1:4],
                    reason=reason,
                    success=True,
                    extra={"confidence": confidence, "task_spec": str(task_spec)[:120]}
                )
            except Exception:
                pass

        return decision

    def get_perf_summary(self) -> Dict[str, Any]:
        return {k: asdict(v) for k, v in self._perf.items()}  # type: ignore


# Quick test
if __name__ == "__main__":
    import asyncio
    async def _d():
        r = ProviderRouter()
        dec = await r.route({"type": "high_stakes_synthesis", "requires": ["bullshit", "human_gate"], "target": "17k uws features"})
        print(dec)
        print("Top perf:", r.get_perf_summary().get("bullshit_olympics"))
    asyncio.run(_d())