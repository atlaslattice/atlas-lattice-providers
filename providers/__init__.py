# Atlas Lattice Providers package (v3.0 — wired to Maximum Grok E145 + Feature Spec v3.0)
from .provider_contract import ProviderContract

# Primary canon feed (real engine now wired)
try:
    from .provider_notion import NotionProvider, NotionIPArchiveProvider
except Exception:
    NotionProvider = None
    NotionIPArchiveProvider = None

# Re-export advanced engine for direct use by orchestrator/CLI
try:
    from .notion.notion_advanced_integrations import NotionAdvancedIntegrationsEngine, PATTERN_REGISTRY, HIGHEST_LEVERAGE
except Exception:
    NotionAdvancedIntegrationsEngine = None
    PATTERN_REGISTRY = {}
    HIGHEST_LEVERAGE = []

# Microsoft Copilot 20 integrations
try:
    from .microsoft_copilot_integrations import MicrosoftCopilotIntegrations, COPILOT_INTEGRATIONS
except Exception:
    MicrosoftCopilotIntegrations = None
    COPILOT_INTEGRATIONS = {}

# E145 Project-Oriented 20 Features Engine
try:
    from .project_oriented_features import ProjectOrientedFeaturesEngine, PROJECT_FEATURES
except Exception:
    ProjectOrientedFeaturesEngine = None
    PROJECT_FEATURES = {}

# 20 Bleeding-edge Advanced Copilot Capabilities
try:
    from .advanced_capabilities_engine import AdvancedCapabilitiesEngine, ADVANCED_CAPABILITIES
except Exception:
    AdvancedCapabilitiesEngine = None
    ADVANCED_CAPABILITIES = {}

# Google Provider (now with full live Drive API + bridge token support)
try:
    from .provider_google import GoogleProvider
except Exception:
    GoogleProvider = None

# Google I/O 2026 + next 20 bleeding-edge (full 40+ Google features) now part of AdvancedCapabilitiesEngine (google_advanced / advanced_capability tools). All 60+ wired with ClaimPackets, symbiosis, ledgers.

# Maximum Grok v3.0 — 20 INV-L28-coherent 12D-aware GrokFeatureClaimPacket primitives (axiomatic elevation)
try:
    from .grok_maximum_features import GrokMaximumFeaturesEngine, GROK_MAX_FEATURES
except Exception:
    GrokMaximumFeaturesEngine = None
    GROK_MAX_FEATURES = {}

# UWS / Aluminum OS — Universal Workspace CLI + kernel for 12k-20k+ (~17k) unified features (Google/MS/Apple/etc. drivers)
try:
    from .uws_integrations import UwsIntegrations, UWS_INTEGRATIONS
except Exception:
    UwsIntegrations = None
    UWS_INTEGRATIONS = {}

