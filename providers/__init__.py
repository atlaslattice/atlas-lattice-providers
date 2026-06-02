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

# Bullshit Olympics (E145 Tier 1 #1 - Advanced multi-round adversarial) - FULL world-class impl
try:
    from .bullshit_olympics import BullshitOlympics, AdvancedBullshitOlympics, TruthClaimPacket, AdversarialPersona
except Exception:
    BullshitOlympics = None
    AdvancedBullshitOlympics = None
    TruthClaimPacket = None
    AdversarialPersona = None

# Legacy re-export for back-compat (delegates to advanced)
try:
    from .project_oriented_features import BullshitOlympics as LegacyBullshitOlympics
except Exception:
    LegacyBullshitOlympics = None

# GrokOrchestrator (E145 priority 1) - strong central brain (import direct to avoid package relative issues)
GrokOrchestrator = None
try:
    import grok_orchestrator as _go
    GrokOrchestrator = _go.GrokOrchestrator
except Exception:
    pass

# Tier 1 E145 modules (full implementations)
try:
    from .provider_router import ProviderRouter, RoutingDecision
except Exception:
    ProviderRouter = None
    RoutingDecision = None

try:
    from .uws_high_level import UwsHighLevel
except Exception:
    UwsHighLevel = None

try:
    from ..pipelines.feature_synthesis import FeatureSynthesisPipeline
except Exception:
    FeatureSynthesisPipeline = None

# New E145 20 modules (Tier 1/2 full + foundations)
try:
    from ..core.self_improvement_sandbox import RecursiveSelfImprovementSandbox
except Exception:
    RecursiveSelfImprovementSandbox = None

try:
    from .ensemble_reasoner import MultiModelEnsembleReasoner
except Exception:
    MultiModelEnsembleReasoner = None

try:
    from .project_memory_graph import LongHorizonProjectMemoryGraph
except Exception:
    LongHorizonProjectMemoryGraph = None

try:
    from ..core.formal_verifier import FormalVerifier
except Exception:
    FormalVerifier = None

try:
    from .self_debugger import AutonomousSelfDebugger
except Exception:
    AutonomousSelfDebugger = None

try:
    from ..modes.scientific_discovery import ScientificDiscoveryMode
except Exception:
    ScientificDiscoveryMode = None

try:
    from ..core.attestation import CryptographicAttestation
except Exception:
    CryptographicAttestation = None

try:
    from ..core.capability_synthesizer import DynamicCapabilitySynthesizer
except Exception:
    DynamicCapabilitySynthesizer = None

try:
    from ..core.hierarchical_goal_decomposer import HierarchicalGoalDecompositionEngine
except Exception:
    HierarchicalGoalDecompositionEngine = None

try:
    from .multi_modal_grounding import MultiModalGroundingEngine
except Exception:
    MultiModalGroundingEngine = None

try:
    from .resource_scheduler import ResourceAwareIntelligentScheduler
except Exception:
    ResourceAwareIntelligentScheduler = None

try:
    from .swarm_coordinator import EmergentSwarmCoordinator
except Exception:
    EmergentSwarmCoordinator = None

try:
    from .agent_reputation import PersistentAgentReputationSystem
except Exception:
    PersistentAgentReputationSystem = None

try:
    from .decision_replay import CounterfactualSimulator
except Exception:
    CounterfactualSimulator = None

# OpenAI-grade modules (Phase 1 foundational + more to come)
try:
    from .openai import (
        StructuredOutputSchemaSpine,
        ToolPassportFunctionCalling,
        OpenAITracingToGoldenTrace,
        EvalsBullshitOlympicsBridge,
        WorkloadIdentitySecretsHygiene,
        ToolPassport,
        ResponsesAPISpine,
    )
except Exception:
    StructuredOutputSchemaSpine = None
    ToolPassportFunctionCalling = None
    OpenAITracingToGoldenTrace = None
    EvalsBullshitOlympicsBridge = None
    WorkloadIdentitySecretsHygiene = None
    ToolPassport = None
    ResponsesAPISpine = None
    ResponsesAPISpine = None

