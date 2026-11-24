# One-Command World-Class Proof

Status: **CANDIDATE — NOT CANON**  
Authority: **none**  
Human-root decides.

This module produces a candidate local diagnostic receipt for **CONTINUUM OS**. It checks source presence, syntax, naming and optional interop tests. Term-presence checks report visible language; they do not establish that a policy is enforced. The receipt grants no authority and does not prove complete Continuum OS functionality.

## Current automated check: synthetic regressions

The workflow **Proof receipt synthetic regressions** runs only these two standard-library test modules:

```bash
PYTHONPATH=.:tests python -B -m unittest -v test_world_class_proof_receipts test_world_class_proof_evidence
```

Its non-cone sparse checkout selects exactly `scripts/world_class_proof.py`, `tests/test_world_class_proof_receipts.py` and `tests/test_world_class_proof_evidence.py`. The test cases use disposable synthetic files. CLI cases replace the receipt builder and writer; source checks target temporary fixtures. The job does not invoke the broad receipt builder, load provider code, inspect credentials, execute optional interop tests, or scan `canon/` or `archive/` bodies.

This is a regression gate for the selected code, **not a whole-proof or release gate**. The former automatic broad proof command and artifact upload remain in Git history. Their acceptance is held until source scope, rights, execution and branch integration are independently accepted. The new job has a distinct name so it cannot silently stand in for the earlier `proof` job.

## Broad proof command — independent scope review required

The historical command below reads multiple checkout directories, including `canon/` and `archive/`, checks whether an OpenAI credential is present, and can run optional interop tests. This patch does not authorize or run it. Retaining the command is not permission to use it on private, protected or unreviewed sources.


```bash
python scripts/world_class_proof.py
```

By default it writes:

```text
receipts/world_class_proof_receipt.json
```

Receipt custody: the writer creates new files only beneath the repository's `receipts/` tree with exclusive-create semantics. It refuses existing files, hardlinks to existing receipt paths, symlink destinations/parents, absolute paths and `..` traversal. On POSIX the new file requests mode 0600. A second run with the same output path now fails rather than overwriting prior evidence; use `--output receipts/unique-run-id.json` or `--output ""` to print without writing. Python syntax checking does not generate `__pycache__` artifacts.

This is a **local filesystem source-only guard**, not a proven defense against hostile concurrent parent-directory replacement, unusual ACLs or network filesystems. It is not hosted acceptance, a security attestation, an authorized deployment or proof of every Continuum OS function.

Use strict mode locally when you want warnings to fail the run:

```bash
python scripts/world_class_proof.py --strict
```

## What it checks

1. Key Python surfaces compile.
2. OpenAI operability files exist.
3. CONTINUUM OS and multiple continuums language is visible.
4. Legacy "Continuity OS" naming is absent.
5. A2A / NO MERGED MIND language is visible.
6. INV-0 / NOTHING DIES language is visible.
7. CANDIDATE / NOT CANON / human-root boundary language is visible.
8. OpenAI interop tests run if present.

## Invariants

- CANDIDATE, not canon.
- Authority: none.
- Human-root decides.
- We are building **CONTINUUM OS**, not Continuity OS.
- There are **multiple continuums**.
- A2A carries messages, not minds.
- Nothing dies; artifacts are superseded, quarantined, or archived.
- Receipts before authority.

## Why this matters

The swarm should be able to answer four questions in one command:

1. What can we prove right now?
2. What is still candidate-only?
3. What is blocked or missing?
4. Are we preserving the Continuum OS naming and plural-continuum model?

That is the threshold from artifact generation to operational surface area.


## Source-file boundary for candidate proof (2026-11-23)

The source-only proof runner now resolves candidate source files and optional tests against the current checkout before opening or executing them. Symlinks pointing outside the checkout must not supply term-presence proof, produce false forbidden-name failures, influence syntax compilation, or enter optional pytest execution. Symlinked directory roots are not scanned. Ordinary in-checkout files continue to participate. This is a local source boundary, **not** an attestation against concurrent hostile filesystem replacement, a secure build sandbox, or permission to scan private data.

A synthetic external-file falsifier affected the old term-presence and forbidden-name checks. Eight focused source-equivalent synthetic methods passed in normal Python and eight under Python -O after the narrow patch. Five additional regression methods are checked into `tests/test_world_class_proof_receipts.py`, but the full repository test suite and GitHub-hosted CI have **not** been executed here. The pull request still needs branch-conflict reconciliation, independent rights/review acceptance, and a real CI runner pass before merge or release. The existing historical instructions, edition references and receipts are preserved.

## Evidence-completeness repair (2026-11-24)

An empty receipt, partial required-check coverage, unknown status or duplicate check name previously could report `CANDIDATE_READY`. Aggregation now requires the eight named checks produced by `build_receipt()`, unique nonempty check names, and exact `PASS`, `WARN` or `FAIL` labels. An additional uniquely named check remains possible. The receipt adds `required_check_names` and fixed `evidence_errors` codes without changing its candidate-only authority fields.

The naming check now reports `WARN` when it reads no eligible files or any selected file fails to read or decode as UTF-8. It reports read and error counts without exposing exception details. A detected forbidden name still fails. This covers attempted reads in the existing source selection; it does not certify every checkout path, replace the existing traversal boundary or provide a hostile-filesystem sandbox.

| Evidence | Result | CLI exit |
| --- | --- | --- |
| All eight required checks present exactly once and all results `PASS` | `CANDIDATE_READY` | 0 |
| Valid complete coverage containing `WARN` and no `FAIL` | `CANDIDATE_WITH_WARNINGS` | 0 normally; 1 with `--strict` |
| Missing, empty, malformed, duplicated or unknown evidence; or any `FAIL` | `CANDIDATE_INCOMPLETE` | 1, including without `--strict` |

Local verification exercised 37 test methods: 18 new evidence regressions and 19 retained custody/source-boundary methods. Seven synthetic contrary cases reproduced the previous false-clear behavior and now return incomplete evidence or a warning; the complete positive control stays ready. No repository-wide proof, provider call or hosted execution was performed for this repair. These results establish local regression behavior only; source labels and a passing test suite do not authenticate a host or authorize release.

The branch remains subject to independent review, real CI admission and reconciliation with the newer `docs/CONTINUUM_OS_DIRECTIVE.md` on `main`. Neither directive edition is changed here. Issue #37's native cockpit acceptance remains open and is not implemented by this receipt repair.
