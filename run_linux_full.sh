#!/usr/bin/env bash
# =====================================================================
#  Liang 1997 SHE-BTE reproduction -- Linux full-chain runner.
#  Mirrors run_from_scratch.bat (Stages 1-6) for this box.
#
#  Stage 1 (reproduce_all.py --full) is ALREADY running in a separate
#  process; this script WAITS for it, then continues Stages 2-6.
#  Stage 3 (Richardson trio) is run COLD: the committed Windows-box
#  checkpoints were moved to data/backup_windows_trio_2026-10-15/ so a
#  fresh uninterrupted run is produced (and the reference is preserved
#  for the run-to-run drift comparison).
#
#  Idempotent-ish: each stage logs to data/run_linux_full.log and
#  non-trio stages use completion sentinels to allow a safe relaunch.
# =====================================================================
set -u
cd "$(dirname "$0")"
PY=python3
RUNLOG="data/run_linux_full.log"
mkdir -p data figures
exec >>"$RUNLOG" 2>&1

stamp() { echo "$(date '+%F %T')  $1"; }

fail() { stamp "*** FAILED at: $1 (exit $2)"; exit 1; }

stamp "=== RUN LINUX FULL START (interpreter: $(command -v $PY)) ==="
"$PY" -c "import numpy,scipy;print('numpy',numpy.__version__,'scipy',scipy.__version__)" || fail "imports" $?

# ---------------------------------------------------------------- Stage 1
stamp "STAGE 1/6: waiting for in-flight reproduce_all.py --full ..."
waited=0
while pgrep -f "reproduce_all.py --full" >/dev/null 2>&1; do
  sleep 30; waited=$((waited+30))
  if [ "$waited" -ge 21600 ]; then fail "Stage 1 still running after 6h wait" 1; fi
done
if [ -f figures/she2d_iv_moment.png ]; then
  stamp "STAGE 1/6: DONE (sentinel figures/she2d_iv_moment.png present)"
else
  stamp "STAGE 1/6: reproduce_all exited but sentinel figures/she2d_iv_moment.png MISSING -- check data/reproduce_run.log"
fi

# ---------------------------------------------------------------- Stage 2
stamp "STAGE 2/6: Rev5 Anderson-accelerated coupled fixed point, 3 grids (~1.5 h, clean re-run)"
"$PY" src/coupled_anderson.py 40 34 6 0.5 40 1 || fail "coupled_anderson 40x34" $?
"$PY" src/coupled_anderson.py 60 50 6 0.5 40 1 || fail "coupled_anderson 60x50" $?
"$PY" src/coupled_anderson.py 80 66 6 0.5 40 1 || fail "coupled_anderson 80x66" $?
"$PY" src/she2d_anderson_fig.py || fail "she2d_anderson_fig" $?

# ---------------------------------------------------------------- Stage 3
stamp "STAGE 3/6: Rev6 controlled spatial-convergence trio, COLD (~23 h, SEQUENTIAL)"
"$PY" src/run_richardson_trio.py || fail "run_richardson_trio" $?

# ---------------------------------------------------------------- Stage 4
stamp "STAGE 4/6: gated Richardson fit (S_rev verdict)"
"$PY" src/richardson_fit.py data/she2d_richardson_71x58.npz \
    data/she2d_richardson_100x70.npz data/she2d_richardson_141x85.npz || fail "richardson_fit" $?

# ---------------------------------------------------------------- Stage 5
stamp "STAGE 5/6: auto-generate run-results report"
"$PY" src/gen_run_report.py || fail "gen_run_report" $?

# ---------------------------------------------------------------- Stage 6
stamp "STAGE 6/6: archive plots + reports + data/logs"
"$PY" src/archive_run.py || fail "archive_run" $?

stamp "=== RUN LINUX FULL DONE ==="
