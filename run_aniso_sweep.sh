#!/usr/bin/env bash
# ANISO mesh-convergence sweep — spec v1.6 SINGLE-THREADED (user GO 2026-10-25 09:32 MYT).
# Sequential X-family then Y-family, warm-chained within family (harness handles it).
# Every node: OPENBLAS/OMP/MKL_NUM_THREADS=1. 4th level gated by pre-committed resource/convergence
# rule (G1.4) — NOT requested here; "6-node sweep" per reviewer note (3 X + 3 Y, anchor shared).
# G0.2 execution authorization required via campaign/aniso_exec_auth.json (present).
# No auto-push (RUN-03 audit): results committed + pushed by hand after review.
set -euo pipefail
cd ~/.openclaw/workspace/Liang1997
PY=python3                    # system python 3.10.12 / numpy 2.2.6 — matches the certified t1/t8 controls
mkdir -p logs

export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

echo "[aniso] start $(date -Is)"

# X-family (refine drain-x, Ny=70 fixed)
"$PY" campaign/aniso_mesh_study.py --family X --threads 1 2>&1 | tee logs/aniso_X_family.log
echo "[aniso] X-family done $(date -Is)"

# Y-family (refine depth-y, Nx=100 fixed)
"$PY" campaign/aniso_mesh_study.py --family Y --threads 1 2>&1 | tee logs/aniso_Y_family.log
echo "[aniso] Y-family done $(date -Is)"

# G1.6 anchor cross-check
"$PY" -c "import json;from campaign.aniso_mesh_study import compare_anchor;print(json.dumps(compare_anchor(),indent=2))" \
  2>&1 | tee logs/aniso_anchor_compare.log || echo "[aniso] compare_anchor skipped/failed"

echo "[aniso] SWEEP COMPLETE $(date -Is)"
