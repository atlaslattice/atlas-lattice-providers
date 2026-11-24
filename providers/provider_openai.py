#!/usr/bin/env python3
"""First-class OpenAI provider wrapper for Atlas Lattice interop."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .provider_contract import ProviderContract
from .openai import ResponsesAPISpine, StructuredOutputSchemaSpine, ToolPassportFunctionCalling, OpenAITracingToGoldenTrace, EvalsBullshitOlympicsBridge, WorkloadIdentitySecretsHygiene


class OpenAIProvider(ProviderContract):
    def __init__(self, simulate: bool = True, **kwargs: Any):
        self._name = "openai"
        self.responses = ResponsesAPISpine(simulate=simulate)
        self.structured = StructuredOutputSchemaSpine(simulate=simulate)
        self.tools = ToolPassportFunctionCalling(schema_spine=self.structured, simulate=simulate)
        self.traces = OpenAITracingToGoldenTrace(simulate=simulate)
        self.evals = EvalsBullshitOlympicsBridge(simulate=simulate)
        self.hygiene = WorkloadIdentitySecretsHygiene(simulate=simulate)

    @property
    def name(self) -> str:
        return self._name

    async def search(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        return await self.responses.create_response(input=query, metadata={"operation": "search_like_response"}, **kwargs)

    async def fetch(self, resource_id: str, **kwargs: Any) -> Dict[str, Any]:
        return {"provider": self.name, "resource_id": resource_id, "status": "not_applicable", "note": "OpenAIProvider is a model/tool bridge; fetch should use file_search or a storage provider."}

    async def extract_claims(self, content: str, source_metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        claim = self.structured.validate_claim_packet({"claim_text": content[:1000], "payload": {"source_metadata": source_metadata or {}}})
        return [claim.to_dict()]

    async def mirror(self, claim: Dict[str, Any], parent: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        validated = self.structured.validate_claim_packet(claim)
        return {"provider": self.name, "status": "validated_for_openai_interop", "claim": validated.to_dict(), "parent": parent}

    async def execute(self, command: str, args: List[str], **kwargs: Any) -> Dict[str, Any]:
        if command in ("response", "responses.create"):
            prompt = " ".join(args) if args else kwargs.pop("input", "")
            return await self.responses.create_response(input=prompt, **kwargs)
        if command == "hygiene":
            return self.hygiene.check_environment()
        return {"provider": self.name, "status": "unsupported_command", "command": command}

    def capabilities(self) -> Dict[str, Any]:
        return {"provider": self.name, "supports_responses": True, "supports_structured_claims": True, "supports_tool_passports": True, "supports_trace_receipts": True, "supports_eval_exports": True, "requires_openai_api_key_for_live": True}

    async def run(self, operation: str, **kwargs: Any) -> Dict[str, Any]:
        if operation in ("response", "responses.create"):
            return await self.responses.create_response(**kwargs)
        if operation == "validate_claim":
            return {"validated_claim": self.structured.validate_claim_packet(kwargs.get("raw_output", {})).to_dict()}
        if operation == "trace":
            return await self.traces.record_openai_trace(**kwargs)
        if operation == "hygiene":
            return self.hygiene.check_environment()
        return {"status": "unknown_op", "operation": operation}
