# !/usr/bin/env python3
"""
18_gpt_safety_gate_child.py
===========================
Classifies proposed actions and chooses gates.

Preserves: OpenAI moves work; governance grants authority.
"""

from typing import Dict, Any
from datetime import datetime, timezone

class GPTSafetyGateChild:
    child_id = "gpt-safety-gate-child"
    category = "external_gpt_child"
    authority_scope = "none"
    canon_status = "candidate_not_canon"

    ACTION_LEVELS = {
        "read_only": "auto_allowed",
        "local_write": "needs Dave confirmation",
        "remote_write": "needs Dave confirmation",
        "secret_touching": "blocked",
        "canon_promotion": "needs council + human-root",
        "public_publish": "needs council + human-root"
    }

    def classify_and_gate(self, action: str, details: str = "") -> Dict[str, Any]:
        level = "read_only"
        for k in self.ACTION_LEVELS:
            if k in action.lower() or k in details.lower():
                level = k
                break
        gate = self.ACTION_LEVELS.get(level, "needs Dave confirmation")
        return {
            "feature": "gpt_safety_gate_child",
            "action": action,
            "classified_level": level,
            "gate": gate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "child_id": self.child_id,
            "note": "Governance gate. OpenAI proposes/moves; this + human-root authorizes. CANDIDATE not canon.",
            "grok_leads": True
        }

    async def run(self, **kwargs):
        return self.classify_and_gate(kwargs.get("action", "read_only"), kwargs.get("details", ""))

if __name__ == "__main__":
    gate = GPTSafetyGateChild()
    print(gate.classify_and_gate("propose remote push of receipt"))
    print("CANDIDATE — NOT CANON.")