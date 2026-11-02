# Step-B re-run evidence bundle (F1–F7 remediation complete)

**Date:** 2026-11-02 · **Pinned SHA (all evidence below):**
`0f917669298acf1c6cd08147636b1d81e5b843aa`
**Repo:** <https://github.com/chanlikt-lgtm/Liang1997> · **Sweep: HALTED** (no GO recorded; nothing runs).

This is the re-run evidence bundle the reviewer requires for Step-B sign-off after the F1–F7
remediation. Every item below was produced in a **clean, independent `git clone --no-hardlinks`** checked
out at exactly the pinned SHA (`git status --porcelain` EMPTY), so it is provably independent of the
working tree that produced the F1–F7 fixes. All evidence lives under `campaign/logs/stepb_rerun/`.

**F1–F7 status (all addressed):** F1 (boundary-aware peak interp + Node-1 reprocess), F2 (Gate-4 loader
keyed by (family,Nx,Ny)), F3 (checkpoint resume + dry-run), F4 (signed/bound exec-auth + allowlist +
stop conditions + **`--node` also gated**), F5 (single-thread fail-closed), F6 (anchor glob by family
field + regression), F7 (advisory, no change). See the F4/S3-HOLD item below for one gap found during
bundle assembly.

---

## Item 1 — clean independent checkout + independent pytest (log + env + exit code)

- Checkout: `git clone --no-hardlinks` → `git checkout --detach 0f91766` → `git status --porcelain`
  EMPTY (recorded in `env.txt`).
- **Regression suite:** `pytest campaign/test_aniso_mesh_study.py -q` → **34 passed, exit 0**
  (`pytest_mesh_study.txt` + `pytest_mesh_study_verbose.txt`).
- **Gate-4 suite:** `pytest campaign/test_aniso_gate4_analysis.py` → **19 passed, exit 0**
  (`pytest_gate4_verbose.txt`).
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
| drift_interp_Gii | 9.962e-05 | 5e-3 | 1 | 40-iter endpoint delta | ✓ |
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

**Transparent whole-file provenance diffs:** whole-file SHA differs (`c8a2b56c…` / `6596ae26…` /
`6cf32be4…`) **only** because each npz embeds its own `git_commit`/`config_hash` (`52c981f`/`2775697`/
`52ed83a`; `47e3c9ec574b`/`552bb609f0f2`/`1e010e13e26f`) and `warm_source` — physics arrays identical.

---

## Item 3 — LIVE negative auth tests (zero solver exec + HOLD enforcement incl. `--node`)

Two cases, both exit 1 with **no solver execution** (stdout empty; the hard-block fires before any
`_solve`):

| entry point | stale auth (old schema) | auth removed |
|---|---|---|
| `--family X` | exit 1 (F4 "incomplete") | exit 1 (G0.2 "NOT authorized") |
| `--sweep` | exit 1 (F4 "incomplete") | exit 1 (G0.2 "NOT authorized") |
| `--resume 100 70 --warm …` (non-dry) | — | exit 1 (G0.2) |
| `--node 71 70` | exit 1 (F4 "incomplete") | exit 1 (G0.2) |

Archived: `auth_{family,sweep,node}_stale.{out,err,exit}`, `auth_absent_{family,sweep,resume,node}.{out,err,exit}`.

### F4/S3-HOLD gap fixed during assembly (important)

The original F4 remediation gated `--family`/`--sweep`/`--resume` but **`--node` (the S3 single-node
path) still bypassed auth and would have launched a real solver under HOLD** (the reviewer flagged this
as "`--node` bypasses it (S3) though the explicit HOLD supersedes S3"; the S3↔HOLD doc states "under
HOLD, nothing runs — no `--node`"). Fixed in this bundle: `--node` now goes through `_node_path()`, which
applies `_require_exec_auth()` + `_require_single_thread()` + the allowlist — identical to
`--family`/`--sweep`. New regressions: `test_node_path_requires_auth`, `test_node_path_allowlist_enforced`.
The negative-auth table above now includes `--node` proving the HOLD is enforced on every entry point.

---

## Item 4 — regressions (boundary-peak + independent certification + dual-anchor + anchor glob)

Produced by `campaign/stepb_certify_node1.py` → `node1_certify.json` (script committed at pinned SHA).

- **Boundary-peak (F1):** independent recompute of `interpolated_peak()` from the raw Gii array gives
  `Gii_interp=3.078071e25` at `y=0` (surface-pinned, no bulk shift), nodal `Gii=3.077051e25` @
  `(0.589, 0.0)`, `boundary_max=true`. The old −12.58% bulk-shifted value is gone (see
  `campaign/logs/f1_reprocess_71x70_552bb609f0f2.json`).
- **Independent certification:** all seven gates re-derived from the raw arrays → **all PASS, certified=true**;
  `R_phi<1e-4` alone is insufficient (continuity + balance are AND-gated).
- **Dual-anchor (F2):** `test_load_certified_separates_xy_anchor` PASS (X and Y (100,70) anchors keyed by
  family, each reads its own).
- **Anchor glob (F6):** `test_compare_anchor_glob_selects_by_family` + `test_compare_anchor_missing_family_is_unavailable`
  PASS (family selected by JSON `family` field, with/without `--run-id`; missing family → available=false).
  *Note:* this regression was missing from the original F6 fix (code changed, test never added) — added
  here and now covered.

---

## Item 5 — Node-2-first dry run (immutability + stop triggers)

`node2_dryrun.{out,err,exit}` (exit 0, no solver):

- warm-source = preserved Node-1 npz, `warm_source_sha256=6596ae26d356cf3e52af8e1195a8fc9d6d2b125a246ad0dfa6959163e714312d`;
  **immutability verified** — SHA-256 of the warm npz identical before and after the dry-run.
- real run requires signed F4 GO (bound_sha + threads_required=1 + node_allowlist) + `--threads 1`.
- immediate-stop triggers documented: R_phi≥1e-4 at 1500 cap → UNRESOLVED; phi leaves COMMON_PHI_SPAN →
  ABORT; inner-solve hang → manual kill (UNRESOLVED); auth/threads/allowlist hard-block.

---

## Disposition

All five reviewer-required Step-B evidence items are assembled at `0f91766` and re-runnable from a clean
checkout. No solver was invoked (dry-run + audit + tests + live hard-block demos only). Sweep remains
HALTED — nothing resumes without a recorded GO.

**Source documents:** `docs/ANISO_REVIEWER_PACKET_20261101.md`, `docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md`,
`docs/ANISO_RESUME_ORCHESTRATION.md`, `docs/ANISO_READY_FOR_GO_20261029.md`.
