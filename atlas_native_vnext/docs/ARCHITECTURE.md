# Architecture and rewrite boundaries

`atlaslattice` source/OSS ecosystem → source passports → typed capability registry → OpenAI-native function/handoff envelope → *host-owned* admission/approval → Work, Atlas ONE, Alexandria, UWS and numerical-backend adapter ports.

```text
PUBLIC GITHUB / LICENSED OSS / RESEARCH SOURCES
           │  exact URL + commit + blob + ontology edition
           ▼
  ┌───────────────────────────────────────────────────┐
  │ Native synthesis candidate kernel (this patch)    │
  │ Strict wire | 31-asset catalog | units | A+B=C     │
  │ Hash receipt | alternative/falsifier | hold        │
  └───────────────────────┬───────────────────────────┘
                          │ inert, structured proposals
           ┌──────────────┼───────────────┐
           ▼              ▼               ▼
       Atlas ONE       SwarmChat       Alexandria
      TASK_PREVIEW   WORK_NOT_POSTED  GRAPH_NOT_WRITTEN
           ▲              ▲               ▲
           └──────────────┼───────────────┘
                          ▼
          HOST TRUST PORT (NOT IMPLEMENTED)
   signed platform principal + tenant + purpose + epoch
   grants at READ, at RETURN, at each controlled egress
   idempotent receiver inbox + trace + rollback
                          ▼
     UWS / MCP / A2A / OpenAI Agents / Qiskit / OpenMC
     WarpX / REEFCORE / 3D (each separately reviewed)
```

## Single responsibility per platform

**Atlas ONE:** orchestration and task lifecycle; **SwarmChat:** genuine peer collaboration and room receipts; **Alexandria/Noosphere:** source/evidence and typed graph custody; **Sheldonbrain:** retrieval and continuity (memory is never permission); **UWS:** workspace command interface; **OpenAI Responses/Agents SDK:** model tool-call and agent control loop; **science/quantum tools:** external execution inside approved sandbox and model qualification. Reuse each rather than merging unrelated runtimes into one privileged process.

## Novel but source-only components

- **Rights-carrying evidence passport concept:** an experiment references a pinned revision and an exact ontology edition. A future host must verify grants again at RETURN; current offline packet explicitly reports NOT_CHECKED.
- **Falsifier-first typed fusion:** a candidate is rejected without sources from distinct lab families, source revision evidence, at least one plausible alternative and a falsifier. `RELATED_METHOD_TRANSFER_PROPOSED` never becomes `same_as` or a causal claim.
- **Single portable envelope:** prepare one source-only record and emit three unposted, independently scoped candidate formats. Connectors may be developed without copying protected room or laboratory data between systems.
- **Scientific exactness:** use Decimal *strings* plus explicit units; reject floating JSON numbers, overflow/underflow, missing units, and claims of verified physical results without experimental provenance.
- **Idempotency-before-host:** local journal detects duplicate/replayed request IDs; actual exactly-once delivery depends on atomic receiver-side storage and post-revocation egress fencing.

## 12×12×12 collision control

Ariadne v0.7 uses H01–H12 / S01–S12 / N01–N12. Earlier Atlas editions include zero-based H00–H11. Both represent 1,728 addresses but share 1,331 identical strings with potentially different meanings. NEVER merge on `H01.S01.N01` alone. The kernel requires the Ariadne v0.7 edition and the original pinned registry hash for a syntactic candidate; even that does NOT prove semantic equivalence.

The separate REEFCORE physical XYZ grid also contains 1,728 cells. Physical mesh coordinates are not HSN editorial coordinates without an independently reviewed typed mapping.

## Promised / not promised

| Capability | This source-only version | Host implementation still needed |
|---|---|---|
| Inventory | 31 curated source candidates | complete repo/code/license/SBOM scan |
| OpenAI native | Strict Responses function tools | authenticated real API/Agents SDK run |
| Ontology | strict syntactic edition pin | node-level independent semantic review |
| Labs | design or synthetic envelopes | calibrated numerical solvers, data licenses, genuine instrumentation |
| UWS | metadata read request preview | actual host-authorized command execution |
| SwarmChat | Work preview only | current grants, stored seq readback and peer replies |
| Atlas ONE | task intake candidate only | actual dispatch/ack/cancel/idempotency |
| Alexandria | graph candidate only | host graph writes, provenance, review/canon separation |
| Security | synthetic epoch model and negative fixtures | signed platform trust, two-tenant D1, revoked Return, network egress |
| 3D | bounded JSON scene data | real React/Three/Godot tested UI |

No proprietary endpoints, secrets, private Work or Play/Brain/Palace bodies were copied into this package.
