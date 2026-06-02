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
from dataclasses import dataclass, field
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("secure_cli_runner_v1.3-policy")

# ============================================================
# CommandPolicy — per-command policy for the upgraded runner
# ============================================================
@dataclass
class CommandPolicy:
    name: str
    path: str  # full path or name resolved via PATH / sys.executable
    max_args: int = 16
    allow_args: Optional[List[str]] = None  # prefixes or exact; if None, all allowed (subject to max)
    timeout_sec: int = 120
    max_stdout_bytes: int = 256_000
    max_stderr_bytes: int = 64_000
    working_dir: Optional[str] = None
    env: Optional[Dict[str, str]] = field(default_factory=dict)
    description: str = ""

# Default policies file location (editable, no code change)
POLICIES_FILE = Path("config/command_policies.json")

# Fallback built-in policies (used if file missing or for bootstrap)
# These cover canonical grok/lattice + UWS/Alum + existing Windows/Google CLIs
DEFAULT_POLICIES: List[CommandPolicy] = [
    CommandPolicy(
        name="grok",
        path="grok",
        max_args=32,
        allow_args=["canon", "watch", "query", "apply", "diff", "sync", "help"],
        timeout_sec=300,
        description="Canonical Grok CLI (canon diff/sync, lattice ops, etc.)"
    ),
    CommandPolicy(
        name="lattice",
        path="lattice",
        max_args=32,
        allow_args=["query", "apply", "help"],
        timeout_sec=120,
        description="Lattice query/apply for Atlas Lattice ops"
    ),
    CommandPolicy(
        name="uws",
        path="uws",
        max_args=64,
        allow_args=None,  # full surface via UWS manifest; rely on --dry-run etc in special handling
        timeout_sec=300,
        max_stdout_bytes=1_000_000,
        description="Universal Workspace CLI (UWS) - 12k-20k+ unified features (Google/MS/Apple/...)"
    ),
    CommandPolicy(
        name="alum",
        path="alum",
        max_args=64,
        allow_args=None,
        timeout_sec=300,
        max_stdout_bytes=1_000_000,
        description="Aluminum OS unified command surface (kernel over UWS drivers)"
    ),
    CommandPolicy(
        name="antigravity",
        path="antigravity",
        max_args=32,
        allow_args=None,
        timeout_sec=600,
        description="Google Antigravity CLI (sandboxed agents, hardened Git)"
    ),
    CommandPolicy(
        name="antigravity-harness",
        path="antigravity",
        max_args=32,
        allow_args=None,
        timeout_sec=600,
        description="Self-hosted Antigravity Harness alias"
    ),
    CommandPolicy(
        name="adb",
        path="adb",
        max_args=16,
        allow_args=["devices", "logcat", "shell", "install", "emu", "forward", "reverse", "pull", "push"],
        timeout_sec=120,
        description="Android Debug Bridge (safe commands only)"
    ),
    CommandPolicy(
        name="emulator",
        path="emulator",
        max_args=16,
        allow_args=None,
        timeout_sec=120,
        description="Android Emulator for testing"
    ),
    CommandPolicy(
        name="powershell",
        path="powershell.exe",
        max_args=32,
        allow_args=["-Command"],
        timeout_sec=60,
        description="Windows PowerShell (safe via -Command or SAFE_POWERSHELL)"
    ),
    CommandPolicy(
        name="pwsh",
        path="pwsh.exe",
        max_args=32,
        allow_args=["-Command"],
        timeout_sec=60,
        description="PowerShell 7+"
    ),
    CommandPolicy(
        name="python",
        path=sys.executable,
        max_args=8,
        allow_args=["-c", "-m"],  # restrict further in execute
        timeout_sec=60,
        max_stdout_bytes=128_000,
        description="Python (restricted to safe scripts or -c with care)"
    ),
    CommandPolicy(
        name="cmd",
        path="cmd.exe",
        max_args=16,
        allow_args=["/c"],
        timeout_sec=30,
        description="cmd.exe fallback (very restricted)"
    ),
    CommandPolicy(
        name="gemini",
        path="gemini",
        max_args=16,
        allow_args=None,
        timeout_sec=120,
        description="Local Gemini CLI (optional)"
    ),
    # Add more as needed for canonical / UWS
]


# ============================================================
# ALLOWLIST — Only these executables may be invoked
# ============================================================
ALLOWED_EXECUTABLES: Dict[str, str] = {
    "grok": "grok",                    # Grok CLI (must be on PATH or full path)
    "lattice": "lattice",              # Our sovereign Lattice CLI wrapper
    "gemini": "gemini",                # Optional local Gemini CLI
    "antigravity": "antigravity",      # Google Antigravity CLI v2.0 (agent-first, sandboxed, credential masking, hardened Git)
    "python": sys.executable,          # Allow calling python for scripts (use with care)
    "powershell": "powershell.exe",    # Windows PowerShell for Copilot integrations (14,12,19,20, etc.)
    "pwsh": "pwsh.exe",                # PowerShell 7+ if installed
    "cmd": "cmd.exe",                  # Fallback for some Windows tasks
    "adb": "adb",                      # Android Debug Bridge for Google AI Studio Android Vibe Coding + Emulator Integration (19,60)
    "emulator": "emulator",            # Android Emulator direct for Google AI Studio Emulator Integration (60)
    "antigravity-harness": "antigravity",  # Alias for self-hosted Antigravity Agent Harness SDK (45)
    "uws": "uws",                      # Universal Workspace CLI (UWS) from atlaslattice/manus-artifacts/codebases/uws — unifies 12k-20k+ Google/MS/Apple/Android/Chrome features into Aluminum OS functional surface for integrations
    "alum": "alum",                    # Aluminum OS command surface (kernel layer beneath uws) for provider-agnostic unified workspace ops
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
    """
    Policy-driven, safe async CLI execution. No shell=True ever.
    Uses CommandPolicy for per-command control (args, timeout, output caps, env, cwd).
    Supports loading from JSON policies file for easy editing.
    """

    def __init__(self, policies: Optional[List[CommandPolicy]] = None, policies_file: Optional[Path] = None):
        self._policies: Dict[str, CommandPolicy] = {}
        self.execution_count = 0

        # Load from file if provided / default, else use DEFAULT + merge with legacy ALLOWED
        if policies is None:
            policies = self._load_policies(policies_file or POLICIES_FILE)

        for p in policies:
            self._policies[p.name] = p

        # Back-compat: if legacy ALLOWED_EXECUTABLES had extras not in policies, add minimal ones
        for name, path in ALLOWED_EXECUTABLES.items():
            if name not in self._policies:
                self._policies[name] = CommandPolicy(name=name, path=path, description="Legacy allowlisted (auto-migrated)")

    def _load_policies(self, path: Path) -> List[CommandPolicy]:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                policies = []
                for item in data.get("policies", []):
                    policies.append(CommandPolicy(**item))
                logger.info(f"Loaded {len(policies)} CommandPolicies from {path}")
                return policies
            except Exception as e:
                logger.warning(f"Failed to load policies from {path}: {e}. Using defaults.")
        # Ensure default file exists on first run for editing
        self._write_default_policies_if_missing(path)
        return DEFAULT_POLICIES

    def _write_default_policies_if_missing(self, path: Path):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                data = {
                    "version": "1.3",
                    "description": "Edit this file to add/override CommandPolicy for grok, lattice, uws, alum, etc. See Copilot upgrade spec.",
                    "policies": [
                        {
                            "name": p.name,
                            "path": p.path,
                            "max_args": p.max_args,
                            "allow_args": p.allow_args,
                            "timeout_sec": p.timeout_sec,
                            "max_stdout_bytes": p.max_stdout_bytes,
                            "max_stderr_bytes": p.max_stderr_bytes,
                            "working_dir": p.working_dir,
                            "env": p.env or {},
                            "description": p.description
                        } for p in DEFAULT_POLICIES
                    ]
                }
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                logger.info(f"Wrote default policies file to {path} (edit to customize)")
        except Exception as e:
            logger.warning(f"Could not write default policies: {e}")

    def get_policy(self, name: str) -> Optional[CommandPolicy]:
        return self._policies.get(name)

    async def execute(
        self,
        command_name: str,
        arguments: List[str],
        timeout: Optional[float] = None,
        env_overrides: Optional[Dict[str, str]] = None,
        prepared_env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a policy-governed command with full safety guarantees.
        - Never uses shell=True
        - Policy-driven: max_args, allow_args prefixes, timeouts, output caps, cwd, env
        - Captures stdout/stderr separately (truncated per policy)
        - Supports overrides for cross-cloud
        - Always returns structured result + provenance
        """
        policy = self.get_policy(command_name)
        if not policy:
            logger.warning(f"REJECTED: '{command_name}' has no CommandPolicy")
            return {
                "status": "ERROR",
                "exit_code": -1,
                "error": f"Command '{command_name}' is not authorized (no policy).",
                "allowed_commands": list(self._policies.keys())
            }

        if len(arguments) > policy.max_args:
            return {"status": "ERROR", "exit_code": -1, "error": f"Too many arguments (max {policy.max_args})"}

        if policy.allow_args is not None:
            for a in arguments:
                if not any(a == exact or a.startswith(prefix) for prefix in policy.allow_args for exact in [prefix] if not prefix.endswith("*")):  # simple prefix match
                    if not any(a.startswith(p) for p in policy.allow_args):
                        return {"status": "ERROR", "exit_code": -1, "error": f"Argument not allowed: {a}"}

        executable = policy.path

        # Legacy special handling (python, powershell, antigravity, uws/alum, grok, adb etc.) - keep for now, can move into policies later
        if command_name == "python" and arguments:
            script_name = arguments[0]
            if script_name not in SAFE_PYTHON_SCRIPTS.values():
                return {"status": "ERROR", "exit_code": -3, "error": "Only explicitly allowed python scripts may be executed."}

        if command_name in ("powershell", "pwsh") and arguments:
            cmd_or_script = arguments[0] if arguments else ""
            if cmd_or_script in SAFE_POWERSHELL_COMMANDS:
                arguments = ["-Command", SAFE_POWERSHELL_COMMANDS[cmd_or_script]] + arguments[1:]
            elif "-Command" not in " ".join(arguments) and not any(a.startswith("-") for a in arguments):
                return {"status": "ERROR", "exit_code": -3, "error": "PowerShell invocations must use safe predefined commands or explicit -Command with validated content."}

        if command_name in ("antigravity", "antigravity-harness"):
            logger.info("Antigravity CLI/Harness invoked (sandboxed, masked creds, hardened Git policies per Google I/O 2026).")

        if command_name in ("adb", "emulator"):
            safe_adb = ["devices", "logcat", "shell", "install", "emu", "forward", "reverse", "pull", "push"]
            if arguments and not any(arg in safe_adb for arg in arguments[:2]):
                logger.warning("ADB/Emulator restricted to safe commands...")

        if command_name in ("uws", "alum"):
            logger.info("UWS/Alum CLI invoked — Universal Workspace surface for ... 12k-20k+ features unified.")
            if not any(a.startswith("--format") for a in arguments):
                arguments = arguments + ["--format", "json"]
            if any(word in " ".join(arguments).lower() for word in ["send", "create", "delete", "update", "write", "share"]) and "--dry-run" not in arguments:
                logger.warning("UWS/Alum write operation detected — strongly recommend --dry-run first (per UWS spec and safety).")

        # Build env: policy.env + prepared + overrides + legacy injections
        env = dict(policy.env or {})
        if prepared_env:
            env.update(prepared_env)
        if env_overrides:
            env.update(env_overrides)
        if command_name == "grok":
            xai_key = os.getenv("XAI_API_KEY")
            if xai_key:
                env["XAI_API_KEY"] = xai_key
        if command_name in ("uws", "alum"):
            for key in ["GOOGLE_WORKSPACE_CLI_TOKEN", "GOOGLE_API_KEY", "UWS_MS_TOKEN", "UWS_MS_CLIENT_ID", "UWS_MS_TENANT_ID"]:
                val = os.getenv(key)
                if val:
                    env[key] = val

        effective_timeout = timeout if timeout is not None else policy.timeout_sec
        cwd = policy.working_dir

        logger.info(f"EXECUTING (policy): {executable} {' '.join(arguments)}")

        try:
            process = await asyncio.create_subprocess_exec(
                executable,
                *arguments,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=effective_timeout
            )
            exit_code = process.returncode

            self.execution_count += 1

            # Truncate per policy
            stdout = stdout[:policy.max_stdout_bytes]
            stderr = stderr[:policy.max_stderr_bytes]

            result = {
                "status": "SUCCESS" if exit_code == 0 else "FAILED",
                "exit_code": exit_code,
                "stdout": stdout.decode("utf-8", errors="replace").strip(),
                "stderr": stderr.decode("utf-8", errors="replace").strip(),
                "command": command_name,
                "arguments": arguments,
                "execution_id": self.execution_count,
                "policy": {"name": policy.name, "timeout": effective_timeout}
            }

            if exit_code != 0:
                logger.warning(f"Command failed with exit code {exit_code}")

            return result

        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {effective_timeout}s: {command_name}")
            try:
                process.kill()
            except Exception:
                pass
            return {
                "status": "ERROR",
                "exit_code": -4,
                "error": f"Execution timed out after {effective_timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Subprocess failure: {e}")
            return {
                "status": "ERROR",
                "exit_code": -2,
                "error": f"Subprocess execution failed: {str(e)}"
            }

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

        # Special handling for Antigravity CLI (Google I/O 2026 #1 + #46: agent-first, sandboxed, credential masking, hardened Git + self-hosted harness)
        if command_name in ("antigravity", "antigravity-harness"):
            # Antigravity provides its own sandboxing/credential/Git policies per I/O; harness for local SDK control of sandboxes.
            # We enforce no shell=True + full provenance/ledger.
            logger.info("Antigravity CLI/Harness invoked (sandboxed, masked creds, hardened Git policies per Google I/O 2026). Self-hosted mode for local agents.")

        # Special handling for ADB + Emulator (Google AI Studio Android Vibe + Emulator Integration #19/#60)
        if command_name in ("adb", "emulator"):
            safe_adb = ["devices", "logcat", "shell", "install", "emu", "forward", "reverse", "pull", "push"]
            if arguments and not any(arg in safe_adb for arg in arguments[:2]):
                logger.warning("ADB/Emulator restricted to safe commands (devices, logcat, shell, install, emu, etc.) for Android unit tests after codegen.")
            if command_name == "emulator":
                logger.info("Android Emulator direct launch for in-browser/CLI testing (Google AI Studio integration).")

        # Special handling for UWS / Aluminum (Universal Workspace CLI from atlaslattice UWS in manus-artifacts/codebases/uws; 12k-20k+ unified features into functional Aluminum OS for integrations)
        if command_name in ("uws", "alum"):
            # UWS is AI-agent first per UWS_AGENTS.md / UWS_ALUMINUM.md: prefer --format json, --dry-run for writes, --page-all for full data.
            # Enforce provenance, inject relevant env (GOOGLE_*, MS_*, from bridge or UWS_ vars), log for Lattice/ClaimPackets.
            logger.info("UWS/Alum CLI invoked — Universal Workspace surface for Google/MS/Apple/Android/Chrome (Aluminum OS kernel). AI-native, JSON-first, dry-run enforced for writes. 12k-20k+ features unified.")
            if not any(a.startswith("--format") for a in arguments):
                arguments = arguments + ["--format", "json"]
            if any(word in " ".join(arguments).lower() for word in ["send", "create", "delete", "update", "write", "share"] ) and "--dry-run" not in arguments:
                logger.warning("UWS/Alum write operation detected — strongly recommend --dry-run first (per UWS spec and safety).")

        # Build environment (inherit + optional overrides for cross-cloud)
        # Support prepared_env from agent_ms_cli_bridge for Google-MS token mapping
        env = prepared_env if prepared_env is not None else os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
            logger.info(f"Applied {len(env_overrides)} environment overrides for cross-cloud context")

        # Special handling for "grok" (xAI Grok CLI / API): inject user's XAI_API_KEY
        if command_name == "grok":
            xai_key = os.getenv("XAI_API_KEY")
            if xai_key:
                env["XAI_API_KEY"] = xai_key
                logger.info("Injected XAI_API_KEY for grok execution (user's key integrated).")
            else:
                logger.warning("XAI_API_KEY not found in environment. 'grok' commands may fail to authenticate. Set $env:XAI_API_KEY=your-xai-key")

        # Special handling for UWS/Alum: inject common provider tokens from env/bridge for seamless multi-cloud (Google, MS Graph, etc.)
        if command_name in ("uws", "alum"):
            # UWS uses GOOGLE_WORKSPACE_CLI_* , UWS_MS_* , etc. per UWS_AGENTS.md and Aluminum spec.
            # Bridge already prepares some; add common ones.
            for key in ["GOOGLE_WORKSPACE_CLI_TOKEN", "GOOGLE_API_KEY", "UWS_MS_TOKEN", "UWS_MS_CLIENT_ID", "UWS_MS_TENANT_ID"]:
                val = os.getenv(key)
                if val:
                    env[key] = val
            logger.info("Injected UWS-compatible provider tokens (Google/MS/etc.) from environment/bridge for unified workspace access.")

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
        """Standard MCP tool schema (shared by Gemini + Copilot sides, per Copilot upgrade spec)."""
        return {
            "name": "run_cli_command",
            "description": "Run a vetted local CLI command (grok, lattice, uws, alum, etc.) under policy-driven security and return structured output. Canonical commands: grok canon diff/sync, lattice query/apply, uws/alum unified surfaces (17k+ features). Always prefer --dry-run for writes. JSON output preferred for agents.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command_name": {
                        "type": "string",
                        "description": "Logical command name (e.g. 'grok', 'lattice', 'uws', 'alum'). Must have a CommandPolicy."
                    },
                    "arguments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Command arguments, already tokenized. Models should use canonical subcommands (canon, query, etc.)."
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Optional timeout in seconds (overrides policy default)."
                    }
                },
                "required": ["command_name", "arguments"]
            }
        }

    def list_policies(self) -> Dict[str, Any]:
        return {
            "count": len(self._policies),
            "policies": {k: {"path": v.path, "max_args": v.max_args, "allow_args": v.allow_args, "description": v.description} for k, v in self._policies.items()}
        }


# Singleton for convenience (loads default policies)
_default_runner = SecureCLIRunner()


async def run_cli(command_name: str, arguments: List[str], **kwargs) -> Dict[str, Any]:
    """Convenience wrapper around the default runner."""
    return await _default_runner.execute(command_name, arguments, **kwargs)