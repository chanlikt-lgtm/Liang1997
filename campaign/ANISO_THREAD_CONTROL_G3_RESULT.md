# ANISO Mesh Study — G3.1 Paired Thread Controls — RESULT & G3.2 Comparison

**Status:** both controls CERTIFIED · G3.2 tabulation below
**Run:** `campaign/aniso_mesh_study.py --node 71 70 1500 --threads {8,1}`
**Spec:** v1.4 §7 thread policy · **Frozen solver/physics/init identical between the two runs.**

## The two controls

| control | threads | commit | finished | n_iter | R_phi | status |
|---|---|---|---|---|---|---|
| t8 | 8 (OpenBLAS/OMP/MKL) | `52c981f` (clean) | 2026-10-24 14:31 | 421 | 6.002e-05 | ✅ CERTIFIED (committed `77b671e`) |
| t1 | 1 (OpenBLAS/OMP/MKL) | `52c981f` (dirty) | 2026-10-25 03:02 | 531 | 8.092e-05 | ✅ CERTIFIED (this commit) |

Both: same `H_hash=b4319bb03303`, same `config_hash=47e3c9ec574b`, same frozen grading law
(ratio=6, W=0.09, X_C=0.60), same `phi_span=[-0.60,3.65]`, `dH=0.0125`, `NH=591`, `eps_max=3.02`.
The only intentional difference is the thread count. `threadpool_actual` confirmed
`libscipy_openblas` with `num_threads` = 1 and 8 respectively.

## G3.2 tabulation (the point of the control)

Relative difference `d(a,b) = 2|a-b|/(|a|+|b|)`, per spec §7.

| observable | t1 | t8 | d | fallback trigger (d<0.01)? |
|---|---|---|---|---|
| **Gii_max (raw nodal)** | 3.0771e25 | 2.9466e25 | **4.33%** | ❌ TRIPPED |
| **Gii_interp (sub-cell)** | 2.6901e25 | 2.5767e25 | **4.30%** | ❌ TRIPPED |
| **G_tot (integrated)** | 9.1820e13 | 8.7716e13 | **4.57%** | ❌ TRIPPED |
| Te_max | 3.1844e3 | 3.1765e3 | 0.246% | ✅ |
| drain current | 2.9970e-4 | 2.9794e-4 | 0.588% | ✅ |
| hotspot x (µm) | 0.589384 | 0.589384 | 0 | ✅ |
| hotspot y | 0.0 | 0.0 | 0 | ✅ |
| avalanche_y_fwhm (µm) | 2.1418e-3 | 2.1441e-3 | ~0.1% | ✅ |

**Field-level anatomy of the 4.3%:** over the 218 cells with Gii > 1% of peak, the ratio
`Gii(t8)/Gii(t1)` is a near-uniform scale `0.955 ± 0.006` (min 0.942, max 0.965). The peak sits at
the *same cell* `(y=0, ix=41)`, `x = 0.58938 µm` in both. `max|Δphi| = 6.88e-3 V` over a
`phi ∈ [-0.35, 3.59]` range. So the threading difference is a **global ~4.4% amplitude scale on the
impact-ionization rate**, not a relocated or reshaped hotspot.

## Interpretation

- The threading spread is **~4.3% on the near-null-space Gii amplitude**, ~4× the 1% fallback
  trigger and ~17× the 0.25% upper noise figure the spec used as its planning assumption.
- This is the same failure class recorded in MEMORY (2026-10-16): the Gii solve is near-null-space /
  ill-conditioned, so a ~1e-13 floating-point reduction-order seed (OpenBLAS 8-thread SIMD reduction
  vs single-thread) is amplified into a %-level output drift — while well-conditioned quantities
  (Te_max, drain current, hotspot location, FWHM) barely move.
- **Consequence for the sweep:** a fixed-8-thread sweep would carry a ~4% systematic offset on peak
  Gii relative to the single-thread reference, on top of the genuine mesh-convergence signal. The
  8-thread path is therefore **not a safe reference** for the pointwise-peak convergence question.

## Recommendation (for the reviewer GO/HOLD)

1. Run the **full headless sweep single-threaded** (`*_NUM_THREADS=1`), accepting the ~30-50 h/node
   cost, so the mesh signal is not contaminated by threading at the 4% level.
2. Alternatively, keep 8-thread for feasibility but treat `Gii_max`/`Gii_interp` as threading-limited
   at ±4.3% and lean on `G_tot`/hotspot-geometry/drain-current only for any near-threshold pair
   (G3.4 single-thread re-run stays mandatory for those pairs).
3. Either way, the **71×70 threading measurement is 71×70-only** (spec G3.5) — it is not a proven
   bound for the finer meshes, and the fallback trigger `d<0.01` should now be read as *already
   exceeded* for this mesh, not as a safe margin.

## Files

- `data/she2d_aniso_71x70_t1_47e3c9ec574b.{json,npz}` — 1-thread control (this commit).
- `data/she2d_aniso_71x70_t8_47e3c9ec574b.{json,npz}` — 8-thread control (committed `77b671e`).

Full sweep remains **HELD**. Physics validation vs Liang 1997 (Gate E part 2) is separate and still open.
