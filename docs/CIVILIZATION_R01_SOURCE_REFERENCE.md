# Optional Atlas Civilization R01 source reference

CANDIDATE, NOT CANON. AUTHORITY: none. DEPLOYMENT: false.

The pinned upstream source lives at `atlaslattice/Atlas-Intelligence/programs/civilization-r01`, release `ATLAS-CIVILIZATION-R01-20261123-1`. This repository adds a small metadata validator and an optional branch of `HierarchicalGoalDecompositionEngine.decompose`. Existing behavior and the EX1728 source-reference branch remain available. No kernel implementation is copied here.

The optional branch accepts `civilization_kernel_reference_bytes`, `expected_civilization_kernel_reference_sha256`, `kernel_house_id`, a current `room_id`, and `mode="WORK"`. It refuses requests that also supply `excellence_reference_bytes`, since selecting two different source-program namespaces is ambiguous.

```python
from core.hierarchical_goal_decomposer import HierarchicalGoalDecompositionEngine

# selected_bytes and selected_sha256 come from the host's reviewed source pins.
candidate = await HierarchicalGoalDecompositionEngine().decompose(
    "Prepare a source-qualified software operation",
    civilization_kernel_reference_bytes=selected_bytes,
    expected_civilization_kernel_reference_sha256=selected_sha256,
    kernel_house_id="H02", room_id="work-review", mode="WORK"
)
assert candidate["status"] == "SUPPORTING_KERNEL_REFERENCE_PREPARED"
assert candidate["execution_authorized"] is False
```

The reference names an immutable upstream commit and exact file fingerprints. It retains the authentic local synthetic benchmark summary: eleven supporting-kernel gain candidates, one H02 regression, and the H02 reference/scan fallback default. It awards zero original 1,728 primary metric credit, zero specialized-node completion and zero production or whole-system gain claims.

The helper verifies selected reference bytes only. It does not retrieve or execute source, make model calls, post, persist, authorize or promote Canon. A digest does not authenticate an owner. Pinned upstream source checks, current Work READ permission, and the current RETURN fence remain required host checks. Kernel IDs are not converted into original HSNs or EX1728 tasks by ordinal position.

The published JSON carries the optional Providers host annotation `candidate_notice` with the exact value `CANDIDATE, NOT CANON. AUTHORITY: none. DEPLOYMENT: false.`. Older references without this annotation remain accepted. An altered notice or any other extra field is rejected. This annotation changes no upstream runtime, source pin, preparation output, authority or dispatch rule; it is not an amendment to the upstream release's schema authority.

Run `python3 -m unittest discover -s tests -p test_civilization_kernel_reference.py -v` for the reference controls and the optional/legacy decomposer paths. Synthetic test commits are test inputs, not publication evidence.
