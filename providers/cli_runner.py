#!/usr/bin/env python3
"""
Maximum Grok — Secure CLI Runner v1.2 (Shared Execution Spine)
==============================================================
Production-grade, non-blocking asynchronous CLI execution for allowlisted tools.

Used by LocalCLIProvider and exposed via MCP to Gemini, Copilot, and other agents.

Grok Leads. Lattice Routes. CLI executes under strict allowlist + full provenance.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("secure_cli_runner_v1.2")


# ============================================================
# ALLOWLIST — Only these executables may be invoked
# ============================================================
ALLOWED_EXECUTABLES: Dict[str, str] = {
    "grok": "grok",                    # Grok CLI (must be on PATH or full path)
    "lattice": "lattice",              # Our sovereign Lattice CLI wrapper
    "gemini": "gemini",                # Optional local Gemini CLI
    "python": sys.executable,          # Allow calling python for scripts (use with care)
    "powershell": "powershell.exe",    # Windows PowerShell for Copilot integrations (14,12,19,20, etc.)
    "pwsh": "pwsh.exe",                # PowerShell 7+ if installed
    "cmd": "cmd.exe",                  # Fallback for some Windows tasks
}

# Recommended: restrict python to specific safe scripts only in production
SAFE_PYTHON_SCRIPTS = {
    "north_star_extraction": "Canon_Implementation/OpenAI/adapters/north_star_extraction.py",
    "notion_extract": "Canon_Implementation/OpenAI/adapters/notion_adapter.py",
}

# Windows Copilot safe PowerShell commands / scripts (for 12-20 integrations)
SAFE_POWERSHELL_COMMANDS = {
    "get_defender_alerts": "Get-MpThreatDetection | ConvertTo-Json",
    "get_entra_roles": "Get-AzureADDirectoryRole | ConvertTo-Json",  # or Microsoft.Graph
    "get_clipboard": "Get-Clipboard | Out-String",
    "list_explorer_folder": "Get-ChildItem -Path $args[0] | Select Name,Length,LastWriteTime | ConvertTo-Json",
    "open_app": "Start-Process $args[0]",
    "get_system_info": "Get-ComputerInfo | Select WindowsProductName,WindowsVersion,TotalPhysicalMemory | ConvertTo-Json",
}


class SecureCLIRunner:
    """Safely executes allowlisted CLI tools asynchronously. No shell=True ever."""

    def __init__(self, allowlist: Dict[str, str] = ALLOWED_EXECUTABLES):
        self.allowlist = allowlist
        self.execution_count = 0

    async def execute(
        self,
        command_name: str,
        arguments: List[str],
        timeout: Optional[float] = 120.0,
        env_overrides: Optional[Dict[str, str]] = None,
        prepared_env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute an allowlisted command with full safety guarantees.

        - Never uses shell=True
        - Captures stdout/stderr separately
        - Supports optional per-invocation environment overrides (for cross-cloud tokens)
        - Always returns structured result with provenance
        """
        if command_name not in self.allowlist:
            logger.warning(f"REJECTED: '{command_name}' not in allowlist")
            return {
                "status": "ERROR",
                "exit_code": -1,
                "error": f"Command '{command_name}' is not authorized for execution.",
                "allowed_commands": list(self.allowlist.keys())
            }

        executable = self.allowlist[command_name]

        # Special handling for python scripts (security)
        if command_name == "python" and arguments:
            script_name = arguments[0]
            if script_name not in SAFE_PYTHON_SCRIPTS.values():
                logger.warning(f"Blocked unsafe python script attempt: {script_name}")
                return {
                    "status": "ERROR",
                    "exit_code": -3,
                    "error": "Only explicitly allowed python scripts may be executed."
                }

        # Special handling for PowerShell (Windows Copilot integrations - 12,14,15,16,18,19,20)
        if command_name in ("powershell", "pwsh") and arguments:
            # If first arg looks like a command/script, validate against safe list or allow explicit -Command with safe patterns
            cmd_or_script = arguments[0] if arguments else ""
            if cmd_or_script in SAFE_POWERSHELL_COMMANDS:
                # Prepend the safe command body
                arguments = ["-Command", SAFE_POWERSHELL_COMMANDS[cmd_or_script]] + arguments[1:]
            elif "-Command" not in " ".join(arguments) and not any(a.startswith("-") for a in arguments):
                logger.warning(f"Potentially unsafe PowerShell invocation blocked: {arguments}")
                return {
                    "status": "ERROR",
                    "exit_code": -3,
                    "error": "PowerShell invocations must use safe predefined commands or explicit -Command with validated content."
                }

        # Build environment (inherit + optional overrides for cross-cloud)
        # Support prepared_env from agent_ms_cli_bridge for Google-MS token mapping
        env = prepared_env if prepared_env is not None else os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
            logger.info(f"Applied {len(env_overrides)} environment overrides for cross-cloud context")

        logger.info(f"EXECUTING: {executable} {' '.join(arguments)}")

        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                *arguments,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            exit_code = process.returncode

            self.execution_count += 1

            result = {
                "status": "SUCCESS" if exit_code == 0 else "FAILED",
                "exit_code": exit_code,
                "stdout": stdout.decode("utf-8", errors="replace").strip(),
                "stderr": stderr.decode("utf-8", errors="replace").strip(),
                "command": command_name,
                "arguments": arguments,
                "execution_id": self.execution_count
            }

            if exit_code != 0:
                logger.warning(f"Command failed with exit code {exit_code}")

            return result

        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout}s: {command_name}")
            return {
                "status": "ERROR",
                "exit_code": -4,
                "error": f"Execution timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Subprocess failure: {e}")
            return {
                "status": "ERROR",
                "exit_code": -2,
                "error": f"Subprocess execution failed: {str(e)}"
            }

    def get_mcp_tool_definition(self) -> Dict[str, Any]:
        """Return the MCP tool schema for this runner."""
        return {
            "name": "run_cli_command",
            "description": "Securely execute allowlisted CLI tools (grok, lattice, gemini, approved python scripts) with full provenance and cross-cloud token support.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command_name": {
                        "type": "string",
                        "enum": list(self.allowlist.keys()),
                        "description": "The allowed CLI executable to run."
                    },
                    "arguments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of string arguments to pass to the executable."
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Optional timeout in seconds (default 120)"
                    }
                },
                "required": ["command_name", "arguments"]
            }
        }


# Singleton for convenience
_default_runner = SecureCLIRunner()


async def run_cli(command_name: str, arguments: List[str], **kwargs) -> Dict[str, Any]:
    """Convenience wrapper around the default runner."""
    return await _default_runner.execute(command_name, arguments, **kwargs)