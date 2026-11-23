"""Atlas Native Synthesis v0.1: offline, candidate-only, no external effects."""
__version__ = '0.1.0'
from .engine import NativeSynthesis, generic_hold
from .wire import WireError, strict_json, digest, canonical_json
from .catalog import CapabilityCatalog
