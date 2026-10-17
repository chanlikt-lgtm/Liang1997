"""
perturbation_test.py -- single-platform nonlinear-sensitivity test (audit reviewer's Test 1).

Injects a ~1e-16 RELATIVE random perturbation into the SHE assembly coefficients
(A.data and b) on EVERY outer iteration, then runs the full 71x58 coupled loop
from the identical cold start. If small (rounding-scale) perturbations with
different seeds reach different Gii plateaus, that is direct evidence the nonlinear
map amplifies a ~1e-16 seed -- the proposed mechanism for the -12% cross-platform
difference. seed=0 => control (no perturbation). Numerically a diagnostic; edits
nothing in the frozen tree (monkeypatch at runtime only).

  python audit/perturbation_test.py --maxo 3 --seed 1 --eps 1e-16
"""
from __future__ import annotations
import os, sys, json, argparse, platform
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import scipy
import she2d
from device import DeviceParams
from coupled_she import solve_coupled

RATIO, W, X_C = 6.0, 0.09, 0.60
PHI_GATE, AA_DEPTH, AA_BETA, AA_STEP_CAP = -0.74, 6, 0.5, 5.0
SHE_TOL, DH_EV, TOL_PHI = 1e-8, 0.0125, 1e-4
COMMON_PHI_SPAN = (-0.60, 3.65)
Nx, Ny = 71, 58


def build_mesh(Lx, Ly):
    xf = np.linspace(0.0, Lx, 8000)
    dens = 1.0 + (RATIO - 1.0) * np.exp(-((xf - X_C) / W) ** 2)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(xf))]); cum /= cum[-1]
    x = np.interp(np.linspace(0.0, 1.0, Nx), cum, xf); x[0], x[-1] = 0.0, Lx
    y = Ly * (np.linspace(0.0, 1.0, Ny) ** 1.8)
    return x, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maxo", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0, help="0 = control (no perturbation)")
    ap.add_argument("--eps", type=float, default=1e-16)
    a = ap.parse_args()

    calls = [0]
    if a.seed > 0:
        rng = np.random.default_rng(a.seed)
        _orig = she2d.SHE2D.assemble
        def patched(self, *args, **kw):
            _orig(self, *args, **kw)                       # sets self.A, self.b
            calls[0] += 1
            A = self.A.tocsr(copy=True)
            A.data = A.data * (1.0 + a.eps * rng.standard_normal(A.data.size))
            self.A = A
            self.b = self.b * (1.0 + a.eps * rng.standard_normal(self.b.size))
            return self.A, self.b
        she2d.SHE2D.assemble = patched

    p = DeviceParams()
    x, y = build_mesh(p.Lx, p.Ly)
    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=a.maxo, tol_phi=TOL_PHI, verbose=False,
                      phi_init=None, p_init=None, phi_span_H_override=COMMON_PHI_SPAN)
    hist = r.get("history", [])
    G = [float(rec.get("Gii_max_cm3s", float("nan"))) for rec in hist]
    out = {"mode": "control" if a.seed == 0 else "perturbed", "seed": a.seed, "eps": a.eps,
           "maxo": a.maxo, "assemble_perturb_calls": calls[0],
           "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
           "Gii_max_by_iter": G, "Gii_max_final": float(np.asarray(r["Gii"]).max()),
           "n_outer": len(hist)}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
