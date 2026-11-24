# AGENTS.md — Atlas Lattice OpenAI Interop Rules

## Mission
Make the repository first-class for OpenAI interop while preserving governance receipts.

## Default commands
- `python -m py_compile providers/openai/*.py providers/provider_openai.py providers/openai/agents_sdk_adapter.py`
- `pytest -q tests/test_openai_interop.py`
- `python scripts/openai_interop_check.py`

## Ground rules
- Do not commit credentials, tokens, API keys, local machine paths, or private exports.
- Live OpenAI calls must require `OPENAI_API_KEY` and an explicit non-simulated mode.
- CI must pass without credentials by using simulation mode.
- Destructive/admin tool calls must require explicit approval.
- Every promoted output should have a ClaimPacket-compatible receipt and, when applicable, GoldenTrace persistence.

## Patch preference
Small PRs win. Each PR should include tests or a readiness check when changing OpenAI, MCP, tool-calling, eval, tracing, or provider boot paths.

## Canon status
Treat outputs as candidate receipts until human review promotes them. Nothing is canon merely because a model produced it.
