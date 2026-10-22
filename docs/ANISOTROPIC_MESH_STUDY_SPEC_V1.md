# Anisotropic mesh-convergence study — SPEC v1 (pre-registration)

**Date:** 2026-10-22 · **Scope:** Gate E / SCI-01, discretization-convergence only. **No physics change.**
This spec is frozen and committed BEFORE any run (reviewer requirement: metrics + acceptance specified
before results; never tune parameters until outcomes are seen).

## 1. Objective

The sanctioned self-similar trio {(71,58),(100,70),(141,85)} refines drain-x and depth-y *together*
(~√2 each), so it cannot separate the two discretization errors — and it is non-monotone, so no
Richardson/continuum `G_ii` is justified. This study runs **two orthogonal single-direction families**
to answer: under **x-only** and **y-only** refinement (the other direction held fixed), does peak `G_ii`
(and the hotspot depth/width, `G_tot`, drain current) **stabilize**, or keep drifting (a grid-scale
feature)? Separating the directions is what the coupled trio structurally cannot do.

## 2. Why a separate harness (not the frozen driver)

`src/coupled_drain_richardson.py` REFUSES any `(Nx,Ny)` outside the self-similar SEQUENCE by design.
Anisotropic refinement is deliberately **non-self-similar** (`r_x ≠ r_y`), so it must NOT reuse that
guard. New harness `campaign/aniso_mesh_study.py`:
- reuses `build_mesh(Nx,Ny)` and `solve_coupled` **byte-unchanged** (same FROZEN grading law
  ratio=6/W=0.09/X_C=0.60, y=Ly·s^1.8; same FROZEN solver Phi_gate=−0.74, anderson depth6/β0.5,
  she_tol=1e-8, dH=0.0125, phi_span (−0.60,3.65));
- drops ONLY the self-similar SEQUENCE guard; records the identical npz schema;
- warm-chains within a family (each level initialized from the previous via the driver's regrid);
- no solver/physics/acceptance change — this is a mesh-count sweep in one direction.

## 3. Families (PRE-REGISTERED — do not alter after seeing results)

- **X-family** (refine drain-x, hold depth-y): `Ny = 70` fixed; `Nx ∈ {71, 100, 141}` (add `200` iff the
  141 level certifies and compute allows).
- **Y-family** (refine depth-y, hold drain-x): `Nx = 100` fixed; `Ny ∈ {58, 70, 85}` (add `120` iff 85
  certifies and compute allows).
- **Shared anchor `(100,70)`** appears in both families → cross-check both families reproduce it
  (sanity / determinism).
- Both families have ≥3 levels (minimum for an order estimate).

## 4. Observables per node (all already produced by the solver; no new physics)

peak `G_ii` (`Gii_max`); hotspot `xy_Gii_max` (x,y) + width `avalanche_y_fwhm`; `G_tot` (vertically
integrated ∫G_ii, the well-conditioned observable); `drain_current_A_per_um`; `R_phi` at stop +
`ΔG_ii^tail` (last-window relative drift); `relative_number_balance` (conservation).

## 5. Certification (PRE-REGISTERED) — observable flatness, not a single R_phi crossing

A node is CERTIFIED only if: (a) run reaches `R_phi < 1e-4`, AND (b) a 40-iteration diagnostic
continuation (stopping disabled) shows `G_ii` and `G_tot` drift `< 0.5%` and `R_phi` stays in its
mesh-dependent band (per the established R_phi-noise finding). A node that hangs on the inner
Krylov/ILU solve (the 141×85-type stagnation) or fails to reach `R_phi<1e-4` within a 1500 cap is
**UNRESOLVED**, recorded, and NOT compared as a converged value.

## 6. Analysis (PRE-REGISTERED)

Within each single-direction family the spacing ratio in the refined direction is clean (the other
direction is fixed), so:
- If an observable is **monotone** across the ≥3 levels with a consistent apparent order `p`, report
  `p` and a Richardson estimate **for that direction only**, with an error bar.
- If **non-monotone**, report **NON-ASYMPTOTIC** for that direction — no extrapolation (same discipline
  as the trio). 
- Headline decisions: (i) does peak `G_ii` stabilize under x-only refinement? under y-only? (ii) does
  the **hotspot depth** stop shrinking with `Δy` (the grid-scale-feature test) or keep tracking the
  mesh? (iii) is `G_tot` (integrated) better-behaved than the pointwise peak (expected)?
- All plots/metrics are defined here, before running; no acceptance threshold is relaxed post hoc.

## 7. Compute plan

Linux (Friday), single-threaded BLAS (OPENBLAS/OMP/MKL=1), warm-chained within family, each node to
`R_phi<1e-4` (1500 cap = safety). ~6 distinct nodes (shared anchor run once). Hours per node; watch
for inner-solve stagnation at the finest `Ny`. Checkpointed ramp if a node needs multiple windows.
No concurrent heavy trench compute.

## 8. Explicit non-goals

Not physics validation (that is the separate Gate-E part 2: substrate-hole current vs a holdout /
Liang-1997 observable). Not a continuum claim unless an order is cleanly demonstrated in BOTH
directions. Grading law and solver stay frozen. Checkpoint-C / trench untouched.
