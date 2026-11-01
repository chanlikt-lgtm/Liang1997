# Aniso sweep — checkpoint-only resume orchestration (F3)

**Purpose.** Provide a single-node, warm-started resume path so Node-2 (100×70) can be resumed from the
preserved Node-1 (71×70) NPZ without re-running the chain — bound explicitly to the warm-source NPZ, with
its SHA-256 recorded, and with Node-1 outputs provably immutable.

## Exact commands

Dry-run (no solver — works under HOLD, demonstrates the orchestration):
```
python campaign/aniso_mesh_study.py --resume 100 70 \
  --warm data/she2d_aniso_71x70_t1_552bb609f0f2_X.npz --dry-run
```
Real resume (requires a signed F4 GO + single thread):
```
python campaign/aniso_mesh_study.py --resume 100 70 \
  --warm data/she2d_aniso_71x70_t1_552bb609f0f2_X.npz --threads 1
```

`--resume Nx Ny --warm <npz> [--dry-run] [--run-id REP] [--threads N]`:
- `--warm` = the preserved prior-node NPZ (resolved to an absolute path; **G1.1 hard-fail if missing**,
  no silent cold-start fallback).
- `--dry-run` = validate + print the plan, record the warm-source SHA, do **not** invoke the solver.
- `--threads 1` is required for the real run (F5 fail-closed; default is 8 when omitted).

## Warm-source binding + immutability

- The warm-source NPZ is opened **read-only** (`np.load`); the resume writes a **new** artifact
  (`she2d_aniso_100x70_t1_<cfg>_<family>_<run-id>`), never touching Node-1.
- The warm-source SHA-256 is recorded in the node record (`warm_source_sha`) and in the NPZ
  (`warm_source_sha`), so the resume is verifiably tied to the exact preserved state.
- Preserved Node-1 (71×70) NPZ: `data/she2d_aniso_71x70_t1_552bb609f0f2_X.npz`,
  sha256 `6596ae26d356cf3e52af8e1195a8fc9d6d2b125a246ad0dfa6959163e714312d`.

## Immediate-stop triggers (real run)

1. **R_phi ≥ 1e-4 at the 1500-iteration cap** → node is `UNRESOLVED` (recorded, not compared).
2. **Converged φ leaves `COMMON_PHI_SPAN` (−0.6, 3.65) V** → `ABORT` (frozen H-grid no longer bounds the
   solution).
3. **Inner Krylov/ILU solve hang** (outer counter frozen, CPU climbing) → manual kill → `UNRESOLVED`.
4. **Hard-blocks before any solver work:** F4 auth (signed GO missing/incomplete/bound to wrong SHA),
   F5 threads ≠ 1, F4 allowlist (node not listed) — all raise `SystemExit` with zero solver execution.

## F4 authorization requirement (for the real run)

The real resume is a production path and requires a **signed/reviewer-issued GO** written to
`campaign/aniso_exec_auth.json` with the full F4 schema:
`who`, `when`, `bound_sha` (matches the immutable pinned HEAD), `threads_required: 1`,
`node_allowlist` (explicitly lists every permitted node), `output_namespace`, `stop_on_unresolved`,
`stop_on_failed`. A bare `execution_authorized: true` is **no longer sufficient** and hard-blocks.
Sweep stays **HOLD** until that GO is recorded.
