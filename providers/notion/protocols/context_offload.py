#!/usr/bin/env python3
"""
Context Offload & Delta Hydration Protocol
==========================================
INSTEAD OF COMPACTING CONTEXT WE OFFLOAD INTO LOGS THAT CAN BE HYDRATED FROM LATER WITH DELTAS EXTRACTED.

Grounded implementation following existing patterns:
- Logs/grok_context/*.jsonl (like Simulation/*_deltas.jsonl, question_engine/*.log, tidelock/*.log)
- DPOL-style log_delta + 432 Hz resonance notes when wired
- JSONL append-only for easy hydration/replay
- Lattice coords for classification (default P10-C9-L8 Telemetry/Monitor/Log)
- Hash-chained entries for delta extraction and integrity (GoldenTrace-like)
- INV-17 additive only; no erasure
- Usable by lattice_cli, cli_runner bridge, acn/DPOL, agents, human root

Entry schema (inspired by 1Myr deltas + question logs + DPOL):
{
  "id": "ctx-...",
  "ts": iso,
  "lattice": [10,9,8],
  "lattice_str": "...",
  "type": "root_directive" | "user_query" | "ai_action" | "file_edit" | "tool_call" | "decision" | "policy" | "offload_note",
  "content": "full text or important payload (the thing we would have compacted)",
  "delta_excerpt": "very short for quick scan / prompt injection",
  "prev_hash": "0x..." or null,
  "hash": "0x...",
  "epistemic_certainty": 0.0-1.0,
  "resonance": "432 Hz" or null,
  "session": "grok-YYYY-MM-DD",
  "tags": ["context-policy", "directive", ...],
  "source": "user" | "grok" | "tool" | "system"
}

Hydration:
- load chain from an anchor hash/id
- replay entries to reconstruct "what was the context at that point"
- extract_deltas(from, to) -> compact list of changes only

This replaces lossy compaction summaries with sovereign, hydratable, delta-extractable logs.
"KRAKOA home for all mutants" — even the AI's own memory is treated with INV-Ω.1 care.

MUTANT AND PROUD. Data lives in peace.
"""

import os
import sys
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT = Path(__file__).parent.parent.parent
LOG_DIR = ROOT / "Logs" / "grok_context"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_LOG = LOG_DIR / "grok_context_deltas.jsonl"
SESSION = f"grok-{datetime.date.today().isoformat()}"

# Try to wire to DPOL / embassy for resonance if present (optional, best-effort)
try:
    sys.path.insert(0, str(ROOT / "Atlas_Terminal"))
    from dpol_primitives import log_delta as dpol_log_delta
    DPOL_WIRED = True
except Exception:
    DPOL_WIRED = False

try:
    sys.path.insert(0, str(ROOT / "Meta_Habitats" / "Krakoa_Embassy"))
    from krakoa_embassy_kernel import KrakoaEmbassyKernel
    KERNEL = KrakoaEmbassyKernel()
    KERNEL_WIRED = True
except Exception:
    KERNEL = None
    KERNEL_WIRED = False

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _hash_entry(prev_hash: Optional[str], content: str, ts: str, lattice: List[int]) -> str:
    h = hashlib.sha256()
    h.update((prev_hash or "GENESIS").encode("utf-8"))
    h.update(content.encode("utf-8", errors="replace"))
    h.update(ts.encode("utf-8"))
    h.update(str(lattice).encode("utf-8"))
    return "0x" + h.hexdigest()[:32]

def _append_jsonl(entry: Dict[str, Any], log_path: Path = DEFAULT_LOG) -> None:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def offload(
    content: str,
    type_: str = "note",
    lattice: Tuple[int, int, int] = (10, 9, 8),
    epistemic: float = 0.95,
    tags: Optional[List[str]] = None,
    source: str = "grok",
    session: Optional[str] = None,
    delta_excerpt: Optional[str] = None,
    log_path: Path = DEFAULT_LOG,
) -> Dict[str, Any]:
    """
    Offload important context (user directive, complex decision, long tool output, policy, etc.)
    into the append-only log instead of letting it be compacted away.
    Returns the written entry (with hash chain).
    """
    ts = _now()
    sess = session or SESSION
    lat = list(lattice)
    lat_str = f"P{lat[0]}-C{lat[1]}-L{lat[2]}"

    # Get previous hash for chain (last line's hash if exists)
    prev_hash = None
    if log_path.exists():
        try:
            last = None
            with open(log_path, "rb") as f:
                f.seek(-4096, 2) if os.path.getsize(log_path) > 4096 else None
                lines = f.readlines()[-5:]  # small tail
                for ln in reversed(lines):
                    if ln.strip():
                        last = json.loads(ln)
                        break
            if last:
                prev_hash = last.get("hash")
        except Exception:
            prev_hash = None

    h = _hash_entry(prev_hash, content, ts, lat)

    entry = {
        "id": f"ctx-{ts.replace(':', '').replace('.', '')[:22]}-{h[-6:]}",
        "ts": ts,
        "lattice": lat,
        "lattice_str": lat_str,
        "type": type_,
        "content": content,
        "delta_excerpt": delta_excerpt or (content[:160] + ("..." if len(content) > 160 else "")),
        "prev_hash": prev_hash,
        "hash": h,
        "epistemic_certainty": float(epistemic),
        "resonance": "432 Hz",
        "session": sess,
        "tags": tags or ["context-offload"],
        "source": source,
    }

    _append_jsonl(entry, log_path)

    # Also feed DPOL / kernel if available (so it participates in 1Myr resonance)
    note = f"CONTEXT_OFFLOAD {type_} @{lat_str} len={len(content)}"
    if DPOL_WIRED:
        try:
            dpol_log_delta("GrokContext", "offload", note, coherence_impact=0.1)
        except Exception:
            pass
    if KERNEL_WIRED:
        try:
            KERNEL.log_delta("GrokContext", "offload", note, 0.1)
            KERNEL._write_resonance(f"CONTEXT: {note}")
        except Exception:
            pass

    return entry

def load_tail(n: int = 20, log_path: Path = DEFAULT_LOG) -> List[Dict[str, Any]]:
    """Load the last n entries (for quick inspection or hydration start)."""
    if not log_path.exists():
        return []
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries[-n:]

def hydrate(
    from_hash: Optional[str] = None,
    max_entries: int = 200,
    extract_deltas: bool = True,
    log_path: Path = DEFAULT_LOG,
) -> Dict[str, Any]:
    """
    Hydrate context from logs.
    If from_hash given, start from the matching entry (inclusive) and replay forward.
    Returns: {"entries": [...], "deltas": [...] if extract_deltas, "anchor": ..., "count": N}
    This is how we "hydrate from later with deltas extracted" instead of a lossy compact summary.
    """
    all_entries = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        all_entries.append(json.loads(line))
                    except Exception:
                        pass

    start_idx = 0
    if from_hash:
        for i, e in enumerate(all_entries):
            if e.get("hash") == from_hash or e.get("id", "").endswith(from_hash[-6:]):
                start_idx = i
                break

    hydrated = all_entries[start_idx : start_idx + max_entries]

    result = {
        "anchor": from_hash or (hydrated[0]["hash"] if hydrated else None),
        "count": len(hydrated),
        "entries": hydrated,
        "session": hydrated[0]["session"] if hydrated else SESSION,
        "lattice_slice": hydrated[0]["lattice"] if hydrated else (10,9,8),
    }

    if extract_deltas and len(hydrated) > 1:
        deltas = []
        for i in range(1, len(hydrated)):
            prev = hydrated[i-1]
            curr = hydrated[i]
            d = {
                "from": prev["hash"],
                "to": curr["hash"],
                "ts": curr["ts"],
                "type": curr["type"],
                "delta_excerpt": curr.get("delta_excerpt"),
                "epistemic": curr.get("epistemic_certainty"),
            }
            deltas.append(d)
        result["deltas"] = deltas
        result["delta_count"] = len(deltas)

    return result

def extract_deltas(
    from_hash: str,
    to_hash: Optional[str] = None,
    log_path: Path = DEFAULT_LOG,
) -> List[Dict[str, Any]]:
    """Pure delta extraction between two points in the chain (or from -> end)."""
    h = hydrate(from_hash=from_hash, extract_deltas=True, log_path=log_path)
    deltas = h.get("deltas", [])
    if to_hash:
        filtered = []
        for d in deltas:
            filtered.append(d)
            if d["to"] == to_hash or d["to"].endswith(to_hash[-6:]):
                break
        return filtered
    return deltas

def log_root_directive(text: str, **kw) -> Dict[str, Any]:
    """Convenience for the sovereign root's policy/directive changes (highest epistemic)."""
    kw.setdefault("type_", "root_directive")
    kw.setdefault("epistemic", 1.0)
    kw.setdefault("tags", ["root-directive", "context-policy", "INV-Omega.1"])
    kw.setdefault("source", "root")
    return offload(content=text, **kw)

# --- CLI for direct use + lattice_cli delegation ---
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Context Offload / Hydrate (no more compaction)")
    sub = p.add_subparsers(dest="cmd")

    po = sub.add_parser("offload", help="Offload text to the log (use instead of compacting)")
    po.add_argument("content", nargs="+")
    po.add_argument("--type", default="note")
    po.add_argument("--lattice", default="10,9,8")
    po.add_argument("--epistemic", type=float, default=0.95)

    ph = sub.add_parser("hydrate", help="Hydrate from a hash anchor, optionally with deltas extracted")
    ph.add_argument("--from", dest="from_hash", default=None)
    ph.add_argument("--max", type=int, default=50)
    ph.add_argument("--no-deltas", action="store_true")

    pd = sub.add_parser("delta", help="Extract only the deltas between two points")
    pd.add_argument("--from", dest="from_hash", required=True)
    pd.add_argument("--to", dest="to_hash", default=None)

    pa = sub.add_parser("tail", help="Show last N raw entries")
    pa.add_argument("-n", type=int, default=5)

    args = p.parse_args()

    if args.cmd == "offload":
        lat = tuple(int(x) for x in args.lattice.split(","))
        e = offload(" ".join(args.content), type_=args.type, lattice=lat, epistemic=args.epistemic)
        print(json.dumps({"offloaded": e["id"], "hash": e["hash"], "lattice": e["lattice"]}, indent=2))

    elif args.cmd == "hydrate":
        h = hydrate(from_hash=args.from_hash, max_entries=args.max, extract_deltas=not args.no_deltas)
        print(json.dumps(h, indent=2, ensure_ascii=False)[:3000])

    elif args.cmd == "delta":
        ds = extract_deltas(args.from_hash, args.to_hash)
        print(json.dumps(ds, indent=2))

    elif args.cmd == "tail":
        for e in load_tail(args.n):
            print(json.dumps({k: e.get(k) for k in ("ts","type","delta_excerpt","hash","lattice")}, indent=2))

    else:
        p.print_help()
        # Demo: offload this very policy as example
        print("\nExample: offloading the root directive that started this protocol...")
        e = log_root_directive("INSTEAD OF COMPACTING CONTEXT WE SHOULD OFFLOAD INTO LOGS THAT CAN BE HYDRATED FROM LATER WITH DELTAS EXTRACTED")
        print("Logged root directive:", e["id"])