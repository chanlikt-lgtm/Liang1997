# Liang-1997 SHE–BTE reproduction — status for the independent reviewer

**Date:** 2026-10-22  
**Repository:** <https://github.com/chanlikt-lgtm/Liang1997>  
**Current `main` / closure commit:** `1778820c4b55434a0ebabf110c465d2209866ff6`  
**Fix commit (pipeline remediation):** `b8e7b3650515e6ffe1b30860969c8987a787cfde` (audited base `0741874b…`)

This single page consolidates the current state across the two review threads (the cross-platform
reproducibility study and the pipeline/provenance audit) so everything can be verified from one place.

---

## 1. Executive status

- **Reproducibility reversal: established.** Run to outer-residual convergence, the peak impact-
  ionization rate `G_ii` is reproducible **<1 % across Windows/Linux on all three meshes under the
  same solver**, and the central *physical observable* agrees to **<0.5 %**. The earlier ~10–12 %
  "platform gap" was a **premature-stop artifact**, not a non-portable result.
- **Pipeline/provenance audit: remediated and independently testable.** All seven engineering findings
  are fixed at a pinned commit, the auditor's own validator passes on real data, and every fault-
  injection test is green.
- **Spatial / physical science: openly unresolved.** The three-mesh sequence is non-monotone, so **no
  continuum `G_ii` is claimed**, and the model is a reduced/calibrated reconstruction, not a blind
  reproduction of Liang 1997. These remain blockers by design.

---

## 2. Scientific status

### 2.1 Cross-platform convergence (full report: `report/report_reproducibility_technical_20261021.pdf`)

Run continuously to `tol_phi = 1e-4` (cap = safety only), same solver both platforms:

| mesh | n_iter | R_phi | G_ii (cm⁻³s⁻¹) | vs Windows ref | provenance |
|---|---|---|---|---|---|
| 71×58  | 325 | 7.10e-5 | 3.075752e25 | **+0.006 %** | current run (`4e2374e`) |
| 100×70 | 929 | 6.97e-5 | 2.144818e25 | **+0.40 %**  | current run (`4e2374e`) |
| 141×85 | 717 | 7.30e-5 | 2.406344e25 | **+0.79 %**  | earlier run (`1893b9c`), same solver |

Provenance note (disclosed): the 141×85 certified node is from an **earlier run instance** (only a
monitoring script differs → solver-equivalent); the **current run's** 141×85 **hung** at outer 281
(inner Krylov/ILU stagnation) and is classified **UNRESOLVED** for that run. So this is *not* a clean
single-run trio — it is "all three certify <1 % under the same solver; the finest mesh is fragile."

### 2.2 The reproducible quantity is the observable, not the residual

Diagnostic continuation (each converged state continued 100 iterations, stopping disabled), symmetric
Windows↔Linux (data: `report/closure/gate_d_diag_continuation_*.csv`):

| mesh | OS | R_phi recompute | R_phi med (iters >1e-4) | G_ii drift |
|---|---|---|---|---|
| 71×58  | Win   | 3.94e-5 | 1.8e-4 (90/100)  | 0.185 % |
| 71×58  | Linux | 7.10e-5 | 1.6e-4 (82/100)  | 0.181 % |
| 100×70 | Win   | 2.57e-4 | 4.5e-4 (100/100) | 0.31 %  |
| 100×70 | Linux | 6.97e-5 | 3.8e-4 (99/100)  | 0.21 %  |

`R_phi` oscillates mostly **above** `1e-4` while `G_ii`/`G_tot`/drain-current stay flat to <0.35 %.
Decisive datum: on 100×70, Windows parks at `R_phi = 2.57e-4` and Linux stopped at `6.97e-5` — a ~4×
residual difference against a 0.25 % observable. **Certify on sustained observable flatness, not a
single `R_phi` crossing.** (The 100-iteration drift axis is reported separately from the 4-sample
`3e-4` plateau spread; the two are not interchangeable.)

### 2.3 Standing science blockers (accepted)

- **SCI-01:** non-monotone trio `3.0756 → 2.1362 → 2.3874 (×10²⁵)` → no Richardson, no continuum `G_ii`.
- **SCI-02 / SCI-03:** reduced/calibrated physics (one-parameter Kane, lumped `tau1`, Keldysh
  surrogate, calibrated `Vth`) and mixed figure provenance → calibrated demonstration, not predictive
  validation.

---

## 3. Audit closure status (pipeline / provenance)

| Gate | Evidence (in `report/closure/`) | Status |
|---|---|---|
| **A — source identity** | fix SHA `b8e7b36`, pinned raw links, `gate_a_fix_diff_vs_audited.patch` | **DELIVERED** |
| **B — fault-injection** | `gate_b_fault_injection.py`, `gate_b_results.json` | **ALL PASS** at fix commit |
| **C — archival replay** | `gate_c_readonly_checkpoints.json` (your validator, real data) | **INTERNAL CHECKS PASS** |
| **D — new-report numerics** | `gate_d_diag_continuation_*.csv` + `report_reproducibility_technical_20261021` | **DELIVERED** |
| **E — scientific follow-through** | orthogonal mesh families, physics holdout | **OPEN / acknowledged** |

### Seven findings — disposition

| ID | Status |
|---|---|
| RUN-01 PDF build not checked | **Fixed** — exit-code + freshness check; fails nonzero; `--enable-installer` dropped (portable). Fault-test PASS. |
| RUN-02 archive omits sidecars / no hashes | **Fixed + hardened** — archives `*.progress.json` + `.tex`, SHA-256 per payload, env/commit; missing sidecar now **fail-closed (exit 4)** unless `--exploratory` (→ `_UNCERTIFIED`). Fault-test PASS. |
| RUN-03 unsafe shell / auto-push | **Fixed** — `set -euo pipefail`; auto `git push` off by default, gated by `TRIO_AUTOPUSH=1`. (`run_linux_full.sh` sentinel = queued.) |
| RUN-04 `--keep-going` exits 0 on failure | **Fixed** — exits nonzero if any stage failed. Fault-test PASS. |
| RUN-05 stale-NPZ reuse | **Fixed** — missing recalibration NPZ is fatal. Fault-test PASS. |
| NUM-01 chunk-local `last4` uncertainty | **Fixed in the report generator** (`S_rev` now from the certified cumulative window). `richardson_fit.py` + `run_richardson_trio.py` via a shared API = queued. |
| NUM-02 provenance gate skips missing `H_hash` | **Fixed** — missing `H_hash` fails the gate (incl. all-missing). Signed per-node manifest = queued. |

---

## 4. Open / queued (not blocking the engineering closure)

- Shared `read_certified_window()` consumed by `richardson_fit.py` and `run_richardson_trio.py`.
- Signed per-node manifest (source-tree hash + dirty refusal, physics/doping/geometry digests,
  H-array bytes SHA, warm-source SHA, versions) enforced vs the frozen run definition.
- `run_linux_full.sh` hard-fail on a missing Stage-1 sentinel.
- Clean-tree, frozen-tag CP7 replay (the delivered Gate C ran on a working checkout, disclosed).
- **Science (separate studies):** orthogonal drain-x / depth-y mesh families + energy-grid
  sensitivity; independent doping/scattering/II physics and a holdout observable.

---

## 5. How to verify independently (no 40-h rerun)

```
# pinned, immutable — bypasses the raw CDN branch cache
SHA=1778820c4b55434a0ebabf110c465d2209866ff6
# fixed sources
curl -s https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/$SHA/src/gen_run_report.py
curl -s https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/$SHA/src/archive_run.py
curl -s https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/$SHA/trio_launch.sh
curl -s https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/$SHA/reproduce_all.py
# evidence
#   report/AUDIT_CLOSURE_GATE_A_20261022.md
#   report/AUDIT_CLOSURE_GATES_BCD_20261022.md
#   report/closure/{gate_a_fix_diff_vs_audited.patch, gate_b_*, gate_c_*, gate_d_*}
# rerun the fault-injection suite at the pinned commit:
python report/closure/gate_b_fault_injection.py --repo . --json gate_b.json
```

**Bottom line:** reproducibility reversal established and independently testable; pipeline/provenance
findings remediated and verified; continuum and full-paper-physics claims are explicitly **not** made
and remain the open scientific work.
