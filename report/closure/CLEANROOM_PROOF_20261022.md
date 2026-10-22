# Clean-tree frozen replay — proof & data custody (reviewer residual R5)

Date: 2026-10-22 · Host: Linux (chanlik-Inspiron-3020) · Pinned commit: `e4c7587`

## 1. Clean-tree proof

```
$ git clone git@github.com:chanlikt-lgtm/Liang1997.git liang_cleanroom
$ cd liang_cleanroom && git checkout --detach e4c7587
HEAD = e4c7587f64cf4ebf74df15ea6f5ccae442672eed
$ git status --porcelain
<empty>                        # 0 bytes
```

The tree was re-verified pristine immediately BEFORE each gate run and immediately AFTER it:

| step | porcelain before | porcelain after |
|---|---|---|
| Gate B fault injection (11 tests) | empty (0 bytes) | **empty (0 bytes)** |
| Gate C read-only replay | empty (0 bytes) | **empty (0 bytes)** |

Both harnesses left the tree byte-for-byte pristine, so no run artifact contaminated the
clean-tree claim. Gate output JSONs were written OUTSIDE the clone
(`report/closure/gate_b_cleanroom.json`, `gate_c_cleanroom.json`, `gate_c_cleanroom_npzrecon.json`)
specifically so they could not dirty it.

## 2. Gate B — fault injection on the clean tree

`python report/closure/gate_b_fault_injection.py --repo . --json <outside>/gate_b_cleanroom.json`

**Overall: PASS — 11/11.** Identical result to the dirty-checkout run
(`report/closure/gate_b_results.json`): RUN-02 no-sidecar → exit 4, `--exploratory` → exit 0 +
UNCERTIFIED, CLOS-01 partial trio → exit 4, RUN-05 → RuntimeError, RUN-04 `--keep-going` → exit 1,
NUM-02 hash_ok {all-equal / one-missing / all-missing / mismatch} → {T/F/F/F}, and both RUN-01
pdflatex fault cases → nonzero with the RUN-01 branch reached and no import crash.

## 3. Data custody at `e4c7587` — FLAG: sidecars are incomplete

The trio NPZs are committed at `e4c7587`, so the clone's `data/` is hash-pinned by the commit
itself (`git status` stays empty). **But the progress.json sidecars are not all there:**

| node | npz sha256 (committed) | sidecar | sidecar sha256 | sidecar state |
|---|---|---|---|---|
| 71×58 | `632736219b130f79…e5e27b36` | present | `6852c7e52b5a09d2…71656208` | **STALE — do not use** |
| 100×70 | `12e5e7171985014a…fe6a9e59` | **ABSENT** | — | missing from the commit |
| 141×85 | `d9eaf6985ee00bf9…2b82d9817` | **ABSENT** | — | missing from the commit |

Why 71×58 is stale: that sidecar is from the **2026-10-16 cold restart** (`restart_ts
2026-10-16T12:04:16`, `cum_iters=360`, `passed=false`) and its buffer terminal is
`Gii=2.706653e25 / Gtot=8.159518e13`, while the committed NPZ terminal is
`Gii=3.075752e25 / Gtot=9.264380e13`. It describes a different, abandoned trajectory.

### Three mutually distinct datasets exist — this is the decision Claude asked for

| source | 71×58 sha256 | 100×70 sha256 | 141×85 sha256 |
|---|---|---|---|
| **committed at `e4c7587`** (this replay) | `6327362…` | `12e5e71…` | `d9eaf69…` |
| `CLOSEOUT_solver-frozen-2026-09-26/SHA256SUMS.txt` | `2e5736b0…` | `9d8139b5…` | `dd51e353…` |
| Windows Gate C run (`gate_c_readonly_checkpoints.json`) | `33533e2c…` | `ad390eb4…` | `59b16b78…` |

So the previously-reported Gate C PASS was obtained on the **Windows Rev6 campaign set**
(`Gii = 3.075619 / 2.087561 / 2.399434 e25`), whereas the commit carries the **Linux
R_phi-converged set** (`3.075752 / 2.144818 / 2.406344 e25`). Neither equals the 2026-09-26
closeout bundle. Any future gate must state which of the three it is replaying.

## 4. Gate C — read-only replay on the clean tree

**Provenance disclosure:** the reviewer's `Liang1997_Readonly_Checkpoints.py` (sha256 prefix
`1574593918f5…`) **was never transferred to this Linux host and is not in the repository history**,
so it could not be run unmodified. `report/closure/gate_c_cleanroom_local.py` is a **local
reimplementation** of its checks and output schema, run read-only. It must not be presented as the
reviewer's script; replace it when the original is resent.

### 4a. Sidecar-based mode (the reviewer's semantics) — `gate_c_cleanroom.json`

- **`Source tree clean = True`** ← the R5 datum that was missing before.
- 71×58 fails as expected against its stale sidecar (terminal mismatch, `passed=False`,
  spread 9.4e-3 ≫ 3e-4 gate).
- 100×70 and 141×85 cannot be certified because their sidecars are absent from the commit.
- `Phi_gate` absent from the NPZs (known; to be frozen via the signed manifest).
- Archival ±2% parity: `71×58 +2.868%` (outside), `100×70 +0.460%` (inside), `141×85 −0.276%`
  (inside). Note this is materially better than the Windows set (`+2.864 / −2.222 / −0.562`).
- Overall: `INCOMPLETE — see failed checks` (data-custody failures only, not integrity failures).

### 4b. Supplementary sidecar-free mode — `gate_c_cleanroom_npzrecon.json`

Opt-in (`--npz-window`): where a sidecar is absent or stale, the certified window is reconstructed
from the NPZ's own terminal `last4_*` arrays, which the solver writes per iteration. Clearly
labelled in every affected check detail; **this is not the reviewer's sidecar-based certification.**

| node | certified iters | spread_Gii | spread_Gtot | last R_phi | result |
|---|---|---|---|---|---|
| 71×58 | 322–325 | 6.974e-05 | 1.443e-04 | 7.104e-05 | PASS (stale sidecar discarded) |
| 100×70 | 926–929 | 2.131e-05 | 2.760e-05 | 6.970e-05 | PASS |
| 141×85 | 714–717 | 7.748e-06 | 7.125e-06 | 7.302e-05 | PASS |

All three windows are genuine 4-consecutive-iteration windows under the unchanged 3e-4 spread gate
and 1.5e-3 R_phi floor; H-hashes and all six physics/grid parameters identical; drain-refinement
ratios `1.414355 / 1.414368` (target √2). Overall: `INTERNAL CHECKS PASS — PAPER VALIDATION NOT
CLAIMED`. Scientific status unchanged: **NOT SPATIALLY CONVERGED** (non-monotone, no continuum Gii).

## 5. What still blocks a full clean-tree CP7

1. Resend `Liang1997_Readonly_Checkpoints.py` (sha256 prefix `1574593918f5…`) so the reviewer's own
   script — not a reimplementation — produces the clean-tree JSON.
2. Commit the two missing sidecars, and re-commit or delete the stale 71×58 sidecar, so the pinned
   commit is self-contained. **Recommendation:** commit sidecars for all three nodes, regenerated
   from the NPZ `last4_*` terminal chunks via `src/certified_window.py` (NUM-01), and mark the old
   71×58 sidecar superseded rather than silently replacing it.
3. Decide explicitly which dataset (committed / closeout-bundle / Windows Rev6) future gates use.
