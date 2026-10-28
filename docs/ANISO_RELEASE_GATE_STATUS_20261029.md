# ANISO release gate — status & reviewer action list

**Date:** 2026-10-29 · **Status:** HOLD (sweep halted, checkpoint preserved) · **Pinned SHA for all
decisions:** `11ac0fa92cd21370b01a3068859e66fe201f30dc` · **Repo:** <https://github.com/chanlikt-lgtm/Liang1997>

Everything on the maintainer side is closed, verified, and pinned. This page is the single action list
for the reviewer to move from HOLD to a recorded decision. The code at `11ac0fa` is *not* itself
verification/approval/authorization — those are the explicit decisions below.

## What is already done (maintainer side)

- CP0 halt + preserve; CP1–5 preparation closed and maintainer-verified; CP7 Gate-4 rules FROZEN
  (surface-hotspot amendment + `r≥1` screen + edge cases). Evidence map:
  `docs/ANISO_READY_FOR_GO_20261029.md`, crosswalk, §5 package + supplement, halt record, amendment.
- Governance disclosed: v1.6 frozen 09:27 → **owner authorization 09:32** → first run 09:40, external
  sign-off pending; **user-authorized / reviewer-pending** (not unauthorized). Data preserved for an
  admissibility decision.
- Scope: discretization convergence only. No continuum / Liang-1997 physics claim from this study.

## Reviewer action list (the remaining gates)

### 1. Step-B independent re-verification (prerequisite), at SHA `11ac0fa`
- [ ] `pytest campaign/test_aniso_mesh_study.py` — record actual result (the reported 21/21 is not yet
      independently re-run).
- [ ] `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1` + per-node `threadpool_actual=1`.
- [ ] All seven acceptance gates vs recorded per-node values (incl. `continuity_residual < 1e-6`,
      `|relative_number_balance| < 1e-2`, `R_phi < 1e-4`; raw values + units).
- [ ] Authorization hard-block (`campaign/aniso_exec_auth.json` contract) blocks `--family`/`--sweep`.
- [ ] Manifest states (`queued/running/certified/failed/UNRESOLVED`) + failure isolation.
- [ ] Bit-identity of the three single-thread 71×70 runs at full precision (3.0770514168841145e25).

### 2. Three explicit decisions
- [ ] **Prospective GO** — dated authorization: commit SHA, approved scope, constraints, stop conditions.
- [ ] **Node-1 (71×70) admissibility** — admit / re-run / exclude, with rationale.
- [ ] **Gate-4 concurrence** — sign off on the surface-hotspot amendment + the `r≥1` screen (or approve a
      documented alternative) — required *before* any Y-family run.

### 3. Signed decision record (fill in)

| Field | Record |
|---|---|
| Reviewer identity + date | `__________________________` |
| Step-B verification result | `PASS / FAIL (attach log)` |
| Prospective GO | `GO / HOLD` — scope: `__________` — stop conditions: `__________` |
| Reviewed commit SHA | `11ac0fa92cd21370b01a3068859e66fe201f30dc` (confirm) |
| Node-1 admissibility | `ADMIT / RE-RUN / EXCLUDE` — rationale: `__________` |
| Gate-4 amendment | `CONCUR / REVISE / REJECT` — revision id: `__________` |

## In parallel (reviewer-sanctioned; not a gate)

The Gate-4 **analysis** harness (`campaign/aniso_gate4_analysis.py`) is being developed + unit-tested on
synthetic sequences. It launches no runs, does not alter the frozen acceptance rules, and is not a
convergence result — purely so the analysis is instant once certified nodes exist.

## On a recorded GO

The maintainer relays the approved resume to the Linux runner; the single-threaded sweep continues from
the documented checkpoint (node 2 → 141×70 → Y-family 100×58/100×85), per-node certified, with Gate-4
analysis under the frozen rules. If Step-B exposes a defect, it is fixed and re-verified before the
decision proceeds.
