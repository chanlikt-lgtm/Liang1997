# Closeout fixes — response to the independent offline verification (CLOS-01 … CLOS-04)

The reviewer independently replayed the bundle (integrity PASS, Gates A/C/D verified) and found four
items. All four are addressed here. Fault-injection re-runs all PASS at the fix commit.

## CLOS-01 (HIGH) — partial trio could archive as "certified" — FIXED

**Finding:** `archive_run.py` only checked for *zero* sidecars (`if not archived_sidecars`), so an
archive with 3 NPZ but only 1 of 3 progress sidecars still exited 0 as certified.

**Fix:** certification now requires **one-to-one node coverage** — every archived node NPZ must have
its matching `progress.json`, and all three required trio nodes (71×58, 100×70, 141×85) must be
present. Any gap exits **4** (fail-closed) unless `--exploratory` (then labelled `_UNCERTIFIED`).

**Proof:** new negative test `CLOS-01 partial trio (3 NPZ / 1 sidecar) -> exit 4` in
`report/closure/gate_b_fault_injection.py`; result PASS in `gate_b_results.json`.

## CLOS-02 (MEDIUM) — RUN-01 harness false positive — FIXED

**Finding:** the harness invoked `gen_run_report.py` with `python -I`; isolated mode dropped the
script dir from `sys.path`, so `import plateau_gate` crashed *before* pdflatex, and the harness scored
any nonzero exit as PASS.

**Fix:** the RUN-01 test now runs **without `-I`** (so `plateau_gate` imports), asserts the **RUN-01
error marker is present** (proving the pdflatex branch was actually reached) and that there is **no
import crash** and **no false "compiled"**, and covers **both** the failing-compile and the
success-without-PDF cases. On a box where a real `pdflatex` shadows the stub (e.g. MiKTeX on Windows),
it reports **SKIPPED** (not a false PASS). Verified here: both cases exit **2** with the RUN-01 marker,
branch reached, no import crash — matching the reviewer's own `run01_extended_results.json`.

## CLOS-03 (LOW) — 71×58 mean cross-platform figure — CORRECTED

The 71×58 **100-iteration mean** cross-platform `⟨G_ii⟩` agreement is **≈0.0096 %** (not 0.001 %),
normalized by the mean of the two platform means — exactly the reviewer's recomputation. Corrected in
`report/report_reproducibility_technical_20261021.{tex,pdf}` (§4 and the reviewer section) and in
`AUDIT_CLOSURE_GATES_BCD_20261022.md`. It is a **mean** agreement, labelled as such (not endpoint).
The `100×70` figure (0.25 %) and the broader `<0.5 %` two-mesh conclusion are unchanged.

## CLOS-04 (QUALIFICATION) — historical solver bytes, not just hashes — PROVIDED

`report/closure/historical_src/{1893b9c,4e2374e}/*.py` ships the **actual source bytes** of the five
core solver files at both commits, and `historical_src/AUTHENTICATION.txt` lists each file's **git
blob OID**, the **tree OID** and **commit OID**. The reviewer can `git hash-object <file>` and match
the blob OID recorded in each commit's tree — binding the bytes to the commits without the 140 MB full
git bundle. The result is definitive: the five solver blob OIDs are **byte-identical** between
`1893b9c` and `4e2374e` (e.g. `coupled_she.py = 60c0cff9…` at both), so the 141×85 earlier-run node is
provably solver-equivalent, now by object identity rather than a quoted hash list.

## Scope unchanged

Engineering fail-closed behavior is now complete on the five fault paths + the partial-trio case.
Still open and explicitly not claimed: robust finest-grid (141×85 inner-solve) run; full NUM-01
shared-consumer API; signed exact-schema per-node manifest; `run_linux_full.sh` sentinel; clean-tree
frozen-tag replay; and all of Gate E (spatial/continuum convergence and physics validation vs
Liang 1997).
