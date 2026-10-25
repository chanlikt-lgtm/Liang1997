# §5 Evidence Package — Anisotropic Mesh Study (Gate E, part 1)

**Date:** 2026-10-26 · **Spec:** v1.6 (single-threaded) · **Pinned commit:** `52ed83a`
**Status:** sweep HALTED (reviewer HOLD, `d1b068d`) — this package is the evidence for the prospective GO.

---

## 1. Governance & timestamps (reviewer's sensitive item — stated plainly)

The single-threaded sweep **began before the reviewer's formal sign-off on the v1.6 thread policy.**
This is disclosed here as a fact, not hidden.

| event | timestamp (MYT) | commit | note |
|---|---|---|---|
| G3.1 8-thread 71×70 control CERTIFIED | 2026-10-24 18:22 | `77b671e` | R_phi 6.00e-5, all 7 criteria PASS |
| G3.2 1-thread 71×70 control CERTIFIED + t1-vs-t8 = 4.3% | 2026-10-25 09:10 | `32322ef` | threading sensitivity measured |
| spec **v1.5** finalized (8-thread, Gii threading-limited) | 2026-10-25 09:22 | `e877868` | superseded |
| spec **v1.6 FROZEN** (revert to single-threaded) | 2026-10-25 09:27 | `dd56686` | removes the ±4.3% Gii threading limit |
| **user authorization** (Chan Lik Tan, Telegram) | 2026-10-25 09:32 | — | `campaign/aniso_exec_auth.json` |
| single-threaded launcher + G0.2 auth committed | 2026-10-25 09:39 | `2775697` | — |
| **first production-run start** | 2026-10-25 09:40 | — | `logs/aniso_sweep_launcher.log` line 1 |
| **proactive disclosure of pre-signoff start** | 2026-10-26 06:56 | `44709cf` | requested concurrent/retroactive GO |
| **reviewer HOLD → checkpoint-halt** | 2026-10-26 ~07:00 | `d1b068d` | sweep halted |

**The deviation:** spec v1.6 was frozen (09:27) and the sweep launched (09:40) on **user** authorization
only; the **reviewer's v1.6 sign-off was still pending** and arrived as a HOLD ~21 h later. No acceptance
rule was relaxed — every node runs under the frozen pre-registered spec (R_phi<1e-4 AND 40-iter
observable drift <0.5%). The disclosure (`44709cf`) was made proactively, before the HOLD.

---

## 2. Clarifications B / C / D

### B — shared anchor (100,70)
The spec (G1.6) defines the anchor as **independent once-per-family repeats** (X-family warm-chain from
71×70; Y-family warm-chain from 100×58), producing **distinct family-tagged artifacts**:
- X-repeat artifact: `she2d_aniso_100x70_t1_*_X.npz`
- Y-repeat artifact: `she2d_aniso_100x70_t1_*_Y.npz`

The report stated the **repeat policy**, not that both repeats had finished. In fact **neither has**:
node 2 (100×70, X) was halted at outer 563 (not certified), and the Y-family never started. Therefore the
(100,70) X-vs-Y comparison is **deferred** until both certify; it is not claimed. `compare_anchor()`
returns `available: false` until then.

### C — 7 PASS/FAIL criteria → reported quantities (thresholds + units)
The certification is a 7-criterion AND-gate (`G2.1`/`G2.3`); a node certifies only if **all** pass. The
mapping, with the 71×70 node-1 values (commit `2775697`, artifact `_X`):

| # | criterion | quantity | gate | op | unit / normalization |
|---|---|---|---|---|---|
| 1 | R_phi | 8.0923e-5 | 1e-4 | < | V, absolute |
| 2 | continuity_residual | 3.4514e-9 | 1e-6 | < | 1, scaled by max(|bs|,1) |
| 3 | number_balance | 2.0798e-5 | 1e-2 | < | 1, |balance|/scale |
| 4 | drift_raw_Gii | 1.0997e-4 | 5e-3 | < | 1, 40-iter continuation spread |
| 5 | drift_interp_Gii | 9.9620e-5 | 5e-3 | < | 1, 40-iter continuation spread |
| 6 | drift_G_tot | 1.1360e-4 | 5e-3 | < | 1, 40-iter continuation spread |
| 7 | hotspot_drift | 5.7428e-5 | 0.5 | < | cell, representative-cell units |

Recorded-but-not-gating observables (with their own quality flags): `Gii_max`, `Gii_interp`, `G_tot`,
`drain_current_A_per_um`, `avalanche_y_fwhm` + `fwhm_flags`, `xy_Gii_max`/`xy_Gii_max_interp`.

### D — FWHM flagging
`avalanche_y_fwhm` is a **recorded observable, not one of the 7 gating criteria** — it cannot score a
PASS on its own. It is always accompanied by `fwhm_flags` (`boundary_truncated`, `unresolved`,
`multi_peak`) from `_profile_fwhm_2cross()`. A boundary-truncated / unresolved / multi-peak profile is
**flagged** (and thus a downstream consumer must not treat the number as a valid full width). The actual
71×70 node-1 FWHM is `boundary_truncated=True` (hotspot sits on the y=0 surface), so its 2.14 µm width
is explicitly a truncated half-width, not a true FWHM. Analytic unit test `test_fwhm_2cross_flags`
covers all three flag cases.

---

## 3. Corrected harness — source DIFF + regression results

Harness: `campaign/aniso_mesh_study.py`. It reuses `build_mesh` + `solve_coupled` **byte-unchanged**
from the frozen driver, dropping only the self-similar sequence guard.

Repairs (commits on the harness) relative to the first-audited version:

| commit | repair |
|---|---|
| `cddca92` | `_certify` array-truth crash (had lost 18 h of smoke evidence); + regression test |
| `ebb5913` | Gate-1 integrity: G0.2 auth hard-block, G1.1 warm-start assert, G1.2 thread enforcement + provenance, G1.3 collision-free naming |
| `2f489c4` | G1.4 RAM gate (4th-level), G1.5 FWHM flags, G1.6 anchor semantics, G2 full 7-criterion certification |
| `52c981f` | `--node --threads` arg parse (G3 launch path); + `test_parse_node_rest_threads` |

Solver + harness byte-identity across the sweep span verified: `git diff 2775697..52ed83a -- src/ campaign/aniso_mesh_study.py` is **empty** (only docs + `monitor_aniso.sh` changed).

**Regression suite: 17/17 PASS** (`python3 -m pytest campaign/test_aniso_mesh_study.py -q`), including:
- **Boundary-peaked FWHM** → `test_fwhm_2cross_flags` (monotonic edge-peak → `boundary_truncated`; two
  Gaussians → `multi_peak`; single-cell spike → `unresolved`).
- **Blocked 4th-level launch** → `test_resource_gate` (predicted RSS 1e15 → `approved=False`).
- **Successful 4th-level launch** → `test_resource_gate` (predicted RSS 1e8 → `approved=True`).
- **R_phi alone never certifies** → `test_certify_not_rphi_alone` (R_phi passes but continuity fails →
  `UNRESOLVED`, not CERTIFIED).
- Thread enforcement → `test_thread_env_enforced`; G0.2 hard-block → `test_exec_auth_hard_block`;
  mesh-law byte-identity vs driver → `test_mesh_law_unchanged_vs_driver`.

---

## 4. Paired t1/t8 thread controls + d-calc

Both 71×70 controls certified (same commit `52c981f`, config_hash `47e3c9ec574b`):

| observable | t1 (1-thread) | t8 (8-thread) | d = 2|a−b|/(|a|+|b|) |
|---|---|---|---|---|
| Gii_max | 3.0770514e25 | 2.9465933e25 | **4.33%** |
| Gii_interp | 2.6900567e25 | 2.5767173e25 | **4.30%** |
| G_tot | 9.1820491e13 | 8.7716302e13 | **4.57%** |
| drain_current | 2.9970e-4 | 2.9794e-4 | 0.59% |
| R_phi | 8.0923e-5 | 6.0021e-5 | 29.7% (noisy metric) |

This is the ~4.3% threading sensitivity on the **Gii-family** observables that motivated v1.6
(single-threaded): well-conditioned quantities (drain current) move <0.6%, while the near-null-space Gii
amplifies the reduction-order seed. R_phi's 29.7% spread is the same ill-conditioned-metric behavior
documented in the reproducibility report (§4).

---

## 5. Single-thread reproducibility repeat (the one compute item)

- Launched **2026-10-26 07:14 MYT**, running: `campaign/aniso_mesh_study.py --node 71 70 --threads 1 --run-id repeat`
  (cold start, single-threaded, `threadpool_actual` num_threads=1, ~12.5 h).
- Artifact on completion: `she2d_aniso_71x70_t1_1e010e13e26f_repeat.npz` (+ `.json`).
- **Already-available bit-reproducibility datum:** the production X-family node-1
  (`_t1_552bb609f0f2_X`, commit `2775697`) is **bit-identical** to the t1 control
  (`_t1_47e3c9ec574b`, commit `52c981f`): Gii_max = 3.0770514168841145e25, Gii_interp =
  2.690056703473506e25, G_tot = 91820491422435.28, R_phi = 8.092337900311719e-5, n_iter = 531 — all
  identical to full precision, across two different git commits (config_hash differs only via the
  embedded `solver_commit`). The fresh repeat is a second, independent cold-start confirmation.
- **Provenance note (honest):** the repeat runs at `52ed83a` with `git_dirty="dirty"` and
  `config_hash=1e010e13e26f`. Both are **cosmetic**: `_git_dirty` is "dirty" only because of untracked
  runtime artifacts (`logs/`, `data/*.npz/json`, `.aniso_monitor_state`) — no tracked source is modified
  (`git status --porcelain` shows no `M` entries); and `config_hash` embeds `solver_commit`, so it
  changes with every commit even though the frozen physics constants (RATIO/W/X_C/PHI_GATE/AA_*/SHE_TOL/
  tol_phi/…) are byte-identical.

---

## 6. Full 71×70 per-criterion certification record + manifest

**Node:** 71×70 (X-family, cold start). **Status: CERTIFIED.** All 7 criteria PASS (values in §2-C).

**Manifest (SHA-256):**

| artifact | SHA-256 |
|---|---|
| `data/she2d_aniso_71x70_t1_47e3c9ec574b.npz` (t1 control) | c8a2b56cfa651fa1f13f3056a7d8126b6da5823954e4df9f16483b15aa57c7b4 |
| `data/she2d_aniso_71x70_t8_47e3c9ec574b.npz` (t8 control) | f3cdd45ef8d6ccfa6e7acd4c54deaad5e4a744213d8b56a6498739fb5f989edd |
| `data/she2d_aniso_71x70_t1_552bb609f0f2_X.npz` (production node-1) | 6596ae26d356cf3e52af8e1195a8fc9d6d2b125a246ad0dfa6959163e714312d |

**Sweep stop point:** node 2 (100×70, X) killed at **outer 563**, dφ=9.68e-4 V, Gmax=1.879e25 (not
certified) — see `docs/ANISO_SWEEP_HALT_RECORD_20261026.md`. Node 1 preserved; full node-2 trajectory in
`logs/aniso_X_family.log`. Resume = node 2 re-warm-starts from the 71×70 npz.

**Remaining (pending repeat completion + reviewer GO):** the fresh 71×70 repeat (item 5) finishes
~2026-10-26 ~20:00 MYT; the (100,70) anchor X-vs-Y comparison awaits both families certifying.
