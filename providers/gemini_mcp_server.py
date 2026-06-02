#!/usr/bin/env python3
"""
Production-Grade Non-Blocking Gemini CLI MCP Server
==================================================
Implements a non-blocking asynchronous stdio reader loop that handles
JSON-RPC execution for standard tool calls without blocking the Python event loop.
"""

import os
import sys
import json
import asyncio
import logging
from cli_runner import SecureCLIRunner, get_mcp_tool_definition

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("gemini_mcp_server")

class GeminiCLIMCPServer:
    """Manages secure, non-blocking standard JSON-RPC execution."""
    def __init__(self):
        self.runner = SecureCLIRunner()

    async def handle_request(self, req: dict) -> dict:
        mid = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        logger.info(f"Received JSON-RPC method request: {method}")

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": mid,
                "result": {"tools": [get_mcp_tool_definition()]}
            }

        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})

            if name == "run_cli_command":
                result = await self.runner.execute(
                    command_name=args.get("command_name"),
                    arguments=args.get("arguments", []),
                )
                return {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": result,
                }

        return {
            "jsonrpc": "2.0",
            "id": mid,
            "error": {"code": -32601, "message": f"Method '{method}' not found or not supported."},
        }

async def main():
    logger.info("Initializing non-blocking Gemini CLI MCP Server on stdio transport...")
    server = GeminiCLIMCPServer()
    
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        
        line_str = line.decode('utf-8').strip()
        if not line_str:
            continue
            
        try:
            req = json.loads(line_str)
            asyncio.create_task(process_and_respond(server, req))
        except Exception as e:
            logger.error(f"Error parsing JSON-RPC line: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Parsing failed: {str(e)}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

async def process_and_respond(server: GeminiCLIMCPServer, req: dict):
    try:
        response = await server.handle_request(req)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Error processing asynchronous task: {e}")
        error_response = {
            "jsonrpc": "2.0",
            "id": req.get("id"),
            "error": {"code": -32603, "message": str(e)}
        }
        sys.stdout.write(json.dumps(error_response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Gemini CLI MCP Server terminated gracefully.")
