# §5 Supplement — three explicit statements + orchestration evidence (reviewer CP2A/CP3/CP4/CP5)

**Date:** 2026-10-29 · **Spec:** v1.6 (single-threaded) · **Sweep:** HALTED (reviewer HOLD, `d1b068d`).
This closes the four "genuinely-new" items from `docs/ANISO_CHECKPOINT_CROSSWALK_20261027.md`.

---

## S1 — Continuity-residual & number-balance: ACCEPTANCE criteria (gating), not diagnostic-only

**Statement:** `continuity_residual` and `relative_number_balance` are **acceptance criteria** — they
are two of the seven AND-gated certification criteria (G2.1/G2.3), not merely diagnostic observables.

A node is CERTIFIED only if **all seven** criteria pass. A node that reaches `R_phi < 1e-4` but fails
`continuity_residual < 1e-6` or `|relative_number_balance| < 1e-2` is **UNRESOLVED**, not CERTIFIED
(regression test `test_certify_not_rphi_alone`). The thresholds and units are frozen in
`docs/ANISO_S5_EVIDENCE_PACKAGE_20261026.md` §2-C (criteria #2 and #3). The three drift criteria
(`drift_raw_Gii`, `drift_interp_Gii`, `drift_G_tot`) and `hotspot_drift` are also gating. Recorded-but-
NOT-gating observables are only: `Gii_max`, `Gii_interp`, `G_tot`, `drain_current_A_per_um`,
`avalanche_y_fwhm` + `fwhm_flags`, `xy_Gii_max`/`xy_Gii_max_interp`.

## S2 — G3.4 trigger RETIRED under the uniform single-thread protocol (v1.6)

**Statement:** the G3.4 "mandatory single-thread resolution" trigger is **retired** for the v1.6 sweep.

G3.4 existed to re-run decision-critical node-pairs single-threaded when the 8-thread sweep showed a
`d=2|a−b|/(|a|+|b|)` near the threading noise. Under v1.6 the **entire sweep is already single-threaded**
(`OPENBLAS_NUM_THREADS = OMP_NUM_THREADS = MKL_NUM_THREADS = 1` for every node), so the all-1-thread run
**is** the reference — there is no cross-thread pair to re-run. The trigger is therefore structurally
vacuous and is retired. (The t1/t8 measurement in §4 of the evidence package stands as the historical
justification for v1.6; it is not re-run.)

## S3 — Individual `--node` runs are PERMITTED before family-sweep authorization

**Statement:** individual `--node Nx Ny` runs are **permitted** without full-sweep execution
authorization; only the family sweep (`--family` / `--sweep`) is gated by G0.2.

Rationale (matches the harness): `_require_exec_auth()` is invoked only in `run_family` / `run_sweep`,
never in `run_node`. This is deliberate — the smoke node, the t1/t8 controls, and the S5 reproducibility
repeat were all `--node` runs taken under the pre-registered spec while the full sweep was HELD. The
full sweep HARD-BLOCKS without `campaign/aniso_exec_auth.json` (test `test_exec_auth_hard_block`).

---

## S4 — Orchestration evidence (CP2A/CP5) + Gate-4 exclusion (CP3)

New in the harness (`campaign/aniso_mesh_study.py`), all covered by regression tests:

1. **Metadata-on-disk persistence** (CP2A): `_build_node_record` / `_write_node_json` factored out of
   `run_node`; `test_metadata_persisted_on_disk` writes a record, **reopens** it, and asserts every
   provenance field, all 7 criteria (value/unit/gate/passed), and every identity/observable field is
   actually persisted. Also fixed a latent serialization bug: `_profile_fwhm_2cross` could return a
   numpy `bool` for `unresolved`, which would crash `json.dump` on any non-boundary-truncated node
   (now cast to Python `bool`).

2. **Sequential X-then-Y orchestration + failure isolation** (CP2A/CP5): `run_sweep()` runs X then Y
   as independent family runs; `run_family` now catches a mid-chain failure and records it as FAILED
   instead of aborting the whole process. `test_run_sweep_sequential_failure_isolation` proves the
   shared (100,70) anchor runs in **both** families as separate calls, and that X failing does **not**
   mark Y complete (Y still certifies). The per-family manifest is written to
   `aniso_sweep_manifest.json`.

3. **Manifest state vocabulary** (CP5): the manifest emits, for every node, exactly one of
   `queued / running / certified / failed / UNRESOLVED` (`NODE_STATES`). In the failure-isolation test
   the X-family manifest reads `certified, failed, queued` — the states are explicit, not implied.

4. **Gate-4 exclusion of uncertified nodes** (CP3): `gate4_nodes(records)` returns only
   `status == CERTIFIED and certified is True` nodes; `test_gate4_excludes_uncertified` asserts
   UNRESOLVED/FAILED nodes are dropped. Any Gate-4 analysis must consume `gate4_nodes(...)` output only.

**Regression suite: 21/21 PASS** (`python3 -m pytest campaign/test_aniso_mesh_study.py -q`).

---

**Sweep remains HALTED.** Nothing here relaxes the HOLD; this is evidence assembly + the three
explicit statements the reviewer requested. The Gate-4 surface-hotspot amendment (`3c6f8f3`) awaits
user concurrence before any Y-family run.
