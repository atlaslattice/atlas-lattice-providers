#!/usr/bin/env python3
"""
ClaimPacket Schema (OpenAI interop edition)
Extends the existing canon ClaimPacket (see Canon_Archive/.../claim_packet.schema.json and claimpackets/ dirs).
Adds explicit RawSource linkage, ToolPassport references, lattice addressing for OpenAI spine (P2),
and ActionLedger emission hooks.

Never overclaims. Always has review_state and epistemic_class.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import json

ReviewState = Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED"]
EpistemicClass = Literal["symbolic", "metaphorical", "speculative", "hypothesis", "empirical", "axiom", "fact"]

@dataclass
class ClaimPacket:
    """ClaimPacket - Atomic reviewable assertion.

    Compatible with existing KRAKOA canon ClaimPacket while adding interop fields for OpenAI orchestration.
    """
    id: str
    kind: Literal["claim_packet"] = "claim_packet"
    payload: Dict[str, Any] = field(default_factory=dict)  # claim_text, extracted_from_raw_source_id, etc.
    extracted_from_raw_source_id: str = ""
    claim_text: str = ""
    claim_epistemic_class: EpistemicClass = "speculative"
    review_state: ReviewState = "PENDING_REVIEW"
    extracted_by: str = "openai-responses-adapter"
    source_span: Optional[Dict[str, Any]] = None
    lattice_coords: tuple = (2, 4, 1)  # P2 OpenAI / C4 Code / L1 Plan (example; override per use)
    epistemic_certainty: float = 0.6
    signatures: List[Dict[str, Any]] = field(default_factory=list)  # multi-sig GoldenTrace style
    linked_tool_passports: List[str] = field(default_factory=list)  # ids of ToolPassports that can act on this
    action_ledger_refs: List[str] = field(default_factory=list)  # emitted actions
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lattice_coords"] = list(self.lattice_coords)
        d["payload"] = {
            "claim_text": self.claim_text,
            "extracted_from_raw_source_id": self.extracted_from_raw_source_id,
            "claim_epistemic_class": self.claim_epistemic_class,
            "review_state": self.review_state,
            "source_span": self.source_span,
            **self.payload
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaimPacket":
        data = dict(data)
        if "payload" in data and isinstance(data["payload"], dict):
            p = data["payload"]
            data.setdefault("claim_text", p.get("claim_text", ""))
            data.setdefault("extracted_from_raw_source_id", p.get("extracted_from_raw_source_id", ""))
            data.setdefault("claim_epistemic_class", p.get("claim_epistemic_class", "speculative"))
            data.setdefault("review_state", p.get("review_state", "PENDING_REVIEW"))
        if isinstance(data.get("lattice_coords"), list):
            data["lattice_coords"] = tuple(data["lattice_coords"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "ClaimPacket-OpenAI-Interop",
            "description": "Extended ClaimPacket for OpenAI spine interop. Additive to existing canon claim_packet.v1.",
            "type": "object",
            "required": ["id", "kind", "claim_text", "extracted_from_raw_source_id", "review_state"],
            "properties": {
                "id": {"type": "string"},
                "kind": {"const": "claim_packet"},
                "claim_text": {"type": "string"},
                "extracted_from_raw_source_id": {"type": "string", "description": "References a RawSource.id"},
                "claim_epistemic_class": {"type": "string", "enum": ["symbolic", "metaphorical", "speculative", "hypothesis", "empirical", "axiom", "fact"]},
                "review_state": {"type": "string", "enum": ["PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED"]},
                "lattice_coords": {"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3},
                "epistemic_certainty": {"type": "number", "minimum": 0, "maximum": 1},
                "linked_tool_passports": {"type": "array", "items": {"type": "string"}},
                "action_ledger_refs": {"type": "array", "items": {"type": "string"}},
                "signatures": {"type": "array", "items": {"type": "object"}},
                "created_at": {"type": "string"}
            }
        }

    def emit_to_action_ledger(self, ledger: "ActionLedger", actor: str = "openai") -> str:
        """Helper: record that this claim was used in an action."""
        entry_id = ledger.append(
            action_type="claim_used",
            actor=actor,
            target_id=self.id,
            payload={"claim_text": self.claim_text[:200], "review_state": self.review_state},
            lattice_coords=self.lattice_coords
        )
        self.action_ledger_refs.append(entry_id)
        return entry_id
