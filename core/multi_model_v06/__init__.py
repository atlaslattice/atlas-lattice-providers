#!/usr/bin/env python3
"""
Multi-Model Autonomous Agent Framework v0.6 — Phase 1
Minimal Viable Bootstrap package.

Exports the core data models, base agent, five agents, and bootstrap harness.

All communication via TransparentPacket96 v4.0 envelopes.
Human-root final authority. INV-0 — Nothing Dies.

Usage:
    from core.multi_model_v06 import FrameworkV06Bootstrap, TransparentPacket96
    fw = FrameworkV06Bootstrap()
    fw.bootstrap_demo()
    fw.guardrail_violation_demo()
"""

from .data_models import (
    ClaimPacket,
    TransparentPacket96,
    Stack,
    validate_transparent_packet,
    ClaimType,
    PacketStatus,
    StackStatus,
)
from .base_agent import BaseAgent, MemoryPalaceSeed
from .orchestrator_prime import OrchestratorPrime, Task
from .scout import Scout
from .claim_miner import ClaimMiner
from .stack_curator import StackCurator
from .background_executor import BackgroundExecutor
from .bootstrap_v06 import FrameworkV06Bootstrap

__version__ = "0.6.0"
__phase__ = "Phase 1 — Minimal Viable Bootstrap"
__spec_status__ = "Locked + Ratified"

__all__ = [
    "ClaimPacket",
    "TransparentPacket96",
    "Stack",
    "validate_transparent_packet",
    "BaseAgent",
    "MemoryPalaceSeed",
    "OrchestratorPrime",
    "Task",
    "Scout",
    "ClaimMiner",
    "StackCurator",
    "BackgroundExecutor",
    "FrameworkV06Bootstrap",
]

def get_status():
    """Quick package status for lattice queries."""
    return {
        "version": __version__,
        "phase": __phase__,
        "spec_status": __spec_status__,
        "guardrails": "active (human-root + D-54 + INV-0)",
        "comm": "TransparentPacket96 v4.0 only (no direct writes)",
    }
