# Response to the independent technical audit (2026-10-22)

Thank you for the audit. The three toolkit files verify against your `SHA256SUMS.txt`. We accept the
report-integrity and provenance findings; several are already fixed in this commit, and we flag one
important scope point below.

## 1. Scope: the audit predates the reproducibility report

The audit reviewed `report/report_v6_full.tex` (the Rev6 spatial-convergence campaign) and the
production pipeline, on a `main` snapshot from **before** we pushed the cross-platform reproducibility
study. Please read the newer report that the audit did not see:

- **`report/report_reproducibility_technical_20261021.{tex,pdf}`** — the Windows↔Linux
  floating-point / convergence study.

Its central results change the interpretation of your **SCI-01**:

- The `71×58 = +2.86%` you cite is the **archival-parity** delta (3.0756 vs the *archival* 2.990×10^25).
  We have since shown the **archival 2.990 was an under-converged transient**; 3.0756×10^25 is the
  converged value, reproduced bit-exact on Windows and to `<0.01%` on Linux at outer-residual
  convergence. So that "FAIL per authors' own numbers" is **stale framing**, not a live discrepancy.
- More importantly, we now certify on the **physical observable, not the outer residual**. A
  diagnostic continuation (each converged state continued 100 iterations with stopping disabled)
  shows `G_ii`, `G_tot` and drain current flat to `<0.35%` while `R_phi` is itself ill-conditioned and
  oscillates mostly *above* `1e-4`. Cross-platform the observable agrees to `0.001%` (71×58) and
  `0.25%` (100×70), while `R_phi` can differ ~4× (Windows 100×70 parks at `2.57e-4`, Linux stopped at
  `6.97e-5`). This **confirms your methodological instinct** (a single `R_phi` crossing is not
  certification) and strengthens the reproducibility conclusion.

Your `SCI-01` **BLOCKER on spatial/continuum convergence still stands** — we make no continuum claim,
and the non-monotone trio is retained as a negative finding. `SCI-02` (reduced/calibrated model) and
`SCI-03` (figure provenance) are likewise accepted and already stated in both reports.

## 2. Fixed in this commit (verified pipeline/provenance findings)

| ID | Fix |
|---|---|
| **RUN-01** | `gen_run_report.py`: `pdflatex` now runs without `--enable-installer` (portable), checks the return code, and verifies the PDF was freshly produced (mtime advanced + size) before announcing success; a failed/stale compile exits nonzero instead of claiming a fresh PDF. |
| **RUN-02** | `archive_run.py`: now archives `she2d_richardson_*.progress.json` sidecars (the certified acceptance buffer) **and** the report `.tex` source, records python/numpy/scipy versions and the full (not short) commit + dirty flag, and writes a **SHA-256 for every payload** in `MANIFEST.txt`; warns if no sidecar was captured. |
| **RUN-03** | `trio_launch.sh`: `set -euo pipefail`; the automatic `git add/commit/push` is now **off by default** and gated behind an explicit `TRIO_AUTOPUSH=1` deliberate choice, so the scientific runner no longer mutates the repository silently. |
| **RUN-04** | `reproduce_all.py`: `--keep-going` now exits **nonzero** if any stage failed. |
| **RUN-05** | `reproduce_all.py`: a missing recalibration NPZ in `_copy_conv_to_canonical()` is now **fatal**, so overlays cannot silently consume a stale canonical NPZ. |
| **NUM-01** (primary consumer) | `gen_run_report.py`: the reversal half-range `u` feeding `S_rev` is now derived from the **certified cumulative window** (`sp = (max-min)/mean` scaled to an absolute half-range), not the chunk-local `last4_*`. A degenerate 1-iteration terminal chunk can no longer fake a finite/zero `u`. |
| **NUM-02** (report gate) | `gen_run_report.py`: a node that **omits** `H_hash` now **fails** the comparability gate (sentinel in the hash set) rather than being silently skipped. |

## 3. Accepted and queued (larger refactors, not in this commit)

- **NUM-01 full centralization:** a single `read_certified_window(npz, progress)` API consumed by
  `richardson_fit.py` **and** `run_richardson_trio.py` as well (currently only `gen_run_report.py` is
  rewired). Plus your short-terminal-chunk unit test.
- **NUM-02 signed manifest:** per-node exact-schema manifest (full commit + dirty refusal, physics
  constants, doping/geometry SHA, versions, warm-source SHA, `H` bytes SHA) enforced against the
  frozen run definition, with the missing-key / changed-param / changed-source tests.
- **RUN-03 (`run_linux_full.sh`):** hard-fail when the Stage-1 sentinel is absent.
- **Science (your §G 7–8):** orthogonal drain-x / depth-y mesh families and the missing-physics /
  holdout validation are on our roadmap as separate studies; we agree they are prerequisites for any
  continuum or predictive-validity claim, and we are not making those claims.

## 4. Your read-only checkpoint validator

`Liang1997_Readonly_Checkpoints.py` is a good addition. You could not run it against the real NPZs
(clone/network blocked in your environment); we can run it here against the actual archived data and
return its JSON, which would close your `TEST-01` / `CP7` (archive replay) on real artifacts rather
than synthetic ones. Say the word and we will attach the output.

— Repository maintainers
