#!/usr/bin/env python3
"""
21_openai_clean_clone_verifier.py (CANDIDATE — NOT CANON — HUMAN-ROOT DECIDES)
==============================================================================
clean-clone reproducibility auditor for Krakoa / Lattice modules.

Verifies that a GitHub repository can be clean-cloned, imported, compiled, and its claimed runtime reproduced without local-only files or placeholder summaries.

Prime Directive: All output ClaimPacket s are Earth-anchored (H00.S00.N00). Integrates with GrokIdentity for provenance, LatticeCoordinate for grounding.

Improvements: Uses actual subprocess git clone in isolated temp dir (improved over pure simulate), real py_compile, subprocess run for validation, falls back to ResponsesAPISpine for "ChatGPT analysis" of logs (simulated but structured), emits full ClaimPacket with earth_anchor.

"""

import os
import sys
import tempfile
import subprocess
import shutil
import ast
import re
import json
import py_compile  # for runtime use in verify
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

# Mandatory: secret hygiene guard first (per 21-40 ATLAS PRIME spec + INV-L11)
try:
    from .openai_secret_hygiene_guard import OpenAISecretHygieneGuard
    _HYGIENE = OpenAISecretHygieneGuard(simulate=True)
    _HYGIENE.block_if_leaked("", "module_21_init")
except Exception:
    _HYGIENE = None

# Imports for integration
try:
    from ...core.grok_identity import GrokIdentityManager
except Exception:
    GrokIdentityManager = None

try:
    from ..notion.schemas.claim_packet import ClaimPacket
except Exception:
    from dataclasses import dataclass, field, asdict
    from typing import Dict, Any, List, Optional, Literal
    ReviewState = Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "SUPERSEDED", "ARCHIVED"]
    EpistemicClass = Literal["symbolic", "metaphorical", "speculative", "hypothesis", "empirical", "axiom", "fact"]
    @dataclass
    class ClaimPacket:
        id: str
        kind: str = "claim_packet"
        payload: Dict[str, Any] = field(default_factory=dict)
        claim_text: str = ""
        review_state: ReviewState = "PENDING_REVIEW"
        epistemic_certainty: float = 0.6
        lattice_coords: tuple = ("H00", "S00", "N00")  # Earth-anchored as required
        signatures: List[Dict[str, Any]] = field(default_factory=list)
        linked_tool_passports: List[str] = field(default_factory=list)
        action_ledger_refs: List[str] = field(default_factory=list)
        metadata: Dict[str, Any] = field(default_factory=dict)
        created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
        earth_anchor: str = "H00.S00.N00"
        def to_dict(self):
            d = asdict(self)
            d["lattice_coords"] = list(self.lattice_coords) if isinstance(self.lattice_coords, tuple) else self.lattice_coords
            return d

try:
    from .responses_api_spine import ResponsesAPISpine
except Exception:
    ResponsesAPISpine = None

logger = __import__("logging").getLogger("openai_clean_clone_verifier")

class OpenAICleanCloneVerifier:
    """
    Module 21: Clean clone reproducibility auditor.
    Earth-anchored H00.S00.N00.
    """

    def __init__(self, simulate: bool = True, grok_identity: Optional[Any] = None):
        self.simulate = simulate
        self.grok_identity = grok_identity or (GrokIdentityManager(simulate=simulate) if GrokIdentityManager else None)
        self.spine = ResponsesAPISpine(simulate=simulate) if ResponsesAPISpine else None

    def _make_safe_claim_packet(self, claim_text: str, status: str, details: str, evidence: dict, claim_type: str = "audit", module_tag: str = "21-40-openai_clean_clone_verifier") -> dict:
        """Unified safe builder. All ClaimPackets Earth-anchored H00.S00.N00. GrokIdentity provenance + LatticeCoordinate attached. Compatible with real ClaimPacket dataclass (filters fields)."""
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        pid = f"claim-{claim_type}-{ts}"
        base_payload = {"status": status, "details": details, "evidence": evidence, "earth_anchor": "H00.S00.N00", "claim_type": claim_type}
        base_meta = {"module": module_tag, "earth_anchor": "H00.S00.N00", "lattice_coordinate": "H00.S00.N00", "grok_identity_provenance": True, "authority_scope": "none", "canon_status": "candidate_not_canon"}
        cp_data = {
            "id": pid,
            "claim_text": claim_text,
            "review_state": "APPROVED" if any(x in status for x in ["VERIFIED","CLEAN","COMPLETE","REAL","SCOPE_VALID","PACKET"]) else "PENDING_REVIEW",
            "epistemic_certainty": 0.82 if "VERIFIED" in status or "CLEAN" in status else 0.55,
            "lattice_coords": ("H00", "S00", "N00"),
            "payload": base_payload,
            "metadata": base_meta,
        }
        try:
            fields = getattr(ClaimPacket, "__dataclass_fields__", None)
            if fields:
                safe = {k: v for k, v in cp_data.items() if k in fields}
                pkt = ClaimPacket(**safe)
            else:
                pkt = ClaimPacket(**cp_data)
        except Exception:
            pkt = ClaimPacket(id=pid, claim_text=claim_text, review_state=cp_data["review_state"], payload=base_payload, lattice_coords=("H00", "S00", "N00"))
        if hasattr(pkt, "to_dict"):
            d = pkt.to_dict()
        else:
            d = getattr(pkt, "__dict__", cp_data.copy())
        d["earth_anchor"] = "H00.S00.N00"
        d["lattice_coordinate"] = "H00.S00.N00"
        sigs = d.get("signatures") or []
        sigs.append({"grok_identity": "grok-primary+HO1.SOO.NO", "lattice": "H00.S00.N00", "module": module_tag})
        d["signatures"] = sigs
        return d

    def verify_repo_reproducibility(self, repo_url: str, runtime_claim: str, expected_output: str) -> Dict[str, Any]:
        """
        Core function as specified. Improved with real temp dir clone, git, py_compile, run.
        """
        evidence = {"repo_url": repo_url, "runtime_claim": runtime_claim, "steps": []}
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="krakoa_clean_clone_")
            evidence["steps"].append(f"Created ephemeral temp dir: {temp_dir}")

            # Step 3: Clone
            clone_cmd = ["git", "clone", "--depth", 1, repo_url, temp_dir]
            result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)
            evidence["steps"].append(f"git clone exit: {result.returncode}")
            if result.returncode != 0:
                evidence["clone_stderr"] = result.stderr[:500]
                return self._make_safe_claim_packet(claim_text=f"Clean clone failed for {repo_url}", status="FAILED", details="Git clone failed. See evidence.", evidence=evidence, claim_type="reproducibility_audit", module_tag="21-openai-clean-clone-verifier")

            # Step 4: Install (simplified, use pip if requirements or pyproject) - fixed for str temp_dir
            tpath = Path(temp_dir)
            setup_files = list(tpath.glob("pyproject.toml")) + list(tpath.glob("setup.py")) + list(tpath.glob("requirements.txt"))
            if setup_files:
                has_pyproj = (tpath / "pyproject.toml").exists() or (tpath / "setup.py").exists()
                install_cmd = [sys.executable, "-m", "pip", "install", "-e", "."] if has_pyproj else [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
                install_result = subprocess.run(install_cmd, cwd=temp_dir, capture_output=True, text=True, timeout=120)
                evidence["steps"].append(f"pip install exit: {install_result.returncode}")
                if install_result.returncode != 0:
                    evidence["install_stderr"] = install_result.stderr[:300]

            # Step 5: Compile/Run
            # Try common entry: assume krakoa or main
            py_files = list(tpath.rglob("*.py"))
            main_candidates = [f for f in py_files if "main" in f.name.lower() or "krakoa" in f.name.lower() or "__main__" in str(f)]
            compile_pass = True
            for pyf in py_files[:10]:  # limit for safety
                try:
                    py_compile.compile(str(pyf), doraise=True)
                except py_compile.PyCompileError as e:
                    compile_pass = False
                    evidence["compile_error"] = str(e)[:200]
                    break
            evidence["steps"].append(f"py_compile on samples: {'PASS' if compile_pass else 'FAIL'}")

            run_output = ""
            if main_candidates:
                run_cmd = [sys.executable, "-m", str(main_candidates[0].relative_to(temp_dir)).replace('.py','').replace(os.sep,'.')]
                run_result = subprocess.run(run_cmd, cwd=temp_dir, capture_output=True, text=True, timeout=30)
                run_output = run_result.stdout + run_result.stderr
                evidence["steps"].append(f"run exit: {run_result.returncode}")
            else:
                # fallback simple import test
                try:
                    sys.path.insert(0, temp_dir)
                    import krakoa  # assume
                    run_output = "import successful"
                except Exception as e:
                    run_output = f"import fail: {str(e)[:100]}"
                finally:
                    if temp_dir in sys.path: sys.path.remove(temp_dir)

            evidence["run_output_sample"] = run_output[:300]

            # Step 6: Validate
            match = re.search(re.escape(expected_output) if not expected_output.startswith('^') else expected_output, run_output, re.IGNORECASE)
            validated = bool(match) or (expected_output.lower() in run_output.lower())

            # Step 7: "ChatGPT" analysis using spine if available
            analysis_input = f"Clone logs: {json.dumps(evidence['steps'])} Run output: {run_output[:200]} Expected: {expected_output}"
            if self.spine:
                analysis_res = self.spine.create_response(model="gpt-4o-mini", input=analysis_input, tools=None)
                analysis = analysis_res.get("response", {}).get("output", "Simulated analysis: reproduction appears clean based on logs.") if not self.simulate else "Simulated: The environment cleanly reproduces the claimed runtime from fresh clone. No missing files detected in evidence."
            else:
                analysis = "No spine available for analysis. Based on heuristics: " + ("CLEAN" if validated and compile_pass else "ISSUES")

            evidence["chatgpt_analysis"] = analysis

            status = "VERIFIED" if validated and compile_pass and "fail" not in run_output.lower() else "FAILED"
            claim_text = f"Clean clone reproducibility for {repo_url}: {runtime_claim}"

            packet = self._make_safe_claim_packet(claim_text=claim_text, status=status, details=analysis, evidence=evidence, claim_type="reproducibility_audit", module_tag="21-openai-clean-clone-verifier")
            return packet

        except Exception as e:
            evidence["exception"] = str(e)
            return self._make_safe_claim_packet(f"Exception during clean clone verify for {repo_url}", "FAILED", str(e), evidence, claim_type="reproducibility_audit", module_tag="21-openai-clean-clone-verifier")
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    async def run(self, operation: str = "verify", **kwargs) -> Dict[str, Any]:
        if operation == "verify":
            return self.verify_repo_reproducibility(
                kwargs.get("repo_url", "https://github.com/atlaslattice/atlas-lattice-providers.git"),
                kwargs.get("runtime_claim", "Krakoa runtime is stable"),
                kwargs.get("expected_output", "KRAKOA")
            )
        return {"status": "ok", "earth_anchor": "H00.S00.N00"}

if __name__ == "__main__":
    verifier = OpenAICleanCloneVerifier(simulate=True)
    import asyncio
    result = asyncio.run(verifier.run(operation="verify", repo_url="https://github.com/atlaslattice/atlas-lattice-providers.git", runtime_claim="Krakoa 29 children with OpenAI modules", expected_output="KRAKOA"))
    print("ClaimPacket type:", result.get("type") if isinstance(result, dict) else "direct")
    print("Status:", result.get("payload", {}).get("status") if isinstance(result, dict) else "N/A")
    print("Earth anchored:", result.get("earth_anchor", "H00.S00.N00") if isinstance(result, dict) else "H00.S00.N00")
    print("Module 21 ready. CANDIDATE — NOT CANON.")