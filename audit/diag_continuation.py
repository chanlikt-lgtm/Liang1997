"""audit/diag_continuation.py -- P2/P3 diagnostic continuation (read-only).

Loads a converged node state, continues N extra outer iters with stopping
DISABLED (tol_phi=0), reports R_phi / Gii_max / Gtot / balance / drain-current
over the window, and independently recomputes R_phi from the saved state (one
fresh fixed-point application, outside the original stopping logic).

CORRECTED history keys (confirmed from a real run):
  R_phi -> max_dphi_V | Gii -> Gii_max_cm3s | Gtot -> G_tot_cm1s |
  balance -> relative_number_balance | terminal current -> drain_current_A_per_um

Usage:
  python audit/diag_continuation.py data/she2d_richardson_71x58.npz --extra 100
"""
from __future__ import annotations
import os, sys, json, argparse
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from coupled_she import solve_coupled

PHI_GATE, AA_DEPTH, AA_BETA, AA_STEP_CAP = -0.74, 6, 0.5, 5.0
SHE_TOL, DH_EV = 1e-8, 0.0125
COMMON_PHI_SPAN = (-0.60, 3.65)


def run(x, y, phi0, p0, maxo, tol):
    return solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson",
        aa_depth=AA_DEPTH, aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True,
        dH_eV=DH_EV, she_tol=SHE_TOL, max_outer=maxo, tol_phi=tol, verbose=False,
        phi_init=phi0, p_init=p0, phi_span_H_override=COMMON_PHI_SPAN)


def series(H, *keys):
    for k in keys:
        if H and k in H[0]:
            return np.array([float(h.get(k, np.nan)) for h in H]), k
    return np.array([]), None


def stats(v):
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None
    return dict(min=float(v.min()), med=float(np.median(v)), max=float(v.max()),
                mean=float(v.mean()), drift=float((v.max() - v.min()) / v.mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz")
    ap.add_argument("--extra", type=int, default=100)
    ap.add_argument("--out", default="audit")
    a = ap.parse_args()
    d = np.load(a.npz, allow_pickle=True)
    x, y, phi0, p0 = d["x"], d["y"], d["phi"], d["p"]
    tag = os.path.basename(a.npz).replace(".npz", "")

    # (A) independent R_phi recompute at the saved state (one fresh iteration)
    h1 = run(x, y, phi0, p0, 1, 0.0).get("history", [])
    print("history record keys:", sorted(h1[0].keys()) if h1 else "(none)")
    rphi_recap = float(h1[0].get("max_dphi_V", np.nan)) if h1 else float("nan")

    # (B) diagnostic continuation: N extra iters, stopping disabled
    H = run(x, y, phi0, p0, a.extra, 0.0).get("history", [])
    rphi, kphi = series(H, "max_dphi_V", "R_phi")
    gii, kgii = series(H, "Gii_max_cm3s", "Gii_max")
    gtot, kgt = series(H, "G_tot_cm1s", "G_tot")
    bal, kbal = series(H, "relative_number_balance", "bal")
    idr, kidr = series(H, "drain_current_A_per_um")

    out = dict(tag=tag, extra=a.extra,
               keys=dict(rphi=kphi, gii=kgii, gtot=kgt, bal=kbal, idrain=kidr),
               rphi_recompute_at_saved_state=rphi_recap,
               rphi_excursions_above_tol=int((rphi > 1e-4).sum()) if rphi.size else None,
               R_phi=stats(rphi), Gii_max=stats(gii), G_tot=stats(gtot),
               balance=stats(bal), drain_current=stats(idr),
               rphi_series=[float(v) for v in rphi], gii_series=[float(v) for v in gii])
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "diag_cont_LINUX_%s.json" % tag), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in ("tag", "keys", "rphi_recompute_at_saved_state",
        "rphi_excursions_above_tol", "R_phi", "Gii_max", "G_tot", "balance", "drain_current")}, indent=2))


if __name__ == "__main__":
    main()
