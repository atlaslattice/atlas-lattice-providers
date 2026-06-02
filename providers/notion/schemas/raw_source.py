#!/usr/bin/env python3
"""
RawSource Schema
The atomic origin unit. Everything (claims, tasks, evals) is extracted from a RawSource.
Additive to existing canon (see claim_packet.schema.json which references extracted_from_raw_source_id).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import json
import hashlib

@dataclass
class RawSource:
    """RawSource - provenance root for interop.

    Examples:
    - Google Doc / Drive file
    - GitHub issue / PR / file at commit
    - Microsoft SharePoint / OneDrive doc
    - Transcript from Copilot / Grok session
    - OpenAI conversation or eval dataset
    """
    id: str
    uri: str  # canonical locator (gs://, https://github.com/..., onedrive://, etc.)
    content_hash: str  # sha256 of content at extraction time
    kind: Literal["document", "code", "transcript", "issue", "dataset", "other"] = "document"
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    lattice_coords: tuple = (2, 2, 0)  # default P2(OpenAI)-C2(Drive/Storage)-L0(Observe) or adjusted per source
    epistemic_certainty: float = 1.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lattice_coords"] = list(self.lattice_coords)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RawSource":
        data = dict(data)
        if isinstance(data.get("lattice_coords"), list):
            data["lattice_coords"] = tuple(data["lattice_coords"])
        return cls(**data)

    def content_fingerprint(self, content: str) -> str:
        return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def json_schema() -> Dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "RawSource",
            "description": "Atomic origin material. All ClaimPackets, ToolPassports, and tasks are derived from a RawSource.",
            "type": "object",
            "required": ["id", "kind", "uri", "content_hash"],
            "properties": {
                "id": {"type": "string"},
                "kind": {"type": "string", "enum": ["document", "code", "transcript", "issue", "dataset", "other"]},
                "uri": {"type": "string", "description": "Stable locator (Drive, GitHub, OneDrive, etc.)"},
                "content_hash": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
                "extracted_at": {"type": "string"},
                "metadata": {"type": "object"},
                "lattice_coords": {"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3},
                "epistemic_certainty": {"type": "number", "minimum": 0, "maximum": 1},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }

    def validate(self) -> bool:
        # minimal
        return bool(self.id and self.uri and self.content_hash.startswith("sha256:"))
