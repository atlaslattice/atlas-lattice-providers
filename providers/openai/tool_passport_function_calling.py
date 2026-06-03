#!/usr/bin/env python3
"""Governed OpenAI function/tool calling via ToolPassports."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger("openai_tool_passport")

try:
    from .structured_output_schema_spine import StructuredOutputSchemaSpine, ToolPassport
except Exception:
    from providers.openai.structured_output_schema_spine import StructuredOutputSchemaSpine, ToolPassport

Executor = Callable[[str, Dict[str, Any]], Any]


class ToolPassportFunctionCalling:
    def __init__(self, schema_spine: Optional[StructuredOutputSchemaSpine] = None, ledger: Any = None, executor: Optional[Executor] = None, simulate: bool = True, simulate_default: Optional[bool] = None):
        if simulate_default is not None:
            simulate = simulate_default
        self.schema_spine = schema_spine or StructuredOutputSchemaSpine(simulate=simulate)
        self.ledger = ledger
        self.executor = executor
        self.simulate = simulate
        self._passports: Dict[str, ToolPassport] = {}

    def register_passport(self, passport: ToolPassport) -> Dict[str, Any]:
        self._passports[passport.name] = passport
        self._passports[passport.id] = passport
        return self.schema_spine.register_tool_passport(passport)

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        unique = {p.id: p for p in self._passports.values()}.values()
        return self.schema_spine.compile_tool_schemas(list(unique))

    def _ledger_emit(self, passport: ToolPassport, arguments: Dict[str, Any], actor: str) -> None:
        if not self.ledger:
            return
        try:
            if hasattr(self.ledger, "append"):
                self.ledger.append(action_type="openai_tool_call", actor=actor, target_id=passport.id, payload={"arguments": arguments, "safety_level": passport.safety_level}, lattice_coords=passport.lattice_coords)
            elif hasattr(self.ledger, "emit"):
                self.ledger.emit("openai_tool_call", {"actor": actor, "target_id": passport.id, "arguments": arguments, "safety_level": passport.safety_level})
        except Exception as exc:
            logger.warning("ActionLedger emission failed: %s", exc)

    async def execute_governed_tool(self, tool_name: str, arguments: Dict[str, Any], actor: str = "openai", approved: bool = False) -> Dict[str, Any]:
        passport = self._passports.get(tool_name)
        if not passport:
            return {"error": "unknown_tool_passport", "tool": tool_name}
        if passport.safety_level in ("destructive", "admin") and not approved:
            return {"status": "requires_human_approval", "passport": passport.id, "safety_level": passport.safety_level}
        self._ledger_emit(passport, arguments, actor)
        if self.executor and not self.simulate:
            result_payload = self.executor(passport.name, arguments)
        else:
            result_payload = {"simulated_output": f"Executed {passport.name} with {list(arguments.keys())}"}
        return {"status": "executed" if not self.simulate else "simulated", "tool": passport.name, "arguments": arguments, "result": result_payload, "timestamp": datetime.utcnow().isoformat() + "Z"}

    async def run(self, operation: str = "get_tools", **kwargs: Any) -> Dict[str, Any]:
        if operation == "get_tools":
            return {"feature": "openai_tool_passport_function_calling", "openai_tools": self.get_openai_tools(), "grok_leads": True}
        if operation == "execute":
            return await self.execute_governed_tool(kwargs.get("tool_name"), kwargs.get("arguments", {}), kwargs.get("actor", "openai"), kwargs.get("approved", False))
        if operation in ("register_passport", "register_tool_passport"):
            return self.register_passport(ToolPassport(**kwargs.get("passport", {})))
        return {"error": "unknown_operation", "operation": operation}


if __name__ == "__main__":
    print("ToolPassport Function Calling ready.")
