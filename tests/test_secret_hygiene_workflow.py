"""Exercise the actual workflow Python with synthetic guard reports only.

The source-loader function is replaced in the parsed AST. No provider, filesystem scan,
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
    loaders = [node for node in tree.body if isinstance(node, ast.FunctionDef)
               and node.name == "load_guard"]
    if len(loaders) != 1:
        raise ValueError("workflow source loader changed; review the fixture boundary")
    tree.body = [node for node in tree.body if node is not loaders[0]]
    return compile(tree, str(WORKFLOW), "exec")


def execute_report(result):
    calls = []
    class FixtureGuard:
        def __init__(self, *, simulate):
            calls.append(("construct", simulate))
        def scan_files(self, root, *, paths):
            calls.append(("scan", root, paths))
            return copy.deepcopy(result)
    output = io.StringIO()
    status = 0
    with contextlib.redirect_stdout(output):
        try:
            exec(workflow_program(), {"load_guard": lambda: FixtureGuard})
        except SystemExit as error:
            status = error.code
    return status, output.getvalue(), calls


def report(**changes):
    value = {"status": "clean", "scanned_files": 5, "requested_files": 5,
             "hits": [], "errors": [], "selected_inputs_complete": True,
             "scope": "explicit_work_source_files"}
    value.update(changes)
    return {"report": value}


class SecretHygieneWorkflowTests(unittest.TestCase):
    def test_clean_nonempty_report_passes_without_coverage_claim(self):
        status, output, calls = execute_report(report())
        self.assertEqual(status, 0)
        summary = json.loads(output.splitlines()[0])
        self.assertFalse(summary["whole_repository_coverage_attested"])
        self.assertEqual(summary["reported_hit_count"], 0)
        self.assertEqual(calls, [("construct", True), ("scan", ".", (
            "providers/openai/openai_secret_hygiene_guard.py",
            ".github/workflows/secret_hygiene.yml",
            "tests/test_secret_hygiene_workflow.py",
            "tests/test_secret_hygiene_files.py",
            "docs/WORK_SOURCE_HYGIENE.md",
        ))])

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

    def test_input_errors_fail_without_disclosing_error_content(self):
        marker = "SYNTHETIC_PRIVATE_EXCEPTION"
        status, output, _ = execute_report(report(errors=[{"message": marker}]))
        self.assertEqual(status, 1)
        self.assertNotIn(marker, output)
        self.assertEqual(json.loads(output.splitlines()[0])["input_error_count"], 1)

    def test_incomplete_selection_fails(self):
        for changes in ({"scanned_files": 4}, {"requested_files": 4},
                        {"selected_inputs_complete": False}, {"selected_inputs_complete": 1}):
            with self.subTest(changes=changes):
                self.assertEqual(execute_report(report(**changes))[0], 1)

    def test_wrong_scope_fails(self):
        self.assertEqual(execute_report(report(scope="whole_tree"))[0], 1)


if __name__ == "__main__":
    unittest.main()
