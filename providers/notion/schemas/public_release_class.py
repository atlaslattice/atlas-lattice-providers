#!/usr/bin/env python3
"""PublicReleaseClass - Python dataclass for public_release_class.schema.json"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime

@dataclass
class PublicReleaseClass:
    id: str
    kind: Literal["public_release_class"] = "public_release_class"
    target_id: str = ""
    release_class: Literal["internal", "preview", "public", "canon_candidate"] = "internal"
    criteria_status: Dict[str, bool] = field(default_factory=lambda: {
        "code_exists": False,
        "schema_exists": False,
        "test_exists": False,
        "demo_exists": False,
        "action_ledger_emits": False,
        "release_gate_passes": False,
        "readme_explains_boundary": False,
        "human_root_approved": False
    })
    lattice_coords: tuple = (2, 8, 8)
    gitHub_pr_url: Optional[str] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lattice_coords"] = list(self.lattice_coords)
        return d

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        import json
        with open("public_release_class.schema.json") as f:
            return json.load(f)

    def is_fully_released(self) -> bool:
        return all(self.criteria_status.values())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PublicReleaseClass":
        data = dict(data)
        if isinstance(data.get("lattice_coords"), list):
            data["lattice_coords"] = tuple(data["lattice_coords"])
        return cls(**data)
