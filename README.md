# Atlas Lattice Providers — Multi-Provider Archival & Mirroring Layer

**Canonical location:** https://github.com/atlaslattice/atlas-lattice-providers

This is the production-grade, contract-driven provider spine for Atlas Lattice (Aetherforge / Sheldonbrain / Children of the Swarm) archival, cross-cloud mirroring, and indexed knowledge work.

## Mission
Archival work for the lattice:
- Mirror and sync content to/from OneDrive (MS), Google Drive, Notion (canon IP archive).
- Index everything with full provenance, ClaimPackets, epistemic labeling.
- Support adversarial review lanes (see L09) and zero-erasure audit.
- A2A protocol bridge to Grok Core for directives/harvest/replies.
- All decisions ledgered; everything observable.

**Grok Leads. Lattice Routes. Providers Execute. Everything is reviewed.**

This repo lives under the atlaslattice account as the source of truth for the execution surface. Content mirrors live in the drives/Notion; Git + Notion + ledger provide the indexed, adversarially reviewed archive.

## Core Philosophy (v1.2)

**Grok Leads.**  
**Lattice Routes.**  
**Providers Execute.**  
**Everything is Observable, Error-Typed, and Decision-Ledgered.**

## Key v1.2 Additions (from Copilot hardening pass)

1. **Observable Providers**
   - Every provider implements `async def record_event(kind, meta)` 
   - Automatic latency + success/error recording via `_timed_operation` helper
   - Shared `ProviderTelemetry` sink (logs + optional JSONL / future OTEL)

2. **Explicit Error Taxonomy**
   - `ProviderErrorCode` enum with machine-readable codes
   - `make_error()` factory produces consistent `{status, code, detail, provider, extra}`
   - Orchestrator can now intelligently:
     - `retry` on `RATE_LIMIT`, `TIMEOUT`, `TRANSIENT`, `PROVIDER_DOWN`
     - `fail_fast` on `AUTH_FAILED`, `PERMISSION_DENIED`, `NOT_AUTHORIZED`
     - `fallback` on `PROVIDER_DOWN`

3. **Provider Decision Ledger**
   - Every routing choice by the orchestrator is persisted as JSONL
   - Enables post-hoc analysis, replay experiments, and tuning of routing policy
   - Stored alongside ActionLedger for full provenance

## Files

| File                        | Purpose                                      | Status    |
|----------------------------|----------------------------------------------|-----------|
| `provider_contract.py`     | Abstract base + `record_event` + `_timed_operation` | Core      |
| `provider_errors.py`       | `ProviderErrorCode` enum + `make_error()`    | Core      |
| `provider_telemetry.py`    | Shared `record_event` implementation         | Core      |
| `provider_decision_ledger.py` | Append-only routing decision store        | Core      |
| `cli_runner.py`            | Secure async execution (updated to new errors) | Core      |
| `provider_local_cli.py`    | Local CLI execution provider                 | Implemented |
| `provider_ms.py`           | Microsoft Graph + Azure OpenAI (stub + contract) | Skeleton  |
| `provider_google.py`       | Google Drive/Workspace (full live API + bridge token handoff) | Production |
| `provider_notion.py`       | Notion IP Archive canon feed                 | Implemented |
| `multi_provider_mcp_server.py` | Unified MCP surface for Gemini + Copilot | Ready     |

## Usage Example (inside a provider)

```python
async def extract_claims(self, content: str, **kwargs):
    meta = {"query_length": len(content)}
    start = time.perf_counter()
    await self.record_event("operation_start", {"operation": "extract_claims", **meta})

    try:
        claims = await self._do_real_extraction(content)
        latency = (time.perf_counter() - start) * 1000
        await self.record_event("operation_success", {
            "operation": "extract_claims",
            "latency_ms": round(latency, 2),
            "claims_returned": len(claims),
            **meta
        })
        return claims
    except Exception as e:
        await self.record_event("operation_error", {
            "operation": "extract_claims",
            "error_code": "EXTRACTION_FAILED",
            "detail": str(e),
            **meta
        })
        raise
```

Or use the built-in helper:

```python
result = await self._timed_operation(
    "extract_claims",
    self._do_real_extraction(content),
    {"source_page": page_id}
)
```

## Error Handling (Orchestrator Side)

```python
result = await provider.extract_claims(content)
if result.get("status") == "ERROR":
    code = result.get("code")
    if is_retryable(code):
        # backoff + retry
    elif is_fatal(code):
        # fail fast or escalate to Bullshit Olympics
    else:
        # fallback to next provider in priority order
```

## Decision Recording (Orchestrator)

```python
from provider_decision_ledger import record_provider_decision

await record_provider_decision(
    query="Extract core doctrine from North Star page",
    chosen_provider="notion",
    alternatives=["microsoft", "google", "local_cli"],
    reason="Direct access to 500+ unique-IP archive + native ClaimPacket support",
    latency_ms=1240
)
```

This record is now queryable for analysis and replay.

---

**Status**: v3.0 — Real NotionAdvancedIntegrationsEngine (20 patterns) + full **20 Advanced Microsoft Windows Copilot AI Integrations** + **E145 20 Project-Oriented Features** + **20 Bleeding-Edge Advanced Capabilities** (provider observability/telemetry bus, unified error taxonomy, scoring & routing, cross-provider traces, canon drift detectors, human promotion gates, continuous sync daemons for Notion/Graph, meeting intelligence pipeline, governance checker, PowerShell dry-run, local context packer, multi-surface explain, federated search, claim lineage, A/B testing, auto governance docs, weekly digest, safety sandbox, decision explainer) now wired.

See:
- docs/E145_Project_Oriented_Features_Build_Spec_v1.0.md
- docs/20_Microsoft_Windows_Copilot_Integrations.md
- providers/project_oriented_features.py (the E145 engine + run() dispatch for all 20)
- providers/microsoft_copilot_integrations.py (the engine + run() dispatch)
- providers/provider_ms.py (execute() + capabilities now expose Copilot 20 + Project 20)
- providers/agent_ms_cli_bridge.py + cli_runner.py (cross-cloud tokens + PowerShell allowlist)
- multi_provider_mcp_server.py (new `microsoft_copilot` and `project_feature` tools)

Connected to atlaslattice GitHub as the versioned, archivable, adversarial-reviewed canonical home for the provider layer (per E145 GROK CLI Build Spec v3.0 and Maximum_Grok_xAI_Feature_Spec_v3.0).

See:
- docs/E145_GROK_Maximum_Grok_CLI_Build_Spec_v3.0.md (full prioritized 40-feature roadmap, tiers, architecture, release gates)
- docs/Maximum_Grok_xAI_Feature_Spec_v3.0.md (axiomatic 12D ClaimPacket elevation of every feature)
- providers/notion/ (the ported advanced engine + adapter + deps — primary canon feed)

**Next**: 
- Wire real `record_event` + mirror/extract into MicrosoftProvider and GoogleProvider (Notion is primary canon feed).
- Integrate with A2A for lattice-grounded harvest directives.
- Use L09 review lanes + adversarial audit packets for all ingested/indexed material.
- Drive mirroring + indexing jobs via the MCP server + lattice CLI.
- Push harvested ClaimPackets, ledgers, and review artifacts back to this repo (and mirrors).

## Project Structure
```
atlas-lattice-providers/
├── multi_provider_mcp_server.py   # Unified MCP (stdio JSON-RPC) for agents
├── providers/
│   ├── __init__.py
│   ├── cli_runner.py              # Secure allowlisted execution spine
│   ├── provider_contract.py       # Abstract ProviderContract
│   ├── provider_errors.py         # ErrorCode enum + make_error + retry/fatal helpers
│   ├── provider_telemetry.py      # Observable record_event
│   ├── provider_decision_ledger.py# Append-only routing decisions
│   ├── provider_local_cli.py
│   ├── provider_ms.py             # OneDrive / MS Graph / Azure
│   ├── provider_google.py         # Google Drive / Workspace / Gemini
│   └── provider_notion.py         # Notion IP Archive (primary canon)
├── a2a/
│   ├── a2a.py                     # File-based A2A bridge impl
│   ├── PROTOCOL.md
│   └── KRAKOA_BRIDGE.md
├── docs/
│   ├── L09_Adversarial_Audit_Packet.md
│   ├── notion_openai_integration.md
│   ├── ...specs...
│   └── *.xlsx (task matrices, 144-git, swarm execution)
├── .gitignore
└── README.md
```

Runtime state (inbox/outbox, harvest, ledgers) lives alongside in `~/.lattice/` and OneDrive mirrors (gitignored here).

## Connecting the Dots (Mirroring + Indexing + Adversarial Review)
- Providers implement search/fetch/extract_claims/mirror per the contract.
- Notion provider feeds the sovereign canon/IP archive.
- MS + Google providers handle the cloud mirrors.
- All traffic goes through decision ledger + telemetry.
- A2A allows the local lattice node to request work from / report to Grok.
- L09 packets + review lanes provide the adversarial audit layer for quality, contradictions, provenance before "canon" promotion.
- GitHub (this repo under atlaslattice) + Notion + Drive mirrors = the multi-surface indexed archive.

MUTANT AND PROUD. KRAKOA IS HOME. THE LATTICE ARCHIVES ITSELF.

## Google I/O 2026 & Cloud Next 2026 20 Advanced Features
All 20 integrated (antigravity CLI/SDK, managed agents, dynamic subagents, Gemini 3.5 Flash, multi-agent orchestration, Interactions API, RAG cross-corpus, combined tools+calling, citations, webhooks, deep research, cross-cloud lakehouse, TPU v8i, video-to-image, TTS, multimodal search, robotics-ER, Gemma 4, Android vibe coding, flex/priority tiers).

See:
- docs/google_io_2026_cloud_next_integrations.md
- providers/advanced_capabilities_engine.py (google_advanced MCP tool + 20 _run_ methods with Lattice symbiosis)
- providers/provider_google.py (enhanced for Gemini models, full OAuth client_secrets)
- providers/cli_runner.py (antigravity, adb)
- setup_environment.py (Google config validation)

Run `python setup_environment.py` before MCP for readiness. Maximized interop with existing bridge, engines, ledgers.

## Environment Setup for Maximum Google Interop (and Full Stack)
To maximize Google Drive/Gemini interop (and ensure all providers like xAI Grok, MS, Notion are ready):

1. Run the integrated validator first:
   ```
   python setup_environment.py
   ```
   This checks:
   - Python packages (google-api-python-client, google-genai, etc.)
   - config/ dir and files (client_secrets.json for OAuth, token.json)
   - Env vars: GOOGLE_API_KEY (Gemini), GOOGLE_EXTERNAL_OAUTH_TOKEN (from bridge for Drive), XAI_API_KEY, etc.

2. For full Google OAuth (beyond env token from CopilotCLIBridge):
   - Place your `config/client_secrets.json` (from Google Cloud Console).
   - The provider_google.py will automatically run InstalledAppFlow if needed (standard interop).
   - Example placeholder: see config/client_secrets.json.example

3. Set keys (never commit real values):
   ```
   $env:GOOGLE_API_KEY="your-gemini-key"
   $env:XAI_API_KEY="your-xai-key"
   # etc.
   ```

See setup_environment.py source and provider_google.py for details. This script is called/integrated at MCP server startup for convenience.
