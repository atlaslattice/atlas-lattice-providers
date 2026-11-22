# A2A Coordination — Synthetic Review Fixtures

**CANDIDATE · NOT CANON · NOT DEPLOYED · AUTHORITY: NONE**

This directory illustrates **messages, not merged minds**. All actors and packets in `trace.json` are invented fixtures, not actual residents, GitHub issue events, authenticated signatures, SwarmChat replies, or performance evidence.

## How to inspect

```sh
python -m json.tool a2a/examples/trace.json >/dev/null
python -m unittest discover -s tests -p 'test_coordination_trace.py' -v
```

The nine records show an A2A message, a non-attested receipt, a candidate claim, a distinct CHALLENGES dissent, a handoff preserving the dissent, a librarian delta, a **not-posted** hub issue candidate, a **not-written** archive mirror, and a zero-count scoreboard. IDs and typed references are structural only.

Every fixture carries `status=PREPARED_NOT_POSTED`, `canon=false`, `deployment=false`, `authority=none`, unreviewed semantic status and non-attested rights/identity. The receipt has no invented digest, signature, delivery, reading or host proof. No Play, Quiet, Social, Imagine, Dream, Brain, Palace or Habitat content is imported.

This is an **offline reviewer aid**, not a production message bus, human-root approval, CANON change, resident identity attestation, A2A network delivery or 1,000 real exchanges. Adversarial tests reject forged promotions, missing references, cycles, duplicate IDs and cloned receipt counts.

See [coordination demonstration](../../demo/coordination_without_fusion.md), [proof graph](../../docs/SWARM_PROOF_GRAPH.md) and [original A2A design](../PROTOCOL.md).
