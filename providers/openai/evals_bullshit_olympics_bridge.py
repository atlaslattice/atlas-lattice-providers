#!/usr/bin/env python3
"""Durable OpenAI-evals-style bridge for Bullshit Olympics grading."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging
import math
import re

logger = logging.getLogger("openai_evals_bullshit_bridge")

try:
    from ..bullshit_olympics import BullshitOlympics as AdvancedBullshitOlympics
except Exception:
    AdvancedBullshitOlympics = None


@dataclass
class EvalItem:
    id: str
    input: str
    expected: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    eval_id: str
    item_id: str
    score: Optional[float]
    grader: str
    explanation: str
    status: str = "NOT_RUN"
    score_basis: str = "NONE"
    claim_packet_id: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))


class EvalsBullshitOlympicsBridge:
    def __init__(self, bullshit_engine: Any = None, simulate: bool = True, simulate_default: Optional[bool] = None, eval_dir: str = "evals/openai"):
        if simulate_default is not None:
            simulate = simulate_default
        self.bullshit = bullshit_engine if bullshit_engine is not None else (None if simulate else (AdvancedBullshitOlympics(simulate_default=simulate) if AdvancedBullshitOlympics else None))
        self.simulate = simulate
        self.eval_dir = Path(eval_dir)
        self._evals: Dict[str, List[EvalItem]] = {}

    @staticmethod
    def _checked_eval_name(name: str) -> str:
        # No lossy filename normalization: "a/b" and "a_b" MUST NOT alias.
        # This is a single, portable namespace, not a filesystem path or host grant.
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
            raise ValueError("eval_name must be 1..80 ASCII letters, digits, '-' or '_'")
        return name

    def _dataset_path(self, name: str) -> Path:
        return self.eval_dir / f"{self._checked_eval_name(name)}.jsonl"

    def _results_path(self, name: str) -> Path:
        return self.eval_dir / f"{self._checked_eval_name(name)}.results.jsonl"

    async def create_eval_dataset(self, name: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if name is None or name == "":
            name = "atlas_lattice_eval"
        name = self._checked_eval_name(name)
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("items must be a list of dictionaries")
        eval_items = [EvalItem(id=item.get("id") or f"{name}-{i}", input=item.get("input", ""), expected=item.get("expected"), metadata=item.get("metadata", {})) for i, item in enumerate(items)]
        # Serialize before opening, so a bad input cannot leave a partly written file.
        text = "".join(json.dumps(asdict(item), default=str) + "\n" for item in eval_items)
        path = self._dataset_path(name)
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        # Exclusive creation is atomic at the path level. Existing datasets,
        # including symlinks and previous versions, are never overwritten.
        with path.open("x", encoding="utf-8") as fh:
            fh.write(text)
        # An unsuccessful write must not replace the in-memory dataset either.
        self._evals[name] = eval_items
        return {"feature": "openai_evals_bullshit_bridge", "eval_name": name, "item_count": len(eval_items), "dataset_path": str(path), "grok_leads": True}

    async def run_bullshit_as_grader(self, eval_name: str, item_id: str, output: str) -> Dict[str, Any]:
        try:
            self._checked_eval_name(eval_name)
        except ValueError:
            return {"error": "invalid_eval_name"}
        item = next((it for it in self._evals.get(eval_name, []) if it.id == item_id), None)
        if not item:
            path = self._dataset_path(eval_name)
            if path.exists():
                with path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        data = json.loads(line)
                        if data.get("id") == item_id:
                            item = EvalItem(**data)
                            break
        if not item:
            return {"error": "item_not_found", "eval_name": eval_name, "item_id": item_id}
        # Simulation is only a test fixture, never a scored evaluation.
        score = None
        status = "NOT_RUN"
        score_basis = "NONE"
        grader = "none"
        explanation = "No evaluation executed (simulation or grader unavailable)"
        if not self.simulate and self.bullshit is not None:
            try:
                review = await self.bullshit.review(
                    f"Eval output for input: {item.input[:300]}\n\nOutput: {output[:600]}",
                    high_stakes=False,
                )
            except Exception:
                # Backend failure is not an endorsement, and private exception text
                # must not escape into an exported result ledger.
                logger.warning("Evaluation backend failed; no grade recorded")
                status = "GRADER_FAILED"
                explanation = "Evaluation backend failed; no grade recorded"
            else:
                raw_score = review.get("inv_l28_coherence") if isinstance(review, dict) else None
                if (isinstance(raw_score, (float, int)) and not isinstance(raw_score, bool)
                        and math.isfinite(raw_score) and 0.0 <= raw_score <= 1.0):
                    score = float(raw_score)
                    status = "SCORED"
                    score_basis = "BACKEND_RESPONSE_UNVERIFIED"
                    grader = "advanced_bullshit_olympics"
                    explanation = "Backend returned a numeric grade; independent review not established"
                else:
                    status = "INVALID_GRADE"
                    explanation = "Backend result lacked a finite numeric 0..1 grade"
        result = EvalResult(
            eval_id=eval_name, item_id=item_id, score=score, grader=grader,
            explanation=explanation, status=status, score_basis=score_basis,
        )
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        with self._results_path(eval_name).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(result), default=str) + "\n")
        return {"feature": "openai_evals_bullshit_olympics_bridge", "eval_result": asdict(result), "grok_leads": True, "lattice_routes": True, "symbiosis": "bullshit_olympics -> openai_evals"}

    async def run(self, operation: str = "create_dataset", **kwargs: Any) -> Dict[str, Any]:
        if operation == "create_dataset":
            return await self.create_eval_dataset(kwargs.get("name"), kwargs.get("items", []))
        if operation == "grade_with_bullshit":
            return await self.run_bullshit_as_grader(kwargs.get("eval_name"), kwargs.get("item_id"), kwargs.get("output", ""))
        return {"status": "unknown_op", "op": operation}


if __name__ == "__main__":
    print("Evals <-> Bullshit Olympics Bridge ready.")
