# Audit closure — Gates B, C, D (evidence package)

Follows `AUDIT_CLOSURE_GATE_A_20261022.md`. All artifacts referenced here are committed under
`report/closure/`. Fix commit: `b8e7b3650515e6ffe1b30860969c8987a787cfde`.

## Gate B — fault-injection negative tests (all PASS)

Harness `report/closure/gate_b_fault_injection.py` drives the **actual fixed source** (no
reimplementation) with injected faults, run against the fix commit. Results in
`report/closure/gate_b_results.json`:

| Test | Expected | Observed | Result |
|---|---|---|---|
| RUN-01 real `gen_run_report.py` with stubbed failing `pdflatex` | nonzero exit, no "compiled" | exit 1, no false success | **PASS** |
| RUN-02 certified archive, no `progress.json` sidecar | exit 4 (fail-closed) | exit 4 | **PASS** |
| RUN-02 `--exploratory` | exit 0 + `_UNCERTIFIED` label | exit 0 + labelled | **PASS** |
| RUN-04 `reproduce_all --keep-going` with a failed stage | nonzero exit | exit 1 | **PASS** |
| RUN-05 `_copy_conv_to_canonical()` with recal NPZ missing | `RuntimeError` | raised | **PASS** |
| NUM-02 `hash_ok` — all present equal / one missing / **all missing** / mismatch | T / F / F / F | T / F / F / F | **PASS** |

The **all-missing** NUM-02 case (your point 2) is explicitly covered: three sentinel values collapse
to a cardinality-one set, but the sentinel-presence check fails `hash_ok`, so an all-missing trio does
**not** pass. Rerun: `python report/closure/gate_b_fault_injection.py --repo . --json out.json`.

RUN-01 note: the stub relies on PATH precedence over a real `pdflatex`; it ran end-to-end here on the
real `data/` trio. On a box where a real `pdflatex` precedes the stub, run the test under TeX Live.

## Gate C — read-only checkpoint replay on REAL archived data

Your `Liang1997_Readonly_Checkpoints.py` was run (unmodified, isolated `python -I`) against the real
archived Rev6 trio. Output: `report/closure/gate_c_readonly_checkpoints.json`. Summary:

- **Overall: INTERNAL CHECKS PASS — PAPER VALIDATION NOT CLAIMED.**
- Three nodes load with genuine 4-consecutive-iteration certified windows:
  `71x58` Gii `3.075619e25` [356–359]; `100x70` Gii `2.087561e25` [297–300]; `141x85` Gii
  `2.399434e25` [117–120]. Each sidecar's last sample matches its NPZ scalar; `passed=True`,
  `cum_iters == last abs_iter`; plateau spread ≤ 3e-4 and last `R_phi` ≤ 1.5e-3; all three `H_hash`
  equal; drain-refinement ratios ≈ √2.
- **Honest FAILs (expected):** source tree **dirty** (this is a working checkout, not a frozen tag —
  disclosed); archival **±2% parity YELLOW** (`71x58 +2.86%`, `100x70 −2.22%`, `141x85 −0.56%`); the
  optional `Phi_gate`/`eps_max` fields absent (to be frozen via the signed manifest).
- **Scientific status: NOT SPATIALLY CONVERGED** (non-monotone), as you require.

**Dataset identity (disclosure):** this `data/` trio is the Oct-15 Windows-clean Rev6 campaign set,
whose `100x70 = 2.0876e25` is the **premature-gate-trip snapshot** (NUM-01's motivating case), not the
`R_phi`-converged `2.1362e25` in the reproducibility report. Both are legitimate and distinct: the
former is the archived Rev6 plateau certificate; the latter is the outer-residual-converged value.
A fully frozen-tag, clean-tree replay is the remaining step for an independent CP7 at a pinned commit.

## Gate D — 100-iteration observable histories (separated from the 4-sample spread)

`report/closure/gate_d_diag_continuation_{71x58,100x70}.csv` give the per-iteration `R_phi` and
`G_ii` for both Windows and Linux over the 100-iteration diagnostic continuation (stopping disabled).
These are the **100-iteration drift** axis, reported **separately** from the 4-sample `3e-4`
(`= 0.03%`) plateau spread, per your point 5. Observed: `G_ii` drift `0.185%`/`0.31%` (71×58/100×70),
`R_phi` oscillating mostly above `1e-4` (82–100 of 100 iters); cross-platform `⟨G_ii⟩` agrees to
`0.0096%`/`0.25%`. Metric definitions, platform/build, and starting checkpoints are in
`report/report_reproducibility_technical_20261021.tex` (§4). The two convergence axes are **not**
interchangeable, and we do not treat one as proof of the other.

## Status against the five closure gates

| Gate | Status |
|---|---|
| **A** source identity | **DELIVERED** — fix SHA `b8e7b36`, pinned raw links, full diff |
| **B** fault-injection | **DELIVERED** — harness + JSON, all PASS at the fix commit |
| **C** archival replay | **DELIVERED on real data** (working checkout); clean-tree frozen-tag replay = remaining |
| **D** new-report numerics | **DELIVERED** — 100-iter CSVs + `report_reproducibility_technical_20261021` |
| **E** scientific follow-through | **OPEN / acknowledged** — orthogonal mesh families, physics holdout (separate studies) |

SCI-01 remains a BLOCKER (no continuum `G_ii`); SCI-02/03 open and accepted. No continuum or
full-paper-reproduction claim is made.
