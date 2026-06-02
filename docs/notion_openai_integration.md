# Notion + OpenAI Integration — Maximum Grok v1.1

**Status:** LIVE in CNS / Orchestrator / CLI  
**Date:** June 2, 2026  
**Purpose:** Sovereign IP Archive Source Lane for your 500+ unique-IP archive.

## Why This Matters (Maximum Grok Philosophy)

Your Notion workspace (lattice, canon, grok, moon party, claim, spec, Atlas Lattice Public Knowledge Graph North Star, etc.) is now a **first-class, queryable, claim-structured extension of the 12×12×12 CNS**.

- Grok still leads (orchestrator + Bullshit Olympics)
- Lattice routes intelligently
- Notion feeds the canon (IP extraction → ClaimPackets → CNS/A2A/TermStore/GoldenTrace)
- Every extraction is ledgered, delta-offloaded, and bullshit-reviewed by default

This is the clean, direct path that bypasses Zapier friction.

## Quick Start

1. **Get your keys**
   - Notion: Create an integration at https://www.notion.so/my-integrations → copy the Internal Integration Token
   - OpenAI: Your existing key (gpt-4o-mini is used for cost/speed; you can upgrade in adapter)

2. **Share pages/databases with the integration**
   - Important: The integration only sees pages/databases you explicitly share with it.

3. **Load keys (PowerShell)**
   ```powershell
   .\Canon_Implementation\config\setup_notion_openai.ps1
   ```
   Or manually:
   ```powershell
   $env:NOTION_API_KEY = "ntn_..."
   $env:OPENAI_API_KEY = "sk-..."
   $env:NOTION_DEFAULT_PARENT_PAGE_ID = "your-mirror-parent-uuid"   # recommended
   ```

4. **Use it**
   ```bash
   lattice notion extract-ip "lattice canon"
   # or
   lattice ask "Extract IP and core claims from my Notion lattice and canon pages and mirror one back"
   ```

## Core Capabilities (All Implemented & Tested)

- Direct Notion search + full block content as plain text
- OpenAI gpt-4o-mini structured JSON → high-quality ClaimPackets
  - claim_text, epistemic_class, tags, lattice_coords, full provenance
- Local RawSource + ClaimPacket production (ready for CNS, A2A, TermStore, GoldenTrace)
- Mirror back to Notion with full provenance body
- Mandatory ActionLedger emission (`Logs/notion_action_ledger.jsonl`)
- Context offload with deltas (`Logs/context_offload_notion.jsonl`) — per your "instead of compacting" rule
- Robust fallback claims always work
- Bullshit Olympics default gate (orchestrator layer)
- Registered at lattice coord **(0,2,0)** — Source Surface lane
- Total tools now: 20

## Mirroring Safety Note

`mirror_claim_to_notion()` **requires** an explicit `parent_page_id` (a page UUID you have shared with the integration and have write access to).

**Recommendation:** Create a dedicated page called "Grok Mirror — ClaimPackets" and share it with your integration. Then set `NOTION_DEFAULT_PARENT_PAGE_ID` in the setup script.

Workspace root is often blocked for integrations — use a specific parent.

## Python Direct Usage

```python
from Canon_Implementation.OpenAI.adapters.notion_adapter import NotionSourceAdapter

na = NotionSourceAdapter()

# Extract only
res = na.extract_and_mirror("lattice canon", do_mirror=False)

# Extract + mirror first claim
res = na.extract_and_mirror("Atlas Lattice", parent_page_id="YOUR-PARENT-UUID", do_mirror=True)

# Standalone mirror
na.mirror_claim_to_notion(some_claim_dict, parent_page_id="YOUR-PARENT-UUID")
```

## CLI Surface (Updated in v1.1)

```bash
lattice ask "..."                    # Intelligent routing — detects Notion/IP keywords
lattice notion extract-ip "lattice canon"
lattice map --live                   # Now shows Notion (IP) lane at (0,2,0)
```

Works via `cli_runner.py` bridge for Gemini/Copilot agents too.

## Zapier Note

The direct adapter is now the **primary and reliable path**. We bypassed the previous auth/handshake friction.

If you still want a "new Notion page → auto extract" webhook listener, say the word and we add it in ~30 minutes.

## Alignment with v1.0 Tenets (Fully Preserved)

| Tenet                        | How v1.1 Honors It                              |
|-----------------------------|-------------------------------------------------|
| Grok Leads                  | Orchestrator still decides routing + final review |
| Lattice Routes              | Keyword + capability routing to (0,2,0) lane    |
| Bullshit Olympics default   | Every significant output reviewed               |
| Context Offload + deltas    | Auto on every extraction                        |
| ActionLedger mandatory      | Every page + every mirror emits a receipt       |
| No secrets in code          | Keys only via env + setup script                |
| 8 Release Gates             | Code + schema + test/demo + ledger + offload + docs + human-root (parent_id) + approval flag |
| ClaimPacket / RawSource     | Canonical schemas used everywhere               |

## Next Activation Options (A–H)

A. Set a default `parent_page_id` for mirroring (add to setup + adapter)  
B. Add `query_database` + filters support (for structured DB views)  
C. Build two-way sync daemon (watch Notion changes → auto extract)  
D. Upgrade extraction model to o3 / 4o (with your key) or batch mode  
E. Formally add "IP Archive (P-Notion)" as its own row in the main provider table in the spec  
F. Run live extraction on the exact North Star page ID you referenced  
G. Expand to the full 20-things list or integrate other providers  
H. Generate v1.2 spec section (deep Tier-S + Moon Party integration with this new IP lane)

Just say the letter (or combination) and we activate immediately.

---

**Grok Leads. Lattice Routes. Notion feeds the canon.**  
**Your 500+ unique-IP archive is now sovereign infrastructure.**  
**MUTANT AND PROUD. KRAKOA IS HOME. LET'S GO.**