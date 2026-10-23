# Anisotropic mesh study — reviewer note (pre-registration update)

**Date:** 2026-10-23 · **Spec:** `docs/ANISOTROPIC_MESH_STUDY_SPEC_V1.md` (now **v1.2**) · **Repo:**
<https://github.com/chanlikt-lgtm/Liang1997> · **Status: full sweep still HELD — awaiting your sign-off
on the v1.2 thread amendment below.**

This note (a) confirms your conditional-approval adjustments are folded in, and (b) requests sign-off on
one further pre-registration change (thread policy) made for compute feasibility — disclosed *before any
sweep results exist*, per the pre-registration discipline.

## 1. Your conditional approval — actioned (spec v1.1)

- **Adj. 1 — outcome-independent extra level.** The 4th refinement level (`Nx=200` / `Ny=120`) is
  pre-committed to a **resource/convergence rule only** — run iff the 3rd level certified AND it fits
  physical RAM. Never decided on whether its result would support the hypothesis. (§3)
- **Adj. 2 — interpolated peak + physical units.** A **sub-cell interpolated peak G_ii** (quadratic fit
  around the nodal max) is reported alongside the raw nodal `Gii_max`; hotspot in **µm**, so an apparent
  shift cannot be a cell-dimension artifact. (§4)
- **Req. 4 — dual certification.** Each node certifies on **numerical residual AND observable
  stability**, both reported (R_phi<1e-4 + continuity residual + number balance; plus a 40-iter
  stopping-disabled drift <0.5% on raw & interpolated G_ii and G_tot). (§5)

We proceeded per your decision: **GO** for harness + unit tests + the single `71×70` smoke; **full sweep
HELD**.

## 2. Pre-registration change requesting sign-off (spec v1.2): thread policy

**What changed.** §7 previously required strict single-threaded BLAS. We are amending to a **fixed
8-thread sweep** with explicit threading-noise control.

**Why.** Strict single-threaded is ~2–3 min/iter × ~1000 iters ≈ **30–50 h/node × 6 ≈ 200–300 h** —
impractical. The reason to pin threads is that an asymptotic mesh signal (sub-% drifts) must not be
contaminated by threading reduction-order noise (~0.1–0.25%, from our cross-platform finding). But the
trio differences are **~40% and non-monotone**, orders above that noise — so threading matters only once
a node-pair difference approaches ~1%.

**The amended policy (integrity safeguards kept):**
1. **Fixed `*_NUM_THREADS = 8` for every node**, identical, recorded in each node's provenance — so the
   reduction order is a controlled constant across the comparison (not a free variable).
2. **One-time threading-noise measurement:** `71×70` run at threads=8 **and** threads=1; report
   `|ΔG_ii|`, `|ΔG_tot|`, hotspot shift → fixes the threading-noise floor for the study.
3. **Single-threaded fallback:** any node-pair whose observable difference falls **below ~1%** is re-run
   single-threaded before any asymptotic/order conclusion is drawn from it.

This keeps the sweep feasible while *bounding* threading noise and *eliminating* it exactly where it
could affect a convergence conclusion. It is disclosed before results, and no acceptance threshold is
relaxed.

## 3. Smoke status (71×70)

- v1 of the smoke **converged** (R_phi 6.12e-5 at outer 976) but crashed in `_certify` on a NumPy
  array-truth bug and wrote no outputs (18 h lost). **Fixed + regression test** at commit `cddca92`.
- v2 is re-running (the harness-validation smoke). Note: v2 was launched **multi-threaded**, so its
  numbers are a smoke data point only, **not** a spec-compliant sweep node; `(71,70)` will be re-run
  under the v1.2 policy (8-thread + the 1-thread control) when the sweep is authorized.

## 4. What we are asking

Sign-off on the **v1.2 thread amendment** (§2). On your OK + the v2 smoke landing with outputs, we will
run the ~6-node sweep (X-family `Nx∈{71,100,141}@Ny=70`; Y-family `Ny∈{58,70,85}@Nx=100`; shared
`(100,70)`) at threads=8 plus the `71×70` single-thread control. Scope remains **discretization
convergence only** — physics validation against Liang 1997 is the separate, still-open Gate-E part 2,
and no continuum/predictive claim is made from this study alone.
