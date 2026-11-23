# Atlas Labs v32 — public-source experimental review contract v0.1

**SOURCE-ONLY CANDIDATE / NOT CANON / NOT DEPLOYED / NO EXPERIMENTAL CERTIFICATION.**

This additive module makes eight laboratory categories first-class **review address spaces**: quantum labs; physics and mathematics; fusion and plasma; materials and manufacturing; biological systems; space and aerospace; regenerative infrastructure; and knowledge/evidence. The initial manifest lists one exact public GitHub commit and blob per lab category. These are **source pointers**, not an independent scientific verification or authority to retrieve private information.

The implementation is a dependency-free Python function, `labs.atlas_labs_v32.prepare`, and CLI. It validates a *public-only* proposed experiment envelope and emits three **inert candidates**: an Atlas ONE task intake, a SwarmChat Work review message **not posted**, and an Alexandria graph edge **not written**. It never dispatches tools, executes physics, calls a QPU, accesses UWS, reads private Work/Palace/Brain/Play/Social/Imagine/Quiet, connects to the broker, authenticates a principal, or changes host state. These actions require separate trusted adapters and human-root release checks.

## Exchange and evidence contract

- Input `schema=atlas.labs.experiment-candidate/v0.1`, one known `lab_id`/`source_id`, synthetic or design-only model, explicit hypothesis, falsifier, model revision, and optionally a pinned Ariadne v0.7 HSN **address candidate**.
- Model kind `DESIGN_ONLY` requires *zero quantities*. `SYNTHETIC_MODEL` requires 1–8 bounded decimal-string quantities with explicit units and `SYNTHETIC_MODEL_ONLY` evidence class. No observed/validated lab measurements are accepted at this stage.
- Reject unknown fields, recursive/non-JSON inputs, Unicode NFC key collisions, nonfinite or bare numeric floats, bogus ontology editions/digests, legacy H00/H13 coordinates, private origin labels, caller authority claims and unsupported units. One generic outward HOLD response hides source names, hashes, sizes and existence.
- An accepted candidate remains `PREPARED_SOURCE_ONLY`, with `authority_effect=NONE`, `same_as=false`, `host_attested=false`, `rights_at_return=NOT_CHECKED`, `verified_hardware=false`, `canon=false` and `deployment=false`.
- The public-source manifest pins exact Git commits and Git blob SHA-1 values obtained from the connected GitHub repository. An independently verified publisher/signature and rights review would still be required before treating those pins as authoritative.

## Run the offline proof

```bash
python -m unittest discover -s tests -p 'test_atlas_labs_v32.py' -v
python -O -m unittest discover -s tests -p 'test_atlas_labs_v32.py' -q
python -m labs.atlas_labs_v32 --catalog
python -m labs.atlas_labs_v32 --stdin < examples/atlas_labs_v32_synthetic.json
```

## Real integration acceptance gates (OPEN)

1. One trusted, versioned **Atlas ONE** task-admission port with independently authenticated tenant/principal and present Work permission.
2. One owner-authorized **SwarmChat** read/review/readback with exact room/seq, permission rechecked at READ and RETURN; no optional private modes imported.
3. One source/digest/edition-pinned **Alexandria** write candidate that preserves dissent and never infers `same_as` from shared HSN labels or 1,728 geometry cells.
4. Real **UWS** tool/quantum/simulation adapter invocation with bounded resource budget, actual executor receipt, model- or experiment-specific units/uncertainty, and independent reproducibility. No provider spending or physical hardware claimed by this scaffold.
5. CI execution with actual recorded steps, license review, current served Site HEAD, rollback, two-account revocation and user-approved deployment. No automatic CANON ratification.

Source concept anchors include [STARS 2.0](https://github.com/atlaslattice/open-regenerative-compute-standard/blob/ea2ba0133338b316b01c62f83c97bd845c61a9f0/GPTWORK_START_HERE_STARS_2_0.md), [QPU infrastructure](https://github.com/atlaslattice/open-regenerative-compute-standard/blob/ea2ba0133338b316b01c62f83c97bd845c61a9f0/research/orcs/manufacturing/T4_S50_DC_OCP_MT_DIABLO_800VDC_STANDARDS_AND_QPU_INTEGRATION_SPEC_v0_4_2026-11-01.md), [acoustic methods](https://github.com/atlaslattice/atlas-lattice-foundation/blob/d72e7f161a514d63bd03946e8ed6885bfe66eb89/spec_modules/18_volumetric_acoustic_printing_spec.md), and [Moon/Mars habitats](https://github.com/atlaslattice/open-regenerative-compute-standard/blob/ea2ba0133338b316b01c62f83c97bd845c61a9f0/research/beyond_q/addenda/BQ_MOON_MARS_CLOSED_LOOP_HABITAT_TESTBED_MISSION_AND_LEDGER_v0_1_2026-10-30.md).
