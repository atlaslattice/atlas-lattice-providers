# Prompt Patterns for `run_cli_command` (Canonical Interop Contract)

This document sketches reliable prompting patterns so that models (Grok, Gemini, Copilot, etc.) use the **standard `run_cli_command`** MCP tool (exposed by both Gemini and Microsoft/Copilot MCP servers) instead of hallucinating raw shell or direct API calls.

All models that support function calling should treat `run_cli_command` as the **canonical local execution primitive** for the stack.

## Standard Tool Schema (shared)

See `SecureCLIRunner.get_mcp_tool_definition()` for the exact schema (name: "run_cli_command").

Key:
- `command_name`: logical name with a `CommandPolicy` (e.g. "grok", "lattice", "uws", "alum").
- `arguments`: tokenized list.
- Optional `timeout`.

Models **must**:
- Use canonical subcommands where defined.
- Prefer `--dry-run` / `--format json` for UWS/Alum.
- Never invent shell commands.

## Canonical Command Patterns (Grok / Lattice)

### Grok Canon (for specs / v3.0 / E145)
- `grok canon diff <target>` — compare current state vs canonical (e.g. Maximum_Grok_xAI_Feature_Spec_v3.0.md, UWS specs).
- `grok canon sync <target>` — apply updates from canon.
- Example prompt addition:
  ```
  To inspect or sync against the canonical Lattice / Grok specs, always use:
  run_cli_command with command_name="grok" and arguments=["canon", "diff", "moon_party"] or ["canon", "sync", "uws"].
  Never use raw `grok` without the "canon" subcommand for spec work.
  ```

### Lattice Ops
- `lattice query <expr>` — query Atlas Lattice (12x12x12, ClaimPackets, INV-L28).
- `lattice apply <patch>` — structural changes.
- Prompt:
  ```
  For any Atlas Lattice interaction, use run_cli_command command_name="lattice" arguments=["query", "<12D expr>"] or ["apply", "<patch>"].
  ```

### Watch / Long-running (future streaming variant)
- `grok watch <target>`
- Use with care; prefer short timeouts or background via policies.

## UWS / Aluminum OS (17k+ Unified Features)
- Use `uws` or `alum` for the full surface (Google Workspace, MS Graph, Apple, etc.).
- Always: `--format json`, `--dry-run` before writes, `--provider` for targeting.
- High-level via UwsIntegrations or raw:
  - `uws drive list --provider all --format json`
  - `alum mail send ... --dry-run`
  - `uws search "Q1 budget" --provider all`
- Prompt pattern:
  ```
  For unified access to Google Drive/Gmail/Calendar, Microsoft Outlook/Teams/OneDrive, Apple iCloud, etc., use:
  run_cli_command command_name="uws" arguments=["drive", "search", "lattice", "--provider", "all", "--format", "json"]
  or command_name="alum" ...
  Always include --dry-run for any create/delete/update. Prefer the high-level UWS integrations in the MCP 'uws' tool when available.
  ```

## Cross-Model Consistency (Gemini + Copilot + Grok)

- Both MCP servers return the **exact same** `run_cli_command` in `tools/list`.
- Both dispatch to the **same** policy-driven `SecureCLIRunner`.
- Models should see it as provider-agnostic local execution spine.
- Combine with cloud tools: e.g. use `search_provider` / `google_advanced` / `uws` then `run_cli_command` for local follow-up (canon diff, lattice apply).

## Safety / Best Practices to Prompt

Add to system prompts:
- "You have access to run_cli_command for vetted local tools only. All local execution MUST go through it."
- "For UWS/Alum: always --dry-run before writes. Parse JSON results."
- "For Grok canon/lattice: use only the documented subcommands (canon, query, apply)."
- "If a command is not in the policy list returned by the tool, do not attempt raw execution."

## Editing Policies

See `config/command_policies.json` (auto-generated on first run of runner with defaults for grok/lattice/uws/alum + safe Windows/Google CLIs).

To add a new canonical command:
- Edit the JSON (or the DEFAULT_POLICIES in code).
- Restart the MCP server.
- Update this doc + any model system prompts.

This makes `run_cli_command` the **single audited interop contract** for the entire Maximum Grok / Lattice / UWS / Aluminum stack.

MUTANT AND PROUD. KRAKOA IS HOME. GROK LEADS. LATTICE ROUTES. UWS UNIFIES.
