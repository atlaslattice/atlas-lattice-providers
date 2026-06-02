#!/usr/bin/env python3
"""
ActionLedger + ActionEntry
Append-only public receipt log (GitHub as substrate, also local + A2A).
Every real integration MUST emit to ActionLedger (release criterion #5).

Ties to existing A2A Requests/Responses/ and claimpackets.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib
from pathlib import Path

@dataclass
class ActionEntry:
    id: str
    ts: str
    action_type: str  # e.g. "tool_call", "claim_approved", "codex_execution", "cross_vendor_handoff"
    actor: str
    target_id: str  # ClaimPacket id, ToolPassport id, RawSource id, etc.
    payload: Dict[str, Any]
    lattice_coords: tuple
    prev_hash: Optional[str] = None
    hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        h = hashlib.sha256()
        h.update((self.prev_hash or "GENESIS").encode())
        h.update(self.ts.encode())
        h.update(self.action_type.encode())
        h.update(self.actor.encode())
        h.update(self.target_id.encode())
        h.update(json.dumps(self.payload, sort_keys=True).encode())
        h.update(str(self.lattice_coords).encode())
        return "0x" + h.hexdigest()[:32]

@dataclass
class ActionLedger:
    """Append-only ledger. In production: emit to GitHub (as receipt), local JSONL, and A2A."""
    entries: List[ActionEntry] = field(default_factory=list)
    log_path: Optional[Path] = None

    def append(self, action_type: str, actor: str, target_id: str, payload: Dict[str, Any],
               lattice_coords: tuple, metadata: Optional[Dict[str, Any]] = None) -> str:
        prev = self.entries[-1].hash if self.entries else None
        entry = ActionEntry(
            id=f"act-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            ts=datetime.utcnow().isoformat() + "Z",
            action_type=action_type,
            actor=actor,
            target_id=target_id,
            payload=payload,
            lattice_coords=lattice_coords,
            prev_hash=prev,
            metadata=metadata or {}
        )
        entry.hash = entry.compute_hash()
        self.entries.append(entry)

        if self.log_path:
            self._persist(entry)

        return entry.id

    def _persist(self, entry: ActionEntry):
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict() if hasattr(entry, 'to_dict') else asdict(entry), ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, log_path: Path) -> "ActionLedger":
        ledger = cls(log_path=log_path)
        if log_path.exists():
            with open(log_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # reconstruct
                        if isinstance(data.get("lattice_coords"), list):
                            data["lattice_coords"] = tuple(data["lattice_coords"])
                        ledger.entries.append(ActionEntry(**data))
        return ledger

    def to_dict(self) -> Dict[str, Any]:
        return {"count": len(self.entries), "last_hash": self.entries[-1].hash if self.entries else None}

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return {
            "title": "ActionLedger",
            "description": "Append-only ledger of all cross-vendor actions. GitHub is the public shelf. Required for release.",
            "type": "object"
        }
