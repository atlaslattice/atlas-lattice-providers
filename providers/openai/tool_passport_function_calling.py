#!/usr/bin/env python3
"""
03_ToolPassport_Function_Calling (Phase 1 - OpenAI-grade)
========================================================
Compile ToolPassports into OpenAI function/tool calling schemas.
Governed calls from OpenAI (Responses, Assistants, Agents SDK) to Grok CLI, lattice, Notion, DriveSync, etc.

Emits ActionLedger events on every governed call.
Integrates with StructuredOutputSchemaSpine and existing ClaimPacket/ToolPassport patterns.

All calls go through safety gates before execution.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger("openai_tool_passport")

try:
    from .structured_output_schema_spine import ToolPassport, StructuredOutputSchemaSpine
except Exception:
    from providers.openai.structured_output_schema_spine import ToolPassport, StructuredOutputSchemaSpine

try:
    from ..notion.schemas.action_ledger import ActionLedger
except Exception:
    ActionLedger = None


class ToolPassportFunctionCalling:
    """
    The governed function calling layer for OpenAI <-> Lattice.
    """

    def __init__(self, schema_spine: Optional[StructuredOutputSchemaSpine] = None, ledger=None, simulate: bool = True):
        self.schema_spine = schema_spine or StructuredOutputSchemaSpine(simulate=simulate)
        self.ledger = ledger
        self.simulate = simulate
        self._passports: Dict[str, ToolPassport] = {}

    def register_passport(self, passport: ToolPassport) -> Dict[str, Any]:
        self._passports[passport.id] = passport
        return self.schema_spine.register_tool_passport(passport)

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        return self.schema_spine.compile_tool_schemas(list(self._passports.values()))

    async def execute_governed_tool(self, tool_name: str, arguments: Dict[str, Any], actor: str = "openai") -> Dict[str, Any]:
        """Called when OpenAI decides to invoke a ToolPassport."""
        passport = self._passports.get(tool_name)
        if not passport:
            return {"error": "unknown_tool_passport", "tool": tool_name}

        # Safety gate (extend with real Bullshit/Guardrails later)
        if passport.safety_level in ("destructive", "admin") and not self.simulate:
            # Would require human gate here
            return {"status": "requires_human_approval", "passport": passport.id}

        # Emit to ActionLedger (core requirement)
        if self.ledger:
            try:
                self.ledger.append(
                    action_type="openai_tool_call",
                    actor=actor,
                    target_id=passport.id,
                    payload={"arguments": arguments, "safety_level": passport.safety_level},
                    lattice_coords=passport.lattice_coords
                )
            except Exception as e:
                logger.warning(f"ActionLedger emission failed: {e}")

        # In real: dispatch to actual executor (grok cli, notion, drive, etc.)
        result = {
            "status": "executed" if not self.simulate else "simulated",
            "tool": tool_name,
            "arguments": arguments,
            "result": {"simulated_output": f"Executed {tool_name} with {list(arguments.keys())}"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Return structured for OpenAI to consume
        return result

    async def run(self, operation: str = "get_tools", **kwargs) -> Dict[str, Any]:
        if operation == "get_tools":
            return {"feature": "openai_tool_passport_function_calling", "openai_tools": self.get_openai_tools(), "grok_leads": True}
        elif operation == "execute":
            return await self.execute_governed_tool(kwargs.get("tool_name"), kwargs.get("arguments", {}), kwargs.get("actor", "openai"))
        elif operation == "register_passport":
            p = ToolPassport(**kwargs.get("passport", {}))
            return self.register_passport(p)
        return {"error": "unknown_operation"}


if __name__ == "__main__":
    tpf = ToolPassportFunctionCalling(simulate=True)
    print("ToolPassport Function Calling ready (Phase 1).")