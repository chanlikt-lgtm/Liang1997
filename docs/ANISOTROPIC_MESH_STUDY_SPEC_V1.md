# Anisotropic mesh-convergence study — SPEC v1.6 (pre-registration)

**v1.6 (2026-10-25) — SUPERSEDES v1.5: full sweep is SINGLE-THREADED.** After reviewing *why* G3.2
returned ~4.3% (G_ii is near-null-space ill-conditioned, so the 8-thread reduction-order seed is
amplified into a %-level amplitude drift on all G_ii-family observables incl. integrated G_tot), the
user elected (2026-10-25) the **fully single-threaded sweep** — `OPENBLAS_NUM_THREADS = OMP_NUM_THREADS
= MKL_NUM_THREADS = 1` for EVERY node. This REMOVES the ±4.3% G_ii threading limitation entirely: all
observables (including peak and integrated G_ii) are then clean, and the peak-G_ii *amplitude*
convergence question is answerable, not just the well-conditioned geometry. Cost: ~12–50 h/node (the
71×70 1-thread control ran ~12.5 h), ~a week total; no concurrent heavy compute. The v1.5 8-thread
policy and the v1.2–v1.4 history are retained below as superseded record. The G3.2 measurement stands
as the justification for requiring single-thread.

(Superseded v1.5 header follows.)
# Anisotropic mesh-convergence study — SPEC v1.5 (pre-registration)

**v1.5 (2026-10-25) — thread policy FINALIZED by the G3.2 measurement (not post-hoc tuning; this is
the decision G3.2 was pre-registered to make).** The 71×70 1-vs-8-thread control
(`campaign/ANISO_THREAD_CONTROL_G3_RESULT.md`) measured **~4.3% threading sensitivity on ALL Gii-family
observables** — Gii_max 4.33%, Gii_interp 4.30%, **G_tot 4.57%** — a near-uniform ~4.4% amplitude scale
(ratio 0.955±0.006, same peak cell), while well-conditioned quantities move <0.6% (Te_max 0.25%,
drain-I 0.59%, hotspot x/y 0, FWHM ~0.1%). This is ~17× the 0.25% planning assumption. **Decision
(user-approved 2026-10-25):** keep the FIXED-8-THREAD sweep for feasibility, but treat the Gii-family
observables as **threading-limited at ±4.3% (71×70-measured; 71×70-only, may be worse on finer meshes
per G3.5)**. See §7 for the finalized rules. v1.3/v1.4/v1.2 history retained below.

(Original header text from v1.3 follows.)
# Anisotropic mesh-convergence study — SPEC v1.3 (pre-registration)

**v1.3 (2026-10-23):** adopts the reviewer gating checkpoint
(`docs/ANISO_STUDY_REVIEW_CHECKPOINT_20261023.md`, Gates 0–4, all blocking before full-sweep
authorization) and sharpens three pre-registration points per it: authorization status split into
acceptance / sign-off / execution (G0.1, above); exact fallback trigger `d=2|a−b|/(|a|+|b|)<0.01` as an
operational trigger not a bound (G3.3); the 71×70 thread measurement is a 71×70-only reference, not a
universal noise bound (G3.5). Harness-integrity (Gate 1), full certification recording (Gate 2), and
paired-thread controls (Gate 3) are implementation items for the harness.

**v1.2 (2026-10-22, user-approved):** thread policy amended from strict single-threaded to a FIXED
8-thread sweep + a one-time 71×70 single-vs-8 measurement + single-threaded fallback for triggered
node-pairs (§7). Rationale: strict single-threaded ≈ 200–300 h is impractical; the trio's ~40%
non-monotone differences sit far above threading noise.


**Date:** 2026-10-22 · **Scope:** Gate E / SCI-01, discretization-convergence only. **No physics change.**
This spec is frozen and committed BEFORE any run (reviewer requirement: metrics + acceptance specified
before results; never tune parameters until outcomes are seen).

**Authorization status (reviewer G0.1 — three distinct things, do not conflate):** (a) *proposal /
thread-amendment acceptance* = **user-approved** (Chan Lik, 2026-10-22); (b) *scientific-review
sign-off* = **PENDING** (reviewer checkpoint `docs/ANISO_STUDY_REVIEW_CHECKPOINT_20261023.md`, Gates
0–4); (c) *execution authorization for the full sweep* = **HELD** until Gates 0–3 PASS with evidence and
Gate 4 rules are frozen. "User-approved" in §7 means (a) only; it is NOT (b) or (c). The harness must
HARD-BLOCK a full-sweep launch while (c) is absent (G0.2), not merely warn.

**v1.1 — folds in the reviewer's conditional-approval adjustments (2026-10-22):** (adj. 1) the 4th
refinement level is pre-committed to a resource/convergence rule, never an outcome-dependent one (§3);
(adj. 2) report a sub-cell interpolated peak G_ii alongside the raw nodal max, hotspot in physical units
(§4); (req. 4) certify on numerical residual AND observable stability, both reported (§5). Reviewer
status: GO for harness + unit tests + the single 71×70 smoke; full sweep HELD pending the smoke evidence
and confirmation of the five requirements.

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

- **X-family** (refine drain-x, hold depth-y): `Ny = 70` fixed; `Nx ∈ {71, 100, 141}`.
- **Y-family** (refine depth-y, hold drain-x): `Nx = 100` fixed; `Ny ∈ {58, 70, 85}`.
- **Shared anchor `(100,70)`** appears in both families → cross-check both families reproduce it
  (sanity / determinism).
- Both families have ≥3 levels (minimum for an order estimate).
- **4th level (`Nx=200` / `Ny=120`) — pre-committed decision rule (reviewer adj. 1):** run the 4th
  level **iff** (a) the 3rd level CERTIFIED (per §5) **and** (b) its peak working set fit available
  physical RAM with no swap-thrash. The decision is **resource/convergence-based only** — it is NEVER
  made on whether the extra level's result would support or weaken the hypothesis. This rule is frozen
  here, before any result exists.

## 4. Observables per node (all already produced by the solver; no new physics)

peak `G_ii` (raw nodal `Gii_max`); **sub-cell interpolated peak `G_ii`** (parabolic/quadratic fit
around the nodal max in both x and y) reported ALONGSIDE the raw nodal max (reviewer adj. 2 — a nodal
maximum alone is grid-sensitive and does NOT establish spatial convergence); hotspot location
`xy_Gii_max` **in physical units (µm)** + width `avalanche_y_fwhm` (µm); `G_tot` (vertically integrated
∫G_ii, the well-conditioned observable); `drain_current_A_per_um`; `R_phi` at stop + `ΔG_ii^tail`
(last-window relative drift); `relative_number_balance` (conservation). Because the hotspot is reported
in fixed physical units against the pre-registered observable set, an apparent shift cannot be an
artifact of merely changing cell dimensions — it must move in µm to count.

## 5. Certification (PRE-REGISTERED) — observable flatness, not a single R_phi crossing

A node is CERTIFIED only if BOTH are met and BOTH are reported (reviewer req. 4 — observable stability
AND numerical residual, never one alone): (a) **numerical residual** — run reaches `R_phi < 1e-4`, with
the linear/continuity residual and `relative_number_balance` recorded at the endpoint; AND (b)
**observable stability** — a 40-iteration diagnostic continuation (stopping disabled) shows raw and
interpolated `G_ii` and `G_tot` drift `< 0.5%` while `R_phi` stays in its mesh-dependent band (per the
established R_phi-noise finding). Both the residual history and the observable-drift window are reported
for every node. A node that hangs on the inner Krylov/ILU solve (the 141×85-type stagnation) or fails
to reach `R_phi<1e-4` within a 1500 cap is **UNRESOLVED**, recorded, and NOT compared as a converged
value. Per-node provenance (full commit + dirty flag, mesh+H hashes, versions, warm-source) is recorded
for every run.

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

Linux (Friday), warm-chained within family, each node to `R_phi<1e-4` (1500 cap = safety). ~6 distinct
nodes (shared anchor run once). Checkpointed ramp if a node needs multiple windows. No concurrent heavy
trench compute. Watch for inner-solve stagnation at the finest `Ny` (→ UNRESOLVED).

**Thread policy (v1.2 amendment — user-approved 2026-10-22; reviewer to be notified).** Strict
single-threaded (`*_NUM_THREADS=1`) would be ~2–3 min/iter × ~1000 iters ≈ 30–50 h/node × 6 ≈ 200–300 h
— impractical. The pinned-thread reason is that the asymptotic mesh signal (sub-% drifts) must not be
contaminated by threading reduction-order noise (~0.1–0.25%, per our cross-platform finding); but the
trio differences are ~40% and non-monotone, orders above that noise, so threading matters only once a
node-pair difference approaches ~1%. Policy:
1. **Fixed thread count for the whole sweep:** `OPENBLAS_NUM_THREADS = OMP_NUM_THREADS = MKL_NUM_THREADS
   = 8`, identical for EVERY node, recorded in each node's provenance. Feasible (~10 h/node).
2. **Quantify the threading contribution once:** run the cheap `71×70` BOTH at threads=8 and threads=1
   (identical frozen physics/solver/init), retain separate artifacts, and tabulate raw + normalized
   `ΔG_ii,max`, `ΔG_tot`, hotspot `(x,y)` shift. This is an **operational reference for `71×70` only** —
   **NOT** a rigorous threading-noise bound generalizable to every mesh (reviewer G3.5). Larger meshes
   are not assumed to share this difference.
3. **Fallback trigger (pre-registered, reviewer G3.3):** for an adjacent node-pair `(a,b)` of a positive
   observable, the relative difference `d(a,b) = 2|a−b| / (|a|+|b|)`; the **operational trigger** is
   `d < 0.01` (with separate absolute tolerances for near-zero quantities and for coordinate/hotspot
   shifts). The `1%` is a **trigger, not a proven uncertainty bound.** Whenever such a pair is used for a
   near-convergence or asymptotic-order claim and meets the trigger, **re-run BOTH members
   single-threaded** and compare the inferred mesh trend before drawing the conclusion (G3.4).
This keeps the sweep feasible while controlling threading exactly where a convergence conclusion depends
on it — without overclaiming a universal noise bound.

**v1.5 FINALIZED policy (after the G3.2 measurement returned ~4.3%):**
1. **Sweep runs at fixed 8 threads** (feasibility, ~10 h/node), identical config per node, recorded.
2. **Gii-family observables (Gii_max, Gii_interp, G_tot) are reported with an explicit ±4.3%
   threading-limitation flag.** No quantitative peak/integrated-Gii *amplitude* convergence conclusion
   is drawn from the 8-thread sweep alone — that question is threading-limited at 8 threads.
3. **Quantitative convergence conclusions come from the well-conditioned observables** — hotspot
   location (µm), avalanche FWHM (µm), drain current, Te_max — which are threading-robust (<0.6%). The
   headline grid-feature test (does the hotspot depth stop tracking Δy?) rests on these.
4. **Mandatory single-thread resolution (G3.4):** for ANY observable used in a near-convergence /
   asymptotic-order claim where an adjacent node-pair relative difference `d=2|a−b|/(|a|+|b|)` is of
   order the threading noise (i.e. `< ~4.3%` for Gii-family, `< 0.01` for the well-conditioned set),
   BOTH members of that pair are re-run single-threaded before the claim. In practice a definitive
   peak-Gii convergence statement requires single-thread for the decision-critical pairs; the 8-thread
   sweep provides the map and the well-conditioned conclusions.
5. The ±4.3% is the **71×70 figure only**; finer meshes are not assumed to share it and are re-measured
   if a conclusion depends on it.

## 8. Explicit non-goals

Not physics validation (that is the separate Gate-E part 2: substrate-hole current vs a holdout /
Liang-1997 observable). Not a continuum claim unless an order is cleanly demonstrated in BOTH
directions. Grading law and solver stay frozen. Checkpoint-C / trench untouched.
