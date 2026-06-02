# 20 Bleeding-Edge Advanced Capabilities (Copilot Recommendations)

Implemented in `providers/advanced_capabilities_engine.py` as `AdvancedCapabilitiesEngine`.

Exposed via:
- MCP tool: `advanced_capability` with `capability` name
- `AdvancedCapabilitiesEngine.run("canon_drift_detector", ...)`
- Routed through `MicrosoftProvider.execute` where relevant

All integrate with existing telemetry (cap 1), error taxonomy (cap 2), ledgers, offload, previous 20 Copilot + E145 Project features, and the full provider layer.

See the engine source for full specs and delegation logic.

MUTANT AND PROUD.
