# Public Candidate Bundle 0001

```text
STATUS: CANDIDATE PUBLIC BUNDLE
CANON: NO
DEPLOYMENT: NO
AUTHORITY: NONE
```

This bundle is a public-safe staging surface. It is designed to make the project easier to fork, audit, and review without implying canon, deployment, endorsement, or completeness.

## Rules

- Graph edge is not authority.
- Receipt is not approval.
- Dashboard is not deployment.
- Simulation is not proof.
- Human-root holds promotion.
- Nothing dies.

## Contents

- `BUNDLE_0001_FILE_MANIFEST.yaml` — candidate file manifest.
- `PR_CHECKLIST.md` — safe PR checklist.
- `docs/ontology/` — public ontology slices.
- `schemas/` — schema copies or public-safe schema links.
- `toy_graph/` — public-safe demo graph.
- `receipts/` — candidate receipts.

## First Gate

Run Eight Gates before public release:

```bash
python core/eight_gates.py public_candidate_bundle_0001/README.md
```
