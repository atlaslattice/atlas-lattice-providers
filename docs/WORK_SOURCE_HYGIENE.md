# Check an explicit Work-source selection

**CANDIDATE · NOT CANON · AUTHORITY: NONE · DEPLOYMENT: NONE**

The hygiene workflow checks five named source files: the guard, the workflow,
its two synthetic test files and this guide. Its selection is the literal
`WORK_SOURCE_PATHS` tuple in `.github/workflows/secret_hygiene.yml`.
It does not search the repository for additional files or certify the rest
of the repository. Changes to this selection need a fresh source/authorization
review; filenames alone cannot establish rights or current consent.

## Run the finite local checks

From the repository root on a Unix system supporting descriptor-relative,
non-following opens:

```sh
python -m unittest discover -s tests -p 'test_secret_hygiene_*.py' -v
```

The file tests create disposable synthetic inputs in a temporary directory.
The workflow tests replace its source-loader function with a synthetic report
fixture. Neither suite scans the actual repository, imports provider package
initializers, resolves credentials, contacts a provider or reads a real corpus.

## Scanner contract

`OpenAISecretHygieneGuard.scan_files(root, paths=...)` is an additive API for
caller-authorized, exact relative file paths. The workflow loads the guard file
directly so `providers/__init__.py` is not executed. It uses these bounds:

| Bound | Maximum |
| --- | --- |
| Explicit selected files | 128 |
| Bytes read from one selected file | 1 MiB |
| Total bytes read | 8 MiB |

Callers may lower these limits. Invalid limits, missing selections, duplicate
paths, globs, traversal, reserved-mode path names and unsupported source suffixes
are rejected before any selected file is opened. The entire selection is checked
first. No symlink is followed in the root, intermediate directories or selected
file. Nonregular files and files with multiple hard links are rejected. Unsupported
platforms fail closed rather than falling back to a less restrictive open.

Reads are bounded by each file's observed size and the remaining byte budget.
Missing/unreadable inputs, interrupted reads, changed metadata, invalid UTF-8,
NUL-containing content and limit failures produce explicit error entries. The report
uses input indexes and fixed diagnostic codes instead of paths, excerpts or OS
exception messages. Findings contain pattern indexes and aggregate counts,
never the matched value or its prefix.

The workflow succeeds only if all five selected files were read completely,
the result has the expected scope, no input error was reported and none of the
configured secret patterns matched. `selected_inputs_complete` describes that
selection only. It is not complete repository coverage or a guarantee that every
possible secret format is detectable. The `simulate` argument does not disable
file reads in this scanner.

## Compatibility and remaining gates

The historical `scan_codebase()` and other legacy methods remain unchanged for
compatibility. They are outside this explicit-file guarantee and are not used
by the Work workflow. Do not run the guard module directly: its historical
`__main__` path invokes the legacy directory scanner and credential resolver.

The workflow still uses a normal checkout. These guarantees bound the selected
scanner reads; they do not sandbox checkout contents or arbitrary future changes
to the guard implementation. Review the exact source before approving execution.

Independent security/runtime acceptance and actual GitHub step execution remain
separate gates. Passing local synthetic checks is not a hosted scan receipt.
No CI, release, identity or rights conclusion follows from this source change.
