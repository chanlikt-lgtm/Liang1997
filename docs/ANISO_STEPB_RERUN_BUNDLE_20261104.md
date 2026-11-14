# Step-B re-run evidence bundle — R2 + R3 remediation complete (re-pinned at the post-R3 code tip)

**Date:** 2026-11-14 (REFRESHED — re-pinned from `e73a135`) · **Pinned SHA (single reference for the reviewer):**
`de68026667772e8b71e0d9972825179d1294c9c7`
**Repo:** <https://github.com/chanlikt-lgtm/Liang1997> · **Sweep: HALTED** (no GO recorded; nothing runs).

> **This refresh supersedes the `e73a135` pin** in the prior bundle (`docs/ANISO_STEPB_RERUN_BUNDLE_20261104.md`).
> That pin predated R3 items **D+E** (`c514bcf`, which changed both `campaign/aniso_mesh_study.py` and
> `campaign/aniso_gate4_analysis.py`) and R3 item **C** (`de68026`, provenance-capture fix). The prior
> "no code change between `e73a135` and the tip" statement is therefore **withdrawn** (it is false: D/E
> changed both harness files). This bundle re-runs the no-solver evidence in a clean clone at `de68026`.

**Pinned SHA disambiguation.** `de68026` is the **post-R3 code tip**: R2 (F1-R1/F1-R2/F3-R1/F4-R1/F4-R2)
+ R3 (**C** `c514bcf`+`de68026`, **D/E** `c514bcf`). Relay/communication commits on top (e.g. `2055d8b`)
touch `communication/*.md` only and do **not** change code. Every no-solver item below was generated in a
clean independent `git clone --no-hardlinks` checked out at exactly `de68026`; each evidence log records
its own `git HEAD` (= `de68026`) in `env.txt`. The evidence dir (`campaign/logs/stepb_rerun_v3/`) and this
doc are committed at the current `main` tip.

**Amended-script SHAs (fresh capture — `campaign/logs/stepb_rerun_v3/blob_shas.txt`):**
- `git rev-parse HEAD` → `de68026667772e8b71e0d9972825179d1294c9c7`
- `campaign/aniso_mesh_study.py` → `3648f203c57222fa0c8330d25df7f82b8a19c213`
- `campaign/aniso_gate4_analysis.py` → `830b8b77649153305080eb8374c7675f28a7d583`

**R2 worklist (all fixed + reviewer-verified):** F1-R1 (recertification reads stale interp scalars),
F1-R2 (corrected observable never reached Gate-4), F3-R1 (resume loses the family tag), F4-R1 (false
stop flags passed the schema), F4-R2 (output_namespace declared but never enforced).

**R3 worklist (all landed, reviewer-verified on source 2026-11-14):**
- **C** — stale amended-script blob SHAs fixed; `blob_shas.txt` captures the current-tip blobs + history.
- **D** — `apply_derivatives()` fail-closed: `stale_Gii_interp` REQUIRED (raise if absent),
  `supersedes.npz_sha256` REQUIRED and hash-validated against the on-disk NPZ (raise on missing/mismatch).
- **E** — `_authorized_node(auth, family, Nx, Ny)` keyed on `(family,Nx,Ny)` triples; bare pairs rejected
  fail-closed; `family` plumbed through `--node` / `--resume` / `run_family` / 4th-level gate.

---

## Item 1 — clean independent checkout + independent pytest (log + env + exit code)

- Checkout: `git clone --no-hardlinks` → `git checkout --detach de68026` → `git status --porcelain`
  EMPTY (0 bytes) — archived separately in `porcelain_prerun.txt`.
- **Regression suite:** `pytest campaign/test_aniso_mesh_study.py -q` → **42 passed, exit 0**
  (`pytest_mesh_study.txt` + `pytest_mesh_study_verbose.txt`). *(D/E added 2 regressions: was 40.)*
- **Gate-4 suite:** `pytest campaign/test_aniso_gate4_analysis.py -q` → **28 passed, exit 0**
  (`pytest_gate4.txt` + `pytest_gate4_verbose.txt`). *(D/E added 4 regressions: was 24.)*
- **Combined: 42 + 28 = 70 passed** (matches the `c514bcf` "70 passed" headline).
- Env (`env.txt`): Python 3.10.12 (`/usr/bin/python3`), pytest 9.1.1, numpy 2.2.6, scipy 1.15.3,
  Linux 6.8.0-124-generic x86_64.

---

## Item 2 — LIVE negative auth tests (zero solver exec + HOLD enforcement incl. `--node`)

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

Archived as `auth_{stale,absent,badsha,threads}_{family,sweep,resume,node}.{out,err,exit}`. The badsha
scenario uses a valid F4-schema auth with `bound_sha=deadbeef…` (mismatch → F4); the threads scenario uses
a valid F4-schema auth with the correct `bound_sha=de68026` but `--threads` omitted (default 8 → G3.2).

The `--node` (S3 single-node) path is gated behind the same signed auth + single-thread + allowlist as
`--family`/`--sweep` (F1–F7 pass; regressions `test_node_path_requires_auth` +
`test_node_path_allowlist_enforced`).

---

## Item 3 — Node-2-first dry run (immutability + stop triggers) — representative command

`node2_dryrun.{out,err,exit}` (exit 0, no solver), with **`--threads 1 --family X`**:

- warm-source = preserved Node-1 npz, `warm_source_sha256=6596ae26d356cf3e52af8e1195a8fc9d6d2b125a246ad0dfa6959163e714312d`;
  **immutability verified** — the warm npz is git-tracked and opened READ-ONLY (`np.load`); `git status`
  after the dry-run shows the npz untouched.
- printed command: `python campaign/aniso_mesh_study.py --resume 100 70 --warm <npz> --family X` (with
  `threads=1`); real run requires signed F4 GO (bound_sha + threads_required=1 + node_allowlist) +
  `--threads 1`.
- immediate-stop triggers documented: R_phi≥1e-4 at 1500 cap → UNRESOLVED; phi leaves COMMON_PHI_SPAN →
  ABORT; inner-solve hang → manual kill (UNRESOLVED); auth/threads/allowlist hard-block.

---

## Deferred to the post-B second pass (NOT part of this no-solver half)

The **Node-1 audit + certification** (prior bundle's Items 2 & 4: `node1_audit.json`,
`node1_certify.json`, `node1_derivative.json`) are **deferred** — they require re-running the 40-iter
diagnostic continuation inside `stepb_certify_node1.py`, which is the **only solver invocation** in the
evidence set and waits on the maintainer's **signed B** ruling. The independent `node1_certify` +
bit-for-bit determinism re-confirmation is a **separate, clearly-labelled second pass** that fires only
after B is signed.

**F1-R1 solver-invocation caveat (carried verbatim, reviewer-flagged):**

> the F1-R1 recompute re-invokes `solve_coupled()` inside `_continuation()` — 40 warm-started iterations
> from the preserved converged phi/p (stopping disabled). This is the SAME diagnostic continuation that
> was already part of the original certification, NOT a fresh cold Node-1 production solve, and the frozen
> NPZ is untouched. The bit-for-bit determinism match is what makes it a faithful RECONSTRUCTION rather
> than a new result. But it IS a solver invocation — so it is not literally "array-only reprocessing."
> The original continuation Gii array was never persisted, so this was the only faithful way to regenerate
> it. It is defensible and within reprocess-not-rerun; final admissibility is the reviewer's call.

---

## Porcelain — pre-run (clean) vs post-run (expected output), separately archived

- **PRE-run** (`porcelain_prerun.txt`): `git status --porcelain` → **empty (0 bytes)**, captured
  immediately after `git checkout --detach de68026`, before any evidence generation.
- **POST-run** (`porcelain_postrun.txt`): `git status --porcelain` →
  `?? campaign/logs/stepb_rerun_v3/` — only the generated evidence dir; the tracked tree is untouched.

---

## Disposition

All no-solver Step-B evidence items are assembled at `de68026` and re-runnable from a clean checkout.
No production solver was invoked (dry-run + tests + live hard-block demos only). The single solver
invocation (the 40-iter diagnostic continuation) remains **deferred** to the maintainer's signed B ruling.
Sweep remains HALTED — nothing resumes without a recorded GO.

**Source documents:** `docs/ANISO_REVIEWER_PACKET_20261101.md`, `docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md`,
`docs/ANISO_READY_FOR_GO_20261029.md`, `docs/ANISO_RESUME_ORCHESTRATION.md`.
