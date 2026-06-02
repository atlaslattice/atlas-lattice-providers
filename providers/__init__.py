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

