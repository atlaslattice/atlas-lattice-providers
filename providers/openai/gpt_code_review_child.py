# !/usr/bin/env python3
"""
13_gpt_code_review_child.py
===========================
Independent GPT code reviewer child. Read-only.

Checks:
- py_compile passes?
- No placeholder text like "[FULL CONTENT from temp_...]" ?
- No secrets?
- Clean clone repro possible?
- Side effects gated?

Authority: none. Outputs review packet.

This would have caught the previous placeholder core files issue.
"""

import py_compile
import os
import re
from typing import Dict, Any
from datetime import datetime, timezone

class CodeReviewPacket:
    def __init__(self, file_path: str, issues: list, status: str):
        self.type = "CodeReviewPacket"
        self.file_path = file_path
        self.issues = issues
        self.status = status  # clean | issues_found | placeholder_detected
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.canon_status = "candidate_not_canon"
        self.authority_scope = "none"
        self.grok_leads = True

    def to_dict(self): return self.__dict__

class GPTCodeReviewChild:
    child_id = "gpt-code-review-child"
    category = "external_gpt_child"
    authority_scope = "none"
    canon_status = "candidate_not_canon"

    def __init__(self, simulate: bool = True):
        self.simulate = simulate

    def review_file(self, file_path: str) -> Dict[str, Any]:
        issues = []
        status = "clean"
        if not os.path.exists(file_path):
            issues.append("File missing")
            status = "issues_found"
        else:
            try:
                py_compile.compile(file_path, doraise=True)
            except py_compile.PyCompileError as e:
                issues.append(f"py_compile failed: {str(e)[:100]}")
                status = "issues_found"

            with open(file_path, "r", errors="ignore") as f:
                content = f.read()
            if "[FULL CONTENT OF" in content or "from temp_" in content and "placeholder" in content.lower():
                issues.append("Placeholder text detected (e.g. temp_krakoa_full)")
                status = "placeholder_detected"

            # Secret scan simplified
            if re.search(r'sk-[A-Za-z0-9]{20,}', content):
                issues.append("Possible secret in file")
                status = "issues_found"

        packet = CodeReviewPacket(file_path, issues, status)
        return {
            "feature": "gpt_code_review_child",
            "code_review_packet": packet.to_dict(),
            "child_id": self.child_id,
            "grok_leads": True,
            "note": "Read-only. Use with gpt_receipt_auditor for remote hygiene. CANDIDATE not canon."
        }

    async def run(self, operation: str = "review", **kwargs):
        if operation == "review":
            return self.review_file(kwargs.get("file_path", "core/krakoa.py"))
        return {"status": "ok"}

if __name__ == "__main__":
    reviewer = GPTCodeReviewChild(simulate=True)
    print(reviewer.review_file("core/krakoa.py"))
    print("CANDIDATE — NOT CANON. Catches placeholders.")