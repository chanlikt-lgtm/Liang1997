#!/usr/bin/env bash
# Full-trio R_phi-convergence confirmation (reviewer-approved, corrected methodology).
# Nodes sequential, warm-chained; each node runs to tol_phi=1e-4 (1500 cap = safety only).
set -u
cd ~/.openclaw/workspace/Liang1997
PY=.venv/bin/python
mkdir -p logs
echo "[trio] start $(date -Is)"

"$PY" src/coupled_drain_richardson.py 71 58 1500 2>&1 | tee logs/trioRphi_71x58.log
echo "[trio] node 71x58 done $(date -Is)"

"$PY" src/coupled_drain_richardson.py 100 70 1500 data/she2d_richardson_71x58.npz 2>&1 | tee logs/trioRphi_100x70.log
echo "[trio] node 100x70 done $(date -Is)"

"$PY" src/coupled_drain_richardson.py 141 85 1500 data/she2d_richardson_100x70.npz 2>&1 | tee logs/trioRphi_141x85.log
echo "[trio] node 141x85 done $(date -Is)"

echo "[trio] all 3 done $(date -Is)"
git add logs/trioRphi_*.log data/she2d_richardson_*.npz
git commit -m "relay: full-trio R_phi-convergence confirmation (Linux)" 2>&1
git push 2>&1
echo "[trio] pushed $(date -Is)"
