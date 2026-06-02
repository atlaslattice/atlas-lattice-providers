#!/usr/bin/env python3
"""
Microsoft Copilot Multi-Cloud CLI Bridge Adapter
================================================
Provides a clean, asynchronous bridge for Microsoft Copilot (or other Azure-native
services) to invoke allowlisted local CLI tools while automatically injecting
multi-cloud session credentials.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List
from cli_runner import SecureCLIRunner

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_ms_cli_bridge")

class CopilotCLIBridge:
    """Manages secure CLI tool invocation and credential inheritance for multi-cloud workflows."""
    
    def __init__(self):
        self.runner = SecureCLIRunner()

    def _prepare_multicloud_environment(self) -> Dict[str, str]:
        """
        Gathers Azure session variables and maps them to standard GCP environment vars,
        ensuring secure authentication inheritance during cross-cloud handoffs.
        """
        env_copy = os.environ.copy()
        
        azure_token = os.getenv("AZURE_ACCESS_TOKEN")
        if azure_token:
            logger.info("Azure active session detected. Mapping cross-cloud token contexts...")
            env_copy["GOOGLE_EXTERNAL_OAUTH_TOKEN"] = azure_token
            
        gcp_project = os.getenv("GCP_PROJECT_ID") or os.getenv("AZURE_PROJECT_ID")
        if gcp_project:
            env_copy["GCLOUD_PROJECT"] = gcp_project
            
        return env_copy

    async def run_grok_canon_diff(self, target: str) -> Dict[str, Any]:
        """
        Invoke the local 'grok' CLI tool to calculate canonical differences.
        Automatically inherits the multi-cloud authentication environment.
        """
        logger.info(f"Copilot Bridge: Executing grok canon diff on target: '{target}'")
        arguments = ["canon", "diff", target]
        prepared = self._prepare_multicloud_environment()
        return await self.runner.execute("grok", arguments, prepared_env=prepared)

    async def run_lattice_optimization(self, model: str) -> Dict[str, Any]:
        """
        Invoke the local 'lattice' CLI tool to execute optimization sweeps.
        """
        logger.info(f"Copilot Bridge: Initiating lattice optimization for model: '{model}'")
        arguments = ["optimize", "--model", model]
        prepared = self._prepare_multicloud_environment()
        return await self.runner.execute("lattice", arguments, prepared_env=prepared)
