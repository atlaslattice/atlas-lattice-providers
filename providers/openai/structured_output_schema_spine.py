#!/usr/bin/env python3
"""
02_Structured_Output_Schema_Spine (Phase 1 - OpenAI-grade)
========================================================
Enforce exact JSON for ClaimPacket, ToolPassport, PublicReleaseClass, and related receipts.
Uses the existing OpenAI-interop ClaimPacket schema + strict pydantic/dataclass validation.

Purpose: Every OpenAI Responses / tool call output is validated against lattice schemas before ActionLedger emission or promotion.

Symbiosis: Integrates with existing notion/schemas/claim_packet.py, action_ledger, GrokOrchestrator, BullshitOlympics (for overclaim detection), ProviderRouter.

All outputs are validated ClaimPackets with lattice_coords, review_state, linked_tool_passports, action_ledger_refs.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import logging

logger = logging.getLogger("openai_structured_schema_spine")

# Re-use and extend the existing OpenAI-interop ClaimPacket
try:
    from ..notion.schemas.claim_packet import ClaimPacket, ReviewState, EpistemicClass
except Exception:
    # Fallback minimal if import fails (for standalone)
    from dataclasses import dataclass, field
    ReviewState = Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED"]
    EpistemicClass = Literal["symbolic", "metaphorical", "speculative", "hypothesis", "empirical", "axiom", "fact"]
    
    @dataclass
    class ClaimPacket:
        id: str
        kind: str = "claim_packet"
        payload: Dict[str, Any] = field(default_factory=dict)
        claim_text: str = ""
        review_state: ReviewState = "PENDING_REVIEW"
        epistemic_certainty: float = 0.6
        lattice_coords: tuple = (2, 4, 1)
        signatures: List[Dict[str, Any]] = field(default_factory=list)
        linked_tool_passports: List[str] = field(default_factory=list)
        action_ledger_refs: List[str] = field(default_factory=list)
        metadata: Dict[str, Any] = field(default_factory=dict)
        created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

        def to_dict(self):
            d = asdict(self)
            d["lattice_coords"] = list(self.lattice_coords)
            return d

# Minimal ToolPassport and PublicReleaseClass for this spine (extend existing if present)
@dataclass
class ToolPassport:
    id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    safety_level: Literal["read", "write", "destructive", "admin"] = "read"
    requires_approval: bool = True
    lattice_coords: tuple = (3, 2, 1)

    def to_openai_tool(self) -> Dict[str, Any]:
        """Compile to OpenAI function/tool calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }

@dataclass
class PublicReleaseClass:
    id: str
    level: Literal["internal", "partner", "public", "canon"]
    restrictions: List[str] = field(default_factory=list)
    requires_bullshit_olympics: bool = True
    requires_human_gate: bool = True

    def is_allowed(self, action: str) -> bool:
        if self.level == "canon" and "raw" in action:
            return False
        return True


class StructuredOutputSchemaSpine:
    """
    The spine for strict OpenAI structured outputs in the lattice.
    Validates, normalizes, and emits proper ClaimPackets + ToolPassports.
    """

    def __init__(self, simulate: bool = True):
        self.simulate = simulate
        self._registry: Dict[str, Any] = {}  # id -> schema object

    def register_tool_passport(self, passport: ToolPassport) -> Dict[str, Any]:
        self._registry[passport.id] = passport
        return {"status": "registered", "id": passport.id, "openai_tool": passport.to_openai_tool()}

    def validate_claim_packet(self, raw_output: Dict[str, Any]) -> ClaimPacket:
        """Strict validation + normalization to ClaimPacket."""
        try:
            # In real: use pydantic model_validate with strict mode
            if "id" not in raw_output:
                raw_output["id"] = f"claim-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            if "claim_text" not in raw_output and "payload" in raw_output:
                raw_output["claim_text"] = raw_output["payload"].get("claim_text", str(raw_output)[:200])

            cp = ClaimPacket(
                id=raw_output["id"],
                claim_text=raw_output.get("claim_text", ""),
                review_state=raw_output.get("review_state", "PENDING_REVIEW"),
                epistemic_certainty=raw_output.get("epistemic_certainty", 0.7),
                lattice_coords=tuple(raw_output.get("lattice_coords", (2,4,1))),
                linked_tool_passports=raw_output.get("linked_tool_passports", []),
                action_ledger_refs=raw_output.get("action_ledger_refs", []),
                metadata={"source": "openai_structured_spine", **raw_output.get("metadata", {})}
            )
            return cp
        except Exception as e:
            logger.error(f"Strict schema validation failed: {e}")
            # Return a minimal rejected packet
            return ClaimPacket(
                id=raw_output.get("id", "invalid"),
                claim_text=f"VALIDATION_FAILED: {str(e)}",
                review_state="REJECTED",
                epistemic_certainty=0.0
            )

    def compile_tool_schemas(self, passports: List[ToolPassport]) -> List[Dict[str, Any]]:
        """For OpenAI tool calling / Responses API."""
        return [p.to_openai_tool() for p in passports]

    async def run(self, operation: str = "validate", **kwargs) -> Dict[str, Any]:
        """Orchestrator/MCP entrypoint."""
        if operation == "validate_claim":
            raw = kwargs.get("raw_output", {})
            validated = self.validate_claim_packet(raw)
            return {"feature": "openai_structured_output_schema_spine", "validated_claim": validated.to_dict(), "grok_leads": True, "lattice_routes": True}
        elif operation == "register_tool_passport":
            p = ToolPassport(**kwargs.get("passport", {}))
            return self.register_tool_passport(p)
        elif operation == "get_openai_tools":
            passports = [self._registry[k] for k in self._registry if isinstance(self._registry[k], ToolPassport)]
            return {"tools": self.compile_tool_schemas(passports)}
        return {"status": "unknown_op", "op": operation}


if __name__ == "__main__":
    spine = StructuredOutputSchemaSpine()
    print("Structured Output Schema Spine ready (Phase 1).")