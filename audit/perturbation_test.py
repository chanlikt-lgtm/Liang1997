"""
perturbation_test.py -- single-platform nonlinear-SENSITIVITY experiment (audit reviewer's Test 1).

Injects a RELATIVE random perturbation (default 1e-16) into the SHE assembly
coefficients (A.data and b) on EVERY outer iteration, then runs the full 71x58
coupled loop from the identical cold start. seed=0 => control (no perturbation).

This is a SENSITIVITY probe, NOT a causal attribution: random 1e-16 noise is not
the structured, sign-correlated actual Windows-Linux coefficient difference.
- different certified plateaus => long-term sensitivity to THESE perturbations.
- same certified plateau    => robustness to THESE perturbations (NOT proof the
  real coefficient differences cannot produce the 12%).
- fail to certify           => convergence sensitivity, not a separate attractor.
Causal attribution needs cross-platform COEFFICIENT REPLAY (see audit notes).

Records (reviewer's requirements): exact perturbation def/seed; applied vs
rounded-away coefficient changes (frac changed, max/RMS rel) for A_data and b;
full Gii_max/Gtot/R_phi/last-4-spread/gate histories; final hotspot node + value;
certify status; post-gate continuation. Runtime monkeypatch only; no source edit.

  python audit/perturbation_test.py --maxo 400 --seed 1 --eps 1e-16 --post-gate 20
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
GATE = 3e-4


def build_mesh(Lx, Ly):
    xf = np.linspace(0.0, Lx, 8000)
    dens = 1.0 + (RATIO - 1.0) * np.exp(-((xf - X_C) / W) ** 2)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(xf))]); cum /= cum[-1]
    x = np.interp(np.linspace(0.0, 1.0, Nx), cum, xf); x[0], x[-1] = 0.0, Lx
    y = Ly * (np.linspace(0.0, 1.0, Ny) ** 1.8)
    return x, y


def applied_stats(orig, new):
    """relative change actually realized after FP rounding, vs intended."""
    orig = np.asarray(orig, float); new = np.asarray(new, float)
    nz = orig != 0
    rel = np.zeros_like(orig); rel[nz] = (new[nz] - orig[nz]) / orig[nz]
    changed = new != orig
    return {"n": int(orig.size), "frac_changed": float(np.count_nonzero(changed) / max(orig.size, 1)),
            "max_abs_rel_applied": float(np.max(np.abs(rel))) if orig.size else 0.0,
            "rms_rel_applied": float(np.sqrt(np.mean(rel ** 2))) if orig.size else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maxo", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0, help="0 = control (no perturbation)")
    ap.add_argument("--eps", type=float, default=1e-16)
    ap.add_argument("--post-gate", type=int, default=20, help="min outer iters to continue after first gate PASS (persistence check)")
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args()
    for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(k, str(a.threads))

    calls = [0]; first_perturb = {}
    if a.seed > 0:
        rng = np.random.default_rng(a.seed)
        _orig = she2d.SHE2D.assemble
        def patched(self, *args, **kw):
            _orig(self, *args, **kw)                       # sets self.A, self.b
            calls[0] += 1
            A = self.A.tocsr(copy=True)
            a_orig = A.data.copy(); b_orig = self.b.copy()
            A.data = a_orig * (1.0 + a.eps * rng.standard_normal(a_orig.size))
            self.A = A
            self.b = b_orig * (1.0 + a.eps * rng.standard_normal(b_orig.size))
            if not first_perturb:
                first_perturb["A_data"] = applied_stats(a_orig, A.data)
                first_perturb["b"] = applied_stats(b_orig, self.b)
            return self.A, self.b
        she2d.SHE2D.assemble = patched

    p = DeviceParams()
    x, y = build_mesh(p.Lx, p.Ly)
    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=a.maxo, tol_phi=TOL_PHI, verbose=False,
                      phi_init=None, p_init=None, phi_span_H_override=COMMON_PHI_SPAN)

    hist = r.get("history", [])
    G = np.array([float(rec.get("Gii_max_cm3s", np.nan)) for rec in hist])
    Gt = np.array([float(rec.get("G_tot_cm1s", np.nan)) for rec in hist])
    Rp = np.array([float(rec.get("max_dphi_V", np.nan)) for rec in hist])
    # rolling last-4 cumulative spread of Gii + gate status per iteration
    spread = np.full(G.size, np.nan); gate = [False] * G.size
    for i in range(3, G.size):
        w = G[i - 3:i + 1]
        spread[i] = (w.max() - w.min()) / w.mean()
        gate[i] = bool(spread[i] <= GATE and Rp[i] <= 1.5e-3)
    first_gate = next((i for i, g in enumerate(gate) if g), None)
    certified = first_gate is not None and (G.size - first_gate) >= a.post_gate

    Gii = np.asarray(r["Gii"], float)
    jh, ih = np.unravel_index(int(np.argmax(Gii)), Gii.shape)

    out = {
        "mode": "control" if a.seed == 0 else "perturbed", "seed": a.seed, "eps": a.eps,
        "threads": a.threads, "assemble_perturb_calls": calls[0],
        "perturbation_applied_first_iter": first_perturb,
        "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
        "n_outer": len(hist),
        "Gii_max_final": float(Gii.max()), "Gtot_final": float(Gt[-1]) if Gt.size else None,
        "R_phi_final": float(Rp[-1]) if Rp.size else None,
        "first_gate_iter": first_gate, "post_gate_iters": (G.size - first_gate) if first_gate is not None else 0,
        "certified_persistent": bool(certified),
        "hotspot_node_ij": [int(ih), int(jh)], "hotspot_xy_um": [float(r["x"][ih]), float(r["y"][jh])],
        "Gii_max_by_iter": [float(v) for v in G],
        "Gtot_by_iter": [float(v) for v in Gt],
        "R_phi_by_iter": [float(v) for v in Rp],
        "last4_spread_by_iter": [None if np.isnan(s) else float(s) for s in spread],
        "gate_by_iter": gate,
    }
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "perturb_seed%d.json" % a.seed), "w") as f:
        json.dump(out, f, indent=2)
    brief = {k: out[k] for k in ("mode", "seed", "assemble_perturb_calls", "perturbation_applied_first_iter",
                                 "Gii_max_final", "first_gate_iter", "post_gate_iters", "certified_persistent",
                                 "hotspot_node_ij", "n_outer")}
    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
