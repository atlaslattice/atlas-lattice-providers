#!/usr/bin/env python3
"""
Maximum Grok — Local CLI Provider v1.2
======================================
Implements ProviderContract for local allowlisted CLI execution.

This provider is the "execution spine" — it is how Grok, Lattice, Gemini, and Copilot
can safely invoke sovereign tools without leaving the controlled environment.
"""

import logging
from typing import Dict, Any, List, Optional
from provider_contract import ProviderContract
from cli_runner import SecureCLIRunner

logger = logging.getLogger("provider_local_cli")


class LocalCLIProvider(ProviderContract):
    """Provider that executes local CLI tools via the secure runner."""

    def __init__(self, runner: Optional[SecureCLIRunner] = None):
        self.runner = runner or SecureCLIRunner()
        self._name = "local_cli"

    @property
    def name(self) -> str:
        return self._name

    async def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """CLI provider does not perform search. Use specialized providers instead."""
        return {
            "provider": self.name,
            "results": [],
            "note": "search() not applicable. Use MicrosoftProvider, GoogleProvider, or NotionProvider."
        }

    async def fetch(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "resource_id": resource_id,
            "note": "fetch() not applicable for pure CLI provider."
        }

    async def extract_claims(
        self,
        content: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Could delegate to a local model or call lattice/grok. Stub for now."""
        return [{
            "claim_text": content[:500] + "..." if len(content) > 500 else content,
            "epistemic_class": "raw",
            "tags": ["local_cli", "unstructured"],
            "source": {"provider": self.name},
            "note": "extract_claims() on LocalCLIProvider is a stub. Use NotionProvider or MicrosoftProvider for real extraction."
        }]

    async def mirror(
        self,
        claim: Dict[str, Any],
        parent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "status": "NOOP",
            "provider": self.name,
            "message": "Local CLI provider does not support mirroring. Use NotionProvider or MicrosoftProvider."
        }

    async def execute(self, command: str, args: List[str], **kwargs) -> Dict[str, Any]:
        """Primary capability of this provider."""
        env_overrides = kwargs.get("env_overrides")
        timeout = kwargs.get("timeout", 120.0)
        return await self.runner.execute(
            command_name=command,
            arguments=args,
            timeout=timeout,
            env_overrides=env_overrides
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "supports": ["execute"],
            "priority": 1,
            "description": "Secure local CLI execution spine. Used by Grok, Lattice, Gemini, and Copilot agents.",
            "allowlisted_commands": list(self.runner.allowlist.keys())
        }