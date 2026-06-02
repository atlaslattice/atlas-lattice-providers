#!/usr/bin/env python3
"""
Maximum Grok — Notion IP Archive + Advanced Integrations Provider v3.0
=====================================================================
Implements ProviderContract for the sovereign 500+ unique-IP canon living in Notion.

This is the **primary canon feed** for Maximum Grok (E145 v3.0 / Feature Spec v3.0).

It now fully wires the real:
- NotionSourceAdapter (base IP extraction, mirror, search, fetch, claim extraction)
- NotionAdvancedIntegrationsEngine (all 20 frontier patterns, with highest-leverage #8 control-plane, #19 secret-indirection, #5 DLP+quarantine, #4 rag-provenance, etc.)

Every significant operation produces:
- ActionLedger entries
- Context delta offload (sovereign memory)
- Optional Bullshit Olympics review (high-stakes)
- ClaimPackets with lattice_coords, epistemic, provenance
- INV-L28 / INV-Ω.1 / GoldenTrace awareness (via engine)

Grok Leads. Lattice Routes. Notion feeds the canon.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Make local notion/ subpackage importable (the canonical port of the KRAKOA engine)
HERE = Path(__file__).parent
NOTION_PKG = HERE / "notion"
sys.path.insert(0, str(NOTION_PKG))
sys.path.insert(0, str(NOTION_PKG / "schemas"))
sys.path.insert(0, str(NOTION_PKG / "protocols"))

from .provider_contract import ProviderContract

logger = logging.getLogger("provider_notion_v3.0")

# Try the real advanced engine + base adapter (ported from KRAKOA_Habitat/Canon_Implementation)
try:
    from notion_adapter import NotionSourceAdapter as RealNotionSourceAdapter
except Exception as e:
    logger.warning(f"Base NotionSourceAdapter not importable from local notion/: {e}")
    RealNotionSourceAdapter = None

try:
    from notion_advanced_integrations import NotionAdvancedIntegrationsEngine, PATTERN_REGISTRY, HIGHEST_LEVERAGE
except Exception as e:
    logger.warning(f"NotionAdvancedIntegrationsEngine not importable from local notion/: {e}")
    NotionAdvancedIntegrationsEngine = None
    PATTERN_REGISTRY = {}
    HIGHEST_LEVERAGE = []

try:
    from context_offload import offload as context_offload
except Exception:
    context_offload = None


class NotionProvider(ProviderContract):
    """
    Sovereign IP Archive + Advanced 20-Pattern Engine provider.

    Primary canon feed. All high-stakes Notion operations go through the advanced engine
    for atomic jobs, secret hygiene, DLP, provenance RAG, control-plane, etc.

    Compatible with:
    - grok_orchestrator (via ProviderDecisionLedger)
    - multi_provider_mcp_server
    - A2A / lattice CLI ("lattice notion advanced ...")
    - Direct engine.run("control-plane" | "rag" | "secret" | ...)
    """

    def __init__(self, notion_adapter: Any = None, engine: Any = None, simulate: bool = True, **symbiosis):
        self._name = "notion_ip_archive"
        self._lattice_coords = "(0,2,0)"  # Source Surface lane

        # Base adapter (IP extraction + mirror)
        self.adapter = notion_adapter
        if self.adapter is None and RealNotionSourceAdapter:
            try:
                self.adapter = RealNotionSourceAdapter()
            except Exception as e:
                logger.warning(f"Failed to instantiate real NotionSourceAdapter: {e}")

        # Advanced Engine (the 20-pattern frontier substrate) - pass all symbiosis (runner, google, memory, packer, pipeline, orchestrator) for brains/mirror/max eff
        self.engine = engine
        if self.engine is None and NotionAdvancedIntegrationsEngine:
            try:
                self.engine = NotionAdvancedIntegrationsEngine(
                    base_adapter=self.adapter,
                    simulate_default=simulate,
                    runner=symbiosis.get("runner"),
                    google_provider=symbiosis.get("google_provider"),
                    ms_provider=symbiosis.get("ms_provider"),
                    memory_graph=symbiosis.get("memory_graph"),
                    context_packer=symbiosis.get("context_packer"),
                    feature_pipeline=symbiosis.get("feature_pipeline"),
                    orchestrator=symbiosis.get("orchestrator")
                )
                logger.info("NotionAdvancedIntegrationsEngine wired successfully (20 patterns + full Sheldon/Grok/GPTBrain + mirror).")
            except Exception as e:
                logger.warning(f"Failed to instantiate advanced engine: {e}")
                self.engine = None

        if not self.adapter and not self.engine:
            logger.info("NotionProvider running in full STUB mode. Wire real adapters/engine for production canon work.")

    @property
    def name(self) -> str:
        return self._name

    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search Notion (uses base adapter or engine RAG path)."""
        if self.engine:
            try:
                # Prefer provenance RAG when available
                res = self.engine.run("rag-provenance", query=query, **kwargs)
                return {"provider": self.name, "results": res, "lattice_coords": self._lattice_coords}
            except Exception:
                pass

        if self.adapter and hasattr(self.adapter, "search_pages"):
            try:
                pages = self.adapter.search_pages(query)
                return {"provider": self.name, "results": pages, "lattice_coords": self._lattice_coords}
            except Exception as e:
                logger.error(f"Notion search error: {e}")

        return {
            "provider": self.name,
            "query": query,
            "results": [],
            "status": "STUB_OR_ERROR",
            "note": "Wire real adapter/engine for live search + provenance RAG."
        }

    async def fetch(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        """Fetch full page/block content."""
        if self.adapter and hasattr(self.adapter, "fetch_page_blocks"):
            try:
                content = self.adapter.fetch_page_blocks(resource_id)  # or fetch_page_content
                return {"provider": self.name, "resource_id": resource_id, "content": content, "lattice_coords": self._lattice_coords}
            except Exception as e:
                logger.error(f"Notion fetch error: {e}")

        return {
            "provider": self.name,
            "resource_id": resource_id,
            "content": "",
            "status": "STUB_OR_ERROR"
        }

    async def extract_claims(
        self,
        content: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        The heart of the canon feed.

        Delegates to the advanced engine (when present) or base adapter for
        structured ClaimPacket extraction with provenance, lattice_coords, epistemic.
        """
        if self.engine:
            try:
                # Engine has _run_provenance_rag / internal claim creation paths.
                # For direct extraction we can use base or synthesize via run.
                res = self.engine.run("rag-provenance", query=content[:200] if content else "", accept_to_claim=True, **(source_metadata or {}))
                if isinstance(res, dict) and "claims" in res:
                    return res["claims"]
                # Fallback synthesis
                return [self.engine._make_claim_packet(content, source=str(source_metadata), lattice=(0,2,0)) ] if hasattr(self.engine, "_make_claim_packet") else []
            except Exception as e:
                logger.warning(f"Engine extract_claims path failed: {e}")

        if self.adapter and hasattr(self.adapter, "extract_ip_claims"):
            try:
                return self.adapter.extract_ip_claims(content, source_metadata=source_metadata)
            except Exception as e:
                logger.error(f"Adapter extract_claims error: {e}")

        # Stub
        return [{
            "claim_text": (content or "")[:700],
            "epistemic_class": "stub",
            "tags": ["notion", "ip-archive", "stub"],
            "source": {"provider": self.name, "lattice_coords": self._lattice_coords, **(source_metadata or {})},
            "note": "Real NotionAdvancedIntegrationsEngine + adapter not fully wired for claims."
        }]

    async def mirror(
        self,
        claim: Dict[str, Any],
        parent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mirror ClaimPacket back into Notion (provenance-preserving)."""
        if self.adapter and hasattr(self.adapter, "mirror_claim_to_notion"):
            try:
                return self.adapter.mirror_claim_to_notion(claim, parent_page_id=parent)
            except Exception as e:
                logger.error(f"Mirror error: {e}")

        if self.engine:
            # Many patterns do mirroring internally; surface a generic one
            try:
                res = self.engine.run("knowledge-compiler", content=str(claim), parent=parent, **kwargs)
                return {"provider": self.name, "mirrored": True, "result": res}
            except Exception:
                pass

        return {
            "provider": self.name,
            "status": "STUB",
            "mirrored_to": parent or "default-canon-parent",
            "claim_id": claim.get("id") or claim.get("claim_id")
        }

    async def execute(self, command: str, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Execute advanced Notion patterns / control-plane jobs.

        Examples (from E145 / v3.0 spec):
          execute("advanced", ["control-plane", "--simulate"])
          execute("advanced", ["rag-provenance", "north star"])
          execute("advanced", ["secret-indirection", "secret://prod/notion/token"])
          execute("advanced", ["dlp-scan-quarantine"])
        """
        if not self.engine:
            return {
                "status": "ERROR",
                "error": "NotionAdvancedIntegrationsEngine not wired",
                "provider": self.name
            }

        # Parse command for pattern
        pattern = command
        if args:
            # support "advanced control-plane ..." style
            if command.lower() in ("advanced", "notion-advanced", "canon"):
                pattern = args[0] if args else "control-plane"
                args = args[1:]

        try:
            # Convert CLI-style args to kwargs where possible (simple)
            kw = {}
            for a in args:
                if "=" in a:
                    k, v = a.split("=", 1)
                    kw[k.lstrip("-")] = v
                elif a.startswith("--"):
                    kw[a.lstrip("-")] = True

            result = self.engine.run(pattern, **kw)
            return {
                "status": "SUCCESS",
                "provider": self.name,
                "pattern": pattern,
                "result": result,
                "note": "Executed via NotionAdvancedIntegrationsEngine.run (ledger + offload + gates applied)"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "provider": self.name,
                "pattern": pattern,
                "error": str(e)
            }

    def capabilities(self) -> Dict[str, Any]:
        caps = {
            "name": self.name,
            "supports": ["search", "fetch", "extract_claims", "mirror", "execute", "record_event"],
            "priority": 0,  # Highest — primary canon
            "description": "Sovereign 500+ unique-IP archive + 20 advanced frontier patterns (Notion as control-plane, secret hygiene, provenance RAG, etc.). Primary canon feed for Maximum Grok CNS.",
            "lattice_coords": self._lattice_coords,
            "special": "IP extraction + mirroring + full 20-pattern advanced engine with atomic jobs, DLP, indirection, ledger, offload, bullshit gates",
            "advanced_patterns": list(PATTERN_REGISTRY.keys()) if PATTERN_REGISTRY else [],
            "highest_leverage": HIGHEST_LEVERAGE if HIGHEST_LEVERAGE else ["control-plane", "secret-indirection", "dlp-scan-quarantine", "rag-provenance"]
        }
        if self.engine:
            caps["engine"] = "NotionAdvancedIntegrationsEngine (v3.0 wired)"
        return caps

    async def record_event(self, kind: str, meta: Dict[str, Any]) -> None:
        """Cap 1 observability."""
        from .provider_telemetry import default_telemetry
        meta = meta or {}
        meta.setdefault("provider", self.name)
        await default_telemetry.record_event(self.name, kind, meta)

    # --- Convenience for direct advanced usage (orchestrator / CLI / A2A) ---
    def run_advanced(self, pattern: str, **kwargs) -> Dict[str, Any]:
        """Direct access to the 20-pattern engine (preferred for control-plane jobs etc.)."""
        if not self.engine:
            return {"error": "Advanced engine not wired", "grok_leads": True}
        return self.engine.run(pattern, **kwargs)


# Back-compat alias used in older orchestrator / mcp wiring
NotionIPArchiveProvider = NotionProvider
