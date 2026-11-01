# ANISO sweep — reviewer decision packet

**Date:** 2026-11-01 · **Status:** HOLD (sweep halted at documented checkpoint; nothing has run since).
**Decision pin (code + artifacts):** `11ac0fa92cd21370b01a3068859e66fe201f30dc` · **Repo:**
<https://github.com/chanlikt-lgtm/Liang1997>

One page for the reviewer. Everything on the maintainer side is closed, verified, and pinned. The sweep
does **not** resume until the two decisions in §3 are recorded. Scope throughout: **discretization
convergence only** — no continuum / Liang-1997 physics claim follows from this study.

## 1. What is being asked of you

Three items, all at the pinned SHA `11ac0fa`:

1. **Step-B independent re-verification** (prerequisite) — re-run the audit below and confirm it.
2. **Prospective GO** (your decision) — dated authorization: scope, constraints, stop conditions.
3. **Node-1 (71×70) admissibility** (your decision) — admit / re-run / exclude, with rationale.

**Gate-4 concurrence is NOT requested of you as a gate** — it is owner-closed (Chan Lik, 2026-10-30,
definitive); your view on the Gate-4 *analysis rule* is advisory. The frozen rule is the parameter-free
`r = d23/d12 ≥ 1` contraction screen (amendment §3.1).

## 2. Step-B evidence already assembled (for your re-verification)

Full report: **`docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md`**. Executed in a worktree at exactly
`11ac0fa`; harness/tests/`src` are byte-identical `11ac0fa..main` on those paths (later Gate-4-analysis
addition does not touch them). Headline results, each with archived logs under
`campaign/logs/stepb_20261029/`:

- **Regression suite:** `pytest campaign/test_aniso_mesh_study.py -q` → **21 passed, exit 0**
  (`pytest_mesh_study.txt` + verbose). Env in `env.txt`.
- **Threading:** harness pins `OPENBLAS/OMP/MKL_NUM_THREADS=1` at import; all three canonical 71×70
  nodes record `threadpool_actual blas=1`; the 8-thread control is excluded from convergence analysis.
- **Seven acceptance gates (canonical 71×70, raw values):** all seven PASS — `R_phi=8.09e-5<1e-4`,
  `continuity_residual=3.45e-9<1e-6`, `|number_balance|=2.08e-5<1e-2`, three drift gates `<5e-3`,
  `hotspot_drift=5.74e-5<0.5`. `R_phi<1e-4` alone is explicitly **not** sufficient (two continuity-class
  criteria are AND-gated, enforced by `test_certify_not_rphi_alone`).
- **Authorization hard-block (live):** with `aniso_exec_auth.json` removed, both `--family X` and
  `--sweep` reject with **exit 1** before any solver work (`auth_block_*`).
- **Manifest lifecycle + failure isolation:** `queued/running/certified/failed/UNRESOLVED`; a failing
  X-family does not mark Y-family complete (`test_run_sweep_sequential_failure_isolation`).
- **CANONICAL bit-identity** (float.hex + SHA-256 of array `.tobytes()`, not decimal repr): the three
  single-thread 71×70 runs are byte-identical on the physics arrays —
  `Gii_max=0x1.973e8ea5f5dd7p+84`, `SHA256(Gii)=c6a906cd…`, `SHA256(phi)=be38607b…`, `n_iter=531`,
  identical ×3. Whole-file hashes differ **only** because each npz embeds its own `git_commit`/`warm_source`
  provenance; arrays identical. (`bit_identity.txt`.)

## 3. Signed decision record (please fill in)

| Field | Record |
|---|---|
| Reviewer identity + date | `__________________________` |
| Step-B verification result | `PASS / FAIL (attach log)` |
| Reviewed commit SHA | `11ac0fa92cd21370b01a3068859e66fe201f30dc` (confirm) |
| Prospective GO | `GO / HOLD` — scope: `__________` — stop conditions: `__________` |
| Node-1 admissibility | `ADMIT / RE-RUN / EXCLUDE` — rationale: `__________` |
| Gate-4 amendment (advisory) | `CONCUR / REVISE / REJECT` — revision id: `__________` |

## 4. On a recorded GO

The maintainer relays the approved resume to the Linux runner; the **single-threaded** sweep continues
from the documented checkpoint (node 2 → 141×70 → Y-family 100×58 / 100×85), per-node certified under the
seven gates, Gate-4 analysis under the frozen `r≥1` rule. If Step-B exposes a defect, it is fixed and
re-verified before the decision proceeds.

## 5. Source documents (all on `main`; attach immutable SHAs for the record)

- Step-B report — `docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md`
- Release-gate status + action list — `docs/ANISO_RELEASE_GATE_STATUS_20261029.md`
- Ready-for-GO crosswalk — `docs/ANISO_READY_FOR_GO_20261029.md`
- Checkpoint crosswalk — `docs/ANISO_CHECKPOINT_CROSSWALK_20261027.md`
- Gate-4 surface-hotspot amendment (r≥1 criterion) — `docs/ANISO_GATE4_SURFACE_HOTSPOT_AMENDMENT_20261027.md`
- Archived Step-B logs — `campaign/logs/stepb_20261029/`
