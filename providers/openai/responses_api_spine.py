#!/usr/bin/env python3
"""OpenAI Responses API spine with simulation-safe real SDK support."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = __import__("logging").getLogger("openai_responses_spine")


class ResponsesAPISpine:
    def __init__(self, simulate: bool = True, simulate_default: Optional[bool] = None, client: Any = None):
        if simulate_default is not None:
            simulate = simulate_default
        self.simulate = simulate
        self.client = client

    def _enabled_for_live_call(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY")) and not self.simulate

    def _make_client(self) -> Any:
        if self.client is not None:
            return self.client
        from openai import AsyncOpenAI  # type: ignore
        self.client = AsyncOpenAI()
        return self.client

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        text = getattr(response, "output_text", None)
        if text:
            return str(text)
        try:
            data = response.model_dump() if hasattr(response, "model_dump") else dict(response)
            chunks: List[str] = []
            for item in data.get("output", []) or []:
                for content in item.get("content", []) or []:
                    if "text" in content:
                        chunks.append(str(content["text"]))
            return "\n".join(chunks) if chunks else json.dumps(data, default=str)[:4000]
        except Exception:
            return str(response)[:4000]

    async def create_response(self, model: str = "gpt-4.1-mini", input: str = "", tools: Optional[list] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        metadata = metadata or {}
        timestamp = datetime.utcnow().isoformat() + "Z"
        used_live_api = False
        error = None

        if not self._enabled_for_live_call():
            output = f"[simulated OpenAI Responses API] Processed: {input[:240]}"
            raw_response: Dict[str, Any] = {"mode": "simulate"}
        else:
            try:
                client = self._make_client()
                payload: Dict[str, Any] = {"model": model, "input": input}
                if tools:
                    payload["tools"] = tools
                if metadata:
                    payload["metadata"] = metadata
                payload.update(kwargs)
                response = await client.responses.create(**payload)
                used_live_api = True
                output = self._extract_output_text(response)
                raw_response = response.model_dump() if hasattr(response, "model_dump") else {"raw": str(response)[:4000]}
            except Exception as exc:
                error = str(exc)
                logger.warning("OpenAI Responses call failed; using fallback: %s", exc)
                output = f"[fallback after OpenAI error] Processed: {input[:240]}"
                raw_response = {"mode": "fallback", "error": error}

        claim = {
            "type": "OpenAIResponsesClaimPacket",
            "model": model,
            "input": input[:2000],
            "output": output[:4000],
            "tools_used": [t.get("name") or t.get("function", {}).get("name") for t in (tools or []) if isinstance(t, dict)],
            "timestamp": timestamp,
            "openai_live_api": used_live_api,
            "error": error,
            "metadata": metadata,
            "grok_leads": True,
            "lattice_routes": True,
        }
        return {"feature": "openai_responses_api_spine", "response": {"output": output, "raw": raw_response}, "claim_packet": claim, "grok_leads": True, "lattice_routes": True}

    async def run(self, operation: str = "create", **kwargs: Any) -> Dict[str, Any]:
        if operation in ("create", "responses.create"):
            return await self.create_response(**kwargs)
        if operation == "status":
            return {"status": "ready", "simulate": self.simulate, "live_call_enabled": self._enabled_for_live_call()}
        return {"status": "unknown_op", "op": operation}


if __name__ == "__main__":
    print("Responses API Spine ready.")
