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
        # Cross-cloud bridge for Google <-> Microsoft interop (token mapping, Copilot handoff) - create FIRST
        self.multicloud_bridge = CopilotCLIBridge() if CopilotCLIBridge else None
        if self.multicloud_bridge:
            logger.info("Multi-cloud (Google-MS) CopilotCLIBridge active for token inheritance.")
        # Pass the multicloud bridge so GoogleProvider can consume GOOGLE_EXTERNAL_OAUTH_TOKEN
        # Gemini API key is picked from GOOGLE_API_KEY env (user's key integrated)
        self.google = GoogleProvider(bridge=self.multicloud_bridge)
        self.notion = NotionProvider()   # Real advanced engine wired in providers/notion/

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
                uws_integrations=self.uws,
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

        # UWS / Aluminum OS Integrations (17k+ unified features from atlaslattice UWS)
        try:
            from providers.uws_integrations import UwsIntegrations
            self.uws = UwsIntegrations(
                runner=self.cli_runner,
                project_engine=self.project_engine,
                advanced_engine=self.advanced_capabilities,
                bridge=self.multicloud_bridge,
                copilot_engine=self.microsoft.copilot_engine if hasattr(self.microsoft, "copilot_engine") else None,
                simulate_default=True
            )
            logger.info("UwsIntegrations (Aluminum OS 12k-20k+ feature surface) active.")
        except Exception as e:
            self.uws = None
            logger.warning(f"UWS integrations not loaded: {e}")

        # Advanced Bullshit Olympics (E145 Tier 1 #1) - direct instance for MCP + high-stakes
        try:
            from providers.bullshit_olympics import BullshitOlympics as AdvancedBullshitOlympics
            self.bullshit_olympics = AdvancedBullshitOlympics(
                project_engine=self.project_engine,
                advanced_engine=self.advanced_capabilities,
                decision_ledger=None,
                uws=self.uws,
                simulate_default=True
            )
            logger.info("AdvancedBullshitOlympics (multi-round adversarial, 12D provenance) active.")
        except Exception as e:
            self.bullshit_olympics = None
            logger.warning(f"Advanced Bullshit Olympics not loaded: {e}")

        # GrokOrchestrator as the strong central brain (E145 priority 1) - exposed for direct use + synthesis
        # Pass full symbiosis (memory, packer, pipeline, runner, providers) so brains/mirror/activation use max efficiency + real metatag/mirror
        try:
            from grok_orchestrator import GrokOrchestrator
            self.orchestrator = GrokOrchestrator(
                project_id="atlas-lattice-mcp-orchestrated",
                simulate_default=True,
                enforce_human_gates=True
            )
            # Enhance notion in orchestrator with mcp-level providers for real drive mirrors
            if hasattr(self.orchestrator, "notion_engine") and self.orchestrator.notion_engine:
                self.orchestrator.notion_engine.google_provider = self.google
                self.orchestrator.notion_engine.ms_provider = self.microsoft
            logger.info("GrokOrchestrator (central brain: routing + ledger + bullshit + gates) active as primary entrypoint.")
            logger.info("Notion brains/mirror wired with full providers for Sheldon/Grok/GPTBrain + GH/OneDrive/GDrive pipelines.")
        except Exception as e:
            self.orchestrator = None
            logger.warning(f"Orchestrator not loaded (will use direct engines): {e}")

        # OpenAI-grade modules (Phase 1)
        try:
            from providers.openai import (
                StructuredOutputSchemaSpine,
                ToolPassportFunctionCalling,
                OpenAITracingToGoldenTrace,
                EvalsBullshitOlympicsBridge,
                WorkloadIdentitySecretsHygiene,
                ResponsesAPISpine,
            )
            self.openai_structured = StructuredOutputSchemaSpine(simulate_default=True)
            self.openai_tool_passport = ToolPassportFunctionCalling(simulate_default=True)
            self.openai_trace = OpenAITracingToGoldenTrace(simulate_default=True)
            self.openai_evals = EvalsBullshitOlympicsBridge(simulate_default=True)
            self.openai_secrets = WorkloadIdentitySecretsHygiene(simulate_default=True)
            self.openai_responses = ResponsesAPISpine(simulate_default=True)
            logger.info("OpenAI-grade Phase 1+ modules active (structured, tool_passport, trace, evals, secrets, responses).")
        except Exception as e:
            self.openai_structured = self.openai_tool_passport = self.openai_trace = self.openai_evals = self.openai_secrets = self.openai_responses = None
            logger.warning(f"OpenAI-grade modules not fully loaded: {e}")

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
                },
                {
                    "name": "uws",
                    "description": "Execute UWS/Aluminum OS unified commands for the full 12,000-20,000+ (~17k) feature surface from atlaslattice UWS (Google Workspace 300+ + discovery 10k+, MS Graph 2k+, Apple, Android, Chrome as drivers). High-level: mail_list, drive_search, calendar_create, search_all, tasks_list, etc. Raw passthrough for any. Supports --provider, --dry-run, JSON. Outputs as UwsCommandClaimPacket with lattice (UWS/Aluminum/*), grok_leads, INV-L28. Symbiosis with project memory/ledger/advanced. See UWS_FEATURE_MANIFEST.md, UWS_ALUMINUM.md.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "integration": {"type": "string", "description": "UWS integration (e.g. mail_list, drive_search, search_all, raw_uws) or high-level like calendar_create"},
                            "kwargs": {"type": "object", "description": "Args like provider='google', query='lattice', command='gmail users messages list --params {...}', dry_run=True"}
                        },
                        "required": ["integration"]
                    }
                },
                {
                    "name": "grok_orchestrate",
                    "description": "THE STRONG CENTRAL BRAIN (E145 priority 1 highest). Routes any feature (Grok v3.0 20 + E145 20 + UWS 17k+ + Advanced 60+) through unified decision ledger, INV-L28 quality gates, mandatory Bullshit Olympics (priority 2) for high-stakes, and mandatory Teams Adaptive Card human promotion gates (priority 5). Maximizes symbiosis across entire lattice: v3 arena -> project E145 + bullshit + uws data + copilot gate + ledger. All high-stakes (physical, self-improve, writes, promotions, canon) go through full pipeline. Use this as primary entry for coherence instead of fragmented direct calls. Returns rich ClaimPacket.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "feature": {"type": "string", "description": "Any feature across lattice e.g. arena_mode, bullshit_olympics, uws:drive_search, physical_world_actuation_hooks_with_safety, project_memory_graph, mail_send (high-stakes auto-enforces gates)"},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["feature"]
                    }
                },
                {
                    "name": "bullshit_olympics",
                    "description": "Advanced Bullshit Olympics (E145 Tier 1 #1 - highest leverage). Multi-round (3-5) adversarial critique using distinct personas (Contrarian, Reductio, EvidenceAuditor, InvariantEnforcer, OverclaimDetector...). Produces rich TruthClaimPacket with inv_l28_coherence_score, overall_verdict, critical_flaws, evidence_pack (real provenance from DecisionLedger + Notion RAG + UWS audit). Called automatically for high-stakes by orchestrator; callable directly here. Uses Grok (XAI) when available for real critique.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "description": "The thing to review (ClaimPacket JSON, plan text, UWS result, synthesis, feature output, etc.)"},
                            "high_stakes": {"type": "boolean", "default": True},
                            "evidence": {"type": "object", "description": "Optional extra evidence dict"}
                        },
                        "required": ["target"]
                    }
                },
                {
                    "name": "feature_synthesis",
                    "description": "End-to-End Feature Synthesis Pipeline (E145 Tier 1 #4). 6-stage governed flow for 17k UWS + cross-provider features: Ingest (UWS/Notion/Graph) -> Cluster/Dedup -> Synthesize (multi-agent) -> Advanced Bullshit Olympics -> Human Gate (Teams) -> Promote to Canon (Notion + Ledger + ClaimPacket). The canonical way to turn raw surface into high-quality, reviewed canon. Returns full trace + final ClaimPacket.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "What to synthesize (e.g. 'UWS 17k + Google 40 + v3.0 20 features')"},
                            "kwargs": {"type": "object"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "self_improve",
                    "description": "Recursive Self-Improvement Sandbox (E145 Tier 1 #1). Safe bounded proposals for prompt/routing/bullshit changes. Full pipeline: sim -> eval -> bullshit -> human gate. Returns SelfImprovementClaimPacket with deltas.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "before": {"type": "string"},
                            "after": {"type": "string"},
                            "rationale": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "openai_structured",
                    "description": "02_Structured_Output_Schema_Spine (OpenAI Phase 1). Strict JSON schema enforcement for ClaimPacket, ToolPassport, PublicReleaseClass. Compile to OpenAI tool schemas. Validates all OpenAI outputs before lattice emission.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["validate_claim", "register_tool_passport", "get_openai_tools"]},
                            "raw_output": {"type": "object"},
                            "passport": {"type": "object"}
                        }
                    }
                },
                {
                    "name": "openai_tool_passport",
                    "description": "03_ToolPassport_Function_Calling (OpenAI Phase 1). Register governed ToolPassports and execute calls from OpenAI with ActionLedger emission and safety gates.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "arguments": {"type": "object"}
                        }
                    }
                },
                {
                    "name": "openai_trace",
                    "description": "06_OpenAI_Tracing_To_GoldenTrace (OpenAI Phase 1). Map OpenAI trace/thread/run IDs into immutable ActionLedger + GoldenTrace v2 receipts for full auditability.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "openai_trace_id": {"type": "string"},
                            "openai_thread_id": {"type": "string"},
                            "openai_run_id": {"type": "string"},
                            "payload": {"type": "object"}
                        }
                    }
                },
                {
                    "name": "openai_evals",
                    "description": "07_Evals_Bullshit_Olympics_Bridge (OpenAI Phase 1). Turn Grok Bullshit Olympics adversarial reviews into OpenAI Eval datasets and use them as powerful graders.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string"},
                            "name": {"type": "string"},
                            "items": {"type": "array"},
                            "eval_name": {"type": "string"},
                            "item_id": {"type": "string"},
                            "output": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "openai_secrets",
                    "description": "20_Workload_Identity_Secrets_Hygiene (OpenAI Phase 1). Env-only checks, workload identity recommendations, secret hygiene for OpenAI + lattice keys.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "openai_responses",
                    "description": "01_Responses_API_Spine (OpenAI Phase 2). Unified OpenAI Responses API surface for the entire lattice. Every flow goes through native request/response with ClaimPacket + ActionLedger emission.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "input": {"type": "string"},
                            "tools": {"type": "array"}
                        }
                    }
                },
                {
                    "name": "notion_mirror",
                    "description": "Mirror ClaimPacket to GitHub/OneDrive/GoogleDrive from Notion canon. Supports metatag sync. For adversarial review + multi-cloud mirror (primary Notion canon).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "object"},
                            "target": {"type": "string", "enum": ["github", "onedrive", "gdrive"]},
                            "tags": {"type": "object"}
                        }
                    }
                },
                {
                    "name": "ingest_brain",
                    "description": "Ingest Sheldonbrain RAG, GrokBrain, GPTBrain pathways using Notion RAG + OpenAI structured + pipeline. Activate for maximum efficiency ingestion.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "brain_name": {"type": "string"},
                            "query": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "metatag_notion",
                    "description": "Metatag Notion page with lattice metadata (lattice_coords, epistemic, INV tags, bullshit, provenance) for canon mirroring and review.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string"},
                            "tags": {"type": "object"}
                        }
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

            if name == "uws":
                integration = args.get("integration")
                kws = args.get("kwargs", {})
                if self.uws:
                    result = await self.uws.run(integration, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                else:
                    # Fallback to raw cli if engine missing
                    result = await self.cli_runner.execute("uws", [integration] + list(kws.values()) if isinstance(kws, dict) else [], timeout=120)
                    return {"jsonrpc": "2.0", "id": mid, "result": {"raw_fallback": result}}

            if name == "grok_orchestrate":
                feature = args.get("feature")
                kws = args.get("kwargs", {})
                if self.orchestrator:
                    result = await self.orchestrator.run(feature, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                else:
                    # Fallback synthesis via grok_max + project + bullshit if orchestrator missing
                    if self.grok_maximum:
                        res = await self.grok_maximum.run(feature, **kws)
                    elif self.project_engine:
                        res = await self.project_engine.run(feature, **kws)
                    else:
                        res = {"error": "No orchestrator or engines", "feature": feature}
                    # Force bullshit + gate in fallback for high-stakes
                    if feature and any(h in feature.lower() for h in ["physical", "self_improve", "arena", "bullshit", "write"]):
                        if self.project_engine:
                            bs = await self.project_engine.run("bullshit_olympics", target=feature, high_stakes=True)
                            res["fallback_bullshit"] = bs
                    return {"jsonrpc": "2.0", "id": mid, "result": res}

            if name == "bullshit_olympics":
                target = args.get("target")
                kws = {k: v for k, v in args.items() if k != "target"}
                if self.bullshit_olympics:
                    result = await self.bullshit_olympics.review(target, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                elif self.project_engine:
                    result = await self.project_engine.run("bullshit_olympics", target=target, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "Bullshit Olympics engine not available"}}

            if name in ("feature_synthesis", "synthesize_features"):
                q = args.get("query") or args.get("target") or "17k feature synthesis"
                kws = {k: v for k, v in args.items() if k not in ("query", "target")}
                # Prefer orchestrator if present (it has the full pipeline + gates + router)
                if self.orchestrator:
                    result = await self.orchestrator.run("feature_synthesis", query=q, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                # Direct
                try:
                    from pipelines.feature_synthesis import FeatureSynthesisPipeline
                    pipe = FeatureSynthesisPipeline(simulate_default=True)
                    result = await pipe.run(q, **kws)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                except Exception as e:
                    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}

            # General dispatch for new E145 20 modules (self_improve, ensemble, formal_verify, scientific, attest, etc.)
            if name in ("self_improve", "ensemble_reasoner", "formal_verifier", "self_debugger", "scientific_discovery", "attestation", "capability_synthesizer", "hierarchical_goals", "multi_modal", "resource_scheduler", "swarm", "agent_reputation", "counterfactual"):
                if self.orchestrator:
                    result = await self.orchestrator.run(name, **args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": f"Orchestrator required for {name}"}}

            # OpenAI-grade Phase 1 tools dispatch
            if name == "openai_structured":
                if self.openai_structured:
                    result = await self.openai_structured.run(**args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "OpenAI structured spine not loaded"}}

            if name == "openai_tool_passport":
                if self.openai_tool_passport:
                    result = await self.openai_tool_passport.run(**args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "OpenAI tool passport not loaded"}}

            if name == "openai_trace":
                if self.openai_trace:
                    result = await self.openai_trace.run(**args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "OpenAI trace bridge not loaded"}}

            if name == "openai_evals":
                if self.openai_evals:
                    result = await self.openai_evals.run(**args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "OpenAI evals bridge not loaded"}}

            if name == "openai_secrets":
                if self.openai_secrets:
                    result = await self.openai_secrets.run(**args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "OpenAI secrets hygiene not loaded"}}

            if name == "openai_responses":
                if self.openai_responses:
                    result = await self.openai_responses.run(**args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "OpenAI responses spine not loaded"}}

            if name in ("notion_mirror", "mirror_notion"):
                if self.notion and hasattr(self.notion, "engine") and self.notion.engine:
                    claim = args.get("claim", {})
                    target = args.get("target", "github")
                    result = self.notion.engine.mirror_claim_to_external(claim, target, **args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "Notion engine not available for mirror"}}

            if name in ("ingest_brain", "brain_ingest"):
                if self.notion and hasattr(self.notion, "engine") and self.notion.engine:
                    brain = args.get("brain_name", args.get("query", "sheldonbrain"))
                    result = self.notion.engine.ingest_brain(brain, **args)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "Notion engine not available for brain ingest"}}

            if name in ("metatag_notion", "metatag"):
                if self.notion and hasattr(self.notion, "engine") and self.notion.engine:
                    page = args.get("page_id", "")
                    tags = args.get("tags", {})
                    result = self.notion.engine.metatag_page(page, tags)
                    return {"jsonrpc": "2.0", "id": mid, "result": result}
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": "Notion engine not available for metatag"}}

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