"""
probe_fp.py -- platform floating-point reproducibility probe (71x58).

Runs the REAL coupled SHE solve for a few CAPPED outer iterations from the
identical cold start (same frozen settings as coupled_drain_richardson.py),
then fingerprints the result. The mesh input is built from element-wise numpy
ops (bit-identical across OS), so any divergence in Gii/phi across platforms is
the platform numerical stack (BLAS/LAPACK/SuperLU), which is the hypothesis.

Run IDENTICALLY on Windows and Linux (same --maxo):
    python probe_fp.py --maxo 4 --tag windows
    python probe_fp.py --maxo 4 --tag linux
Each writes probe_<tag>.json (fingerprints) + probe_<tag>.npz (full arrays).
Diff the two .npz element-wise to see the ~1e-12 seed grow per iteration.
Numerically inert: a diagnostic, does not touch the solver or the trio data.
"""
from __future__ import annotations
import os, sys, json, hashlib, platform, argparse
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import scipy
from device import DeviceParams
from coupled_she import solve_coupled
from she2d import EPS_MAX
from constants import eV

# --- frozen settings, identical to coupled_drain_richardson.py ---
RATIO, W, X_C = 6.0, 0.09, 0.60
PHI_GATE, AA_DEPTH, AA_BETA, AA_STEP_CAP = -0.74, 6, 0.5, 5.0
SHE_TOL, DH_EV, TOL_PHI = 1e-8, 0.0125, 1e-4
COMMON_PHI_SPAN = (-0.60, 3.65)
Nx, Ny = 71, 58


def build_mesh(Lx, Ly, Nx, Ny):
    xf = np.linspace(0.0, Lx, 8000)
    dens = 1.0 + (RATIO - 1.0) * np.exp(-((xf - X_C) / W) ** 2)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(xf))]); cum /= cum[-1]
    x = np.interp(np.linspace(0.0, 1.0, Nx), cum, xf); x[0], x[-1] = 0.0, Lx
    y = Ly * (np.linspace(0.0, 1.0, Ny) ** 1.8)
    return x, y


def h64(a):
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()[:16]


def blas_fingerprint():
    info = {}
    try:
        cfg = np.show_config(mode="dicts")
        bd = cfg.get("Build Dependencies", {})
        for k in ("blas", "lapack"):
            if k in bd:
                info[k] = {kk: bd[k].get(kk) for kk in ("name", "version", "pc file directory") if kk in bd[k]}
    except Exception as e:
        info["show_config_error"] = repr(e)
    try:
        import threadpoolctl
        info["threadpool"] = [{kk: d.get(kk) for kk in ("internal_api", "version", "num_threads", "threading_layer")}
                              for d in threadpoolctl.threadpool_info()]
    except Exception:
        info["threadpool"] = "threadpoolctl not installed"
    info["env_threads"] = {k: os.environ.get(k) for k in
                           ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "SHE2D_DISABLE_NUMBA")}
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maxo", type=int, default=4)
    ap.add_argument("--tag", default=platform.system().lower())
    a = ap.parse_args()

    p = DeviceParams()
    x, y = build_mesh(p.Lx, p.Ly, Nx, Ny)

    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=a.maxo, tol_phi=TOL_PHI, verbose=False,
                      phi_init=None, p_init=None, phi_span_H_override=COMMON_PHI_SPAN)

    Gii = np.asarray(r["Gii"], float); phi = np.asarray(r["phi"], float)
    H = np.asarray(r["H"], float)
    hist = r.get("history", [])
    G_by_iter = [float(rec.get("Gii_max_cm3s", np.nan)) for rec in hist]

    out = {
        "tag": a.tag, "max_outer": a.maxo, "Nx": Nx, "Ny": Ny,
        "platform": platform.platform(), "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "blas": blas_fingerprint(),
        "mesh_x_hash": h64(x), "mesh_y_hash": h64(y),
        "H_hash": hashlib.sha1(np.ascontiguousarray(H, dtype=np.float64).tobytes()).hexdigest()[:12],
        "n_outer_ran": len(hist),
        "Gii_max_by_iter": G_by_iter,
        "Gii_max": float(Gii.max()),
        "Gii_hash": h64(Gii), "phi_hash": h64(phi),
        "Gii_l2": float(np.sqrt(np.sum(Gii ** 2))), "phi_l2": float(np.sqrt(np.sum(phi ** 2))),
        "Gii_first8": [float(v) for v in Gii.ravel()[:8]],
        "phi_first8": [float(v) for v in phi.ravel()[:8]],
    }
    here = os.path.dirname(os.path.abspath(__file__))
    jpath = os.path.join(here, "probe_%s.json" % a.tag)
    npath = os.path.join(here, "probe_%s.npz" % a.tag)
    with open(jpath, "w") as f:
        json.dump(out, f, indent=2)
    np.savez(npath, Gii=Gii, phi=phi, x=x, y=y, H=H, Gii_max_by_iter=np.array(G_by_iter))
    print(json.dumps(out, indent=2))
    print("\nwrote %s and %s" % (os.path.basename(jpath), os.path.basename(npath)))


if __name__ == "__main__":
    main()
