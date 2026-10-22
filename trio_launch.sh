#!/usr/bin/env bash
# Full-trio R_phi-convergence confirmation (reviewer-approved, corrected methodology).
# Nodes sequential, warm-chained; each node runs to tol_phi=1e-4 (1500 cap = safety only).
#
# RUN-03 (audit): fail-closed pipes and NO automatic git push by default. A scientific runner must
# not silently mutate the repository, and a failed solver/tee must not be hidden by the pipe. Set
# TRIO_AUTOPUSH=1 explicitly, as a deliberate manual choice, to stage+commit+push the results.
set -euo pipefail
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

if [ "${TRIO_AUTOPUSH:-0}" = "1" ]; then
    echo "[trio] TRIO_AUTOPUSH=1 -> staging + committing + pushing results"
    git add logs/trioRphi_*.log data/she2d_richardson_*.npz
    git commit -m "relay: full-trio R_phi-convergence confirmation (Linux)"
    git push
    echo "[trio] pushed $(date -Is)"
else
    echo "[trio] results NOT pushed (set TRIO_AUTOPUSH=1 to push deliberately). Review, then push by hand."
fi
