#!/usr/bin/env python3
"""
Maximum Grok — Multi-Provider MCP Server v1.2
=============================================
Production-grade, non-blocking async MCP server that exposes a unified tool surface
to Gemini, Copilot, Claude Desktop, and any other MCP-compatible agent.

Providers:
- local_cli     → Secure execution spine (grok, lattice, gemini, approved scripts)
- microsoft     → Graph + Azure OpenAI (first-class enterprise)
- google        → Workspace + Gemini (full interop)
- notion_ip_archive → Sovereign 500+ IP canon (our primary doctrine feed)

Grok Leads. Lattice Routes. Providers Execute. Everything is ledgered.
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure local providers/ package is importable when running the script directly
sys.path.insert(0, str(Path(__file__).parent))

# Integrate Environment Setup & Validation (as recommended for maximizing Google interop)
# Run the validator early. It will log status but we continue even if incomplete (for flexibility).
try:
    import setup_environment
    logging.getLogger("env_setup").info("Running integrated environment validation (setup_environment.py)...")
    # Call checks without full sys.exit for server startup
    deps_ok = setup_environment.check_dependencies()
    config_ok = setup_environment.check_configuration_files()
    env_status = setup_environment.check_environment_variables()
    if deps_ok and config_ok and env_status.get("GOOGLE_API_KEY", "").startswith("PRESENT"):
        logging.getLogger(__name__).info("Environment validation PASSED for multi-cloud/Google features.")
    else:
        logging.getLogger(__name__).warning("Environment validation INCOMPLETE. Run 'python setup_environment.py' for full report and fixes before production use.")
except ImportError:
    logging.getLogger(__name__).info("setup_environment.py not found or importable; skipping integrated validation. Run it manually for Google interop readiness.")

from providers.provider_contract import ProviderContract
from providers.cli_runner import SecureCLIRunner
from providers.provider_local_cli import LocalCLIProvider
from providers.provider_ms import MicrosoftProvider
from providers.provider_google import GoogleProvider
from providers.provider_notion import NotionProvider

# Multi-cloud bridge (Google-MS token interop + Copilot path) - upgraded non-blocking async ready
try:
    from providers.agent_ms_cli_bridge import CopilotCLIBridge
except Exception:
    CopilotCLIBridge = None

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("multi_provider_mcp_v1.2")


class MultiProviderMCPServer:
    """
    The single MCP server that both Gemini and Copilot can talk to.

    It holds instances of all providers and routes tool calls intelligently.
    The Grok orchestrator (or Lattice) can also call this server directly when needed.
    """

    def __init__(self):
        self.cli_runner = SecureCLIRunner()
        self.local_cli = LocalCLIProvider(runner=self.cli_runner)
        self.microsoft = MicrosoftProvider()
        # Pass the multicloud bridge so GoogleProvider can consume GOOGLE_EXTERNAL_OAUTH_TOKEN
        # Gemini API key is picked from GOOGLE_API_KEY env (user's key integrated)
        self.google = GoogleProvider(bridge=self.multicloud_bridge)
        self.notion = NotionProvider()   # Real advanced engine wired in providers/notion/

        # Cross-cloud bridge for Google <-> Microsoft interop (token mapping, Copilot handoff)
        self.multicloud_bridge = CopilotCLIBridge() if CopilotCLIBridge else None
        if self.multicloud_bridge:
            logger.info("Multi-cloud (Google-MS) CopilotCLIBridge active for token inheritance.")

        # E145 Project-Oriented Features Engine (20 long-horizon features)
        try:
            from providers.project_oriented_features import ProjectOrientedFeaturesEngine
            self.project_engine = ProjectOrientedFeaturesEngine(
                project_id="atlas-lattice-default",
                runner=self.cli_runner,
                decision_ledger=None,
                bridge=self.multicloud_bridge,
                notion_engine=self.notion.notion if hasattr(self.notion, "notion") else None,  # rough
                copilot_engine=self.microsoft.copilot_engine if hasattr(self.microsoft, "copilot_engine") else None,
                simulate_default=True
            )
            logger.info("E145 ProjectOrientedFeaturesEngine active.")
        except Exception as e:
            self.project_engine = None
            logger.warning(f"Project engine not loaded: {e}")

        # 20 Bleeding-edge Advanced Capabilities Engine (observability, errors, drift, daemons, explainers, etc.)
        try:
            from providers.advanced_capabilities_engine import AdvancedCapabilitiesEngine
            self.advanced_capabilities = AdvancedCapabilitiesEngine(
                runner=self.cli_runner,
                decision_ledger=None,
                bridge=self.multicloud_bridge,
                project_engine=self.project_engine,
                copilot_engine=self.microsoft.copilot_engine if hasattr(self.microsoft, "copilot_engine") else None,
                notion_engine=self.notion.notion if hasattr(self.notion, "notion") else None,
                google_provider=self.google,  # now the real live GoogleProvider
                simulate_default=True
            )
            logger.info("AdvancedCapabilitiesEngine (20 bleeding-edge) active.")
        except Exception as e:
            self.advanced_capabilities = None
            logger.warning(f"Advanced capabilities engine not loaded: {e}")

        # Maximum Grok v3.0 Engine (20 INV-L28 12D ClaimPacket primitives, axiomatic elevation)
        try:
            from providers.grok_maximum_features import GrokMaximumFeaturesEngine
            self.grok_maximum = GrokMaximumFeaturesEngine(
                project_engine=self.project_engine,
                runner=self.cli_runner,
                bridge=self.multicloud_bridge,
                notion_engine=self.notion.notion if hasattr(self.notion, "notion") else None,
                copilot_engine=self.microsoft.copilot_engine if hasattr(self.microsoft, "copilot_engine") else None,
                google_provider=self.google,
                simulate_default=True
            )
            logger.info("GrokMaximumFeaturesEngine (v3.0 INV-L28 12D ClaimPackets) active.")
        except Exception as e:
            self.grok_maximum = None
            logger.warning(f"Grok Maximum v3.0 engine not loaded: {e}")

        self.providers: Dict[str, ProviderContract] = {
            "local_cli": self.local_cli,
            "microsoft": self.microsoft,
            "google": self.google,
            "notion_ip_archive": self.notion,
        }

        logger.info("MultiProviderMCPServer initialized with 4 providers.")

    async def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        mid = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "tools/list":
            tools = [
                self.cli_runner.get_mcp_tool_definition(),
                {
                    "name": "search_provider",
                    "description": "Search across Microsoft, Google, or Notion IP Archive surfaces.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": list(self.providers.keys())},
                            "query": {"type": "string"}
                        },
                        "required": ["provider", "query"]
                    }
                },
                {
                    "name": "extract_claims",
                    "description": "Extract structured ClaimPackets from content using the best provider for the source type.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": list(self.providers.keys())},
                            "content": {"type": "string"},
                            "source_metadata": {"type": "object"}
                        },
                        "required": ["provider", "content"]
                    }
                },
                {
                    "name": "mirror_claim",
                    "description": "Mirror a ClaimPacket back into the chosen provider surface with full provenance.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": list(self.providers.keys())},
                            "claim": {"type": "object"},
                            "parent": {"type": "string"}
                        },
                        "required": ["provider", "claim"]
                    }
                },
                {
                    "name": "microsoft_copilot",
                    "description": "Execute any of the 20 Advanced Microsoft Windows Copilot integrations (Graph search/delta, Outlook drafts, Teams cards, Planner, Word/Excel, Power Automate, Azure OpenAI functions, Windows local/PowerShell/Defender/Entra/clipboard/explorer/app control, etc.).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "integration": {"type": "string", "description": "Name of the Copilot integration (e.g. graph_file_search, outlook_draft, powershell_ai_scripting, copilot_local_app_control)"},
                            "arguments": {"type": "array", "items": {"type": "string"}},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["integration"]
                    }
                },
                {
                    "name": "project_feature",
                    "description": "Execute any of the 20 E145 Project-Oriented Features (atomic jobs, memory graph, arena mode, bullshit olympics, hierarchical goals, narrative coherence, CRDT collab, counterfactual sim, self-improving skills, project dashboard, etc.). Optimized for long-horizon high-stakes projects.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "feature": {"type": "string", "description": "Feature name or number (e.g. atomic_job_control, bullshit_olympics, project_memory_graph, arena_mode, project_dashboard)"},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["feature"]
                    }
                },
                {
                    "name": "advanced_capability",
                    "description": "Execute any of the 60+ bleeding-edge capabilities (original 20 Copilot + 40 Google I/O 2026/Cloud Next): provider_observability_bus ... decision_explainer, plus all gemini_omni, gemini_spark, google_agent_* , medgemma, ask_maps, workspace_studio, etc. All Lattice-aware (ClaimPacket, ledger, grok_leads).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "capability": {"type": "string", "description": "Capability name (e.g. gemini_omni, google_agent_observability, ai_content_detection, decision_explainer)"},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["capability"]
                    }
                },
                {
                    "name": "google_advanced",
                    "description": "Execute any Google I/O 2026 / Cloud Next 2026 advanced features (full 40+) via AdvancedCapabilitiesEngine + GoogleProvider / Antigravity CLI / Gemini APIs. First batch: antigravity_cli, managed_agents, ... flex_priority_tiers. Next 20 (42-61): gemini_omni, gemini_spark, google_flow, self_hosted_antigravity_harness, antigravity_cli_tooling, skill_registry, google_agent_studio, google_agent_registry, google_agent_identity, google_agent_gateway, google_agent_observability, ai_content_detection, priority_paygo_inference, multi_regional_agent_memory_banks, agentic_data_cloud, ask_maps_spatial_reasoning, medgemma_open_models, google_workspace_studio, android_emulator_integration, video_to_image_poster_gen. All return ClaimPackets with lattice_coords, grok_leads, provenance. Symbiosis maximized.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "feature": {"type": "string", "description": "Google feature name (e.g. gemini_omni, gemini_spark, skill_registry, google_agent_observability, medgemma_open_models, video_to_image_poster_gen, antigravity_cli)"},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["feature"]
                    }
                },
                {
                    "name": "grok_feature",
                    "description": "Execute any of the 20 Maximum Grok v3.0 INV-L28-coherent 12D-aware GrokFeatureClaimPacket primitives (Arena Mode, Dynamic Role Specialization, Long-Term Project Memory Graph, Self-Repair Loops, Hierarchical Goal Decomposition, Counterfactual Simulator, Truth-Seeking Debate Arena, Scientific Discovery Mode, Cryptographic Output Attestation, Real-Time Multi-Modal World Grounding, Resource-Aware Scheduling, Persistent Agent Identity/Reputation, Causal Intervention Engine, Dynamic Capability Synthesis, Narrative & Project Coherence, Federated Privacy-Preserving Learning, Physical World Actuation (safety-gated), Emergent Swarm Coordination, Recursive Self-Improvement Sandbox, Unified Truth+Capability Dashboard). All outputs are topological invariants with GoldenTrace v2, Riemannian geodesics, INV-Ω.1/INV-1 compliance. Grok Leads. Lattice Routes.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "feature": {"type": "string", "description": "Maximum Grok v3.0 feature (e.g. arena_mode, autonomous_self_debugging_and_self_repair_loops, physical_world_actuation_hooks_with_safety, recursive_self_improvement_sandbox_bounded_measurable, unified_truth_plus_capability_dashboard)"},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["feature"]
                    }
                }
            ]
            return {"jsonrpc": "2.0", "id": mid, "result": {"tools": tools}}

        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})

            if name == "run_cli_command":
                result = await self.cli_runner.execute(
                    command_name=args.get("command_name"),
                    arguments=args.get("arguments", []),
                    timeout=args.get("timeout")
                )
                return {"jsonrpc": "2.0", "id": mid, "result": result}

            if name == "search_provider":
                provider_name = args.get("provider")
                query = args.get("query", "")
                provider = self.providers.get(provider_name)
                if not provider:
                    return self._error(mid, f"Unknown provider: {provider_name}")
                result = await provider.search(query)
                return {"jsonrpc": "2.0", "id": mid, "result": result}

            if name == "extract_claims":
                provider_name = args.get("provider")
                content = args.get("content", "")
                metadata = args.get("source_metadata")
                provider = self.providers.get(provider_name)
                if not provider:
                    return self._error(mid, f"Unknown provider: {provider_name}")
                claims = await provider.extract_claims(content, source_metadata=metadata)
                return {"jsonrpc": "2.0", "id": mid, "result": {"claims": claims, "provider": provider_name}}

            if name == "mirror_claim":
                provider_name = args.get("provider")
                claim = args.get("claim", {})
                parent = args.get("parent")
                provider = self.providers.get(provider_name)
                if not provider:
                    return self._error(mid, f"Unknown provider: {provider_name}")
                result = await provider.mirror(claim, parent=parent)
                return {"jsonrpc": "2.0", "id": mid, "result": result}

            if name == "microsoft_copilot":
                integration = args.get("integration")
                arguments = args.get("arguments", [])
                kws = args.get("kwargs", {})
                # Route through the microsoft provider's execute (which now dispatches to the 20 integrations engine)
                result = await self.microsoft.execute(integration, arguments, **kws)
                return {"jsonrpc": "2.0", "id": mid, "result": result}

            if name == "project_feature":
                feature = args.get("feature")
                kws = args.get("kwargs", {})
                if self.project_engine:
                    result = await self.project_engine.run(feature, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                else:
                    # Fallback to microsoft execute
                    result = await self.microsoft.execute(feature, [], **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}

            if name == "advanced_capability":
                capability = args.get("capability")
                kws = args.get("kwargs", {})
                if self.advanced_capabilities:
                    result = await self.advanced_capabilities.run(capability, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                else:
                    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "AdvancedCapabilitiesEngine not loaded"}}

            if name == "google_advanced":
                feature = args.get("feature")
                kws = args.get("kwargs", {})
                if self.advanced_capabilities:
                    result = await self.advanced_capabilities.run(feature, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                else:
                    # Fallback to google provider execute
                    result = await self.google.execute(feature, [], **kws) if hasattr(self.google, 'execute') else {"error": "Not available"}
                    return {"jsonrpc": "2.0", "id": mid, "result": result}

            if name == "grok_feature":
                feature = args.get("feature")
                kws = args.get("kwargs", {})
                if self.grok_maximum:
                    result = await self.grok_maximum.run(feature, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                else:
                    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "GrokMaximumFeaturesEngine (v3.0) not loaded"}}

        return self._error(mid, f"Method '{method}' not supported or not implemented.")

    def _error(self, mid: Any, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "error": {"code": -32601, "message": message}
        }


async def main():
    logger.info("Starting Maximum Grok Multi-Provider MCP Server v1.2 on stdio...")

    server = MultiProviderMCPServer()

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break

        line_str = line.decode("utf-8").strip()
        if not line_str:
            continue

        try:
            req = json.loads(line_str)
            # Non-blocking: fire and forget the response task
            asyncio.create_task(process_and_respond(server, req))
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()


async def process_and_respond(server: MultiProviderMCPServer, req: Dict[str, Any]):
    try:
        response = await server.handle_request(req)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        err = {
            "jsonrpc": "2.0",
            "id": req.get("id"),
            "error": {"code": -32603, "message": str(e)}
        }
        sys.stdout.write(json.dumps(err) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Multi-Provider MCP Server terminated gracefully.")