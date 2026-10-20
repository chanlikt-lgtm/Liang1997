#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
echo "[launch] start $(date -Is)"
for s in 0 1 2 3; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "$PY" audit/perturbation_test.py \
    --maxo 800 --seed "$s" --eps 1e-16 --persist-n 40 > "audit/run800_seed$s.log" 2>&1 &
done
wait
echo "[launch] all 4 seeds done $(date -Is)"
for s in 0 1 2 3; do
  echo "=== seed $s ==="
  tail -20 "audit/run800_seed$s.log"
done
git add audit/perturb_seed*.json
git commit -m "relay: 800-iter ensemble (hardened metric)" 2>&1
git push 2>&1
echo "[launch] pushed $(date -Is)"
