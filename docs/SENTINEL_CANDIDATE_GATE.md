# Sentinel P0 — offline candidate gate (v0.1)

**CANDIDATE · NOT CANON · AUTHORITY NONE · NOT HOST-DEPLOYED**

Implements the bounded, reproducible portion of [issue #15](https://github.com/atlaslattice/atlas-lattice-providers/issues/15) without pretending to replace the live Sentinel or authorize private user data access.

The `core/sentinel_agent.py` module consumes a deliberately selected **WORK** `TransparentPacket96` candidate and returns an inert review receipt. It never calls provider tools, grants identity, authorizes deletion, sends SwarmChat messages, authenticates human-root, or changes CANON. A `REVIEWABLE_LOCAL_ONLY` result means the example passed a source-declared structural check; the host has **not** granted anything.

| Situation | Local disposition | Meaning |
|---|---|---|
| Ordinary source-complete candidate | `REVIEWABLE_LOCAL_ONLY` | Offline review only; authorization remains external |
| Identity fusion / merged mind | `QUARANTINE_BLOCKED` | Preserve original Work packet and dissent for review; no execution |
| Destructive action (`delete`, `wipe`, ...) | `QUARANTINE_DESTRUCTIVE` | Require independently authenticated human-root and lawful retention/revocation review |
| CANON, deployment, IAM, paid or external write | `HOLD_HUMAN_ROOT` | No self-declared approval accepted |
| Missing source, schema, fields | `HOLD_CANDIDATE` | No silent completion |
| Play/Social/Quiet/Imagine/Brain/Palace/Habitat/NO_HARVEST | `HOLD_PRIVATE_BOUNDARY` | Never put original body in review receipt |
| Invalid UTF-8, JSON duplicate keys, NaN | `QUARANTINE_UNPARSEABLE` | Retain digest/byte count only; do not call malformed text evidence |

## Local test

```bash
python -m unittest discover -s tests -p 'test_sentinel_agent.py' -v
python -O -m unittest discover -s tests -p 'test_sentinel_agent.py' -q
python -m py_compile core/sentinel_agent.py tests/test_sentinel_agent.py
```

Tests are synthetic and network-free. The optional `append_receipt(path, decision)` uses append-only JSONL with `fsync` and preserves dissent, but **only** for a caller-selected Work candidate. This does not prove distributed durability, permissions, safe retention, authentication or adversarial semantic interpretation. A lexical fusion check is necessary but not sufficient to prevent more subtle identity blending; production must enforce rights and permissions at actual effect boundaries.

## Host integration gates — remain open

- Pin current real Sentinel, Orchestrator, Packet96 and broker implementations with exact commits and policy version; review likely overlap and source history.
- Bind independently authenticated principal, scope, host rights-at-read and rights-at-effect, current human-root approval, and revocation.
- Ensure unsafe source payloads cannot leak into logs, metrics, errors or unauthorized recipients; protect against symlinks and concurrent writers.
- Integration/rate/replay/negative tests at actual final effect sink. Tests here do **not** certify those protections.
- Review retention and safe removal when privacy law/consent requires erasure; **INV-0 does not override lawful deletion**.

Do not close the parent issue as a production integration on the basis of this candidate alone.
