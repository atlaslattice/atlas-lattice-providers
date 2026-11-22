# One-Command World-Class Proof

Status: **CANDIDATE — NOT CANON**  
Authority: **none**  
Human-root decides.

This module gives the swarm a single visible proof surface for **CONTINUUM OS**. It does not promote artifacts. It checks that the repository can produce receipts for OpenAI interop, A2A boundaries, INV-0 preservation, candidate/canon separation, Continuum OS naming, plural continuums, and smoke-test readiness.

## Run

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
