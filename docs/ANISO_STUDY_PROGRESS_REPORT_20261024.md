# Anisotropic mesh study — progress report for the reviewer

**Date:** 2026-10-24 · **Against:** `docs/ANISO_STUDY_REVIEW_CHECKPOINT_20261023.md` (Gates 0–4) ·
**Spec:** v1.3 · **Repo:** <https://github.com/chanlikt-lgtm/Liang1997> ·
**Full sweep: HELD · Reviewer sign-off: PENDING**

Status mapped to your gate checklist. "Verified (maintainer)" means we checked the evidence against the
pre-registered rule, not merely that code ran; your independent verification is of course the gate.

## Gate 0 — Governance

| Item | Status | Evidence |
|---|---|---|
| G0.1 authorization split (acceptance / sign-off / execution) | **Done** | spec v1.3 header + reviewer note; you accepted the v1.3 governance change |
| G0.2 hard-block on unauthorized full-sweep launch | **Done (code) — pending your verify** | `ebb5913`; harness refuses the sweep without execution authorization (not a warning) |
| G0.3 freeze experiment definitions before inspecting results | **Done** | spec v1.3 + checkpoint committed; per-node provenance recorded |

## Gate 1 — Harness integrity

| Item | Status | Evidence |
|---|---|---|
| G1.1 warm-start path assert, no silent cold fallback | **Done — pending verify** | `ebb5913`; 12/12 tests (`fd1dafa`) |
| G1.2 thread enforcement + per-node provenance | **Done — pending verify** | `ebb5913`; records effective threads + versions + CPU + commit |
| G1.3 collision-free output naming (mesh+threads+run-id+cfg) | **Done — pending verify** | `ebb5913` |
| G1.4 measured RAM gate for the 4th level | **Pending** (next batch) | — |
| G1.5 two-crossing interpolated FWHM + quality flags | **Pending** (next batch; see smoke note) | — |
| G1.6 shared-anchor shared-vs-repeats statement | **Pending** (next batch) | — |

## Gate 2 — Numerical certification (demonstrated on the 71×70 smoke)

The corrected 71×70 smoke (v2) is **CERTIFIED** on both criteria; maintainer-verified against spec §5.
Evidence: `campaign/ANISO_SMOKE_71x70_RESULT.md`, `data/she2d_aniso_71x70.{npz,json}` (commit `6b051d4`).

| Criterion | Value | Gate | Pass |
|---|---|---|---|
| R_phi (numerical residual) | 9.261e-05 | < 1e-4 | ✓ |
| continuity residual | 3.437e-09 | recorded | ✓ |
| relative number balance (conservation) | 2.039e-05 | recorded | ✓ |
| 40-iter drift, raw G_ii | 2.823e-05 | < 0.5% | ✓ |
| 40-iter drift, **interp** G_ii | 1.007e-05 | < 0.5% | ✓ |
| 40-iter drift, G_tot | 2.216e-05 | < 0.5% | ✓ |

**Observable note (on-point to your concern):** the sub-cell **interpolated peak (2.690e25) is ~13%
BELOW the raw nodal max (3.077e25)** — an early, concrete signal that the mesh-point maximum is partly a
grid spike, so the interpolated and integrated (`G_tot = 9.183e13`) observables are the ones to trust
for the convergence conclusion. Hotspot width `avalanche_y_fwhm = 2.477e-3`; drain current 2.997e-4 A/µm.

**Caveats (disclosed):** (1) the smoke ran on `cddca92` (pre-Gate-1-fix), so it used the OLD output
naming — acceptable for a harness smoke, but **every actual sweep node will run on the Gate-1-fixed
harness** (collision-free naming + full provenance). (2) It converged at iter 574 vs ~976 for the
single-threaded v1 — threading path-dependence, which is exactly why the Gate-3 controls are required.

- G2.1–G2.4 **full per-node PASS/FAIL recording** (every criterion, raw values+units) and the explicit
  continuation-state documentation (incl. Anderson history; endpoint→restart delta vs drift) land in the
  next batch; the smoke demonstrates the criteria are computed and gated.

## Gate 3 — Threading comparability

| Item | Status | Plan |
|---|---|---|
| G3.1 paired 71×70 at effective 1 and 8 threads | **Pending** | 8-thread (~10 h, auto); 1-thread (~30–50 h, held for user go — ties up the box ~1–2 days) |
| G3.2 tabulate raw+normalized ΔG_ii/ΔG_tot/Δhotspot | **Pending** | after both controls |
| G3.3 fallback trigger `d=2|a−b|/(|a|+|b|)<0.01` | **Frozen (spec v1.3 §7)** | operational trigger, not a bound |
| G3.5 71×70 measurement is 71×70-only, not a universal bound | **Frozen (spec v1.3 §7)** | — |

## Gate 4 — Analysis rules

Frozen in spec v1.3 (§6): per-direction apparent order from **effective** spacings; monotone →
order + direction-only Richardson; **non-monotone/uncertified → inconclusive, no extrapolation**;
hotspot quality flags; discretization-only boundary preserved (no Liang-1997/continuum claim). **Pending
your confirmation that the rules are frozen before results are interpreted.**

## What remains before a full-sweep GO

1. Friday commits **G1.4/1.5/1.6**, the **G2 full per-node recording**, and the **G3 paired thread
   controls** (8-thread now; 1-thread on the user's go) — each with linked evidence.
2. Maintainer verifies the controls **match** the pre-registered rules; assembles the Gate-0..3 bundle.
3. Reviewer issues the documented GO/HOLD. The sweep runs only on GO, on the Gate-1-fixed harness, at
   fixed 8 threads, with the single-thread fallback for any triggered pair.

Scope unchanged: this is **discretization convergence only**. Physics validation vs Liang 1997 (Gate E
part 2) is separate and still open; no quantitative/physical claim is made from this study alone.
