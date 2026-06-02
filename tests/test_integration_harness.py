#!/usr/bin/env python3
"""
Simple integration test harness (E145 priority 4).
Exercises full stack via orchestrator + direct engines + MCP-like dispatch simulation.
Run after every major edit.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from grok_orchestrator import GrokOrchestrator
from providers.project_oriented_features import ProjectOrientedFeaturesEngine, BullshitOlympics
from providers.uws_integrations import UwsIntegrations
from providers.cli_runner import SecureCLIRunner
from providers.provider_errors import make_error, ProviderErrorCode


async def harness_full_lattice_smoke():
    print("HARNESS: full lattice smoke (orchestrator as brain)")
    orch = GrokOrchestrator(project_id="harness-lattice", simulate_default=True)

    feats = [
        ("arena_mode", {"task": "harness 17k uws + 20 v3 + 20 e145"}),
        ("bullshit_olympics", {"target": "harness synthesis", "high_stakes": True}),
        ("uws", {"integration": "immutable_audit", "operation": "harness"}),
        ("project_memory_graph", {"query": "harness decision traces"}),
        ("unified_truth_plus_capability_dashboard", {}),
    ]
    for feat, kw in feats:
        r = await orch.run(feat, **kw)
        assert isinstance(r, dict)
        assert r.get("grok_leads") or "grok_leads" in str(r)
        print(f"  [ok] {feat}")

    # Direct bullshit component
    bs = BullshitOlympics(project_engine=orch.project_engine)
    rbs = await bs.review("harness claim", high_stakes=True)
    assert rbs.get("inv_l28_coherence", 0) > 0.75
    print("  [ok] direct BullshitOlympics")

    # UWS error path taxonomy
    u = UwsIntegrations(runner=SecureCLIRunner(), simulate_default=True)
    err = await u._execute_uws(["nonexistent"], dry_run=True)
    if isinstance(err, dict) and (err.get("code") or err.get("status") == "ERROR"):
        print("  [ok] UWS error taxonomy via make_error")

    # High stakes gate
    rp = await orch.project_engine.run("self_improving_skills", pattern="harness-evolve", high_stakes=True)
    assert "mandatory_human_gate" in rp or rp.get("gate_status")
    print("  [ok] mandatory gate in direct project path")

    print("HARNESS: all integration points exercised, symbiosis maximized.")
    return True


if __name__ == "__main__":
    ok = asyncio.run(harness_full_lattice_smoke())
    print("INTEGRATION HARNESS:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
