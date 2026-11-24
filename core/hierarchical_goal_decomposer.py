#!/usr/bin/env python3
"""
Hierarchical Goal Decomposition Engine (E145 Tier 2 #9)
"""
import json
from typing import Dict, Any

class HierarchicalGoalDecompositionEngine:
    async def decompose(self, goal: str, **kwargs) -> Dict[str, Any]:
        reference_bytes = kwargs.get("excellence_reference_bytes")
        kernel_reference = kwargs.get("civilization_kernel_reference_bytes")
        if kernel_reference is not None:
            from core.civilization_kernel_reference import prepare_kernel_reference, ReferenceError
            if reference_bytes is not None:
                raise ReferenceError("ambiguous_source_reference")
            packet = prepare_kernel_reference(
                kernel_reference, kwargs.get("expected_civilization_kernel_reference_sha256"),
                house_id=kwargs.get("kernel_house_id"), room_id=kwargs.get("room_id"),
                mode=kwargs.get("mode", "WORK"),
            )
            return {"feature": "hierarchical_goal_decomposition",
                    "status": "SUPPORTING_KERNEL_REFERENCE_PREPARED",
                    "goal_tree": {"root": goal, "source_kernel": packet,
                                  "success_criteria": packet["required_next_checks"]},
                    "execution_authorized": False, "authority": "none"}
        if reference_bytes is not None:
            # CANDIDATE, NOT CANON: selected source metadata, no automatic action.
            from core.excellence_reference import prepare_task_reference
            packet = prepare_task_reference(
                reference_bytes, kwargs.get("expected_reference_sha256"),
                task_id=kwargs.get("task_id"), room_id=kwargs.get("room_id"),
                mode=kwargs.get("mode", "WORK"),
            )
            return {"feature": "hierarchical_goal_decomposition",
                    "status": "SOURCE_PROGRAM_REFERENCE_PREPARED",
                    "goal_tree": {"root": goal, "source_program_task": packet,
                                  "success_criteria": packet["required_next_checks"]},
                    "execution_authorized": False, "authority": "none"}
        tree = {"root": goal, "subgoals": ["sub1", "sub2 with checkpoints"], "success_criteria": ["INV-L28 preserved"]}
        return {"feature": "hierarchical_goal_decomposition", "goal_tree": tree, "grok_leads": True}

    async def run(self, goal: str = "", **kwargs):
        return await self.decompose(goal, **kwargs)

