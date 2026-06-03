#!/usr/bin/env python3
"""Workload identity and environment hygiene checks for OpenAI interop."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import os


class WorkloadIdentitySecretsHygiene:
    REQUIRED_ENV = ["OPENAI_API_KEY"]
    OPTIONAL_ENV = ["OPENAI_ORG_ID", "OPENAI_PROJECT_ID", "GITHUB_TOKEN", "NOTION_API_KEY", "XAI_API_KEY", "GOOGLE_API_KEY", "MS_GRAPH_TOKEN"]

    def __init__(self, simulate: bool = True, simulate_default: Optional[bool] = None):
        if simulate_default is not None:
            simulate = simulate_default
        self.simulate = simulate

    def check_environment(self) -> Dict[str, Any]:
        report = {"timestamp": datetime.utcnow().isoformat() + "Z", "present": {}, "missing_required": [], "recommendations": []}
        for key in self.REQUIRED_ENV + self.OPTIONAL_ENV:
            present = bool(os.getenv(key))
            report["present"][key] = "PRESENT" if present else "MISSING"
            if key in self.REQUIRED_ENV and not present:
                report["missing_required"].append(key)
        if report["missing_required"]:
            report["recommendations"].append("Set OPENAI_API_KEY locally or in the deployment environment; never commit key material.")
        report["recommendations"].append("Prefer short-lived workload identity/OIDC and environment injection for CI/deploy flows.")
        report["recommendations"].append("Keep CI smoke tests in simulation mode so public pull requests do not require credentials.")
        return {"feature": "openai_workload_identity_secrets_hygiene", "report": report, "grok_leads": True}

    def scan_for_obvious_literals(self, root: str = ".") -> Dict[str, Any]:
        findings: List[str] = []
        for path in Path(root).rglob("*"):
            if path.is_dir() or any(part.startswith(".git") for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".md", ".yml", ".yaml", ".json", ".txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:200000]
            except Exception:
                continue
            if "sk-" in text or "OPENAI_API_KEY=" in text:
                findings.append(str(path))
        return {"feature": "secrets_hygiene", "finding_count": len(findings), "findings": findings[:20], "grok_leads": True}

    async def run(self, operation: str = "check", **kwargs: Any) -> Dict[str, Any]:
        if operation == "check":
            return self.check_environment()
        if operation == "scan_for_secrets":
            return self.scan_for_obvious_literals(kwargs.get("root", "."))
        return {"status": "unknown_op", "op": operation}

    def enforce_env_only(self) -> None:
        return None


if __name__ == "__main__":
    print(WorkloadIdentitySecretsHygiene().check_environment())
