"""
OpenAI Interop Schemas (P2 spine in 12x12x12 lattice)
Core canonical types for maximum interop:
- RawSource: origin material (docs, code, claims, transcripts)
- ClaimPacket: signed, reviewable assertion (extends existing canon claim_packet)
- ToolPassport: portable tool capability descriptor with lattice address + scopes
- ActionLedger: append-only receipt of executed actions (GitHub public substrate)
- CodexTaskPacket: structured task for OpenAI Codex / o-series execution

All support:
- lattice_coords: (provider, capability, lifecycle) e.g. (2, 4, 0) for OpenAI Code/Observe
- epistemic_certainty
- provenance (source_id, hash)
- to_json_schema() for MCP / OpenAI structured outputs
- to_dict() / from_dict()

See release criteria: schema + code + test + demo + ActionLedger + gate + README + human approval.
"""

from .raw_source import RawSource
from .claim_packet import ClaimPacket
from .tool_passport import ToolPassport
from .action_ledger import ActionLedger, ActionEntry
from .codex_task_packet import CodexTaskPacket
from .missing_receipt import MissingReceipt
from .public_release_class import PublicReleaseClass

__all__ = [
    "RawSource",
    "ClaimPacket",
    "ToolPassport",
    "ActionLedger",
    "ActionEntry",
    "CodexTaskPacket",
    "MissingReceipt",
    "PublicReleaseClass",
]
