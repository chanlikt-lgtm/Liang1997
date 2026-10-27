# Crosswalk — reviewer Checkpoints 0–7 vs. committed evidence

**Date:** 2026-10-27 · **For:** `ANISO_SWEEP_NEXT_STEP_CHECKPOINTS_20261027.md` (reviewer checklist) ·
**Sweep: HALTED.**

**Important context the checklist predates:** the reviewer checklist was built from the Oct-26 interim
snapshot + the earlier HOLD review. Since then we have committed, on `main`:
- **Halt record** `ANISO_SWEEP_HALT_RECORD_20261026.md` (`6d55242`) — Checkpoint 0.
- **§5 evidence package** `ANISO_S5_EVIDENCE_PACKAGE_20261026.md` (`f22a851`).
- **Gate-4 surface-hotspot amendment** `ANISO_GATE4_SURFACE_HOTSPOT_AMENDMENT_20261027.md` (`3c6f8f3`).

Status: **DONE** = committed with evidence (maintainer-verified where noted); **PARTIAL** = mostly
there, one explicit statement/test to add; **TODO** = genuinely new item from the checklist.

| CP | Item | Status | Evidence / gap |
|---|---|---|---|
| **0** | Contain + preserve state | **DONE** | Halt record `6d55242`: node 2 killed at outer 563 (not certified), node-1 certified artifacts + node-2 trajectory preserved, stop point + state hash, monitor cron disabled, resumable. |
| **1** | Governance / version freeze / authorization | **DONE (verify)** | §5 §1: v1.6 FROZEN 2026-10-25 09:27 (`dd56686`) vs first run 09:40 — deviation stated plainly; two separate decisions (admissibility vs prospective) named; G0.2 hard-block tested (`ebb5913`). **PARTIAL:** add explicit "individual `--node` runs vs family-sweep authorization" statement + bind-auth-to-commit/manifest line. |
| **2A** | Warm-start + provenance integrity | **DONE (verify)** + 1 TODO | G1.1/G1.2/G1.3 (`ebb5913`, 12/12). **TODO:** add a regression that **reopens each output JSON on disk** and asserts metadata present (not just in-memory); add a **clean sequential X-then-Y** orchestration test. |
| **2B** | Thread enforcement + CLI parse | **DONE (verify)** | `--node/--threads` parse fix + regression (`52c981f`); `threadpool_actual` recorded; fail-closed on mismatch. Confirm the family-sweep rejects a non-v1.6 thread count. |
| **2C** | 4th-level RAM gate | **DONE (verify)** | G1.4 measured preflight + blocked/allowed tests (§5 §3). `--include-4th` gated. |
| **2D** | FWHM + quality flags | **DONE (verify)** | G1.5 two-crossing FWHM + flags; 71×70 flagged `boundary_truncated=True`; smoke FWHM reclassified; analytic tests (§5 §3). |
| **3** | Per-node certification + restart diagnostics | **DONE (verify)** + 1 PARTIAL | §5 §2-C (7-criteria map, thresholds/units) + §6 (full 71×70 record); endpoint→restart separated from drift; Anderson reset documented. **PARTIAL:** state explicitly whether **continuity residual / number balance are acceptance criteria or diagnostic-only.** Uncertified-node exclusion from Gate-4 to confirm in the runner. |
| **4** | Threading-control evidence + v1.6 rationale | **DONE (maintainer-verified)** + 1 PARTIAL | §5 §4 d-calc (4.33/4.30/4.57%); **bit-identity verified at FULL precision** — t1(`52c981f`)==node-1(`2775697`)==repeat(`52ed83a`) = 3.0770514168841145e25 (not rounded). Well-cond <0.6% listed. **PARTIAL:** explicit **G3.4 reconciliation** — an all-single-thread sweep IS the reference, so there is no cross-thread pair to re-run; state this and that the trigger is retired for the uniform-1-thread protocol. |
| **5** | Shared anchor + orchestration | **DONE (verify)** + 1 TODO | §5 §2-B: anchor = independent X/Y repeats (collision-free run IDs via G1.3), neither finished → comparison deferred until both certify. **TODO:** the sequential two-family run test (shared with 2A) + failure-isolation assertion + manifest `running/queued/certified/failed/UNRESOLVED` states. |
| **7** | Gate-4 analysis + release | **amendment filed** | Rules frozen v1.6 §6; **surface-hotspot amendment `3c6f8f3`** reframes the hotspot-depth test (peak at y=0) — awaiting reviewer concurrence. G3.4 reconciliation (CP4) feeds here. |

## Remaining work for Friday (the genuinely-new items)

1. **Metadata-on-disk regression** — reopen each node JSON and assert all provenance/criteria fields are
   persisted (CP2A).
2. **Sequential X-then-Y orchestration test** — a clean two-family dry run proving the shared anchor
   doesn't make the second family fail, with failure-isolation (CP2A/CP5).
3. **Two short explicit statements** (no code): continuity-residual / number-balance = acceptance vs
   diagnostic (CP3); G3.4 trigger retired under the uniform single-thread protocol (CP4); and the
   `--node`-vs-family-sweep authorization scope (CP1).
4. **Manifest state vocabulary** — ensure the family manifest emits `running/queued/certified/failed/
   UNRESOLVED` explicitly (CP5).

Everything else the checklist asks for is already committed; CP6 (continuation) and the final GO are the
reviewer's prospective decision once the above close. Scope unchanged: discretization only.
