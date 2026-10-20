#!/usr/bin/env bash
# =====================================================================
#  Liang-1997 SHE-BTE reproduction -- full pipeline from scratch (Linux).
#  Linux equivalent of run_from_scratch.bat. Performs a TRUE full wipe of
#  ALL stages (so the idempotent trio harness cannot SKIP shipped
#  checkpoints), then runs Stages 1-6 cold.
#
#  Usage (from repo root):   ./run_from_scratch.sh
#  Full console capture:     ./run_from_scratch.sh 2>&1 | tee data/run_console.log
#
#  Pure Python (numpy/scipy; numba optional) -- no Windows C extension.
#  Total ~26-40 h; the 141x85 trio node is the long pole. Needs a box with
#  >~8 GB free RAM (the trio warns below 7 GB); OOM-free on >=16 GB.
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-python3}"
RUNLOG="data/run_from_scratch.log"
mkdir -p data figures

stamp(){ echo "$(date '+%a %F %T')  $*" | tee -a "$RUNLOG"; }

# --- Full wipe of all stages (back up any shipped trio checkpoints first) ---
if ls data/she2d_richardson_*.npz >/dev/null 2>&1; then
  BK="data/prerun_backup_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$BK"
  cp -p data/she2d_richardson_*.npz "$BK"/ 2>/dev/null || true
  cp -p data/she2d_richardson_*.progress.json "$BK"/ 2>/dev/null || true
  cp -p data/richardson_trio_metrics.csv data/richardson_trio_run.log "$BK"/ 2>/dev/null || true
  stamp "WIPE: backed up existing trio checkpoints -> $BK"
fi
rm -f data/she2d_richardson_*.npz data/she2d_richardson_*.progress.json \
      data/richardson_trio_metrics.csv data/richardson_trio_run.log \
      figures/she2d_iv_moment.png figures/she2d_anderson_converge.png
stamp "WIPE: removed all node NPZ + progress sidecars + Stage-1/2 sentinels (cold)"

stamp "=== RUN START.  Interpreter: $PY"
"$PY" -c "import numpy,scipy;print('numpy',numpy.__version__,'scipy',scipy.__version__)"

stamp "STAGE 1/6: foundation -> one-way SHE -> coupled -> Figs 2-8 overlays (~1.5-2 h)"
"$PY" reproduce_all.py --full

stamp "STAGE 2/6: Rev 5 Anderson-accelerated coupled fixed point, 3 grids (~1.5 h)"
"$PY" src/coupled_anderson.py 40 34 6 0.5 40 1
sleep 300   # thermal cooldown between Anderson grids (inert, wall-time only)
"$PY" src/coupled_anderson.py 60 50 6 0.5 40 1
sleep 300   # thermal cooldown between Anderson grids (inert, wall-time only)
"$PY" src/coupled_anderson.py 80 66 6 0.5 40 1
"$PY" src/she2d_anderson_fig.py

stamp "STAGE 3/6: Rev 6 controlled spatial-convergence trio (~23 h, SEQUENTIAL, continue-until-plateau)"
"$PY" src/run_richardson_trio.py

stamp "STAGE 4/6: gated Richardson fit (S_rev verdict)"
"$PY" src/richardson_fit.py data/she2d_richardson_71x58.npz data/she2d_richardson_100x70.npz data/she2d_richardson_141x85.npz

stamp "STAGE 5/6: auto-generate run-results report from THIS run's data"
"$PY" src/gen_run_report.py

# optional: recompile canonical report if a LaTeX toolchain is present
if command -v pdflatex >/dev/null 2>&1; then
  stamp "optional: recompiling canonical report_v6_full.pdf"
  ( cd report && for i in 1 2 3; do pdflatex -interaction=nonstopmode report_v6_full.tex >/dev/null 2>&1 || true; done )
fi

stamp "STAGE 6/6: archive all plots + reports + data/logs into runs (timestamped subdir)"
"$PY" src/archive_run.py

stamp "=== DONE. Snapshot under runs/ (timestamped); run report: report/report_run_latest.pdf ==="
