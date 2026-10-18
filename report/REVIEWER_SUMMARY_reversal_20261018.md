# 800-iteration ensemble reverses the ~12% platform finding — reviewer summary (2026-10-18)

Following approval of the 800-iteration extension and the driver-equivalence isolation, both are complete, and the result **reverses the central ~12% platform conclusion**.

## 1. Extended ensemble (control + three 1e-16-perturbed seeds; hardened persistence = 40 consecutive gated iters + drift test)
All four exited on the R_phi outer-residual tolerance at 422–613 iterations (none reached the 800 cap). The peak-Gii bands **merged**:

| seed | Gii @ iter 400 | Gii @ R_phi convergence | n_outer |
|---|---|---|---|
| 0 (control) | 3.029e25 | 3.0678e25 | 465 |
| 1 | 3.049e25 | 3.0742e25 | 470 |
| 2 | 3.050e25 | 3.0553e25 | 422 |
| 3 | **2.738e25 (−11%)** | **3.0766e25 (+0.03%)** | 613 |

Four converged values span **0.69%** (3.055–3.077e25), all within **0.66%** of the Windows reference (3.0756e25). Hotspot [41,0] throughout. Seed 3 — the −11% "band" at iteration 400 — climbed back to +0.03% by convergence at 613 iterations.

## 2. Interpretation
The −9…−12% Windows↔Linux differences were **finite-iteration-snapshot artifacts**. The fixed-iteration trio harness stopped Linux 71×58 at ~360 iterations, mid-transient, before its slower (~470–613-iter) convergence. Run to R_phi convergence, platforms and all 1e-16 perturbations agree to **<1%**. The near-null-space ill-conditioning manifests as **slow, path-dependent convergence** (variable iteration count; transient excursions up to ~11%), not a non-reproducible converged value.

## 3. Against the prior scorecard
- "Distinct long-term attracting states / multiple stable attractors" — **not demonstrated** (bands merge; the ~11% separation was transient).
- "A reproducibly converged absolute peak Gii" — **now established to <1%** (R_phi-converged, 71×58).
- "Actual platform assembly differences cause the 12% gap" — **moot**: no persistent 12% gap at convergence.

## 4. Driver equivalence (Priority A)
Windows continuous (3.0749e25, converged R_phi@395) vs chunked with Anderson reset every 60 (3.0614e25, non-settling) differ by only **0.44%**. **Anderson reset rejected** as the cause of the ~10% driver gap; the Linux driver sensitivity is a symptom of non-convergence × stopping logic.

## 5. Caveats preserved
- "R_phi-converged" ≠ "Gii-plateau-certified": the original pointwise last-4 Gii gate never holds >35 consecutive iterations even for these converged runs — **over-strict** — so the quantity still oscillates ~1% at R_phi convergence. The <1% agreement is of the R_phi-converged peak values.
- Only **71×58** tested this way; the full three-mesh trio has **not** been re-run to per-node R_phi convergence across platforms.
- Convergence remains slow and path-dependent: a conditioning statement, not a claim of a well-posed pointwise observable.

## 6. Questions
1. Does this close the reproducibility question (peak Gii reproducible to <1% when run to convergence; prior 12% = premature-stop + over-strict-gate artifact)?
2. Is a corrected-methodology full-trio cross-platform run (each node to R_phi convergence) warranted for completeness, or is 71×58 + the mechanism sufficient?
3. Given converged values agree to <1%, is Stage-A/B coefficient replay still wanted, or is per-iteration seed localization no longer load-bearing?

Full revised report (`report_reproducibility_technical_20261016.pdf`) and harnesses (`audit/fixed_state_probe.py`, `audit/perturbation_test.py`, `audit/driver_equiv.py`) + ensemble JSONs (`audit/perturb_seed*.json`) are in this repository.
