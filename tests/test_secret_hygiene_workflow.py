"""Exercise the actual workflow Python with synthetic guard reports only.

The provider import is replaced in the parsed AST. No provider, filesystem scan,
environment lookup or credential resolution executes in this suite.
"""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/secret_hygiene.yml"


def workflow_program():
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = lines.index("          python - <<'PY'") + 1
    end = lines.index("          PY", start)
    source = "\n".join(line[10:] for line in lines[start:end])
    tree = ast.parse(source)
    imports = [node for node in tree.body
               if isinstance(node, ast.ImportFrom)
               and node.module == "providers.openai.openai_secret_hygiene_guard"]
    if len(imports) != 1 or [alias.name for alias in imports[0].names] != ["OpenAISecretHygieneGuard"]:
        raise ValueError("workflow guard import changed; review the fixture boundary")
    tree.body = [node for node in tree.body if node is not imports[0]]
    return compile(tree, str(WORKFLOW), "exec")


def execute_report(result):
    calls = []
    class FixtureGuard:
        def __init__(self, *, simulate):
            calls.append(("construct", simulate))
        def scan_codebase(self, root):
            calls.append(("scan", root))
            return copy.deepcopy(result)
    output = io.StringIO()
    status = 0
    with contextlib.redirect_stdout(output):
        try:
            exec(workflow_program(), {"OpenAISecretHygieneGuard": FixtureGuard})
        except SystemExit as error:
            status = error.code
    return status, output.getvalue(), calls


def report(**changes):
    value = {"status": "clean", "scanned_files": 3, "hits": []}
    value.update(changes)
    return {"report": value}


class SecretHygieneWorkflowTests(unittest.TestCase):
    def test_clean_nonempty_report_passes_without_coverage_claim(self):
        status, output, calls = execute_report(report())
        self.assertEqual(status, 0)
        summary = json.loads(output.splitlines()[0])
        self.assertFalse(summary["coverage_attested"])
        self.assertEqual(summary["reported_hit_count"], 0)
        self.assertEqual(calls, [("construct", True), ("scan", ".")])

    def test_reported_detection_fails_without_disclosing_hit(self):
        marker = "SYNTHETIC_SENSITIVE_LITERAL_DO_NOT_PRINT"
        status, output, _ = execute_report(report(status="SECRETS_DETECTED_BLOCK",
                                                 hits=[{"match_preview": marker}]))
        self.assertEqual(status, 1)
        self.assertNotIn(marker, output)
        self.assertEqual(json.loads(output.splitlines()[0])["reported_hit_count"], 1)

    def test_clean_status_with_nonempty_findings_fails(self):
        status, _, _ = execute_report(report(hits=[{"source": "synthetic.py"}]))
        self.assertEqual(status, 1)

    def test_zero_scan_does_not_pass(self):
        status, _, _ = execute_report(report(scanned_files=0))
        self.assertEqual(status, 1)

    def test_malformed_report_shapes_fail(self):
        for value in (None, [], {}, {"report": None}, {"report": {}}, report(hits=None)):
            with self.subTest(value=value):
                self.assertEqual(execute_report(value)[0], 1)

    def test_invalid_scan_counts_fail(self):
        for count in (True, False, -1, "3", 3.0, None):
            with self.subTest(count=count):
                self.assertEqual(execute_report(report(scanned_files=count))[0], 1)

    def test_unknown_status_is_held_and_redacted(self):
        marker = "SYNTHETIC_PRIVATE_STATUS_VALUE"
        status, output, _ = execute_report(report(status=marker))
        self.assertEqual(status, 1)
        self.assertNotIn(marker, output)
        self.assertEqual(json.loads(output.splitlines()[0])["status"], "UNKNOWN_OR_MALFORMED")


if __name__ == "__main__":
    unittest.main()
