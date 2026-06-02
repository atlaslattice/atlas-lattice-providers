#!/usr/bin/env python3
"""
Multi-Cloud Integration Environment Setup and Validator
=======================================================
Verifies that all standard dependencies, local directory structures,
and required authentication tokens are correctly configured and secure.

This script should be run before starting the unified MCP server
(multi_provider_mcp_server.py) or any CLI tools in the Maximum Grok
provider layer to ensure Google interop (Drive, Gemini) and other
multi-cloud features are ready.

Adapted for atlas-lattice-providers architecture with support for:
- Google Drive/Gemini via google-api-python-client + google-genai
- xAI Grok, Microsoft, Notion providers
- Existing config/ for tokens and client secrets
"""

import os
import sys
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("env_setup")

REQUIRED_PACKAGES = {
    "googleapiclient": "google-api-python-client",
    "google.auth": "google-auth",
    "google.genai": "google-genai",  # Modern for Gemini 3.x, Omni video, Spark, 3 Pro Image, MedGemma, Ask Maps, Agent Platform, Workspace Studio, etc. (all 40+ I/O 2026 + next 20)
    "google.generativeai": "google-generativeai",  # Legacy; prefer google-genai
    "google-cloud-aiplatform": "google-cloud-aiplatform",  # Optional for Agent Studio/Registry/Observability, Agentic Data Cloud, TPU, high-concurrency (use if Vertex endpoints needed)
    "pydantic": "pydantic"
}

REQUIRED_FILES = [
    "config/client_secrets.json",
    "config/token.json"  # For Google OAuth tokens, used by provider_google.py
]

# Additional env vars relevant to our full multi-cloud setup
ADDITIONAL_ENV_VARS = [
    "XAI_API_KEY",           # For xAI Grok API
    "MS_GRAPH_TOKEN",        # For Microsoft provider
    "AZURE_TENANT_ID",       # For MS
    "NOTION_API_KEY"         # For Notion advanced integrations
]

def check_dependencies() -> bool:
    """Verify that all required standard libraries are installed."""
    all_present = True
    logger.info("Checking Python package dependencies...")
    for module_name, package_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
            logger.info(f"  [OK] {package_name} is installed.")
        except ImportError:
            logger.error(f"  [MISSING] {package_name} is not installed.")
            all_present = False
    return all_present

def check_configuration_files() -> bool:
    """Verify that the required local config directories and files exist."""
    all_present = True
    logger.info("Checking local configuration files...")
    
    # Ensure config directory exists (as used by provider_google.py and others)
    if not os.path.exists("config"):
        os.makedirs("config")
        logger.info("  Created missing 'config' directory.")

    for file_path in REQUIRED_FILES:
        if os.path.exists(file_path):
            logger.info(f"  [OK] Found configuration file: {file_path}")
            # Basic JSON validation
            try:
                with open(file_path, "r") as f:
                    json.load(f)
                logger.info(f"  [OK] {file_path} is valid JSON.")
            except json.JSONDecodeError:
                logger.error(f"  [ERROR] {file_path} contains invalid JSON.")
                all_present = False
        else:
            logger.warning(f"  [MISSING] Configuration file is absent: {file_path}")
            all_present = False
            
    return all_present

def check_environment_variables() -> Dict[str, str]:
    """
    Checks for required authentication variables.
    Reports presence without exposing sensitive token contents.
    Extends the provided spec with our full stack (xAI, MS, Notion, Google).
    """
    logger.info("Checking environment variables...")
    status = {}
    
    # Check Gemini API Key (for GoogleProvider Gemini integration)
    gemini_key = os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        # Check standard key prefix pattern securely
        if gemini_key.startswith("AIzaSy"):
            status["GOOGLE_API_KEY"] = "PRESENT (Valid format)"
            logger.info("  [OK] GOOGLE_API_KEY is configured with a valid format.")
        else:
            status["GOOGLE_API_KEY"] = "PRESENT (Incorrect format)"
            logger.warning("  [WARNING] GOOGLE_API_KEY is present but does not match standard patterns.")
    else:
        status["GOOGLE_API_KEY"] = "MISSING"
        logger.warning("  [MISSING] GOOGLE_API_KEY is not configured in the environment.")

    # Note: Next 20 Google bleeding-edge (Gemini Omni video edit, Spark proactive, Agent Studio/Registry/Identity/Gateway/Observability, Skill Registry, MedGemma offline, Workspace Studio, Ask Maps, AI Content Detection, Priority PayGo, Multi-Regional Memory, Agentic Data Cloud, Android Emulator/ADB, Video-Poster) are covered via GOOGLE_API_KEY + google-genai + cli_runner (antigravity/adb). For full Agent Platform/Vertex use google-cloud-aiplatform (optional). client_secrets.json enables standard OAuth for Drive/Studio.

    # Check Multi-Cloud Access Token (from CopilotCLIBridge or direct)
    mc_token = os.getenv("GOOGLE_EXTERNAL_OAUTH_TOKEN") or os.getenv("AZURE_ACCESS_TOKEN")
    if mc_token:
        status["MULTI_CLOUD_TOKEN"] = "PRESENT"
        logger.info("  [OK] Multi-cloud access token is active in the environment.")
    else:
        status["MULTI_CLOUD_TOKEN"] = "MISSING"
        logger.info("  [INFO] No active multi-cloud session token detected (bridge may provide at runtime).")

    # Check xAI Grok key (integrated for grok CLI and AdvancedCapabilitiesEngine)
    xai_key = os.getenv("XAI_API_KEY")
    if xai_key:
        if xai_key.startswith("xai-"):
            status["XAI_API_KEY"] = "PRESENT (Valid format)"
            logger.info("  [OK] XAI_API_KEY is configured with a valid format.")
        else:
            status["XAI_API_KEY"] = "PRESENT (Incorrect format)"
            logger.warning("  [WARNING] XAI_API_KEY present but format unexpected.")
    else:
        status["XAI_API_KEY"] = "MISSING"
        logger.warning("  [MISSING] XAI_API_KEY is not configured (needed for Grok API features).")

    # Check Microsoft/Graph
    ms_token = os.getenv("MS_GRAPH_TOKEN")
    if ms_token:
        status["MS_GRAPH_TOKEN"] = "PRESENT"
        logger.info("  [OK] MS_GRAPH_TOKEN is configured.")
    else:
        status["MS_GRAPH_TOKEN"] = "MISSING"
        logger.info("  [INFO] MS_GRAPH_TOKEN missing (MicrosoftProvider may use other auth).")

    # Check Notion (for advanced integrations)
    notion_key = os.getenv("NOTION_API_KEY")
    if notion_key:
        status["NOTION_API_KEY"] = "PRESENT"
        logger.info("  [OK] NOTION_API_KEY is configured (for NotionProvider advanced engine).")
    else:
        status["NOTION_API_KEY"] = "MISSING"
        logger.info("  [INFO] NOTION_API_KEY missing (Notion advanced features limited).")

    # Optional for real GH/OneDrive/GDrive mirroring pipelines + adversarial canon (git/gh use GITHUB_TOKEN or gh auth)
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if gh_token:
        status["GITHUB_TOKEN"] = "PRESENT"
        logger.info("  [OK] GITHUB_TOKEN present — real github mirror via git/gh + MCP grok_com_github push_files possible for canon/adversarial.")
    else:
        status["GITHUB_TOKEN"] = "OPTIONAL"
        logger.info("  [INFO] GITHUB_TOKEN optional — mirroring uses local git (projects/atlas-lattice-providers) + sim; MCP or gh auth for full external push.")

    return status

def main():
    logger.info("Starting Multi-Cloud Environment Validation for Maximum Grok Providers...\n")
    
    dep_ok = check_dependencies()
    print()
    config_ok = check_configuration_files()
    print()
    env_vars = check_environment_variables()
    print()
    
    # Generate structured report
    google_ready = (env_vars.get("GOOGLE_API_KEY") == "PRESENT (Valid format)")
    overall_ready = dep_ok and config_ok and google_ready
    
    report = {
        "status": "READY" if overall_ready else "INCOMPLETE",
        "dependencies_satisfied": dep_ok,
        "configuration_satisfied": config_ok,
        "environment_variables": env_vars,
        "recommendations": []
    }
    
    if not google_ready:
        report["recommendations"].append("Set GOOGLE_API_KEY (for Gemini/Drive AI features in GoogleProvider).")
    if env_vars.get("XAI_API_KEY") != "PRESENT (Valid format)":
        report["recommendations"].append("Set XAI_API_KEY for full Grok API integration (CLI + advanced capabilities).")
    if env_vars.get("MULTI_CLOUD_TOKEN") == "MISSING":
        report["recommendations"].append("Run CopilotCLIBridge or set GOOGLE_EXTERNAL_OAUTH_TOKEN for cross-cloud Drive access.")
    
    print("================== Environment Report ==================")
    print(json.dumps(report, indent=2))
    print("========================================================")
    
    if report["status"] == "READY":
        logger.info("Environment validation successful. System is ready to initialize providers/MCP server.")
        sys.exit(0)
    else:
        logger.warning("Environment validation incomplete. Check the log messages and recommendations above.")
        logger.info("Run this script again after fixing issues. Then start: python multi_provider_mcp_server.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
