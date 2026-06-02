#!/usr/bin/env python3
"""Print a local readiness report for OpenAI interop."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.openai import ResponsesAPISpine, StructuredOutputSchemaSpine, ToolPassportFunctionCalling, OpenAITracingToGoldenTrace, EvalsBullshitOlympicsBridge, WorkloadIdentitySecretsHygiene
from providers.openai.agents_sdk_adapter import default_lattice_agents


async def main() -> None:
    hygiene = WorkloadIdentitySecretsHygiene(simulate=True).check_environment()["report"]
    responses = await ResponsesAPISpine(simulate=True).run("status")
    tools = ToolPassportFunctionCalling(simulate=True).get_openai_tools()
    agents = default_lattice_agents(tools)
    report = {
        "status": "READY_FOR_LOCAL_OPENAI_INTEROP" if hygiene["present"].get("OPENAI_API_KEY") == "PRESENT" else "READY_FOR_SIM_AND_CI__SET_OPENAI_API_KEY_FOR_LIVE",
        "modules": {
            "responses_spine": responses,
            "structured_schema": StructuredOutputSchemaSpine(simulate=True).__class__.__name__,
            "tool_passport": ToolPassportFunctionCalling(simulate=True).__class__.__name__,
            "tracing": OpenAITracingToGoldenTrace(simulate=True).__class__.__name__,
            "evals": EvalsBullshitOlympicsBridge(simulate=True).__class__.__name__,
        },
        "env": hygiene["present"],
        "agent_manifests": [a["name"] for a in agents],
        "next": "Run pytest, then set OPENAI_API_KEY locally and call ResponsesAPISpine(simulate=False).",
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
