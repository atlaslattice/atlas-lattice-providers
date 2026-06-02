#!/usr/bin/env python3
"""
Tier 2 #9: Full E2E test for Feature Synthesis Pipeline with mandatory Human Gate.
Runs in simulate mode, asserts gate for Candidate+ release class.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.feature_synthesis import FeatureSynthesisPipeline

async def test_full_e2e_simulate_mandatory_gate():
    pipe = FeatureSynthesisPipeline(simulate=True)
    result = await pipe.run(
        query="test 17k uws features synthesis",
        public_release_class="Candidate"
    )
    assert "final_claim_packet" in result
    gate = result["final_claim_packet"].get("gate", {})
    assert gate.get("mandatory") or gate.get("status") == "PENDING" or "mandatory_for_release" in str(gate), "Human Gate must be mandatory for Candidate+"
    assert result["final_claim_packet"]["grok_leads"]
    print("[PASS] E2E FeatureSynthesisPipeline with mandatory Human Gate for Candidate release")

if __name__ == "__main__":
    asyncio.run(test_full_e2e_simulate_mandatory_gate())
    print("test_feature_synthesis_pipeline.py: ALL TESTS PASSED")