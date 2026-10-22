#!/usr/bin/env bash
# P2 diagnostic continuation (fresh, corrected keys), single-threaded.
set -u
cd ~/.openclaw/workspace/Liang1997
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
echo "[p2] start $(date -Is)"
.venv/bin/python -u audit/diag_continuation.py data/she2d_richardson_71x58.npz --extra 100 > logs/diag_cont_71x58.log 2>&1
echo "[p2] 71x58 done $(date -Is)"
.venv/bin/python -u audit/diag_continuation.py data/she2d_richardson_100x70.npz --extra 100 > logs/diag_cont_100x70.log 2>&1
echo "[p2] 100x70 done $(date -Is)"
echo "[p2] all done $(date -Is)"
