"""
driver_equiv.py -- driver-equivalence isolation (audit reviewer Priority A).

On ONE OS, identical cold start / mesh / bias / Anderson settings, isolate the
effect of RE-INITIALIZING Anderson acceleration every CHUNK iterations:

  --mode continuous : one solve_coupled(max_outer=MAXO) call (Anderson history
                      accumulates over the whole run).
  --mode chunked    : ceil(MAXO/CHUNK) sequential solve_coupled(max_outer=CHUNK)
                      calls, each warm-started from the previous chunk's phi/p
                      (phi stays continuous) but with Anderson history RESET each
                      chunk (a fresh solve_coupled call). This is the continuous
                      driver + Anderson-reset-every-CHUNK = the reviewer's 3rd arm,
                      and mimics the trio harness's per-chunk reset.

Compare continuous vs chunked (same OS, same everything else) to decide whether
the Anderson reset alone reproduces the ~10% continuous-vs-trio-harness gap.
Diagnostic only; no source edit, no change to the running ensemble.

  python audit/driver_equiv.py --mode continuous --maxo 420
  python audit/driver_equiv.py --mode chunked    --maxo 420 --chunk 60
"""
from __future__ import annotations
import os, sys, json, argparse, platform, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import scipy
from device import DeviceParams
from coupled_she import solve_coupled

RATIO, W, X_C = 6.0, 0.09, 0.60
PHI_GATE, AA_DEPTH, AA_BETA, AA_STEP_CAP = -0.74, 6, 0.5, 5.0
SHE_TOL, DH_EV, TOL_PHI = 1e-8, 0.0125, 1e-4
COMMON_PHI_SPAN = (-0.60, 3.65)
GATE = 3e-4
Nx, Ny = 71, 58


def build_mesh(Lx, Ly):
    xf = np.linspace(0.0, Lx, 8000)
    dens = 1.0 + (RATIO - 1.0) * np.exp(-((xf - X_C) / W) ** 2)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(xf))]); cum /= cum[-1]
    x = np.interp(np.linspace(0.0, 1.0, Nx), cum, xf); x[0], x[-1] = 0.0, Lx
    y = Ly * (np.linspace(0.0, 1.0, Ny) ** 1.8)
    return x, y


def run_once(x, y, maxo, phi0, p0):
    return solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                         aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                         she_tol=SHE_TOL, max_outer=maxo, tol_phi=TOL_PHI, verbose=False,
                         phi_init=phi0, p_init=p0, phi_span_H_override=COMMON_PHI_SPAN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("continuous", "chunked"), required=True)
    ap.add_argument("--maxo", type=int, default=420)
    ap.add_argument("--chunk", type=int, default=60)
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args()
    for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(k, str(a.threads))

    p = DeviceParams(); x, y = build_mesh(p.Lx, p.Ly)
    G = []
    if a.mode == "continuous":
        r = run_once(x, y, a.maxo, None, None)
        G = [float(rec.get("Gii_max_cm3s", np.nan)) for rec in r.get("history", [])]
    else:
        phi0 = p0 = None; nchunk = math.ceil(a.maxo / a.chunk)
        for c in range(nchunk):
            r = run_once(x, y, a.chunk, phi0, p0)   # fresh Anderson each chunk
            G += [float(rec.get("Gii_max_cm3s", np.nan)) for rec in r.get("history", [])]
            phi0, p0 = r["phi"], r["p"]             # warm-start phi/p (continuous state)
    G = np.array(G)
    Gii = np.asarray(r["Gii"], float); jh, ih = np.unravel_index(int(np.argmax(Gii)), Gii.shape)
    last40 = G[-40:] if G.size >= 40 else G
    out = {"mode": a.mode, "maxo": a.maxo, "chunk": a.chunk, "threads": a.threads,
           "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
           "n_iter": int(G.size), "Gii_max_final": float(Gii.max()),
           "last40_drift": float((last40.max() - last40.min()) / last40.mean()) if last40.size else None,
           "hotspot_node_ij": [int(ih), int(jh)],
           "Gii_max_by_iter": [float(v) for v in G]}
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "driver_%s.json" % a.mode), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in ("mode", "n_iter", "Gii_max_final", "last40_drift", "hotspot_node_ij")}, indent=2))


if __name__ == "__main__":
    main()
