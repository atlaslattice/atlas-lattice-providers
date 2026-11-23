# OSS and Atlas selection matrix — first reviewed cut

These are **candidate source pointers**, not vendored dependencies, completed license audits, or proof of deployed integration. A fork in the organization may be months behind upstream. Current proprietary, trademark, provider, patent and transitive rights need independent review. `DO_NOT_VENDOR` is a real hold, not a recommendation to copy code.

| Asset | Family | Source / fork | License candidate | Integration strategy | Current evidence |
|---|---|---|---|---|---|
| `atlas-one` | agent-core | [atlaslattice/Atlas-Intelligence](https://github.com/atlaslattice/Atlas-Intelligence) | UNKNOWN_PROJECT_LICENSE | `WRAP_READ_ONLY` | `SOURCE_PINNED` |
| `atlas-providers` | agent-core | [atlaslattice/atlas-lattice-providers](https://github.com/atlaslattice/atlas-lattice-providers) | UNKNOWN_PROJECT_LICENSE | `WRAP_READ_ONLY` | `SOURCE_PINNED` |
| `noosphere` | knowledge | [atlaslattice/noosphere-archive](https://github.com/atlaslattice/noosphere-archive) | UNKNOWN_PROJECT_LICENSE | `WRAP_READ_ONLY` | `SOURCE_PINNED` |
| `alexandria` | knowledge | [atlaslattice/continuum-os](https://github.com/atlaslattice/continuum-os) | UNKNOWN_PROJECT_LICENSE | `REVIEW_ONLY` | `REVIEW_LICENSE` |
| `manus` | knowledge | [atlaslattice/manus-artifacts](https://github.com/atlaslattice/manus-artifacts) | MIXED | `WRAP_READ_ONLY` | `SOURCE_PINNED` |
| `uws` | workspace | [atlaslattice/uws](https://github.com/atlaslattice/uws) | Apache-2.0 (fork README) | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `orcs` | science | [atlaslattice/open-regenerative-compute-standard](https://github.com/atlaslattice/open-regenerative-compute-standard) | MIXED | `WRAP_READ_ONLY` | `SOURCE_PINNED` |
| `foundation` | knowledge | [atlaslattice/atlas-lattice-foundation](https://github.com/atlaslattice/atlas-lattice-foundation) | UNKNOWN_PROJECT_LICENSE | `REVIEW_ONLY` | `SOURCE_PINNED` |
| `element145` | math | [atlaslattice/element-145](https://github.com/atlaslattice/element-145) | FOUNDATION_CUSTOM | `REVIEW_ONLY` | `REVIEW_LICENSE` |
| `swarmchat` | collaboration | [HOST_SCOPED_NO_GIT_PIN](https://swarmchat-private-broker-20261112.tdavesheldon.chatgpt.site/) | NOT_APPLICABLE | `HOST_INTEGRATION` | `HOST_GATED` |
| `atlas-labs-v32` | science | [atlaslattice/atlas-lattice-providers](https://github.com/atlaslattice/atlas-lattice-providers/pull/61) | UNKNOWN_PROJECT_LICENSE | `WRAP_READ_ONLY` | `SOURCE_PINNED` |
| `openai-agents` | agent-runtime | [UPSTREAM_REFERENCE](https://github.com/openai/openai-agents-python) | VERIFY_CURRENT | `OPTIONAL_PLUGIN` | `REVIEW_LICENSE` |
| `a2a` | interop | [atlaslattice/A2A](https://github.com/a2aproject/A2A) | Apache-2.0 | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `openhands` | developer | [atlaslattice/OpenHands](https://github.com/OpenHands/OpenHands) | MIT (community core) | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `langchain` | agent-runtime | [atlaslattice/langchain](https://github.com/langchain-ai/langchain) | MIT | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `browser-use` | developer | [atlaslattice/browser-use](https://github.com/browser-use/browser-use) | MIT | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `ollama` | models | [atlaslattice/ollama](https://github.com/ollama/ollama) | MIT | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `deer-flow` | agent-runtime | [atlaslattice/deer-flow](https://github.com/bytedance/deer-flow) | MIT (reported fork) | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `qiskit` | quantum | [NOT_YET_IMPORTED](https://github.com/Qiskit/qiskit) | Apache-2.0 | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `openmc` | science | [NOT_YET_IMPORTED](https://github.com/openmc-dev/openmc) | MIT/X | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `threejs` | visual | [atlaslattice/three.js](https://github.com/mrdoob/three.js) | MIT | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `godot` | visual | [atlaslattice/godot](https://github.com/godotengine/godot) | MIT | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `clickhouse` | data | [atlaslattice/ClickHouse](https://github.com/ClickHouse/ClickHouse) | Apache-2.0 | `OPTIONAL_PLUGIN` | `REVIEW_SECURITY` |
| `meilisearch` | knowledge | [atlaslattice/meilisearch](https://github.com/meilisearch/meilisearch) | MIXED_OR_UNVERIFIED | `REVIEW_ONLY` | `REVIEW_LICENSE` |
| `dify` | agent-runtime | [atlaslattice/dify](https://github.com/langgenius/dify) | Dify Open Source License (additional conditions) | `DO_NOT_VENDOR` | `REVIEW_LICENSE` |
| `n8n` | workflow | [atlaslattice/n8n](https://github.com/n8n-io/n8n) | Sustainable Use License / Enterprise | `DO_NOT_VENDOR` | `REVIEW_LICENSE` |
| `openwebui` | visual | [atlaslattice/open-webui](https://github.com/open-webui/open-webui) | VERIFY_CURRENT | `REVIEW_ONLY` | `REVIEW_LICENSE` |
| `redis` | data | [atlaslattice/redis](https://github.com/redis/redis) | MIXED_VERSION_DEPENDENT | `REVIEW_ONLY` | `REVIEW_LICENSE` |
| `warpx` | science | [NOT_YET_IMPORTED](https://github.com/ECP-WarpX/WarpX) | VERIFY_CURRENT | `OPTIONAL_PLUGIN` | `REVIEW_LICENSE` |
| `cirq` | quantum | [NOT_YET_IMPORTED](https://github.com/quantumlib/Cirq) | VERIFY_CURRENT | `OPTIONAL_PLUGIN` | `REVIEW_LICENSE` |
| `pytorch` | models | [atlaslattice/pytorch](https://github.com/pytorch/pytorch) | MIXED_OR_UNVERIFIED | `REVIEW_ONLY` | `REVIEW_LICENSE` |

## Notable verified license boundaries

- **A2A:** Apache-2.0 upstream protocol license; confirm exact SDK/binary and notices before bundling. https://github.com/a2aproject/A2A/blob/main/LICENSE
- **OpenHands:** MIT community source, but `enterprise/` has separate terms. https://github.com/OpenHands/OpenHands/blob/main/LICENSE
- **Qiskit:** Apache-2.0 for core SDK; remote hardware provider access/charges are separate. https://github.com/Qiskit/qiskit/blob/main/LICENSE.txt
- **OpenMC:** MIT/X stated upstream; nuclear-data distribution, validation, scientific licensing remain separate. https://github.com/openmc-dev/openmc
- **Dify:** Dify Open Source License with additional multi-tenant and branding conditions. DO NOT bulk vendor. https://github.com/langgenius/dify
- **n8n:** Sustainable Use / enterprise licensing; not an unrestricted OSI open-source package. DO NOT bulk vendor. https://github.com/n8n-io/n8n/blob/master/LICENSE.md
- **redis, Open WebUI, Meilisearch, broad source forks:** exact release or per-file licensing not yet verified. HOLD copying.

## Selected default implementations (subject to host tests)

OpenAI Agents SDK for multi-agent runtime; Responses API for strict function calls; UWS for workspace data access; existing SwarmChat broker for human/peer Work; Alexandria/Noosphere for evidence; Qiskit optional simulator backend; OpenMC/WarpX only after data and science acceptance; Three.js for optional public graph viewer. Avoid duplicating full model frameworks and avoid separate identity issuers.

## No-copy rule

No third-party source files are included in this patch. Adapter contracts are newly authored. No upstream license notice was removed or modified.
