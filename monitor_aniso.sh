#!/usr/bin/env bash
# Aniso sweep monitor — checks node progress + stall detection.
# Exits 0 (quiet) when healthy; prints a status line when there's news.
set -u
cd ~/.openclaw/workspace/Liang1997

STATE=~/.openclaw/workspace/Liang1997/.aniso_monitor_state
touch "$STATE"

# is the sweep alive?
if ! pgrep -f "run_aniso_sweep.sh|aniso_mesh_study.py" >/dev/null; then
  if grep -q "SWEEP COMPLETE" logs/aniso_sweep_launcher.log 2>/dev/null; then
    echo "SWEEP COMPLETE — see logs/aniso_*.log; needs commit+push"
    exit 0
  fi
  echo "⚠️ SWEEP PROCESS NOT RUNNING and not marked complete — check logs/aniso_sweep_launcher.log"
  exit 0
fi

# current node + iters from the live family log
LIVE=$(ls -t logs/aniso_X_family.log logs/aniso_Y_family.log 2>/dev/null | head -1)
NODE=$(grep -oE "NODE: Nx=[0-9]+ Ny=[0-9]+" "$LIVE" 2>/dev/null | tail -1)
ITERS=$(grep -oE "outer [0-9]+/[0-9]+" "$LIVE" 2>/dev/null | tail -1)
KEY="$NODE|$ITERS"

if ! grep -qF "$KEY" "$STATE"; then
  echo "$KEY" >> "$STATE"
  LOAD=$(cut -d' ' -f1-3 /proc/loadavg)
  TEMP=$(sensors 2>/dev/null | grep -m1 -iE "package id" | awk '{print $4}' || echo "?")
  echo "sweep: $NODE @ $ITERS | load $LOAD | pkg $TEMP"
fi
exit 0
