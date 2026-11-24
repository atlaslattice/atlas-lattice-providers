# Atlas Lattice Providers

Python provider adapters and reviewable coordination components for Atlas.
Start with the local checks below, then choose the component you need.

**CANDIDATE · NOT CANON · AUTHORITY: NONE · DEPLOYMENT: NONE**

This repository contains local reference implementations, integration candidates
and historical experiments. Component status varies. A source file or passing
local test does not establish a running service, production integration or release
approval.

## Start here

| I want to… | Go to |
| --- | --- |
| Run a small, credential-free check | [Local quick start](#local-quick-start) |
| Find the right module or document | [Documentation guide](docs/README.md) |
| Fix a bug or propose a focused change | [Contributing](CONTRIBUTING.md) |
| Review current work | [Open pull requests](https://github.com/atlaslattice/atlas-lattice-providers/pulls) and [issues](https://github.com/atlaslattice/atlas-lattice-providers/issues) |
| Understand a failed hosted check | [CI admission issue #54](https://github.com/atlaslattice/atlas-lattice-providers/issues/54) |

## Local quick start

Use Python 3.11 or newer from the repository root. These three targeted suites
use the Python standard library and synthetic inputs; they do not need API keys,
package installation or provider calls.

```bash
python -m unittest discover -s tests -p 'test_candidate_bus.py' -v
python -m unittest discover -s tests -p 'test_coordinate_resolver.py' -v
python -m unittest discover -s tests -p 'test_transparent_packet96.py' -v
```

The suites cover candidate message preparation, coordinate routing and packet
review. Their passing result applies to those local components only. Provider
integrations have separate dependencies, access requirements and test scopes.

## Repository map

| Location | Purpose |
| --- | --- |
| [`a2a/`](a2a/) | Candidate message envelopes and coordination examples |
| [`core/`](core/) | Packet review, coordinate handling and local validation |
| [`providers/`](providers/) | Provider-specific adapters and integration candidates |
| [`schemas/`](schemas/) | Claim, source, evidence and receipt schemas |
| [`tests/`](tests/) | Focused regression and integration tests |
| [`docs/`](docs/) | Contracts, implementation notes and historical specifications |
| [`scripts/`](scripts/) | Operator utilities; check each utility's inputs and side effects |

## Working boundaries

- Keep source editions explicit. The default-branch coordinate resolver uses
  its documented zero-based namespace; an Ariadne edition or a pending PR must
  not be silently substituted. Read the [coordinate contract](docs/COORDINATE_RESOLVER_CONTRACT.md).
- Keep local tests, hosted CI, merge and runtime evidence separate.
- Use synthetic or explicitly authorized Work data. Do not include credentials,
  private source bodies or protected non-Work content in issues or examples.
- Preserve source attribution, license notices, historical versions and objections.
  Repository visibility does not establish permission to reuse every source.

For the longer architecture and component contracts, use the
[documentation guide](docs/README.md). For a reviewable contribution, follow
[Contributing](CONTRIBUTING.md).
