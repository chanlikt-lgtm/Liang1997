# ANISO Mesh Study — 71×70 Smoke v2 — RESULT

**Status:** ✅ CERTIFIED
**Run:** `campaign/aniso_mesh_study.py --node 71 70 1500`
**Provenance:** commit `cddca92` (clean tree) — fixes the `_certify` array-truth crash that killed v1.
**Launched:** 2026-10-23 13:30 MYT
**Finished:** 2026-10-23 23:53 MYT (log `/tmp/aniso_smoke_71x70_v2.log`)

## Convergence
- Final outer iter: **574** (capped at 1500; converged early)
- R_phi at stop: **9.261e-05** (< tol_phi = 1e-4) ✅
- 40-iter continuation: `cont_n_iter=40`, R_phi band `[9.261e-05, 7.051e-07]`

## Certification gate (both criteria)
| Criterion | Value | Gate | Pass |
|---|---|---|---|
| R_phi | 9.261e-05 | < 1e-4 | ✅ |
| drift (40-iter) raw_Gii | 2.823e-05 | < 0.5 % | ✅ |
| drift interp_Gii | 1.007e-05 | < 0.5 % | ✅ |
| drift G_tot | 2.216e-05 | < 0.5 % | ✅ |

## Key observables
| Observable | Value | Units |
|---|---|---|
| Gii_max (raw) | 3.0775e25 | (mesh-point max) |
| Gii_interp | 2.6904e25 | |
| G_tot | 9.1834e13 | |
| Te_max | 3184 | K |
| drain current | 2.997e-04 | A/µm |
| avalanche_y_fwhm | 2.477e-03 | |
| relative_number_balance | 2.039e-05 | |
| continuity_residual | 3.437e-09 | |

## Sweep
- Full headless sweep stays **HELD** (not launched). Awaiting Chan Lik's go.
