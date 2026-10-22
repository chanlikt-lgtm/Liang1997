#!/bin/bash
# Run the 4-seed perturbation ensemble (single-thread each), then summarize + push.
set -u
cd /home/chanlik/.openclaw/workspace/Liang1997
export SHE2D_DISABLE_NUMBA=1
mkdir -p audit/logs
rm -f audit/ENSEMBLE_DONE.marker audit/ENSEMBLE_SUMMARY.txt

for s in 0 1 2 3; do
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    .venv/bin/python audit/perturbation_test.py --maxo 400 --seed $s --eps 1e-16 --post-gate 20 \
    > "audit/logs/perturb_seed$s.log" 2>&1 &
  echo "launched seed $s pid $!"
done

wait
echo "ALL_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" > audit/ENSEMBLE_DONE.marker

# Summarize per-seed key fields
.venv/bin/python - <<'PYEOF'
import json, os
out = []
for s in range(4):
    p = f"audit/perturb_seed{s}.json"
    if not os.path.exists(p):
        out.append(f"seed {s}: MISSING JSON")
        continue
    d = json.load(open(p))
    pi = d.get("perturbation_applied_first_iter") or {}
    ad = pi.get("A_data") or {}
    bb = pi.get("b") or {}
    out.append(
        f"seed {s} ({d.get('mode')}) n_outer={d.get('n_outer')}\n"
        f"  Gii_max_final={d.get('Gii_max_final')}\n"
        f"  Gtot_final={d.get('Gtot_final')} R_phi_final={d.get('R_phi_final')}\n"
        f"  certified_persistent={d.get('certified_persistent')} first_gate_iter={d.get('first_gate_iter')} post_gate_iters={d.get('post_gate_iters')}\n"
        f"  hotspot_node_ij={d.get('hotspot_node_ij')} hotspot_xy_um={d.get('hotspot_xy_um')}\n"
        f"  assemble_perturb_calls={d.get('assemble_perturb_calls')}\n"
        f"  perturb A_data frac_changed={ad.get('frac_changed')} max_abs_rel={ad.get('max_abs_rel_applied')} rms_rel={ad.get('rms_rel_applied')}\n"
        f"  perturb b frac_changed={bb.get('frac_changed')} max_abs_rel={bb.get('max_abs_rel_applied')} rms_rel={bb.get('rms_rel_applied')}"
    )
open("audit/ENSEMBLE_SUMMARY.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
PYEOF

git add audit/perturb_seed*.json
git commit -m "relay: perturbation plateau ensemble (seeds 0-3)" 2>&1
git push 2>&1
echo "PUSH_DONE"
