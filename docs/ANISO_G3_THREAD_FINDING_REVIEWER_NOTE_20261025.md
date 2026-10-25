# Reviewer note — G3.2 threading measurement result + finalized thread policy (spec v1.5)

**Date:** 2026-10-25 · **Gate 3 evidence** · **Full sweep still HELD pending your GO.**

The pre-registered one-time threading measurement (G3.2) has returned, and it **materially revises the
thread policy** — exactly the decision G3.2 was designed to make (not post-hoc tuning). Requesting your
sign-off on the finalized v1.5 policy before the sweep.

## 1. The measurement (71×70, 1 vs 8 threads, identical frozen physics/solver/init — both CERTIFIED)

Relative difference `d = 2|a−b|/(|a|+|b|)`:

| observable | t1 | t8 | d |
|---|---|---|---|
| Gii_max (raw) | 3.0771e25 | 2.9466e25 | **4.33%** |
| Gii_interp | 2.6901e25 | 2.5767e25 | **4.30%** |
| **G_tot (integrated)** | 9.1820e13 | 8.7716e13 | **4.57%** |
| Te_max | 3184.4 | 3176.5 | 0.25% |
| drain current | 2.997e-4 | 2.979e-4 | 0.59% |
| hotspot (x,y) | (0.58938, 0) | (0.58938, 0) | 0 |
| avalanche FWHM | 2.142e-3 | 2.144e-3 | ~0.1% |

Field anatomy: a **near-uniform ~4.4% amplitude scale** on the ionization rate (ratio 0.955 ± 0.006,
*same* peak cell, `max|Δφ| = 6.9e-3 V`) — not a relocated or reshaped hotspot. Maintainer-verified; the
arithmetic and the uniform-scale structure check out.

**Interpretation:** this is the documented near-null-space ill-conditioning of Gii — an ~1e-13
reduction-order seed (8-thread SIMD vs single-thread) amplified to a %-level amplitude drift — while
well-conditioned quantities barely move. It is **~17× the 0.25% figure the planning assumption used**,
and it affects the *integrated* G_tot too, not just the pointwise peak.

## 2. Consequence

A fixed-8-thread sweep carries a ~4% threading offset on the Gii-family observables — the very
quantities the study measures for convergence — so **8-thread is not a safe reference for the Gii
*amplitude* convergence question**. The well-conditioned observables (hotspot geometry, FWHM, drain
current, Te_max) are threading-robust (<0.6%).

## 3. Finalized policy (spec v1.5 §7; user-approved 2026-10-25) — requesting sign-off

1. **Sweep at fixed 8 threads** (feasibility, ~10 h/node).
2. **Gii_max / Gii_interp / G_tot reported with an explicit ±4.3% threading-limitation flag**; no
   quantitative Gii-*amplitude* convergence claim from the 8-thread sweep alone.
3. **Quantitative convergence conclusions rest on the well-conditioned observables** — hotspot location
   (µm), FWHM (µm), drain current, Te_max. The headline grid-feature test (does the hotspot depth stop
   tracking Δy?) uses these.
4. **Mandatory single-thread resolution** for any decision-critical pair whose difference is of order
   the threading noise (Gii-family `< ~4.3%`; well-conditioned `< 0.01`) — both members re-run at 1
   thread before the claim. A definitive peak-Gii convergence statement therefore requires single-thread
   for those specific pairs; the 8-thread sweep provides the map + the well-conditioned conclusions.
5. ±4.3% is the **71×70 figure only**; finer meshes re-measured if a conclusion depends on it (G3.5).

## 4. Alternative on the table (for your consideration)

A fully single-threaded sweep (~12–50 h/node; the 71×70 1-thread control took ~12.5 h, so ~a week total)
would remove the Gii threading limitation entirely. The user elected the 8-thread-limited policy above
for feasibility; we flag the single-thread option in case you judge the Gii-amplitude convergence
question essential enough to warrant it.

## 5. Ask

Sign-off on the v1.5 thread policy (or direct us to the fully single-threaded alternative). Gates
0–2 evidence + the G3 controls are now committed; on your GO we run the 6-node sweep under the
finalized policy. Scope remains discretization-only; Liang-1997 physics validation (Gate E pt2) is
separate and open.

---

## DECISION UPDATE (2026-10-25): single-threaded sweep elected (spec v1.6)

After reviewing the mechanism, the user elected the **fully single-threaded alternative** (§4), not the
8-thread-limited policy of §3. Spec is now **v1.6**: every sweep node runs at `*_NUM_THREADS = 1`. This
**removes the ±4.3% G_ii threading limitation entirely** — peak and integrated G_ii become clean, so the
peak-G_ii amplitude convergence question is answerable (not just the well-conditioned geometry). Cost
~12–50 h/node (~a week total). The ask is simplified: **sign-off on the v1.6 single-threaded policy**;
on GO we run the 6-node single-threaded sweep. Scope unchanged (discretization only).
