# Ready for prospective GO — Checkpoints 0–7 closed (maintainer-verified)

**Date:** 2026-10-29 · **Sweep: HALTED** (reviewer HOLD `d1b068d`) · **Requesting the reviewer's
prospective GO + node-1 admissibility decision.**

All items on the reviewer checklist (`ANISO_SWEEP_NEXT_STEP_CHECKPOINTS_20261027.md`) are now closed and
maintainer-verified against the committed evidence (verified = the control matches the pre-registered
rule, not merely that code ran).

| CP | Status | Evidence |
|---|---|---|
| 0 contain + preserve | **CLOSED** | `ANISO_SWEEP_HALT_RECORD_20261026.md` (`6d55242`) |
| 1 governance / auth | **CLOSED** | §5 §1 timeline (v1.6 frozen 09:27 → user auth 09:32 → launch 09:40, reviewer pending); G0.2 hard-block; **S3** `--node` permitted pre-sweep |
| 2A warm-start/provenance | **CLOSED** | G1.1-1.3 + **`test_metadata_persisted_on_disk`** (reopens JSON on disk) (`db61803`) |
| 2B thread enforcement/CLI | **CLOSED** | `--node/--threads` parse + regression (`52c981f`); `threadpool_actual` persisted |
| 2C 4th-level RAM gate | **CLOSED** | G1.4 preflight + blocked/allowed tests |
| 2D FWHM + flags | **CLOSED** | G1.5 two-crossing + `boundary_truncated` flags; analytic tests |
| 3 per-node certification | **CLOSED** | §5 §2-C/§6; **S1** continuity-residual + number-balance are ACCEPTANCE criteria (2 of 7 AND-gated); uncertified nodes excluded from Gate-4 (**S4**) |
| 4 threading evidence / v1.6 | **CLOSED** | §5 §4 d-calc (4.33/4.30/4.57%); **bit-identity verified at FULL precision** across 3 commits = 3.0770514168841145e25; **S2** G3.4 retired under uniform single-thread |
| 5 anchor + orchestration | **CLOSED** | §5 §2-B (independent X/Y repeats, collision-free IDs); `run_sweep()` sequential test + failure isolation (`db61803`); manifest `queued/running/certified/failed/UNRESOLVED` |
| 7 Gate-4 rules | **FROZEN; concurrence requested** | v1.6 §6 + surface-hotspot amendment with the **parameter-free r≥1 divergence criterion** (`1bb7e0a`) |

## Governance framing (for the admissibility decision)

The deviation is **user-authorized, reviewer-pending** — the launch timeline is v1.6 frozen **09:27** →
**user authorization 09:32** → first run **09:40**, with the external reviewer sign-off outstanding. The
run was not unauthorized; it proceeded on the project owner's authorization ahead of the independent
sign-off, and was disclosed and halted on request. The already-generated node-1 data is preserved for a
separate admissibility decision.

## The two decisions requested

1. **Prospective GO** to resume the single-threaded sweep from the documented checkpoint on the reviewed
   commit + frozen v1.6 spec (and concurrence on the Gate-4 amendment incl. the r≥1 criterion).
2. **Admissibility** of the already-generated node-1 (71×70) certified data — three bit-identical
   single-thread runs across three commits; preserved, not discarded.

## Evidence bundle (all on `main`)

- `docs/ANISO_CHECKPOINT_CROSSWALK_20261027.md` — this crosswalk's source
- `docs/ANISO_S5_EVIDENCE_PACKAGE_20261026.md` + `docs/ANISO_S5_SUPPLEMENT_20261029.md`
- `docs/ANISO_SWEEP_HALT_RECORD_20261026.md`
- `docs/ANISO_GATE4_SURFACE_HOTSPOT_AMENDMENT_20261027.md` (with §3.1 r≥1 criterion)
- `campaign/aniso_mesh_study.py` + `campaign/test_aniso_mesh_study.py` (tests), `campaign_manifest.json`
- node-1 / t1 / t8 / repeat artifacts under `data/`

Scope unchanged: **discretization convergence only**; Liang-1997 physics validation (Gate E part 2) is
separate and open; no continuum/predictive claim from this study.
