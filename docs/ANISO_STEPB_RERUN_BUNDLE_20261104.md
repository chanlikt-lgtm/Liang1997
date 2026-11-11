# Step-B re-run evidence bundle — F1–F7 + R2 remediation complete (refreshed at fresh SHA)

**Date:** 2026-11-04 · **Pinned SHA (single reference for the reviewer):**
`e73a135b949c45076eaeb7c5236efc0fac72311c`
**Repo:** <https://github.com/chanlikt-lgtm/Liang1997> · **Sweep: HALTED** (no GO recorded; nothing runs).

> **This document supersedes `docs/ANISO_STEPB_RERUN_BUNDLE_20261102.md`** (which was pinned at
> `19a65cc`, the F1–F7 tip). The F1–F7 bundle is retained for history; every R2 blocker found since
> then (F1-R1 / F1-R2 / F3-R1 / F4-R1 / F4-R2) is now fixed and re-verified at `e73a135`.

**Pinned SHA disambiguation.** `e73a135` is the **code SHA** — the F1–F7 + R2 remediation tip
(relay/communication commits on top do not touch code). Every item below was generated in a clean
independent `git clone --no-hardlinks` checked out at exactly `e73a135`, and each evidence log records
its own `git HEAD` (= e73a135) in `env.txt`. The evidence dir (`campaign/logs/stepb_rerun_v2/`) and this
doc are committed at the current `main` tip, after `e73a135`; there is **no code change** between
`e73a135` and that tip. The reviewer clones the tip (or `e73a135`) and re-runs the same commands.

**Amended-script SHAs (for the reviewer's record):**
- `campaign/aniso_mesh_study.py` → `3648f203c57222fa0c8330d25df7f82b8a19c213`
- `campaign/aniso_gate4_analysis.py` → `830b8b77649153305080eb8374c7675f28a7d583`

> **R3 item C (2026-11-11) — stale-SHA fix.** The earlier `b4c7b412…` / `d906ee2b…` entries were the
> stale `19a65cc` blobs. The interim `e73a135` values were `0920afa4…` / `53de6dfd…`; those are now
> superseded by R3 items D+E (code tip `c514bcf`), which changed both files. The SHAs above are the
> current blobs, captured verbatim in `campaign/logs/stepb_rerun_v2/blob_shas.txt`.

**R2 worklist (all fixed + reviewer-verified):** F1-R1 (recertification reads stale interp scalars),
F1-R2 (corrected observable never reached Gate-4), F3-R1 (resume loses the family tag), F4-R1 (false
stop flags passed the schema), F4-R2 (output_namespace declared but never enforced).

**Hygiene items from the reviewer (all addressed in this pass):**
1. **Bundle link 404** — the F1–F7 package linked `blob/19a65cc/…` which 404s (bundle doc/logs were
   committed at `b5278f3`, after `19a65cc`). This bundle links only the **real evidence commit** (this
   doc + `campaign/logs/stepb_rerun_v2/`), committed at the `main` tip after `e73a135`.
2. **Porcelain overclaim** — the F1–F7 index claimed "`git status --porcelain` EMPTY" while `env.txt`
   showed the untracked output dir. Now the **PRE-run** porcelain (clean, 0 bytes, captured immediately
   after checkout — see `porcelain_prerun.txt`) is archived **separately** from the **POST-run** status
   (`porcelain_postrun.txt`, which shows only the expected untracked `campaign/logs/stepb_rerun_v2/`).
   This index no longer claims EMPTY post-run.
3. **Headline totals** — standardized to the CURRENT **40 + 24 = 64 passed** (mesh_study 40, gate4 24).
   Prior counts (34 + 19 at the F1–F7 tip; 21, 30/30, 37 + 24 as interim) are **superseded**.
4. **Representative dry-run** — the Node-2-first dry-run is re-emitted with `--threads 1 --family X`
   (the intended production command shape), replacing the earlier 8-thread / family=None log.
5. **F1-R1 solver-invocation caveat** — carried verbatim into this bundle (§ Item 4).

---

## Item 1 — clean independent checkout + independent pytest (log + env + exit code)

- Checkout: `git clone --no-hardlinks` → `git checkout --detach e73a135` → `git status --porcelain`
  EMPTY (0 bytes) — archived separately in `porcelain_prerun.txt`.
- **Regression suite:** `pytest campaign/test_aniso_mesh_study.py -q` → **40 passed, exit 0**
  (`pytest_mesh_study.txt` + `pytest_mesh_study_verbose.txt`).
- **Gate-4 suite:** `pytest campaign/test_aniso_gate4_analysis.py` → **24 passed, exit 0**
  (`pytest_gate4.txt` + `pytest_gate4_verbose.txt`).
- Env (`env.txt`): Python 3.10.12 (`/usr/bin/python3`), pytest 9.1.1, numpy 2.2.6, scipy 1.15.3,
  Linux 6.8.0-124-generic x86_64.

---

## Item 2 — raw Node-1 JSON/NPZ audit (7 gates + BLAS counts + SHA-256 ×3 + provenance diffs)

Produced by `campaign/stepb_audit_node1.py` → `node1_audit.json` (script committed at the pinned SHA;
re-runnable). Key results:

**Seven acceptance gates (production Node-1, from the on-disk JSON):**

| criterion | value | gate | unit | norm | PASS |
|---|---|---|---|---|---|
| R_phi | 8.092e-05 | 1e-4 | V | absolute | ✓ |
| continuity_residual | 3.451e-09 | 1e-6 | 1 | scaled by max(\|bs\|,1) | ✓ |
| number_balance | 2.080e-05 | 1e-2 | 1 | \|balance\|/scale | ✓ |
| drift_raw_Gii | 1.100e-04 | 5e-3 | 1 | 40-iter continuation spread | ✓ |
| drift_interp_Gii | 9.962e-05 | 5e-3 | 1 | 40-iter endpoint delta (NPZ scalar) | ✓ |
| drift_G_tot | 1.136e-04 | 5e-3 | 1 | 40-iter continuation spread | ✓ |
| hotspot_drift | 5.743e-05 | 0.5 | cell | \|cont−main hotspot\|/h_rep | ✓ |

`R_phi<1e-4` alone is NOT sufficient — the two continuity-class criteria are AND-gated.

**Actual BLAS counts (threadpool_actual):** all three single-thread nodes record `blas=1`
(`libscipy_openblas` 0.3.29 + 0.3.28, pthreads); `threads_env` = OPENBLAS/OMP/MKL = 1.

**CANONICAL bit-identity (SHA-256 of array `.tobytes()`, float.hex scalars):** Gii and phi arrays are
byte-identical across the three single-thread 71×70 runs —
`SHA256(Gii)=c6a906cd82ce2bee91a1d0b4720d5a8ec5ae5656d00f4210e6190a781170013d`,
`SHA256(phi)=be38607b69b5f32b1cb2a8a9380eac0aa2db05fc5078e5f305296ac9be624198`,
`Gii_max=0x1.973e8ea5f5dd7p+84` ×3, `n_iter=531` ×3.

**Transparent whole-file provenance diffs:** whole-file SHA differs **only** because each npz embeds its
own `git_commit`/`config_hash`/`warm_source` provenance — physics arrays identical (see JSON).

---

## Item 3 — LIVE negative auth tests (zero solver exec + HOLD enforcement incl. `--node`)

Four rejection classes, all exit 1 with **no solver execution** (stdout empty; the hard-block fires before
any `_solve`), demonstrated across **all four entry points** (`--family X`, `--sweep`, `--resume`,
`--node 71 70`) — 16 live demos:

| scenario → | stale auth (old schema) | auth absent | bound_sha mismatch | threads≠1 |
|---|---|---|---|---|
| hard-block | F4 "incomplete schema" | G0.2 | F4 bound_sha | G3.2 |
| `--family X` | exit 1 | exit 1 | exit 1 | exit 1 |
| `--sweep` | exit 1 | exit 1 | exit 1 | exit 1 |
| `--resume …` (non-dry) | exit 1 | exit 1 | exit 1 | exit 1 |
| `--node 71 70` | exit 1 | exit 1 | exit 1 | exit 1 |

Archived as `auth_{stale,absent,badsha,threads}_{family,sweep,resume,node}.{out,err,exit}`.

The `--node` (S3 single-node) path is gated behind the same signed auth + single-thread + allowlist as
`--family`/`--sweep` (fixed in the F1–F7 pass; regressions `test_node_path_requires_auth` +
`test_node_path_allowlist_enforced`).

---

## Item 4 — independent certification + F1-R1/F1-R2 derivative (with the reviewer's caveat)

Produced by `campaign/stepb_certify_node1.py` → `node1_certify.json` + `node1_derivative.json` (script
committed at the pinned SHA; re-runnable).

- **Boundary-peak (F1):** independent recompute of `interpolated_peak()` from the raw Gii array gives
  `Gii_interp=3.0780708e25` at `y=0` (surface-pinned, no bulk shift), nodal `Gii=3.077051e25` @
  `(0.589, 0.0)`, `boundary_max=true`. The old −12.58% bulk-shifted value is gone.
- **Independent certification:** all seven gates re-derived from the raw arrays → **all PASS, certified=true**;
  `R_phi<1e-4` alone is insufficient (continuity + balance are AND-gated).
- **F1-R2 derivative:** `node1_derivative.json` (schema `aniso_node_certified_derivative`, family-labelled,
  provenance-linked, `supersedes.npz_sha256` + `stale_Gii_interp` + `fix_commit=e73a135` (this run's
  HEAD; the originally-committed derivative at `data/derivatives/` records `545bd8c`)) — Gate-4 loads
  it and `apply_derivatives()` OVERWRITES the corrected peak-dependent fields, refusing a stale scalar.

**F1-R1 solver-invocation caveat (carried verbatim, reviewer-flagged):**

> the F1-R1 recompute re-invokes `solve_coupled()` inside `_continuation()` — 40 warm-started iterations
> from the preserved converged phi/p (stopping disabled). This is the SAME diagnostic continuation that
> was already part of the original certification, NOT a fresh cold Node-1 production solve, and the frozen
> NPZ is untouched. The bit-for-bit determinism match is what makes it a faithful RECONSTRUCTION rather
> than a new result. But it IS a solver invocation — so it is not literally "array-only reprocessing."
> The original continuation Gii array was never persisted, so this was the only faithful way to regenerate
> it. It is defensible and within reprocess-not-rerun; final admissibility is the reviewer's call.

**Determinism proof (bit-for-bit):** `drift_raw_Gii` recomputed 0.00010997463242625958 == NPZ,
`drift_G_tot` recomputed 0.00011359729980848199 == NPZ (both `_match: true`). Corrected
`drift_interp_Gii` = 9.9266e-5 (stale 9.9620e-5); `hotspot_drift` = 5.7428e-5 cells (unchanged — the
interp shift cancels exactly in the location difference).

**Byte-identity note (why re-running the continuation reproduces the committed result):**
`stepb_certify_node1.py`, `stepb_audit_node1.py`, `interpolated_peak()`, `_continuation()`,
`solve_coupled()`, and `CONT_N_ITER` are **byte-identical** between the F1-R1/F1-R2 commit and `e73a135`
(verified `git diff` empty); only auth plumbing changed. The frozen NPZ is byte-identical (committed).

---

## Item 5 — Node-2-first dry run (immutability + stop triggers) — representative command

`node2_dryrun.{out,err,exit}` (exit 0, no solver), now with **`--threads 1 --family X`**:

- warm-source = preserved Node-1 npz, `warm_source_sha256=6596ae26d356cf3e52af8e1195a8fc9d6d2b125a246ad0dfa6959163e714312d`;
  **immutability verified** — SHA-256 of the warm npz identical before and after the dry-run.
- printed command: `python campaign/aniso_mesh_study.py --resume 100 70 --warm <npz> --family X` (with
  `threads=1`); real run requires signed F4 GO (bound_sha + threads_required=1 + node_allowlist) +
  `--threads 1`.
- immediate-stop triggers documented: R_phi≥1e-4 at 1500 cap → UNRESOLVED; phi leaves COMMON_PHI_SPAN →
  ABORT; inner-solve hang → manual kill (UNRESOLVED); auth/threads/allowlist hard-block.

---

## Porcelain — pre-run (clean) vs post-run (expected output), separately archived

- **PRE-run** (`porcelain_prerun.txt`): `git status --porcelain` → **empty (0 bytes)**, captured
  immediately after `git checkout --detach e73a135`, before any evidence generation.
- **POST-run** (`porcelain_postrun.txt`): `git status --porcelain` →
  `?? campaign/logs/stepb_rerun_v2/` — only the generated evidence dir; the tracked tree is untouched.

---

## Disposition

All reviewer-required Step-B evidence items are assembled at `e73a135` and re-runnable from a clean
checkout. No production solver was invoked (dry-run + audit + tests + live hard-block demos only); the
single solver invocation is the documented 40-iter diagnostic continuation in Item 4 (see caveat). Sweep
remains HALTED — nothing resumes without a recorded GO.

**Source documents:** `docs/ANISO_REVIEWER_PACKET_20261101.md`, `docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md`,
`docs/ANISO_READY_FOR_GO_20261029.md`, `docs/ANISO_RESUME_ORCHESTRATION.md`.
