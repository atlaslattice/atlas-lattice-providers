# A2A candidate-only message-bus contract

Status: OFFLINE REFERENCE / NOT CONNECTED / NO HOST IDENTITY / NOT CANON.

This implements a testable part of public SwarmHub #5 without replacing its historical protocol placeholder or claiming hosted functionality. Exact protected payloads are never imported. It prepares only inert receipts.

The caller must supply a source-linked Work candidate. `CandidateBus.prepare` validates the envelope, source IDs, separate tenant/room/sender/request/logical operation scopes, duplicate transport replay and crash-retry logical dedup. No identity, ACL or rights attestations are issued by this code. Non-Work content is excluded without leaking its body into receipts; all other candidate payloads are held or prepared locally, never delivered.

To test: `python -m unittest discover -s tests -p "test_candidate_bus.py" -v`. Exactly the same tests can run with `python -O`. Standard library, no provider spend, no network.

A real host implementation would require current principal and Work ACL checks at read, post and return; signatures and key rotation; persistent atomic dedupe across crashes; revocation and privacy auditing; and independent CI/E2E acceptance. Those are not supplied here.

Proposed relation: https://github.com/atlaslattice/atlas-lattice-providers/issues/5