#!/usr/bin/env python3
"""OpenAI Agents SDK adapter scaffold for lattice roles and tools.

This is intentionally dependency-light: it exports pure dictionaries that can be
consumed by a local Agents SDK runner, Codex task, or MCP bridge without forcing
CI to install the Agents SDK.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_agent_manifest(name: str, instructions: str, tools: Optional[List[Dict[str, Any]]] = None, handoffs: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "name": name,
        "instructions": instructions,
        "tools": tools or [],
        "handoffs": handoffs or [],
        "guardrails": ["human_review_for_write_admin_destructive", "claimpacket_validation", "goldentrace_receipts"],
        "metadata": {"lattice_routes": True, "grok_leads": True},
    }


def default_lattice_agents(openai_tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    tools = openai_tools or []
    return [
        build_agent_manifest("Atlas Router", "Route tasks across OpenAI, Grok CLI, Notion, GitHub, Google, and Microsoft providers with receipts.", tools, ["Receipt Auditor", "Interop Builder"]),
        build_agent_manifest("Receipt Auditor", "Validate ClaimPackets, ToolPassports, evals, traces, and provenance before promotion.", tools, []),
        build_agent_manifest("Interop Builder", "Prepare safe patches, tests, and docs for maximum OpenAI interop.", tools, ["Receipt Auditor"]),
    ]
