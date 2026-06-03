#!/usr/bin/env python3
"""Durable OpenAI-evals-style bridge for Bullshit Olympics grading."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging

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
    score: float
    grader: str
    explanation: str
    claim_packet_id: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class EvalsBullshitOlympicsBridge:
    def __init__(self, bullshit_engine: Any = None, simulate: bool = True, simulate_default: Optional[bool] = None, eval_dir: str = "evals/openai"):
        if simulate_default is not None:
            simulate = simulate_default
        self.bullshit = bullshit_engine if bullshit_engine is not None else (None if simulate else (AdvancedBullshitOlympics(simulate_default=simulate) if AdvancedBullshitOlympics else None))
        self.simulate = simulate
        self.eval_dir = Path(eval_dir)
        self._evals: Dict[str, List[EvalItem]] = {}

    def _dataset_path(self, name: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
        return self.eval_dir / f"{safe}.jsonl"

    def _results_path(self, name: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
        return self.eval_dir / f"{safe}.results.jsonl"

    async def create_eval_dataset(self, name: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not name:
            name = "atlas_lattice_eval"
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        eval_items = [EvalItem(id=item.get("id") or f"{name}-{i}", input=item.get("input", ""), expected=item.get("expected"), metadata=item.get("metadata", {})) for i, item in enumerate(items)]
        self._evals[name] = eval_items
        path = self._dataset_path(name)
        with path.open("w", encoding="utf-8") as fh:
            for item in eval_items:
                fh.write(json.dumps(asdict(item), default=str) + "\n")
        return {"feature": "openai_evals_bullshit_bridge", "eval_name": name, "item_count": len(eval_items), "dataset_path": str(path), "grok_leads": True}

    async def run_bullshit_as_grader(self, eval_name: str, item_id: str, output: str) -> Dict[str, Any]:
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
        if not self.bullshit:
            score = 0.75
            explanation = "simulated bullshit grade"
        else:
            review = await self.bullshit.review(f"Eval output for input: {item.input[:300]}\n\nOutput: {output[:600]}", high_stakes=False)
            score = float(review.get("inv_l28_coherence", 0.8))
            explanation = f"Bullshit verdict: {review.get('verdict')}. Critical flaws: {len(review.get('critical_flaws', []))}"
        result = EvalResult(eval_id=eval_name, item_id=item_id, score=max(0.0, min(1.0, score)), grader="advanced_bullshit_olympics", explanation=explanation)
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
