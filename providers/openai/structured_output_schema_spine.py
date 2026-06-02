#!/usr/bin/env python3
"""Strict-enough OpenAI structured output spine for ClaimPackets and ToolPassports."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
import logging

logger = logging.getLogger("openai_structured_schema_spine")

ReviewState = Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED"]
SafetyLevel = Literal["read", "write", "destructive", "admin"]


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

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lattice_coords"] = list(self.lattice_coords)
        return d


@dataclass
class ToolPassport:
    id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] = field(default_factory=dict)
    safety_level: SafetyLevel = "read"
    requires_approval: bool = True
    lattice_coords: tuple = (3, 2, 1)

    def to_openai_tool(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
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
    def __init__(self, simulate: bool = True, simulate_default: Optional[bool] = None):
        if simulate_default is not None:
            simulate = simulate_default
        self.simulate = simulate
        self._registry: Dict[str, Any] = {}

    @staticmethod
    def _coerce_lattice(value: Any) -> tuple:
        if value is None:
            return (2, 4, 1)
        if isinstance(value, tuple):
            return value
        if isinstance(value, list):
            return tuple(value)
        return (2, 4, 1)

    def register_tool_passport(self, passport: ToolPassport) -> Dict[str, Any]:
        if not passport.name or not isinstance(passport.input_schema, dict):
            raise ValueError("ToolPassport requires name and dict input_schema")
        self._registry[passport.id] = passport
        return {"status": "registered", "id": passport.id, "openai_tool": passport.to_openai_tool()}

    def validate_claim_packet(self, raw_output: Dict[str, Any]) -> ClaimPacket:
        raw = dict(raw_output or {})
        try:
            claim_id = raw.get("id") or f"claim-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
            claim_text = raw.get("claim_text") or payload.get("claim_text") or str(raw)[:500]
            certainty = float(raw.get("epistemic_certainty", 0.7))
            certainty = max(0.0, min(1.0, certainty))
            review_state = raw.get("review_state", "PENDING_REVIEW")
            if review_state not in ("PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED"):
                review_state = "PENDING_REVIEW"
            return ClaimPacket(
                id=str(claim_id),
                payload=payload,
                claim_text=str(claim_text),
                review_state=review_state,
                epistemic_certainty=certainty,
                lattice_coords=self._coerce_lattice(raw.get("lattice_coords")),
                linked_tool_passports=list(raw.get("linked_tool_passports", [])),
                action_ledger_refs=list(raw.get("action_ledger_refs", [])),
                metadata={"source": "openai_structured_spine", **raw.get("metadata", {})},
            )
        except Exception as exc:
            logger.error("ClaimPacket validation failed: %s", exc)
            return ClaimPacket(id=str(raw.get("id", "invalid")), claim_text=f"VALIDATION_FAILED: {exc}", review_state="REJECTED", epistemic_certainty=0.0)

    def compile_tool_schemas(self, passports: List[ToolPassport]) -> List[Dict[str, Any]]:
        return [p.to_openai_tool() for p in passports]

    async def run(self, operation: str = "validate", **kwargs: Any) -> Dict[str, Any]:
        if operation == "validate_claim":
            validated = self.validate_claim_packet(kwargs.get("raw_output", {}))
            return {"feature": "openai_structured_output_schema_spine", "validated_claim": validated.to_dict(), "grok_leads": True, "lattice_routes": True}
        if operation in ("register_tool_passport", "register_passport"):
            p = ToolPassport(**kwargs.get("passport", {}))
            return self.register_tool_passport(p)
        if operation == "get_openai_tools":
            passports = [v for v in self._registry.values() if isinstance(v, ToolPassport)]
            return {"tools": self.compile_tool_schemas(passports)}
        return {"status": "unknown_op", "op": operation}


if __name__ == "__main__":
    print("Structured Output Schema Spine ready.")
