# Step-B verification report — anisotropic mesh study (reviewer audit evidence)

**Date:** 2026-10-29 · **Pinned SHA (all decisions):** `11ac0fa92cd21370b01a3068859e66fe201f30dc`
**Scope:** tests + audit of EXISTING artifacts + live auth-block demo. **No production solver run.**
**Status:** HOLD maintained. This report is evidence for the reviewer's Step-B re-verification — it is
**not** the GO, **not** node-1 admissibility, and **not** Gate-4 concurrence. Those remain the
reviewer's three decisions.

All code was executed in a git worktree checked out at exactly `11ac0fa` (HEAD verified). The mesh-study
harness, its test suite, and `src/` are byte-identical between `11ac0fa` and the current `main` tip
(`git diff 11ac0fa..main` on those paths is empty), so nothing below is affected by the later
Gate-4-analysis harness addition.

---

## 1. Regression suite (actual archived run)

**Command:** `python3 -m pytest campaign/test_aniso_mesh_study.py -q` at `11ac0fa`
**Result:** `21 passed` · **exit code 0**
**Archived:** `campaign/logs/stepb_20261029/pytest_mesh_study.txt` (quiet) +
`pytest_mesh_study_verbose.txt` (per-test PASS lines).

Environment used: Python 3.10.12 (`/usr/bin/python3`), pytest 9.1.1, numpy 2.2.6, scipy 1.15.3
(see `campaign/logs/stepb_20261029/env.txt`). The solver venv (Python 3.13.12, numpy 2.2.6, scipy
1.15.3) is not required for these mock-based tests; the test suite exercises harness logic, not the
frozen solver.

## 2. Threading enforcement (per node)

The harness pins `OPENBLAS_NUM_THREADS = OMP_NUM_THREADS = MKL_NUM_THREADS = 1` at import, and every
single-thread node artifact records its *actual* BLAS threads. All three canonical 71×70 nodes:

| artifact | threads_req | threadpool_actual | threads_env |
|---|---|---|---|
| `…_t1_47e3c9ec574b` (t1 control) | 1 | `blas=1` | all three `=1` |
| `…_t1_552bb609f0f2_X` (production node-1) | 1 | `blas=1` | all three `=1` |
| `…_t1_1e010e13e26f_repeat` (repeat) | 1 | `blas=1` | all three `=1` |

The 8-thread t8 control (`threads_req=8`) is a threading-diagnostic artifact and is **excluded** from
single-thread convergence analysis (see `campaign/aniso_gate4_analysis.py` loader).

## 3. Seven acceptance gates — canonical node-1 (71×70), raw values

From `data/she2d_aniso_71x70_t1_552bb609f0f2_X.json` (git `2775697`, config_hash `552bb609f0f2`,
H_hash `b4319bb03303`). **All seven PASS.**

| criterion | value | unit | gate | norm | PASS |
|---|---|---|---|---|---|
| R_phi | 8.09234e-05 | V | 1e-4 | absolute | ✓ |
| continuity_residual | 3.45138e-09 | 1 | 1e-6 | scaled by max(\|bs\|,1) | ✓ |
| number_balance | 2.0798e-05 | 1 | 1e-2 | \|balance\|/scale | ✓ |
| drift_raw_Gii | 1.09975e-4 | 1 | 5e-3 | 40-iter continuation spread | ✓ |
| drift_interp_Gii | 9.962e-05 | 1 | 5e-3 | 40-iter endpoint delta | ✓ |
| drift_G_tot | 1.13597e-4 | 1 | 5e-3 | 40-iter continuation spread | ✓ |
| hotspot_drift | 5.74279e-05 | cell | 0.5 | \|cont−main hotspot\|/h_rep | ✓ |

`R_phi < 1e-4` alone is NOT sufficient: `continuity_residual < 1e-6` and `|number_balance| < 1e-2` are
two of the seven AND-gated acceptance criteria (S1), enforced by `test_certify_not_rphi_alone`.

## 4. Authorization hard-block (live demo, starts no solver)

With `campaign/aniso_exec_auth.json` temporarily removed, both full-sweep entry points reject before any
solver work:

- `python3 campaign/aniso_mesh_study.py --family X` → **exit 1**,
  stderr `G0.2 HARD-BLOCK: full-sweep execution is NOT authorized …`
- `python3 campaign/aniso_mesh_study.py --sweep` → **exit 1**, same message.

Archived: `auth_block_family.{out,err}`, `auth_block_sweep.err`, `auth_block_exit_codes.txt`.
The valid auth path is covered by `test_exec_auth_recorded` and (with a mocked solver) by
`test_run_sweep_sequential_failure_isolation` — the rejection is demonstrated live, the accept path is
demonstrated at the unit level (no solver).

## 5. Manifest lifecycle + failure isolation

Covered by the archived suite: `test_node_state_vocabulary`, `test_gate4_excludes_uncertified`, and
`test_run_sweep_sequential_failure_isolation` all PASS. The last proves the shared (100,70) anchor runs
independently per family, and that a failing X-family does not mark the Y-family complete (X→FAILED,
Y→COMPLETE), with the manifest emitting `queued/running/certified/failed/UNRESOLVED`.

## 6. Reproducibility — CANONICAL bit-identity (float.hex + SHA-256 of array bytes)

Three single-thread 71×70 npz compared as float64 (not decimal repr):

| observable | t1 (52c981f) | production (2775697) | repeat (52ed83a) | identical |
|---|---|---|---|---|
| Gii_max `float.hex()` | `0x1.973e8ea5f5dd7p+84` | `0x1.973e8ea5f5dd7p+84` | `0x1.973e8ea5f5dd7p+84` | ✓ |
| Gii_interp `float.hex()` | `0x1.6406aa937cb07p+84` | `0x1.6406aa937cb07p+84` | `0x1.6406aa937cb07p+84` | ✓ |
| G_tot `float.hex()` | `0x1.4e0a7f18eb8d2p+46` | `0x1.4e0a7f18eb8d2p+46` | `0x1.4e0a7f18eb8d2p+46` | ✓ |
| R_phi `float.hex()` | `0x1.536ad10b10000p-14` | `0x1.536ad10b10000p-14` | `0x1.536ad10b10000p-14` | ✓ |
| n_iter | 531 | 531 | 531 | ✓ |
| SHA256(Gii[70×71] .tobytes()) | `c6a906cd…0013d` | `c6a906cd…0013d` | `c6a906cd…0013d` | ✓ |
| SHA256(phi[70×71] .tobytes()) | `be38607b…4198` | `be38607b…4198` | `be38607b…4198` | ✓ |

Full hashes in `campaign/logs/stepb_20261029/bit_identity.txt`.

**Note (file-level hash):** the whole-file SHA-256 differs across the three npz
(`c8a2b56c…`, `6596ae26…`, `6cf32be4…`) **because each npz embeds its provenance metadata**
(`git_commit` = 52c981f / 2775697 / 52ed83a and `warm_source`). The **physics arrays are byte-identical**;
the scalar observables are bit-identical at `float.hex()` precision. This is the canonical demonstration
the reviewer requested: identity holds at the array-byte level, not merely in displayed digits.

---

## Disposition

Step-B evidence assembled at `11ac0fa`, nothing re-run in production, no acceptance rule changed. Ready
for reviewer audit → then their three decisions (prospective GO / node-1 admissibility / Gate-4
concurrence). Sweep remains HALTED.

Archived logs: `campaign/logs/stepb_20261029/` — `env.txt`, `pytest_mesh_study.txt`,
`pytest_mesh_study_verbose.txt`, `auth_block_family.{out,err}`, `auth_block_sweep.err`,
`auth_block_exit_codes.txt`, `gates_and_threading.txt`, `bit_identity.txt`.
