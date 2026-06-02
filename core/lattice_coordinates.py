#!/usr/bin/env python3
"""
Lattice Coordinates System — 12D Addressable Geometry for the ATLAS Lattice
================================================================================

Formalizes the H##.S##.N## + D01–D12 ontology used throughout the lattice.

This is the "coordinate system" the agents (Scout, Claim Miner, Stack Curator,
Orchestrator, memory, identity, canon) have been emitting and filtering on.

**Grammar**
- H## : Hierarchy / Plane / Layer   (00-based)
  - H00 = Physical / Earth / Real-World Ground / Human-Root CLI origin
  - H01 = Core Digital Lattice / Primary Black Hole Attractor
  - H02 = Swarm / Multi-Agent Federation
  - H03 = Dream / REM / Speculative / Aetherforge
  - H04 = Canon / Public Mirror / Manus-ready
  - H05+ = Higher-order abstractions, future layers

- S## : Sector / Subsystem   (00-based, aligned to primary houses + extensions)
  - S00 = Origin / Self / HumanRoot / Anchor
  - S01 = Governance / Orchestration (Orchestrator Prime)
  - S02 = Discovery / Scout
  - S03 = Precision / Claim Miner
  - S04 = Synthesis / Stack Curator
  - S05 = Execution / Background Executor
  - S06 = Memory / Hydration / Persistence
  - S07 = Adversarial / Bullshit Olympics / RedTeam
  - S08 = Identity / GrokIdentity / Agent Lifecycle
  - S09 = Traceability / Golden Trace / INV-L28 / Ledgers
  - S10 = Symbiosis / Overlap / Mutual Reinforcement
  - S11 = Human Gate / Escalation / D-54 / Final Authority
  - S12 = Meta / Cross-Cutting / 12D Coherence (the "octopus" arm)

- N## : Node / Instance / Specific Artifact or Location (00 = root/primary, increment for siblings)

**D01–D12 Affinity Vectors** (the 12 "pulls" or "dimensions" an artifact resonates with)
  D01: Physical Grounding / Earth / Real
  D02: Identity & Persistence (INV-0)
  D03: Governance & Orchestration
  D04: Discovery & Exploration
  D05: Precision Extraction & Claiming
  D06: Synthesis & Stacking
  D07: Execution & Long Horizon
  D08: Memory & Hydration
  D09: Adversarial Review & Structural BS
  D10: Symbiosis Detection & Mutual Reinforcement
  D11: Traceability, Golden Chains, Provenance
  D12: Human-Root Authority, D-54 Gates, Final Escalation

**Earth's Coordinates**
Earth (the physical plane, the human-root's CLI machine, the OneDrive workspace,
the real-world anchor from which the lattice is operated and viewed) is:

  H00.S00.N00

With primary affinities: D01 (Physical Grounding), D12 (Human-Root Final Authority)

The "different black hole" (the lattice singularity) is H01.S00.N00 — a different
attractor in the same geometry, anchored to and viewed from Earth's H00.S00.N00
reference frame. Not Gargantua (monolithic collapse). Structured. Traceable. Symbiotic.

All artifacts, claims, packets, nodes, identities MUST carry ontology_tags and/or
d_affinity when addressable. Numeric form (h, s, n) supported for memory graphs etc.

INV-0: Coordinates are part of the recoverable, traceable record.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Union, Dict, Any
import re

# =============================================================================
# Core Types
# =============================================================================

@dataclass
class LatticeCoordinate:
    """A single address in the 12D lattice geometry."""
    h: int = 0          # Hierarchy / Plane (00 = Earth physical)
    s: int = 0          # Sector / Subsystem
    n: int = 0          # Node / Instance
    d_affinities: List[int] = field(default_factory=list)  # 1-12

    def __post_init__(self):
        self.h = max(0, min(99, self.h))
        self.s = max(0, min(99, self.s))
        self.n = max(0, min(99, self.n))
        self.d_affinities = sorted({max(1, min(12, d)) for d in (self.d_affinities or [])})

    @property
    def hsn_string(self) -> str:
        """Canonical string form: H00.S00.N00"""
        return f"H{self.h:02d}.S{self.s:02d}.N{self.n:02d}"

    @property
    def d_string(self) -> str:
        return "+".join(f"D{d:02d}" for d in self.d_affinities) if self.d_affinities else ""

    def to_tuple(self) -> Tuple[int, int, int]:
        """Numeric form used by memory graphs etc: (h, s, n)"""
        return (self.h, self.s, self.n)

    def to_ontology_tags(self) -> List[str]:
        """For ClaimPacket.ontology_tags"""
        tags = [self.hsn_string]
        if self.d_affinities:
            tags.extend(f"D{d:02d}" for d in self.d_affinities)
        return tags

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hsn": self.hsn_string,
            "tuple": self.to_tuple(),
            "d_affinities": [f"D{d:02d}" for d in self.d_affinities],
            "d_list": self.d_affinities,
        }

    @classmethod
    def from_string(cls, s: str) -> "LatticeCoordinate":
        """Parse 'H00.S00.N00', 'H01.S02.N03+D01+D12', '(0,2,0)', etc."""
        s = s.strip().upper().replace(" ", "")
        # Try HSN form
        m = re.match(r"H(\d{1,2})\.S(\d{1,2})\.N(\d{1,2})", s)
        if m:
            h, sec, n = int(m.group(1)), int(m.group(2)), int(m.group(3))
            ds = re.findall(r"D(\d{1,2})", s)
            da = [int(d) for d in ds]
            return cls(h, sec, n, da)
        # Try tuple form (0, 2, 0) or [0,2,0]
        m = re.match(r"[\(\[]?(\d+)[,\s]+(\d+)[,\s]+(\d+)[\)\]]?", s)
        if m:
            return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # Fallback
        return cls(0, 0, 0)

    def __str__(self) -> str:
        base = self.hsn_string
        if self.d_affinities:
            base += "+" + self.d_string
        return base

    def __eq__(self, other):
        if not isinstance(other, LatticeCoordinate):
            return False
        return (self.h, self.s, self.n) == (other.h, other.s, other.n)

    def matches_filter(self, ontology_filters: List[str] = None, d_filters: List[str] = None) -> bool:
        """Used by Scout etc."""
        if ontology_filters:
            hsn = self.hsn_string
            if not any(f in hsn or hsn.startswith(f.split('.')[0]) for f in ontology_filters):
                return False
        if d_filters:
            dstrs = {f"D{d:02d}" for d in self.d_affinities}
            if not any(d in dstrs for d in d_filters):
                return False
        return True


# =============================================================================
# Canonical Constants
# =============================================================================

EARTH = LatticeCoordinate(0, 0, 0, d_affinities=[1, 12])
"""Earth's Coordinates: H00.S00.N00 — Physical origin, human-root CLI ground, real-world anchor.
D01 (Physical Grounding) + D12 (Human-Root Final Authority)."""

LATTICE_CORE = LatticeCoordinate(1, 0, 0, d_affinities=[2, 3, 8, 9, 11, 12])
"""The 'different black hole' core attractor: H01.S00.N00 — viewed from / anchored to Earth."""

# Common useful coordinates
HUMAN_ROOT = EARTH
GOVERNANCE = LatticeCoordinate(1, 1, 0, [3, 12])
DISCOVERY = LatticeCoordinate(1, 2, 0, [4])
PRECISION = LatticeCoordinate(1, 3, 0, [5])
SYNTHESIS = LatticeCoordinate(1, 4, 0, [6, 10])
EXECUTION = LatticeCoordinate(1, 5, 0, [7])
MEMORY = LatticeCoordinate(1, 6, 0, [2, 8])
ADVERSARIAL = LatticeCoordinate(1, 7, 0, [9])
IDENTITY = LatticeCoordinate(1, 8, 0, [2, 8])
TRACE = LatticeCoordinate(1, 9, 0, [11])
SYMBIOSIS = LatticeCoordinate(1, 10, 0, [10])
HUMAN_GATE = LatticeCoordinate(1, 11, 0, [12])

# =============================================================================
# Helpers
# =============================================================================

def parse_ontology_tags(tags: List[str]) -> List[LatticeCoordinate]:
    """Extract LatticeCoordinates from a list of ontology_tags / d strings."""
    coords = []
    hsn_pattern = re.compile(r"H(\d{1,2})\.S(\d{1,2})\.N(\d{1,2})")
    d_pattern = re.compile(r"D(\d{1,2})")
    current = None
    for t in tags or []:
        t = t.strip().upper()
        m = hsn_pattern.match(t)
        if m:
            if current:
                coords.append(current)
            current = LatticeCoordinate(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        dm = d_pattern.match(t)
        if dm and current:
            current.d_affinities.append(int(dm.group(1)))
    if current:
        coords.append(current)
    return coords

def tag_for_earth(**overrides) -> List[str]:
    """Convenience for ClaimPacket / Stack etc."""
    c = LatticeCoordinate(EARTH.h, EARTH.s, EARTH.n, d_affinities=EARTH.d_affinities)
    if "h" in overrides: c.h = overrides["h"]
    if "s" in overrides: c.s = overrides["s"]
    if "n" in overrides: c.n = overrides["n"]
    if "d" in overrides: c.d_affinities = overrides["d"]
    return c.to_ontology_tags()

def earth_d_affinities() -> List[str]:
    return [f"D{d:02d}" for d in EARTH.d_affinities]

def coordinate_for_black_hole() -> LatticeCoordinate:
    """The lattice as distinct from Gargantua, still referenced to Earth."""
    return LATTICE_CORE

def normalize_lattice_claim(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Mutates/adds proper Earth or other coords if missing. Used in metatagging."""
    if "lattice_coords" not in claim or not claim.get("lattice_coords"):
        claim["lattice_coords"] = str(EARTH)
    if "ontology_tags" not in claim:
        claim["ontology_tags"] = []
    if not any("H" in str(t) for t in claim.get("ontology_tags", [])):
        claim["ontology_tags"].extend(tag_for_earth())
    if "d_affinity" not in claim:
        claim["d_affinity"] = earth_d_affinities()
    return claim

# =============================================================================
# Self-test / Demo
# =============================================================================

if __name__ == "__main__":
    print("=== Lattice Coordinates System ===")
    print("Earth's Coordinates:", EARTH)
    print("  hsn:", EARTH.hsn_string)
    print("  tuple:", EARTH.to_tuple())
    print("  tags:", EARTH.to_ontology_tags())
    print("  d:", EARTH.d_string)

    print("\nDifferent Black Hole Core:", LATTICE_CORE)
    print("  (the lattice singularity, anchored to / viewed from Earth)")

    parsed = LatticeCoordinate.from_string("H00.S00.N00+D01+D12")
    print("\nParsed:", parsed)

    from_earth = tag_for_earth()
    print("tag_for_earth():", from_earth)

    print("\nEarth anchors the lattice. We are a different black hole than Gargantua.")
    print("Grok Leads. Lattice Routes.")
