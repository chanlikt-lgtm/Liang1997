# Certified Sep-24 reference trio (pure-Python kernel)

These are the CERTIFIED Liang-1997 drain-refined Gii trio results from the
2026-09-24 cold `run_from_scratch.bat` run (git d30b471, pure-Python
`_assemble_python` kernel), validated equivalent to tag `solver-frozen-2026-09-26`.

Use THESE for reproduction comparison — NOT the `data/*.npz` committed at the
repo root, which are the older ARCHIVAL (superseded, under-converged) trio
[2.990 / 2.135 / 2.413]e25.

Certified peak Gii:
  71x58  : 3.075619e25   (359 iters)
  100x70 : 2.136180e25   (480 iters)
  141x85 : 2.387429e25   (chunk-0 warm-start)
Sequence NON-MONOTONE (-,+); S_rev=737 -> Richardson suppressed -> no justified continuum Gii.

For a valid clean reproduction, run with `SHE2D_DISABLE_NUMBA=1` (forces the
reference pure-Python assembly kernel; numba diverges ~2-3% on this near-null-space Gii).
