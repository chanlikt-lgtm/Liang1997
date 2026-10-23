"""
aniso_mesh_study.py -- anisotropic mesh-convergence study harness (Gate E part 1, SCI-01).

Reuses the FROZEN grading law (build_mesh) and the FROZEN coupled solver (solve_coupled)
BYTE-UNCHANGED from the self-similar driver, dropping ONLY the self-similar SEQUENCE guard.
Two orthogonal single-direction families (x-only, y-only refinement) separate the drain-x and
depth-y discretization errors that the self-similar trio structurally cannot.

Pre-registration: docs/ANISOTROPIC_MESH_STUDY_SPEC_V1.md (frozen BEFORE any run).  No physics,
solver, or acceptance change -- this is a mesh-count sweep in one direction.

Families (PRE-REGISTERED -- do not alter after seeing results):
  X-family: Ny=70 fixed, Nx in {71, 100, 141}   (refine drain-x)
  Y-family: Nx=100 fixed, Ny in {58, 70, 85}    (refine depth-y)
  Shared anchor (100,70) in both families (sanity / determinism cross-check).
  4th level (Nx=200 / Ny=120) -- PRE-COMMITTED decision rule (reviewer adj. 1): run it IFF
  (a) the 3rd level CERTIFIED (per spec §5) AND (b) its peak working set fits available RAM
  with no swap-thrash.  The decision is resource/convergence-based ONLY -- never outcome-based.

Certification (PRE-REGISTERED, spec §5) -- a node is CERTIFIED only if BOTH:
  (a) numerical residual: R_phi < 1e-4, with the scaled linear/continuity residual and
      relative_number_balance recorded at the endpoint; AND
  (b) observable stability: a 40-iteration stopping-disabled continuation shows raw AND
      interpolated Gii AND G_tot drift < 0.5%.
A sub-cell INTERPOLATED peak Gii (separable quadratic around the nodal max in x and y) is reported
ALONGSIDE the raw nodal Gii_max, hotspot in um (reviewer adj. 2).  A node that hangs on the inner
Krylov/ILU solve or fails R_phi<1e-4 within the 1500 cap is UNRESOLVED (recorded, not compared).

HOLD: the full family sweep is pre-registered but HELD until smoke evidence + reviewer authorization.
This harness is smoke-tested on the cheapest node (71x70) ONLY.

Usage:
  python campaign/aniso_mesh_study.py --list
  python campaign/aniso_mesh_study.py --node Nx Ny [maxouter]
  python campaign/aniso_mesh_study.py --family X|Y [--include-4th]   # HELD: do not run yet
"""
import os, sys, json, hashlib, subprocess, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from device import DeviceParams
from coupled_she import solve_coupled          # BYTE-UNCHANGED frozen solver
from she2d import EPS_MAX
from constants import eV

# ============================================================================
# FROZEN grading law + solver settings (byte-identical to coupled_drain_richardson.py)
# ============================================================================
RATIO, W, X_C = 6.0, 0.09, 0.60
PHI_GATE, AA_DEPTH, AA_BETA, AA_STEP_CAP, AA_RESTART = -0.74, 6, 0.5, 5.0, 6
SHE_TOL, DH_EV, TOL_PHI = 1e-8, 0.0125, 1e-4
EPS_MAX_EV = EPS_MAX / eV
COMMON_PHI_SPAN = (-0.60, 3.65)
REF_DEPTH = 0.02
MAX_OUTER_CAP = 1500          # spec: 1500-iteration safety cap -> UNRESOLVED beyond this
CONT_N_ITER = 40              # spec: 40-iteration stopping-disabled continuation
DRIFT_GATE = 0.005            # spec: < 0.5% observable drift

p = DeviceParams(); Lx, Ly = p.Lx, p.Ly

# ---- PRE-REGISTERED families (do not alter after seeing results) ----
FAMILIES = {
    "X": {"direction": "x-only (refine drain-x)", "fixed": "Ny=70",
          "levels": [(71, 70), (100, 70), (141, 70)], "fourth": (200, 70)},
    "Y": {"direction": "y-only (refine depth-y)", "fixed": "Nx=100",
          "levels": [(100, 58), (100, 70), (100, 85)], "fourth": (100, 120)},
}
ANCHOR = (100, 70)            # shared by both families


def _git(*a):
    try:
        return subprocess.check_output(["git", *a], cwd=os.path.dirname(__file__),
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "?"
_git_commit = _git("rev-parse", "--short", "HEAD")
_git_dirty = "dirty" if _git("status", "--porcelain") else "clean"


# ============================================================================
# BYTE-UNCHANGED mesh builders (copied verbatim from coupled_drain_richardson.py)
# ============================================================================
def dy_at(y, depth):
    """Local mesh interval size at a given depth [um] -- because y=s^1.8, dy grows with depth, so a
    surface-isotropic sequence is not automatically isotropic at the avalanche depth (user's caveat).
    Verifying dy(REF_DEPTH) also refines ~sqrt2 guards the G_tot (vertically-integrated) observable."""
    k = int(np.clip(np.searchsorted(y, depth) - 1, 0, len(y) - 2))
    return float(y[k + 1] - y[k])


def build_mesh(Nx, Ny):
    xf = np.linspace(0.0, Lx, 8000)
    dens = 1.0 + (RATIO - 1.0) * np.exp(-((xf - X_C) / W) ** 2)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(xf))]); cum /= cum[-1]
    x = np.interp(np.linspace(0.0, 1.0, Nx), cum, xf); x[0], x[-1] = 0.0, Lx
    y = Ly * (np.linspace(0.0, 1.0, Ny) ** 1.8)
    dxd = float(np.diff(x)[np.argmin(np.abs(0.5 * (x[:-1] + x[1:]) - X_C))])
    dys = float(np.diff(y).min())
    dyd = dy_at(y, REF_DEPTH)
    return x, y, dxd, dys, dyd


def _regrid_from_npz(warm_npz, x, y, Nx, Ny):
    """Interpolate phi,p from a warm-source npz onto the target mesh (same policy as the driver)."""
    prev = np.load(warm_npz)
    xo, yo = prev["x"], prev["y"]
    def regrid(F):
        tmp = np.empty((len(yo), Nx))
        for j in range(len(yo)):
            tmp[j] = np.interp(x, xo, F[j])
        out = np.empty((Ny, Nx))
        for i in range(Nx):
            out[:, i] = np.interp(y, yo, tmp[:, i])
        return out
    return regrid(prev["phi"]), regrid(prev["p"]), prev


# ============================================================================
# Sub-cell interpolated peak (reviewer adj. 2): separable quadratic around the nodal max
# ============================================================================
def _quad_vertex(xs, ys):
    """Vertex of the parabola through 3 points; returns (x_vertex, y_vertex). Falls back to the
    middle point if the fit is degenerate or the parabola opens up (a minimum, not a maximum)."""
    xs = np.asarray(xs, dtype=float); ys = np.asarray(ys, dtype=float)
    if len(xs) < 3 or np.ptp(xs) == 0.0 or np.ptp(ys) == 0.0:
        return float(xs[len(xs) // 2]), float(ys[len(ys) // 2])
    a, b, c = np.polyfit(xs, ys, 2)              # y = a x^2 + b x + c (exact through 3 pts)
    if a >= 0.0:                                  # opens up -> minimum; nodal max is the honest peak
        return float(xs[1]), float(ys[1])
    xv = float(np.clip(-b / (2.0 * a), xs.min(), xs.max()))
    return xv, float(a * xv * xv + b * xv + c)


def interpolated_peak(Gii, x, y):
    """Sub-cell peak via 1-D quadratic fits around the nodal max, in x and y separately.

    Returns (G_interp, x_interp_um, y_interp_um, nodal_j, nodal_i).  The separable vertex value
    is G(x*,y*) ~= Gx_fit(x*) + Gy_fit(y*) - G_nodal (each 1-D correction added once)."""
    Gii = np.asarray(Gii, dtype=float)
    jg, ig = np.unravel_index(int(np.argmax(Gii)), Gii.shape)
    Ny, Nx = Gii.shape
    ilo, ihi = max(0, ig - 1), min(Nx - 1, ig + 1)
    xv, gxv = _quad_vertex(x[ilo:ihi + 1], Gii[jg, ilo:ihi + 1])
    jlo, jhi = max(0, jg - 1), min(Ny - 1, jg + 1)
    yv, gyv = _quad_vertex(y[jlo:jhi + 1], Gii[jlo:jhi + 1, ig])
    g0 = float(Gii[jg, ig])
    return float(gxv + gyv - g0), float(xv), float(yv), int(jg), int(ig)


def _dxc_dyc(x, y):
    dxc = np.zeros(len(x)); dxc[1:-1] = 0.5 * (x[2:] - x[:-2]); dxc[0] = 0.5 * (x[1] - x[0]); dxc[-1] = 0.5 * (x[-1] - x[-2])
    dyc = np.zeros(len(y)); dyc[1:-1] = 0.5 * (y[2:] - y[:-2]); dyc[0] = 0.5 * (y[1] - y[0]); dyc[-1] = 0.5 * (y[-1] - y[-2])
    return dxc, dyc


def _avalanche_y_fwhm(Gii, y, ig, jg):
    """Vertical FWHM of Gii along the peak x-column (same definition as the driver)."""
    col = Gii[:, ig]
    half = 0.5 * col.max()
    below = np.where(col[jg:] < half)[0]
    j_fwhm = (jg + int(below[0])) if len(below) else len(y) - 1
    return float(y[min(j_fwhm, len(y) - 1)])


def _solve(Nx, Ny, max_outer, warm_npz=None, verbose=True):
    x, y, dx_drain, dy_surf, dy_depth = build_mesh(Nx, Ny)
    phi0 = p0 = None
    warm_name = ""
    if warm_npz and os.path.exists(warm_npz):
        phi0, p0, _prev = _regrid_from_npz(warm_npz, x, y, Nx, Ny)
        warm_name = os.path.basename(warm_npz)
    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=max_outer, tol_phi=TOL_PHI, verbose=verbose,
                      phi_init=phi0, p_init=p0, phi_span_H_override=COMMON_PHI_SPAN)
    return r, x, y, dx_drain, dy_surf, dy_depth, warm_name


def _extract_observables(r, x, y):
    h = r["history"]
    G = np.array([rec["Gii_max_cm3s"] for rec in h])
    Gt = np.array([rec["G_tot_cm1s"] for rec in h])
    n_iter = len(h)
    Gii = np.asarray(r["Gii"], dtype=float)
    dxc, dyc = _dxc_dyc(x, y)
    G_tot = float(np.sum(Gii * np.outer(dyc, dxc) * 1e-8))
    jg, ig = np.unravel_index(int(np.argmax(Gii)), Gii.shape)
    g_raw = float(Gii.max())
    g_interp, xv, yv, _, _ = interpolated_peak(Gii, x, y)
    y_fwhm = _avalanche_y_fwhm(Gii, y, ig, jg)
    R_phi = float(h[-1]["max_dphi_V"])
    spread = float((G[-4:].max() - G[-4:].min()) / G[-4:].mean())
    cons = r["conservation"]
    return dict(
        Gii_max=g_raw, Gii_interp=g_interp,
        xy_Gii_max=[float(x[ig]), float(y[jg])],
        xy_Gii_max_interp=[xv, yv],
        avalanche_y_fwhm=y_fwhm, G_tot=G_tot,
        drain_current_A_per_um=float(h[-1]["drain_current_A_per_um"]),
        R_phi=R_phi, dGii_tail=spread,
        relative_number_balance=float(h[-1]["relative_number_balance"]),
        continuity_residual=float(cons.get("scaled_linear_residual_inf", np.nan)),
        n_iter=n_iter, history_Gii=G, history_Gtot=Gt,
    )


def _continuation(phi, p, x, y):
    """40-iteration stopping-disabled continuation warm-started from the converged state."""
    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=CONT_N_ITER, tol_phi=0.0, verbose=False,
                      phi_init=phi, p_init=p, phi_span_H_override=COMMON_PHI_SPAN)
    return r


def _certify(obs, cont):
    """Pre-registered certification (spec §5). Returns (certified, status, detail)."""
    R_phi = obs["R_phi"]
    num_residual_ok = R_phi < TOL_PHI
    Gc = np.array([rec["Gii_max_cm3s"] for rec in cont["history"]])
    Gtc = np.array([rec["G_tot_cm1s"] for rec in cont["history"]])
    drift_raw = float((Gc.max() - Gc.min()) / Gc.mean())
    drift_tot = float((Gtc.max() - Gtc.min()) / Gtc.mean())
    g_interp_cont, _, _, _, _ = interpolated_peak(cont["Gii"], cont["x"], cont["y"])
    g_interp_main = obs["Gii_interp"]
    drift_interp = float(2.0 * abs(g_interp_cont - g_interp_main) / (g_interp_cont + g_interp_main))
    stability_ok = (drift_raw < DRIFT_GATE and drift_tot < DRIFT_GATE and drift_interp < DRIFT_GATE)
    certified = num_residual_ok and stability_ok
    status = "CERTIFIED" if certified else "UNRESOLVED"
    detail = ("R_phi=%.3e %s; drift raw_Gii=%.3e interp_Gii=%.3e G_tot=%.3e %s"
              % (R_phi, "<tol" if num_residual_ok else ">=tol",
                 drift_raw, drift_interp, drift_tot,
                 "<0.5%%" if stability_ok else ">=0.5%%"))
    return certified, status, detail, dict(drift_raw_Gii=drift_raw, drift_interp_Gii=drift_interp,
                                           drift_G_tot=drift_tot, cont_R_phi_band=[float(cont["history"][0]["max_dphi_V"]), float(cont["history"][-1]["max_dphi_V"])],
                                           cont_n_iter=len(cont["history"]))


def _save_npz(path, r, x, y, Nx, Ny, dx_drain, dy_surf, dy_depth, warm_name, obs, extra):
    she = r["she"]; NH = int(she.NH)
    Hmin, Hmax = float(she.H.min()) / eV, float(she.H.max()) / eV
    H_hash = hashlib.sha1(np.ascontiguousarray(she.H, dtype=np.float64).tobytes()).hexdigest()[:12]
    last4_G = obs["history_Gii"][-4:]; last4_Gt = obs["history_Gtot"][-4:]
    last4_R = np.array([rec["max_dphi_V"] for rec in r["history"][-4:]])
    np.savez(path,
             x=x, y=y, phi=r["phi"], n=r["n"], p=r["p"], Te=r["Te"], Gii=r["Gii"],
             vx=r["vx"], vy=r["vy"], F3d=r["F3d"].astype(np.float32), H=r["H"],
             Gamma_x_face=r["Gamma_x_face"], Gamma_y_face=r["Gamma_y_face"],
             Nx=Nx, Ny=Ny, ratio=RATIO, W=W, X_C=X_C, dH_eV=DH_EV, eps_max_eV=EPS_MAX_EV,
             she_tol=SHE_TOL, NH=NH, Hmin=Hmin, Hmax=Hmax, H_hash=H_hash,
             common_phi_span=np.array(COMMON_PHI_SPAN), n_iter=obs["n_iter"],
             git_commit=_git_commit, git_dirty=_git_dirty, warm_source=warm_name,
             drain_dx=dx_drain, surface_dy=dy_surf, dy_depth=dy_depth, ref_depth=REF_DEPTH,
             avalanche_y_fwhm=obs["avalanche_y_fwhm"], h_rep=float(np.sqrt(dx_drain * dy_surf)),
             Gii_max=obs["Gii_max"], Gii_interp=obs["Gii_interp"], G_tot=obs["G_tot"],
             Te_max=float(r["Te"].max()), xy_Gii_max=np.array(obs["xy_Gii_max"]),
             xy_Gii_max_interp=np.array(obs["xy_Gii_max_interp"]),
             drain_current_A_per_um=obs["drain_current_A_per_um"],
             continuity_residual=obs["continuity_residual"],
             relative_number_balance=obs["relative_number_balance"],
             R_phi=obs["R_phi"], dGii_tail=obs["dGii_tail"],
             last4_Gii_max=last4_G, last4_G_tot=last4_Gt, last4_R_phi=last4_R,
             mean4_Gii_max=float(last4_G.mean()), mean4_G_tot=float(np.nanmean(last4_Gt)),
             spread=float((last4_G.max() - last4_G.min()) / last4_G.mean()),
             spread_Gtot=float((np.nanmax(last4_Gt) - np.nanmin(last4_Gt)) / np.nanmean(last4_Gt)),
             **extra)
    return H_hash


def run_node(Nx, Ny, max_outer=MAX_OUTER_CAP, warm_npz=None, verbose=True, outdir=None):
    outdir = outdir or os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(outdir, exist_ok=True)
    tag = "she2d_aniso_%dx%d" % (Nx, Ny)
    npz_path = os.path.join(outdir, tag + ".npz")
    json_path = os.path.join(outdir, tag + ".json")

    print("=" * 78)
    print("ANISO MESH-STUDY NODE: Nx=%d Ny=%d  (max_outer=%d, tol_phi=%.1e)" % (Nx, Ny, max_outer, TOL_PHI))
    print("  mesh law: ratio=%.3f W=%.3f X_C=%.3f (x graded, y=Ly*s^1.8); solver Phi_gate=%.3f, anderson d=%d b=%.2f"
          % (RATIO, W, X_C, PHI_GATE, AA_DEPTH, AA_BETA))
    print("  provenance: git %s (%s)" % (_git_commit, _git_dirty), flush=True)

    r, x, y, dx_drain, dy_surf, dy_depth, warm_name = _solve(Nx, Ny, max_outer, warm_npz, verbose)

    # HARD FAIL (same as the frozen driver): the converged phi must stay inside the imposed common
    # span, else the frozen H-grid no longer bounds the final solution's energy domain.
    _pmin, _pmax = float(r["phi"].min()), float(r["phi"].max())
    if _pmin < COMMON_PHI_SPAN[0] or _pmax > COMMON_PHI_SPAN[1]:
        raise SystemExit("ABORT: converged phi [%.4f, %.4f] V leaves COMMON_PHI_SPAN %s V."
                         % (_pmin, _pmax, COMMON_PHI_SPAN))

    obs = _extract_observables(r, x, y)

    # 40-iteration continuation (observable stability, spec §5(b))
    cont = _continuation(r["phi"], r["p"], x, y)
    certified, status, detail, drift = _certify(obs, cont)

    extra = dict(status=status, certified=certified, max_outer=max_outer,
                 tol_phi=TOL_PHI, cont_n_iter=drift["cont_n_iter"],
                 drift_raw_Gii=drift["drift_raw_Gii"], drift_interp_Gii=drift["drift_interp_Gii"],
                 drift_G_tot=drift["drift_G_tot"], cont_R_phi_band=np.array(drift["cont_R_phi_band"]))
    H_hash = _save_npz(npz_path, r, x, y, Nx, Ny, dx_drain, dy_surf, dy_depth, warm_name, obs, extra)

    rec = dict(Nx=Nx, Ny=Ny, family=None, direction=None, level=None, warm_source=warm_name,
               status=status, certified=certified, certification=detail,
               git_commit=_git_commit, git_dirty=_git_dirty, H_hash=H_hash,
               drain_dx=dx_drain, surface_dy=dy_surf, dy_depth=dy_depth, ref_depth=REF_DEPTH,
               **{k: obs[k] for k in ("Gii_max", "Gii_interp", "xy_Gii_max", "xy_Gii_max_interp",
                                      "avalanche_y_fwhm", "G_tot", "drain_current_A_per_um", "R_phi",
                                      "dGii_tail", "relative_number_balance", "continuity_residual",
                                      "n_iter")},
               **drift, npz=os.path.relpath(npz_path, outdir), json_path=os.path.relpath(json_path, outdir))
    with open(json_path, "w") as fh:
        json.dump(rec, fh, indent=2)
    print("\n=== NODE %dx%d -> %s  (R_phi=%.3e, Gii_raw=%.4e, Gii_interp=%.4e, G_tot=%.4e) ==="
          % (Nx, Ny, status, obs["R_phi"], obs["Gii_max"], obs["Gii_interp"], obs["G_tot"]))
    print("    %s" % detail)
    print("    saved %s + %s" % (npz_path, json_path))
    return rec


def run_family(name, include_fourth=False):
    fam = FAMILIES[name]
    levels = list(fam["levels"])
    records = []
    warm = None
    for i, (Nx, Ny) in enumerate(levels):
        rec = run_node(Nx, Ny, warm_npz=warm, verbose=True)
        rec["family"] = name; rec["direction"] = fam["direction"]; rec["level"] = i
        records.append(rec)
        if rec["certified"]:
            warm = rec["npz"]
    # 4th level -- pre-committed resource/convergence gate (reviewer adj. 1)
    if include_fourth:
        third_certified = records[-1]["certified"] if records else False
        if third_certified:
            Nx4, Ny4 = fam["fourth"]
            rec = run_node(Nx4, Ny4, warm_npz=warm, verbose=True)
            rec["family"] = name; rec["direction"] = fam["direction"]; rec["level"] = len(levels)
            records.append(rec)
        else:
            print("4th level SKIPPED: 3rd level not certified (resource/convergence gate).")
    return records


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or argv[0] == "--list":
        print("Pre-registered families (docs/ANISOTROPIC_MESH_STUDY_SPEC_V1.md):")
        for name, fam in FAMILIES.items():
            print("  %s-family: %s  levels=%s  fourth=%s  anchor=%s"
                  % (name, fam["direction"], fam["levels"], fam["fourth"], ANCHOR))
        print("Certification: R_phi<1e-4 AND 40-iter drift<0.5%% (raw+interp Gii, G_tot).")
        print("HELD: full sweep not run without explicit instruction.")
        sys.exit(0)
    if argv[0] == "--node":
        Nx, Ny = int(argv[1]), int(argv[2])
        maxo = int(argv[3]) if len(argv) > 3 else MAX_OUTER_CAP
        run_node(Nx, Ny, max_outer=maxo)
    elif argv[0] == "--family":
        name = argv[1].upper()
        run_family(name, include_fourth=("--include-4th" in argv))
    else:
        sys.exit("usage: --list | --node Nx Ny [maxouter] | --family X|Y [--include-4th]")
