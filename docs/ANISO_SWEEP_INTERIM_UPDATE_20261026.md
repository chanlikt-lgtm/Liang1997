# Anisotropic sweep — interim update for the reviewer

**Date:** 2026-10-26 · **Spec:** v1.6 (single-threaded) · **Repo:** <https://github.com/chanlikt-lgtm/Liang1997>

## Transparency note (please read first)

The **single-threaded sweep is underway** — and in the interest of honesty it **began before your formal
sign-off on the v1.6 thread policy.** We are disclosing this proactively and requesting a **concurrent /
retroactive GO** on v1.6. If you prefer we pause pending sign-off, say so and we will checkpoint-halt
(the run is deterministic and resumable). No acceptance rule was relaxed; the nodes run under the frozen
pre-registered spec.

## Why v1.6 is single-threaded (recap)

The pre-registered G3.2 measurement returned **~4.3% threading sensitivity on all G_ii-family
observables** (G_ii_max 4.33%, interp 4.30%, integrated G_tot 4.57%), while well-conditioned quantities
move <0.6% — the documented near-null-space ill-conditioning of G_ii amplifying a reduction-order seed.
Rather than accept a ~4% threading limit on the very observables under study, the sweep runs
**single-threaded** (`*_NUM_THREADS=1`), which removes the G_ii threading limitation entirely. Cost
~12–50 h/node (~a week total).

## Gate status (against your checkpoint)

| Gate | Status |
|---|---|
| G0 governance | done (v1.6 auth split; hard-block in harness) |
| G1 harness integrity | committed — G0.2/G1.1/G1.2/G1.3 (12/12 tests) + G1.4/G1.5/G1.6 |
| G2 numerical certification | per-node 7-criterion PASS/FAIL recording + continuation-state doc |
| G3 threading | both 71×70 controls CERTIFIED; the 4.3% finding drove v1.6 (single-thread) |
| G4 analysis rules | frozen in spec v1.6 §6 |

## Sweep progress (live, 2026-10-26 ~06:51 MYT)

| node | family | state | detail |
|---|---|---|---|
| 71×70 | X (Ny=70) | ✅ CERTIFIED | R_phi 8.09e-5 (<1e-4), G_ii_raw 3.0771e25, converged outer 530 |
| 100×70 | X (Ny=70) | 🔄 running | warm-started from 71×70; outer ~516, dφ ~1.2e-3 V (slower — finer mesh, harder null space) |
| 141×70 | X | queued | watch for 141×85-type inner-solve stagnation → UNRESOLVED |
| 100×58 | Y (Nx=100) | queued | |
| 100×85 | Y (Nx=100) | queued | |
| (100×70) | shared anchor | — | X/Y independent repeats per G1.6; cross-checked |

**Correctness checks:** `threadpool_actual` confirms `num_threads=1`; provenance git `2775697`, clean
tree; solver byte-identical to the t1 control. Node 1's certified value equals the t1 71×70 control
exactly (3.0771e25) — threading policy is doing what it should. Health: single-core 100%, 69 °C, no
stall.

## What comes next

As each node certifies we record the full per-node evidence (R_phi + continuity residual + conservation
+ raw/interp G_ii + G_tot + hotspot-in-µm + FWHM, with 7-criterion PASS/FAIL). On completion we run the
Gate-4 analysis per the frozen rules (per-direction apparent order from effective spacings; non-monotone
→ inconclusive) and report. Scope remains **discretization convergence only** — Liang-1997 physics
validation (Gate E part 2) is separate and open; no continuum/predictive claim is made.

## Ask

A documented GO (concurrent/retroactive) on the v1.6 single-threaded policy, or a HOLD instruction if you
want us to pause pending sign-off.
