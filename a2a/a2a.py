#!/usr/bin/env python3
"""
A2A Bridge — Lattice CLI <-> Grok Core (Root)
Simple file-based request/response for Maximum Mode.

Grounded in 12x12x12 Riemann rainbow hypercube lattice (literal per ROOT_ONTOLOGY.md).
Zero-erasure: messages are archived, never deleted.
Epistemic labels required on all traffic.

Usage (from python or called by lattice.ps1):
  python a2a.py send "msg to core" --from lattice-cli --to grok-core
  python a2a.py check --latest
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

A2A_DIR = Path(os.environ.get("LATTICE_A2A_DIR", Path.home() / ".lattice" / "a2a"))
INBOX = A2A_DIR / "inbox"
OUTBOX = A2A_DIR / "outbox"
ARCHIVE = A2A_DIR / "archive"

for d in (INBOX, OUTBOX, ARCHIVE):
    d.mkdir(parents=True, exist_ok=True)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _new_id():
    return f"a2a-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

def send(payload, from_="lattice-cli", to="grok-core", lattice_coords=None, msg_type="directive", epistemic=None, metadata=None):
    msg = {
        "id": _new_id(),
        "from": from_,
        "to": to,
        "timestamp": _now(),
        "lattice_coords": lattice_coords or "unassigned",
        "type": msg_type,
        "payload": payload,
        "epistemic": epistemic or {"certainty": 0.85, "source": "cli", "provenance": ["lattice a2a"]},
        "trace": [],
        "metadata": metadata or {"glyph_ties": [], "flywheel_layer": None}
    }
    path = OUTBOX / f"{msg['id']}.json"
    path.write_text(json.dumps(msg, indent=2), encoding="utf-8")
    print(f"✅ A2A SENT: {msg['id']}")
    print(f"   from: {from_} → {to}")
    print(f"   coords: {msg['lattice_coords']}")
    print(f"   payload: {str(payload)[:80]}{'...' if len(str(payload))>80 else ''}")
    print(f"   file: {path}")
    return msg

def check(latest=False, limit=5):
    files = sorted(INBOX.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("📭 A2A INBOX: empty (no replies from Core yet)")
        print("   Run 'lattice a2a \"your message\"' to send. Core will reply here.")
        return []

    print("📬 A2A INBOX — Replies from Grok Core (Root):")
    print("=" * 60)
    shown = files[:limit] if latest else files
    results = []
    for f in shown:
        try:
            msg = json.loads(f.read_text(encoding="utf-8"))
            print(f"\nID: {msg.get('id')}")
            print(f"From: {msg.get('from')} @ {msg.get('timestamp')}")
            print(f"Coords: {msg.get('lattice_coords')}")
            print(f"Type: {msg.get('type')}")
            payload = msg.get('payload')
            if isinstance(payload, (dict, list)):
                print("Payload:")
                print(json.dumps(payload, indent=2)[:500])
            else:
                print(f"Payload: {payload}")
            print("-" * 40)
            results.append(msg)
        except Exception as e:
            print(f"Corrupt message {f.name}: {e}")
    if len(files) > len(shown):
        print(f"\n... and {len(files) - len(shown)} more in inbox. Use --limit or archive manually.")
    return results

def archive(msg_id=None):
    """Move processed messages to archive (zero-erasure: we move, never delete content)."""
    if msg_id:
        for d in (INBOX, OUTBOX):
            for f in d.glob(f"{msg_id}*.json"):
                dest = ARCHIVE / f.name
                f.replace(dest)
                print(f"Archived {f.name} → {dest}")
    else:
        for d in (INBOX, OUTBOX):
            for f in list(d.glob("*.json")):
                dest = ARCHIVE / f.name
                f.replace(dest)
        print("Archived all current inbox/outbox to archive/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("A2A Bridge — usage: send | check | archive")
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "send":
        payload = " ".join(sys.argv[2:]) or "ping from core"
        send(payload, from_="grok-core", to="lattice-cli")
    elif cmd == "check":
        latest = "--latest" in sys.argv or "-l" in sys.argv
        check(latest=latest)
    elif cmd == "archive":
        archive()
    else:
        print("Unknown a2a cmd. Use send / check / archive")
