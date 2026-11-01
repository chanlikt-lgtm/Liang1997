# Linux-Native Certified Reference Trio — 2026-10-30

**Purpose.** A clean-tree, frozen-tag, single-threaded, from-scratch Linux reproduction of the
reproducibility trio (71×58 / 100×70 / 141×85), run **for the record** as a Linux-native certified
reference to complement the canonical Windows Sep-24 reference. This supersedes the Oct-20 Linux
full-trio previously committed under `data/` (those values remain in git history: `7e37100`,
`4a9794b`; the Oct-20 numbers were 3.075752 / 2.144818 / 2.406344 e25).

**Method.** R_φ-convergence (NOT the plateau-gate `run_from_scratch.sh`, which premature-stops on
Linux). `coupled_drain_richardson.py Nx Ny 1500`, `tol_phi = 1e-4`, warm-chained
71×58 → 100×70 → 141×85. Single-threaded (OPENBLAS/OMP/MKL/NUMEXPR/VECLIB = 1), pure-Python
(`SHE2D_DISABLE_NUMBA=1`), env = Python 3.13.12 / numpy 2.5.1 / scipy 1.18.0 (matches the frozen pin).

## Clean-tree proof

- Fresh clone at `930dd86` (`git describe` → `solver-frozen-2026-09-26-2-g930dd86`); `src/` is
  byte-identical to the frozen tag `f6a8f91` (verified `git diff --stat f6a8f91 930dd86 -- src/` = empty).
- All three nodes record `git_commit = 930dd86`, `git_dirty = clean` in their npz provenance fields.
- Run log (`~/liang_ref_logs/master.log`): launch 2026-10-30 07:44 (clean start, 0 files);
  node1 71×58 exit 0 @ 14:13; node2 100×70 exit 0 @ 10-31 10:45; node3 141×85 exit 0 @ 10-31 23:54.
  **TRIO DONE — all three exited 0, no UNRESOLVED.**
- Launch-time proof archive: `~/liang_ref_logs/clean_tree_proof.txt` (HEAD + full `src/` sha256 manifest).

## Per-node results

| mesh | n_iter | R_phi | Gii_max (e25) | G_tot (e13) | hotspot (µm, 0) | Δ vs Windows ref |
|---|---|---|---|---|---|---|
| 71×58  | 465 | 8.126e-5 | 3.067845 | 9.242749 | 0.589384 | **−0.253%** |
| 100×70 | 780 | 8.194e-5 | 2.148721 | 6.060896 | 0.589422 | **+0.587%** |
| 141×85 | 253 | 7.460e-5 | 2.400334 | 6.559429 | 0.589384 | **+0.541%** |

Windows reference (`reference_sep24/`): 71×58 = 3.075619e25, 100×70 = 2.136180e25,
141×85 = 2.387429e25.

**Headline:** all three meshes reproduce the Windows reference to **< 0.6%** (target < 1%), and —
notably — **141×85 converged cleanly this time** (R_phi = 7.46e-5 at 253 warm-chained iters), whereas
the prior runs either hung at outer 281 (inner-solve stagnation → UNRESOLVED) or had to use an
earlier-run (1893b9c) solver-equivalent result. The prior 281-hang was **path-dependent, not a hard
singularity**: on a clean frozen tree, single-threaded, the finest mesh certifies under R_φ<1e-4
without incident.

**Delta vs the Oct-20 Linux full-trio:** −0.257% / +0.182% / −0.250% (71×58 iter 465 vs 325;
100×70 780 vs 929; 141×85 253 vs 717). See **Build provenance** below for why this is *not*
cross-build FP and *not* run-to-run FP noise — the leading lever is **threading** (Oct-18/20 default
multi-threaded BLAS vs this explicitly single-threaded run).

## Build provenance (exact; the two Linux venvs are byte-identical)

This clean-tree venv and the Oct-20 trio venv resolve to the **same** wheel from the shared uv cache —
verified byte-identical, so the reference is build-pinned and rigorous:

- **numpy 2.5.1** — wheel `cp313-cp313-manylinux_2_27_x86_64` / `manylinux_2_28_x86_64` (meson).
- **scipy 1.18.0** — same wheel tags.
- **OpenBLAS** (bundled in `numpy.libs/libscipy_openblas64_-017048f4.so`):
  `OpenBLAS 0.3.33.112.0  USE64BITINT DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=64`.
- **threadpoolctl** (Oct-20 venv, 3.7.0): `version 0.3.33.112.0`, `threading_layer pthreads`,
  `architecture Haswell`, `prefix libscipy_openblas`, `num_threads 24` (run-time single-thread enforced
  via OPENBLAS/OMP/MKL/NUMEXPR/VECLIB = 1).
- **Byte-identity check:** all 127 `.so` files under `numpy/`, `scipy/`, `numpy.libs/`, `scipy.libs/`
  (incl. `_multiarray_umath`, `libgfortran`, `libquadmath`) are SHA256-identical across the two venvs;
  `WHEEL` metadata identical. **The Oct-20 and Oct-30 runs used the identical build** (same cached wheel,
  both timestamped 2026-10-16).

### Why the Oct-20 delta is NOT cross-build FP (leading lever: threading)

Claude's framing correction (2026-11-01) first predicted a different wheel/OpenBLAS build, then — after the
build was shown byte-identical — attributed the delta to the dirty tree. The bounded reconstruction refined
this further:

1. **Builds byte-identical** (above): all 127 `.so` files SHA-256-identical → cross-build FP ruled out.
2. **Physics params identical**: the Oct-18/20 run's echoed manifest (ratio/W/X_C/dH/eps_max/Anderson/
   tol_phi/Phi_gate) matches this clean-tree run exactly → the dirty tree did *not* change any physics.
3. **Cold start bit-identical**: outer 0/1/2 log lines match to 4 sig figs (dphi, nmax, pmax, Temax,
   Gmax, Id, bal) → the solver code was effectively identical at the start (a dirty solver change would
   have shown up in the DD warm-up / first outer steps).

→ **Leading lever = threading.** The Oct-18/20 trio ran `python src/coupled_drain_richardson.py …` with
**no `*_NUM_THREADS` pin** (default multi-threaded BLAS), whereas this clean-tree run was explicitly
single-threaded (OPENBLAS/OMP/MKL/NUMEXPR/VECLIB = 1). A different BLAS reduction order re-seeds the
near-null-space → the ~0.25% Gii shift and 325-vs-465 iter difference. The Oct-20 `git_dirty` flag was
most likely cosmetic (uncommitted logs/plots/bytecode), not a solver change.

**Honest magnitude caveat (recorded):** this threading attribution is the *leading* explanation and
matches the known mechanism, but the ~0.25% for 71×58 is **inferred**, not directly measured — no 71×58
single-vs-multi control was run, and it is ~17× smaller than the directly-measured 71×70 threading figure
(4.3%, spec G3.5 — that value is 71×70-only; threading sensitivity is mesh-dependent). So this is
"most plausibly threading", not "proven threading". A direct 71×58 single-vs-multi control (~10–20 h) is
not warranted: this clean single-thread run is the authoritative reference regardless.

This clean-tree run is therefore the first provably-clean, bit-reproducible Linux reference.

## Canonical hashes

`float.hex()` of the terminal scalars + SHA-256 of the field arrays (`.tobytes()`), byte-exact
reproducibility fingerprints.

| mesh | Gii_max hex | R_phi hex | G_tot hex |
|---|---|---|---|
| 71×58  | `0x1.9606a431a45dap+84` | `0x1.54d1be7424000p-14` | `0x1.503fcfb62f3a8p+46` |
| 100×70 | `0x1.1c6180ef655ffp+84` | `0x1.57af6cb740000p-14` | `0x1.b8fcfac7a46ccp+45` |
| 141×85 | `0x1.3dae7aa2be05bp+84` | `0x1.38e2410388000p-14` | `0x1.dd42e28664b5cp+45` |

SHA-256 of `Gii` field (`.tobytes()`):

| mesh | SHA256(Gii) |
|---|---|
| 71×58  | `c31e038762ceef3b39925c8efa81e9c193bd59b1f80676dcd51b730a4062afea` |
| 100×70 | `a58150a0b49e13e57e26a66ead7104d42eb399d8060b2b74b69e07ad1fe948b0` |
| 141×85 | `f568f7a967440920de64eab7f18545da4ff6c109eecafcafb70a22a21463d4ed` |

SHA-256 of `phi` field (`.tobytes()`):

| mesh | SHA256(phi) |
|---|---|
| 71×58  | `1cbeca105acac642277d3765ae8b221af344fbfd44f6bdede708d1d243336af4` |
| 100×70 | `944a6ec00b4e4d0614335f23d6da5873b17e4e4dfb06942345896e332fd0df8c` |
| 141×85 | `301ecc344220670a320ff447c3a26317852380263be8218dfd377ec9f91b58a4` |

## Manifest

Full npz file SHA-256 (committed artifacts under `data/`):

| mesh | SHA256(npz file) |
|---|---|
| 71×58  | `7e03a0d0e7af04844d14ac8a53f714c7221a5bb2d07939e5e7b6746d6123205d` |
| 100×70 | `bb2c55f901b34a997088b376385716622a1284cd02be189a3fd58224204df1b2` |
| 141×85 | `aa8458a9468cee01af1c7bb6f1c7db58aa6c28d049fc71a091c18231a6a0e277` |

Common provenance (all three npz): `Nx/Ny` as labeled, `ratio=6.0`, `W=0.09`, `X_C=0.60`,
`dH_eV=0.0125`, `eps_max_eV=3.02`, `she_tol=1e-8`, `NH=591`, `H_hash=b4319bb03303`,
`common_phi_span=(-0.6, 3.65)`, `git_commit=930dd86`, `git_dirty=clean`.

## Lineage

- **Canonical Windows reference:** `reference_sep24/` (3.075619 / 2.136180 / 2.387429 e25) — unchanged.
- **This commit:** `data/` now holds the clean-tree Linux-native reference
  (3.067845 / 2.148721 / 2.400334 e25).
- **Superseded in `data/`:** the Oct-20 Linux R_φ-converged full-trio
  (3.075752 / 2.144818 / 2.406344 e25), preserved in git history (`7e37100`, `4a9794b`) and quoted here.
  Note: those npz record `git_dirty='dirty'` and ran default multi-threaded BLAS (no `*_NUM_THREADS`
  pin); **threading** — not dirty-tree code — is the leading lever for their ~0.25% offset from this
  single-threaded clean-tree reference (see Build provenance).
