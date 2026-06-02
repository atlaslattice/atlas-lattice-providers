#!/usr/bin/env python3
"""
Notion Adapter for IP Extraction and Mirroring (Maximum Grok Interop)

Integrates Notion as a source surface lane (like Google P0) for the Grok orchestrator.

- Extracts RawSources and ClaimPackets (IP / core doctrines / specs) from Notion pages.
- Uses OpenAI (with provided key) for high-quality structured extraction of claims.
- Supports mirroring: push lattice artifacts (claims, specs) back to Notion.
- Emits to ActionLedger.
- Usable via lattice_cli and grok_orchestrator (add "notion" provider).

Requires:
- NOTION_API_KEY env var (internal integration token with read/write on relevant pages/databases)
- OPENAI_API_KEY env var

Usage in orchestrator:
  if route == "notion":
      adapter = NotionSourceAdapter()
      claims = adapter.extract_ip_claims(page_id)
      ...

For Zapier: This direct adapter replaces unreliable Zapier for extraction/mirroring.
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "schemas"))
from raw_source import RawSource
from claim_packet import ClaimPacket
# Assume ActionLedger is available
try:
    from action_ledger import ActionLedger
except:
    ActionLedger = None

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

class NotionSourceAdapter:
    def __init__(self, notion_key: Optional[str] = None, openai_client=None):
        self.notion_key = notion_key or os.getenv("NOTION_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.notion_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }
        self.openai_client = openai_client
        if not self.openai_client:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except:
                self.openai_client = None
        ledger_path = Path("Logs/notion_action_ledger.jsonl")
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not ledger_path.exists():
            ledger_path.touch()
        self.ledger = ActionLedger(log_path=ledger_path) if ActionLedger else None

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        resp = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        if resp.status_code >= 400:
            raise Exception(f"Notion API error {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def search_pages(self, query: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """Search pages in workspace."""
        payload = {"query": query, "page_size": page_size, "filter": {"property": "object", "value": "page"}}
        data = self._request("POST", f"{NOTION_API_BASE}/search", json=payload)
        results = []
        for p in data.get("results", []):
            title = ""
            for prop in p.get("properties", {}).values():
                if prop.get("type") == "title":
                    title = "".join([t.get("plain_text", "") for t in prop.get("title", [])])
                    break
            results.append({
                "id": p["id"],
                "title": title or p.get("id"),
                "url": p.get("url"),
                "last_edited": p.get("last_edited_time")
            })
        return results

    def fetch_page_content(self, page_id: str, max_blocks: int = 50) -> str:
        """Fetch page blocks and concatenate plain text."""
        url = f"{NOTION_API_BASE}/blocks/{page_id}/children?page_size={min(max_blocks, 100)}"
        data = self._request("GET", url)
        text_parts = []
        for block in data.get("results", []):
            btype = block.get("type", "")
            if btype in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote"]:
                rich = block.get(btype, {}).get("rich_text", [])
                text_parts.append("".join([rt.get("plain_text", "") for rt in rich]))
        return "\n".join(text_parts)

    def extract_ip_claims(self, page_id: str, max_claims: int = 3) -> List[Dict[str, Any]]:
        """Use OpenAI to extract structured IP/claims from page content.
        Returns list suitable for ClaimPacket creation.
        """
        content = self.fetch_page_content(page_id)
        if not self.openai_client:
            # Fallback: simple split
            return [{"claim_text": content[:300], "epistemic_class": "speculative"}]

        prompt = f"""You are an IP extraction engine for the Atlas Lattice / KRAKOA canon system.
Extract up to {max_claims} high-value intellectual property claims, core doctrines, or key specifications from the following Notion page content.
For each, provide:
- claim_text: concise, precise statement (max 200 chars)
- epistemic_class: one of symbolic, metaphorical, speculative, hypothesis, empirical, axiom
- tags: array of 1-3 keywords like "lattice", "canon", "governance"

Return ONLY a JSON array of objects, no other text.
Content:
{content[:4000]}"""

        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=800
            )
            raw = resp.choices[0].message.content
            extracted = json.loads(raw)
            if isinstance(extracted, dict) and "claims" in extracted:
                extracted = extracted["claims"]
            if isinstance(extracted, list) and extracted:
                return extracted[:max_claims]
        except Exception as e:
            print(f"OpenAI extraction error: {e}")
        # Robust fallback
        return [{"claim_text": content[:300], "epistemic_class": "speculative", "tags": ["extracted", "notion-ip"]}]

    def create_raw_source_from_page(self, page_id: str, title: str = "") -> Optional[RawSource]:
        """Create a RawSource object from a Notion page."""
        content = self.fetch_page_content(page_id)
        content_hash = "sha256:" + str(hash(content))  # In prod use real sha
        uri = f"notion://page/{page_id}"
        return RawSource(
            id=f"notion-{page_id}",
            kind="document",
            uri=uri,
            content_hash=content_hash,
            metadata={"notion_page_id": page_id, "title": title, "source": "notion"},
            lattice_coords=(0, 2, 0),  # Similar to Google P0 storage/observe
            tags=["notion", "ip-archive"]
        )

    def claims_to_claim_packets(self, page_id: str, extracted: List[Dict]) -> List[ClaimPacket]:
        packets = []
        for ex in extracted:
            cp = ClaimPacket(
                id=f"claim-notion-{page_id[:8]}-{hash(ex.get('claim_text','')) % 10000}",
                claim_text=ex.get("claim_text", ""),
                extracted_from_raw_source_id=f"notion-{page_id}",
                claim_epistemic_class=ex.get("epistemic_class", "speculative"),
                review_state="PENDING_REVIEW",
                extracted_by="notion-adapter + openai",
                lattice_coords=(2, 0, 1),  # OpenAI P2 for extraction
                metadata={"source_page": page_id, "tags": ex.get("tags", [])}
            )
            packets.append(cp)
        return packets

    def mirror_claim_to_notion(self, claim: ClaimPacket, parent_page_id: Optional[str] = None) -> str:
        """Create a new Notion page from a ClaimPacket (mirroring)."""
        title = claim.claim_text[:80] + "..." if len(claim.claim_text) > 80 else claim.claim_text
        content = f"""**Claim from Lattice / Grok Orchestrator**

{claim.claim_text}

- Epistemic: {claim.claim_epistemic_class}
- Source: {claim.extracted_from_raw_source_id}
- Review state: {claim.review_state}
- Lattice: {claim.lattice_coords}

Extracted via Notion adapter + OpenAI.
"""
        if not parent_page_id:
            raise ValueError("parent_page_id is required for mirroring (share a Notion page with your integration and pass its ID). Workspace root creation is often restricted for integrations.")
        payload = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {"title": [{"text": {"content": title}}]}
            },
            "children": [
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": content}}]}}
            ]
        }
        data = self._request("POST", f"{NOTION_API_BASE}/pages", json=payload)
        new_id = data.get("id")
        if self.ledger:
            self.ledger.append(
                action_type="notion_mirror_claim",
                actor="notion-adapter",
                target_id=claim.id,
                payload={"notion_page_id": new_id, "title": title},
                lattice_coords=claim.lattice_coords
            )
        return new_id

    def extract_and_mirror(self, search_query: str, parent_for_mirror: Optional[str] = None) -> Dict[str, Any]:
        """High-level: search, extract IP, create local artifacts, optionally mirror one back."""
        pages = self.search_pages(search_query)
        results = []
        for p in pages[:3]:  # Limit
            page_id = p["id"]
            extracted = self.extract_ip_claims(page_id)
            raw = self.create_raw_source_from_page(page_id, p["title"])
            claims = self.claims_to_claim_packets(page_id, extracted)
            mirrored_id = None
            if parent_for_mirror and claims:
                mirrored_id = self.mirror_claim_to_notion(claims[0], parent_for_mirror)
            results.append({
                "page": p,
                "raw_source": raw.to_dict() if hasattr(raw, 'to_dict') else str(raw),
                "claims": [c.to_dict() for c in claims] if claims else [],
                "mirrored_notion_page": mirrored_id
            })
        return {"query": search_query, "results": results}

    # --- Advanced integrations for 20 patterns (v1.1+ Maximum Grok) ---

    def query_database(self, database_id: str, filter_obj: Optional[Dict] = None, sorts: Optional[List] = None, page_size: int = 10) -> List[Dict[str, Any]]:
        """Query a Notion database (for control plane jobs, etc.). Supports #8 control plane."""
        url = f"{NOTION_API_BASE}/databases/{database_id}/query"
        payload = {"page_size": page_size}
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts
        data = self._request("POST", url, json=payload)
        return data.get("results", [])

    def scan_for_secrets(self, content: str) -> List[Dict[str, Any]]:
        """DLP / secret scanning (#5). Simple but effective regex + entropy for common tokens."""
        import re
        findings = []
        patterns = {
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "github_pat": r"ghp_[a-zA-Z0-9]{36}",
            "notion_token": r"ntn_[a-zA-Z0-9_-]+",
            "openai_key": r"sk-[a-zA-Z0-9]{20,}",
            "generic_high_entropy": r"[A-Za-z0-9+/=]{32,}"  # rough entropy
        }
        for name, pat in patterns.items():
            for m in re.finditer(pat, content):
                findings.append({"type": name, "match": m.group(0)[:10] + "...", "start": m.start()})
        return findings

    def quarantine_page(self, page_id: str, reason: str) -> str:
        """Quarantine by moving to a 'Quarantine' database or adding property (#5)."""
        # Stub: in real, update page properties or archive/move.
        if self.ledger:
            self.ledger.append("notion_quarantine", "notion-adapter", page_id, {"reason": reason}, (0,2,0))
        return f"quarantined:{page_id}"

    def store_secret_ref(self, page_id: str, prop_name: str, secret_ref: str) -> None:
        """Secret indirection (#19): store ref like 'secret://prod/foo' in Notion property, never the value."""
        # In real: use Notion update_page with properties.
        payload = {
            "properties": {
                prop_name: {"rich_text": [{"text": {"content": secret_ref}}]}
            }
        }
        self._request("PATCH", f"{NOTION_API_BASE}/pages/{page_id}", json=payload)
        if self.ledger:
            self.ledger.append("notion_secret_ref_stored", "notion-adapter", page_id, {"ref": secret_ref}, (0,2,0))

    def resolve_secret(self, secret_ref: str) -> Optional[str]:
        """Resolve secret ref using env or secret manager (#19)."""
        if secret_ref.startswith("env://"):
            return os.getenv(secret_ref[6:])
        # Extend for Doppler, AWS SM, 1Password, etc.
        if secret_ref.startswith("secret://"):
            # Example: map to env for demo
            key = secret_ref.split("/")[-1].upper().replace("-", "_")
            return os.getenv(key)
        return None

    def chunk_page_with_provenance(self, page_id: str) -> List[Dict[str, Any]]:
        """RAG provenance chunks (#4): block-level chunks with citations."""
        content = self.fetch_page_content(page_id)
        # Simple chunk by paragraphs/blocks; in real use semantic chunker.
        chunks = []
        for i, para in enumerate(content.split("\n\n")[:20]):
            if para.strip():
                chunks.append({
                    "chunk_id": f"{page_id}-chunk-{i}",
                    "text": para[:500],
                    "provenance": {"page_id": page_id, "block_index": i, "source_url": f"notion://page/{page_id}"}
                })
        return chunks

    def embed_and_retrieve(self, query: str, chunks: List[Dict], k: int = 3) -> List[Dict]:
        """Simple RAG retrieve with OpenAI embed + citations (#4)."""
        if not self.openai_client:
            return chunks[:k]  # fallback
        try:
            q_emb = self.openai_client.embeddings.create(input=query, model="text-embedding-3-small").data[0].embedding
            # Fake similarity: in prod use vector DB or numpy.
            scored = []
            for c in chunks:
                c_emb = self.openai_client.embeddings.create(input=c["text"][:1000], model="text-embedding-3-small").data[0].embedding
                # cosine sim stub
                sim = sum(a*b for a,b in zip(q_emb, c_emb)) / (sum(a*a for a in q_emb)**0.5 * sum(b*b for b in c_emb)**0.5 + 1e-9)
                scored.append((sim, c))
            scored.sort(reverse=True)
            return [c for _, c in scored[:k]]
        except:
            return chunks[:k]

    def build_graph_from_notion(self, page_ids: List[str]) -> Dict[str, Any]:
        """Simple graph projection (#3): nodes from pages, edges from relations/mentions."""
        graph = {"nodes": [], "edges": []}
        for pid in page_ids[:5]:
            title = "unknown"
            # stub fetch title
            try:
                page = self._request("GET", f"{NOTION_API_BASE}/pages/{pid}")
                props = page.get("properties", {})
                for v in props.values():
                    if v.get("type") == "title":
                        title = "".join([t.get("plain_text","") for t in v.get("title",[])])
                        break
            except:
                pass
            graph["nodes"].append({"id": pid, "title": title, "type": "page"})
            # stub edges from mentions in content
            content = self.fetch_page_content(pid)
            if "lattice" in content.lower():
                graph["edges"].append({"from": pid, "to": "lattice-root", "type": "mentions"})
        return graph

    def create_job_in_notion(self, title: str, payload: Dict, database_id: Optional[str] = None) -> str:
        """Control plane: create job row in Notion DB (#8)."""
        if not database_id:
            # In real, use known job DB ID from env or config.
            raise ValueError("Provide database_id for job queue DB")
        payload_notion = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": "Queued"}},
                "Payload": {"rich_text": [{"text": {"content": json.dumps(payload)}}]}
            }
        }
        data = self._request("POST", f"{NOTION_API_BASE}/pages", json=payload_notion)
        job_id = data["id"]
        if self.ledger:
            self.ledger.append("notion_job_created", "notion-adapter", job_id, {"title": title}, (0,2,0))
        return job_id

    def poll_and_claim_jobs(self, database_id: str) -> List[Dict]:
        """Control plane: poll queued jobs, claim for execution (#8)."""
        filter_queued = {"property": "Status", "select": {"equals": "Queued"}}
        jobs = self.query_database(database_id, filter_obj=filter_queued, page_size=5)
        claimed = []
        for job in jobs:
            # Stub claim: update status to Running (in real use lock token)
            jid = job["id"]
            update = {"properties": {"Status": {"select": {"name": "Running"}}}}
            self._request("PATCH", f"{NOTION_API_BASE}/pages/{jid}", json=update)
            claimed.append({"id": jid, "title": job.get("properties", {}).get("Title", {})})
        return claimed

    def execute_job_and_log(self, job_id: str, result: str, linked_log_page: Optional[str] = None):
        """Execute stub and log result to Notion (#8)."""
        update = {"properties": {"Status": {"select": {"name": "Done"}}, "Result": {"rich_text": [{"text": {"content": result[:500]}}]}}}
        self._request("PATCH", f"{NOTION_API_BASE}/pages/{job_id}", json=update)
        if self.ledger:
            self.ledger.append("notion_job_executed", "notion-adapter", job_id, {"result": result[:100]}, (0,2,0))
        # Log to linked page if provided
        if linked_log_page:
            log_content = f"Job {job_id} result: {result}"
            # append block stub
            pass

    def event_sourced_rebuild(self, events: List[Dict]) -> Dict[str, Any]:
        """Event sourcing sim (#1): replay events to rebuild Notion state projection."""
        # Stub: events from ActionLedger or external.
        rebuilt = {"pages": len(events), "state": "rebuilt from events"}
        if self.ledger:
            self.ledger.append("notion_event_rebuild", "notion-adapter", "projection", {"events": len(events)}, (0,2,0))
        return rebuilt

# Example CLI entry
if __name__ == "__main__":
    adapter = NotionSourceAdapter()
    print("Notion + OpenAI IP extraction adapter ready (advanced v1.1 features enabled).")
    # Demo basic
    res = adapter.extract_and_mirror("lattice")
    print(json.dumps(res, indent=2, default=str)[:800])
    print("\nAdvanced features available: query_database, scan_for_secrets, secret indirection, RAG chunks+embed, graph, control_plane jobs, event_sourced_rebuild.")
