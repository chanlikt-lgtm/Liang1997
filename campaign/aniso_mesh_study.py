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
  Shared anchor (100,70) in both families -> run INDEPENDENTLY once per family (distinct warm-chains:
  X from 71x70, Y from 100x58), retained as SEPARATE artifacts, and compared as a reproducibility /
  warm-path cross-check (G1.6).  It is NOT a single shared computation.
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
import os, sys

# ---- thread policy (spec v1.2 / reviewer G1.2): pin env BEFORE any BLAS/OpenMP loads ----
def _threads_from_argv(argv):
    if "--threads" in argv:
        i = argv.index("--threads")
        try:
            return int(argv[i + 1])
        except (IndexError, ValueError):
            raise SystemExit("--threads requires an integer argument")
    return 8

THREADS_REQUESTED = _threads_from_argv(sys.argv)
for _tv in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_tv] = str(THREADS_REQUESTED)

import json, hashlib, subprocess, time, platform, resource
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

# ---- Pre-registered certification criteria (G2.1, spec v1.4) ----------------
# A node is CERTIFIED only if EVERY criterion passes (never R_phi alone -- G2.3).  Each criterion is
# recorded per-node with its raw value, unit, normalization, and explicit PASS/FAIL.
CONTINUITY_RESIDUAL_GATE = 1e-6    # scaled linear residual of the final SHE solve (< 1e-6, relative)
NUMBER_BALANCE_GATE = 1e-2         # |relative_number_balance| < 1% (particle conservation)
HOTSPOT_DRIFT_CELLS = 0.5          # G2.3: hotspot (x,y) stable to within half a representative cell

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


# ---- config identity + execution authorization + provenance (G0.2/G1.2/G1.3) ----
AUTH_FILE = os.path.join(os.path.dirname(__file__), "aniso_exec_auth.json")


def _config_hash():
    cfg = dict(ratio=RATIO, W=W, X_C=X_C, phi_gate=PHI_GATE, aa_depth=AA_DEPTH, aa_beta=AA_BETA,
               she_tol=SHE_TOL, dH_eV=DH_EV, tol_phi=TOL_PHI, cont_n_iter=CONT_N_ITER,
               drift_gate=DRIFT_GATE, common_phi_span=list(COMMON_PHI_SPAN), ref_depth=REF_DEPTH,
               solver_commit=_git_commit)
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]


def _exec_auth():
    if not os.path.exists(AUTH_FILE):
        return None
    try:
        with open(AUTH_FILE) as fh:
            return json.load(fh)
    except Exception:
        return None


def _require_exec_auth():
    a = _exec_auth()
    if not (a and a.get("execution_authorized") is True):
        raise SystemExit(
            "G0.2 HARD-BLOCK: full-sweep execution is NOT authorized. The anisotropic sweep is HELD "
            "until Gates 0-3 PASS with evidence (docs/ANISO_STUDY_REVIEW_CHECKPOINT_20261023.md). "
            "To authorize, write %s with {\"execution_authorized\": true, \"who\": ..., \"when\": ...}."
            % AUTH_FILE)
    return a


def _provenance():
    info = {
        "threads_requested": THREADS_REQUESTED,
        "threads_env": {v: os.environ.get(v) for v in
                        ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
        "numpy_version": np.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": platform.processor() or None,
        "git_commit": _git_commit,
        "git_dirty": _git_dirty,
    }
    try:
        import threadpoolctl
        info["threadpool_actual"] = [
            dict(library=t.get("user_api"), internal_api=t.get("internal_api"),
                 num_threads=t.get("num_threads"), prefix=t.get("prefix"),
                 version=t.get("version"), threading_layer=t.get("threading_layer"))
            for t in threadpoolctl.threadpool_info()]
    except Exception as e:  # pragma: no cover
        info["threadpool_actual"] = "unavailable: %s" % e
    return info


# ============================================================================
# G1.4: measured RAM / resource feasibility gate for the optional 4th level
# ============================================================================
def _peak_rss_bytes():
    """Peak resident set size of THIS process so far, in bytes (Linux ru_maxrss is in KiB)."""
    try:
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except Exception:
        return None


def _available_ram_bytes():
    """Available physical RAM (MemAvailable) in bytes, or None if unreadable."""
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    return None


def resource_gate(prev_peak_rss, prev_mesh, next_mesh, safety=1.5):
    """G1.4: decide whether the 4th level fits RAM without swap-thrash.

    Predicts the 4th-level peak working set by scaling the measured 3rd-level peak RSS by the cell-count
    ratio, and requires it to fit available RAM with `safety` headroom.  Returns (approved, decision dict).
    Resource/convergence-based ONLY -- never outcome-based (spec §3)."""
    avail = _available_ram_bytes()
    ratio = (next_mesh[0] * next_mesh[1]) / (prev_mesh[0] * prev_mesh[1])
    predicted = (prev_peak_rss * ratio) if prev_peak_rss else None
    decision = dict(
        prev_mesh=list(prev_mesh), next_mesh=list(next_mesh), cell_ratio=float(ratio),
        prev_peak_rss_bytes=prev_peak_rss, available_ram_bytes=avail,
        predicted_4th_rss_bytes=predicted, safety_margin=safety,
    )
    if prev_peak_rss is None or avail is None or predicted is None:
        decision["approved"] = False
        decision["reason"] = "resource measurement unavailable (peak RSS or MemAvailable)"
        return False, decision
    decision["approved"] = bool(predicted * safety < avail)
    decision["reason"] = ("predicted_4th_rss=%.1f GiB x%.1f %s available %.1f GiB"
                          % (predicted / 2**30, safety,
                             "fits" if decision["approved"] else "EXCEEDS", avail / 2**30))
    return decision["approved"], decision


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


def _profile_fwhm_2cross(profile, coords):
    """G1.5: physical FWHM from TWO interpolated half-maximum crossings + quality flags.

    Distinguishes a valid full width from a boundary-truncated, unresolved, or multi-peak profile.
    Returns a dict: fwhm (always float), left_x, right_x, peak_idx, and the three quality flags."""
    profile = np.asarray(profile, dtype=float)
    coords = np.asarray(coords, dtype=float)
    n = len(profile)
    pk = int(np.argmax(profile))
    half = 0.5 * float(profile.max())
    if n < 3:
        return dict(fwhm=float(coords[-1] - coords[0]), left_x=float(coords[0]),
                    right_x=float(coords[-1]), peak_idx=pk,
                    boundary_truncated=True, unresolved=True, multi_peak=False)

    above = profile > half
    maxima = (profile[1:-1] >= profile[:-2]) & (profile[1:-1] >= profile[2:])
    multi_peak = int(np.count_nonzero(maxima & above[1:-1])) >= 2

    def _cross(lo, hi):
        # linear interpolation of the half-max coordinate between adjacent nodes lo, hi
        f0, f1 = profile[lo], profile[hi]
        x0, x1 = coords[lo], coords[hi]
        if f0 == f1:
            return 0.5 * (x0 + x1)
        return x0 + (half - f0) * (x1 - x0) / (f1 - f0)

    boundary_truncated = False
    left_x = None
    for i in range(pk, 0, -1):
        if profile[i - 1] < half:
            left_x = _cross(i, i - 1)
            break
    if left_x is None:
        left_x = float(coords[0]); boundary_truncated = True

    right_x = None
    for i in range(pk, n - 1):
        if profile[i + 1] < half:
            right_x = _cross(i, i + 1)
            break
    if right_x is None:
        right_x = float(coords[-1]); boundary_truncated = True

    cell_lo = float(coords[max(pk - 1, 0)])
    cell_hi = float(coords[min(pk + 1, n - 1)])
    unresolved = (not boundary_truncated) and (right_x - left_x) <= (cell_hi - cell_lo)
    return dict(fwhm=float(right_x - left_x), left_x=float(left_x), right_x=float(right_x),
                peak_idx=pk, boundary_truncated=boundary_truncated,
                unresolved=unresolved, multi_peak=multi_peak)


def _avalanche_y_fwhm(Gii, y, ig, jg):
    """Vertical FWHM of Gii along the peak x-column (two interpolated crossings, G1.5)."""
    return _profile_fwhm_2cross(Gii[:, ig], y)["fwhm"]


def _solve(Nx, Ny, max_outer, warm_npz=None, verbose=True):
    x, y, dx_drain, dy_surf, dy_depth = build_mesh(Nx, Ny)
    phi0 = p0 = None
    warm_name = ""
    if warm_npz:
        wp = os.path.abspath(warm_npz)          # G1.1: resolve relative-to-outdir or absolute
        if not os.path.exists(wp):
            raise SystemExit("G1.1 HARD-FAIL: warm-start npz not found: %s "
                             "(no silent cold-start fallback)." % wp)
        print("  warm-start: %s (exists -> loading + regridding)" % wp, flush=True)
        phi0, p0, _prev = _regrid_from_npz(wp, x, y, Nx, Ny)
        warm_name = os.path.basename(wp)
    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=max_outer, tol_phi=TOL_PHI, verbose=verbose,
                      phi_init=phi0, p_init=p0, phi_span_H_override=COMMON_PHI_SPAN)
    return r, x, y, dx_drain, dy_surf, dy_depth, warm_name


def _local_rep_spacing(x, y):
    """Representative spacing h_rep = sqrt(dx_drain * dy_surf), same def as build_mesh returns."""
    idx = int(np.argmin(np.abs(0.5 * (x[:-1] + x[1:]) - X_C)))
    dx_drain = float(x[idx + 1] - x[idx])
    dy_surf = float(np.diff(y).min())
    return float(np.sqrt(dx_drain * dy_surf))


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
    fwhm_info = _profile_fwhm_2cross(Gii[:, ig], y)   # G1.5: two interpolated crossings + flags
    y_fwhm = fwhm_info["fwhm"]
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
        h_rep=_local_rep_spacing(x, y),
        fwhm_flags=dict(boundary_truncated=fwhm_info["boundary_truncated"],
                        unresolved=fwhm_info["unresolved"],
                        multi_peak=fwhm_info["multi_peak"],
                        left_x=fwhm_info["left_x"], right_x=fwhm_info["right_x"],
                        peak_idx=fwhm_info["peak_idx"]),
    )


def _continuation(phi, p, x, y):
    """40-iteration stopping-disabled continuation warm-started from the converged state."""
    r = solve_coupled(x_mesh=x, y_mesh=y, Phi_gate=PHI_GATE, accel="anderson", aa_depth=AA_DEPTH,
                      aa_beta=AA_BETA, aa_step_cap=AA_STEP_CAP, freeze_H=True, dH_eV=DH_EV,
                      she_tol=SHE_TOL, max_outer=CONT_N_ITER, tol_phi=0.0, verbose=False,
                      phi_init=phi, p_init=p, phi_span_H_override=COMMON_PHI_SPAN)
    return r


def _certify(obs, cont):
    """Pre-registered certification (spec §5 + G2.1-G2.3). Returns (certified, status, detail, report).

    report keys:
      criteria         : list of {name, value, gate, op, unit, norm, passed} -- one per numerical criterion
      drift_raw/interp_Gii/G_tot   : 40-iter continuation spread/endpoint-delta (observable stability)
      restart_delta_raw_Gii/G_tot  : endpoint -> restart jump (fresh solve_coupled = empty Anderson history)
      hotspot_drift_um/cells       : peak-Gii hotspot (x,y) stability over the continuation
      continuation_state           : Anderson / preconditioner state carried into the continuation
      cont_R_phi_band / cont_n_iter
    """
    R_phi = obs["R_phi"]
    Gc = np.array([rec["Gii_max_cm3s"] for rec in cont["history"]])
    Gtc = np.array([rec["G_tot_cm1s"] for rec in cont["history"]])
    cont_n = len(cont["history"])

    drift_raw = float((Gc.max() - Gc.min()) / Gc.mean()) if Gc.mean() else 0.0
    drift_tot = float((Gtc.max() - Gtc.min()) / Gtc.mean()) if Gtc.mean() else 0.0
    g_interp_cont, xc, yc, _, _ = interpolated_peak(cont["Gii"], cont["x"], cont["y"])
    g_interp_main = obs["Gii_interp"]
    drift_interp = float(2.0 * abs(g_interp_cont - g_interp_main) / (g_interp_cont + g_interp_main)) \
        if (g_interp_cont + g_interp_main) else 0.0

    # G2.2: endpoint -> restart delta (fresh solve_coupled = empty Anderson history) vs continuation drift
    main_last_G = float(obs["history_Gii"][-1])
    main_last_Gt = float(obs["history_Gtot"][-1])
    restart_raw = float(abs(Gc[0] - main_last_G) / main_last_G) if main_last_G else 0.0
    restart_tot = float(abs(Gtc[0] - main_last_Gt) / main_last_Gt) if main_last_Gt else 0.0

    # G2.3: hotspot (x,y) stability (peak-Gii interpolated location) over the continuation
    hx_main, hy_main = obs["xy_Gii_max_interp"]
    h_rep = obs["h_rep"]
    hotspot_drift_um = float(np.hypot(xc - hx_main, yc - hy_main))
    hotspot_drift_cells = float(hotspot_drift_um / h_rep) if h_rep else float("nan")

    criteria = [
        dict(name="R_phi", value=R_phi, gate=1e-4, op="<", unit="V", norm="absolute",
             passed=R_phi < TOL_PHI),
        dict(name="continuity_residual", value=obs["continuity_residual"], gate=CONTINUITY_RESIDUAL_GATE,
             op="<", unit="1", norm="scaled by max(|bs|,1)",
             passed=obs["continuity_residual"] < CONTINUITY_RESIDUAL_GATE),
        dict(name="number_balance", value=obs["relative_number_balance"], gate=NUMBER_BALANCE_GATE,
             op="<", unit="1", norm="|balance|/scale (absolute)",
             passed=abs(obs["relative_number_balance"]) < NUMBER_BALANCE_GATE),
        dict(name="drift_raw_Gii", value=drift_raw, gate=DRIFT_GATE, op="<", unit="1",
             norm="40-iter continuation spread", passed=drift_raw < DRIFT_GATE),
        dict(name="drift_interp_Gii", value=drift_interp, gate=DRIFT_GATE, op="<", unit="1",
             norm="40-iter continuation endpoint delta", passed=drift_interp < DRIFT_GATE),
        dict(name="drift_G_tot", value=drift_tot, gate=DRIFT_GATE, op="<", unit="1",
             norm="40-iter continuation spread", passed=drift_tot < DRIFT_GATE),
        dict(name="hotspot_drift", value=hotspot_drift_cells, gate=HOTSPOT_DRIFT_CELLS, op="<",
             unit="cell", norm="|cont hotspot - main hotspot| / h_rep",
             passed=np.isfinite(hotspot_drift_cells) and hotspot_drift_cells < HOTSPOT_DRIFT_CELLS),
    ]
    certified = all(c["passed"] for c in criteria)
    status = "CERTIFIED" if certified else "UNRESOLVED"
    detail = "; ".join("%s=%.3e%s" % (c["name"], c["value"], "" if c["passed"] else " FAIL")
                       for c in criteria)

    continuation_state = dict(
        warm_started_from="converged (phi,p) of main run",
        anderson_history_reset=True,       # fresh solve_coupled -> Anderson history empty at cont start
        cont_first_used_x0=bool(cont["history"][0].get("she_used_x0", False)) if cont_n else None,
        cont_first_preconditioner_reused=bool(
            cont["history"][0].get("she_preconditioner_reused", False)) if cont_n else None,
        cont_first_krylov_iters=int(cont["history"][0].get("she_krylov_outer_iterations", -1)) if cont_n else None,
    )

    report = dict(
        criteria=criteria,
        drift_raw_Gii=drift_raw, drift_interp_Gii=drift_interp, drift_G_tot=drift_tot,
        restart_delta_raw_Gii=restart_raw, restart_delta_G_tot=restart_tot,
        hotspot_drift_um=hotspot_drift_um, hotspot_drift_cells=hotspot_drift_cells,
        continuation_state=continuation_state,
        cont_R_phi_band=[float(cont["history"][0]["max_dphi_V"]),
                         float(cont["history"][-1]["max_dphi_V"])],
        cont_n_iter=cont_n,
    )
    return certified, status, detail, report


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


def run_node(Nx, Ny, max_outer=MAX_OUTER_CAP, warm_npz=None, verbose=True, outdir=None, run_id=None,
             family=None):
    outdir = outdir or os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(outdir, exist_ok=True)
    cfg = _config_hash()
    prov = _provenance()
    tag = "she2d_aniso_%dx%d_t%d_%s" % (Nx, Ny, THREADS_REQUESTED, cfg)
    if family:                      # G1.6: family dimension -> anchor (100,70) exists once per family
        tag = "%s_%s" % (tag, family)
    if run_id:
        tag = "%s_%s" % (tag, run_id)
    npz_path = os.path.join(outdir, tag + ".npz")
    json_path = os.path.join(outdir, tag + ".json")
    if os.path.exists(npz_path) or os.path.exists(json_path):
        raise SystemExit("G1.3 HARD-FAIL: output already exists for %s (refusing to overwrite a "
                         "control artifact); pass --run-id for a distinct replicate." % tag)

    print("=" * 78)
    print("ANISO MESH-STUDY NODE: Nx=%d Ny=%d  (max_outer=%d, tol_phi=%.1e)" % (Nx, Ny, max_outer, TOL_PHI))
    print("  mesh law: ratio=%.3f W=%.3f X_C=%.3f (x graded, y=Ly*s^1.8); solver Phi_gate=%.3f, anderson d=%d b=%.2f"
          % (RATIO, W, X_C, PHI_GATE, AA_DEPTH, AA_BETA))
    print("  provenance: git %s (%s); config_hash=%s" % (_git_commit, _git_dirty, cfg), flush=True)
    print("  threads: requested=%d env=%s" % (THREADS_REQUESTED, prov["threads_env"]), flush=True)
    print("  threadpool_actual=%s" % prov["threadpool_actual"], flush=True)

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
    certified, status, detail, report = _certify(obs, cont)

    extra = dict(status=status, certified=certified, max_outer=max_outer,
                 tol_phi=TOL_PHI, cont_n_iter=report["cont_n_iter"],
                 drift_raw_Gii=report["drift_raw_Gii"], drift_interp_Gii=report["drift_interp_Gii"],
                 drift_G_tot=report["drift_G_tot"], cont_R_phi_band=np.array(report["cont_R_phi_band"]),
                 restart_delta_raw_Gii=report["restart_delta_raw_Gii"],
                 restart_delta_G_tot=report["restart_delta_G_tot"],
                 hotspot_drift_um=report["hotspot_drift_um"],
                 hotspot_drift_cells=report["hotspot_drift_cells"],
                 config_hash=cfg, threads_requested=THREADS_REQUESTED,
                 numpy_version=prov["numpy_version"], platform=prov["platform"])
    H_hash = _save_npz(npz_path, r, x, y, Nx, Ny, dx_drain, dy_surf, dy_depth, warm_name, obs, extra)

    rec = dict(Nx=Nx, Ny=Ny, family=family, direction=None, level=None, warm_source=warm_name,
               status=status, certified=certified, certification=detail,
               git_commit=_git_commit, git_dirty=_git_dirty, H_hash=H_hash,
               config_hash=cfg, provenance=prov,
               drain_dx=dx_drain, surface_dy=dy_surf, dy_depth=dy_depth, ref_depth=REF_DEPTH,
               **{k: obs[k] for k in ("Gii_max", "Gii_interp", "xy_Gii_max", "xy_Gii_max_interp",
                                      "avalanche_y_fwhm", "G_tot", "drain_current_A_per_um", "R_phi",
                                      "dGii_tail", "relative_number_balance", "continuity_residual",
                                      "n_iter", "h_rep", "fwhm_flags")},
               criteria=report["criteria"], restart_delta_raw_Gii=report["restart_delta_raw_Gii"],
               restart_delta_G_tot=report["restart_delta_G_tot"],
               hotspot_drift_um=report["hotspot_drift_um"],
               hotspot_drift_cells=report["hotspot_drift_cells"],
               continuation_state=report["continuation_state"],
               drift_raw_Gii=report["drift_raw_Gii"], drift_interp_Gii=report["drift_interp_Gii"],
               drift_G_tot=report["drift_G_tot"], cont_n_iter=report["cont_n_iter"],
               cont_R_phi_band=report["cont_R_phi_band"],
               npz=npz_path, npz_rel=os.path.relpath(npz_path, outdir),
               json_path=json_path, json_rel=os.path.relpath(json_path, outdir))
    with open(json_path, "w") as fh:
        json.dump(rec, fh, indent=2)
    print("\n=== NODE %dx%d -> %s  (R_phi=%.3e, Gii_raw=%.4e, Gii_interp=%.4e, G_tot=%.4e) ==="
          % (Nx, Ny, status, obs["R_phi"], obs["Gii_max"], obs["Gii_interp"], obs["G_tot"]))
    print("    %s" % detail)
    print("    saved %s + %s" % (npz_path, json_path))
    return rec


def run_family(name, include_fourth=False):
    auth = _require_exec_auth()          # G0.2: HARD-BLOCK without execution authorization
    fam = FAMILIES[name]
    levels = list(fam["levels"])
    records = []
    warm = None
    peak_rss = None
    for i, (Nx, Ny) in enumerate(levels):
        rec = run_node(Nx, Ny, warm_npz=warm, verbose=True, family=name)
        rec["family"] = name; rec["direction"] = fam["direction"]; rec["level"] = i
        rec["authorized_by"] = auth.get("who"); rec["authorized_when"] = auth.get("when")
        records.append(rec)
        if rec["certified"]:
            warm = rec["npz"]
        peak_rss = _peak_rss_bytes()     # G1.4: measured peak working set (cumulative max to date)
    # 4th level -- pre-committed resource/convergence gate (reviewer adj. 1 / G1.4)
    if include_fourth:
        third = records[-1] if records else None
        third_certified = bool(third["certified"]) if third else False
        Nx4, Ny4 = fam["fourth"]
        Nx3, Ny3 = levels[-1]
        approved, decision = resource_gate(peak_rss, (Nx3, Ny3), (Nx4, Ny4))
        decision["authorized_by"] = auth.get("who"); decision["authorized_when"] = auth.get("when")
        if third_certified and approved:
            rec = run_node(Nx4, Ny4, warm_npz=warm, verbose=True, family=name)
            rec["family"] = name; rec["direction"] = fam["direction"]; rec["level"] = len(levels)
            rec["resource_gate"] = decision
            records.append(rec)
        else:
            print("4th level SKIPPED: certified=%s resource_approved=%s (resource/convergence gate)."
                  % (third_certified, approved))
            print("  resource decision:", decision.get("reason"))
            records.append(dict(family=name, direction=fam["direction"], level=len(levels),
                                fourth_skipped=True, third_certified=third_certified,
                                resource_gate=decision))
    return records


def compare_anchor(outdir=None, families=("X", "Y")):
    """G1.6: tabulate the (100,70) anchor's independent X- and Y-family artifacts and their deltas."""
    outdir = outdir or os.path.join(os.path.dirname(__file__), "..", "data")
    Nx, Ny = ANCHOR

    def _find(fam):
        import glob
        pat = os.path.join(outdir, "she2d_aniso_%dx%d_t*_%s_*.json" % (Nx, Ny, fam))
        hits = sorted(glob.glob(pat))
        return hits[0] if hits else None

    jx, jy = _find("X"), _find("Y")
    if not jx or not jy:
        return dict(anchor=[Nx, Ny], available=False, x_json=jx, y_json=jy)
    dx = json.load(open(jx)); dy = json.load(open(jy))

    def _rel(a, b):
        return 2.0 * abs(a - b) / (abs(a) + abs(b)) if (abs(a) + abs(b)) else 0.0

    return dict(
        anchor=[Nx, Ny], x_json=jx, y_json=jy,
        Gii_max_X=dx["Gii_max"], Gii_max_Y=dy["Gii_max"],
        dGii_max_rel=_rel(dx["Gii_max"], dy["Gii_max"]),
        G_tot_X=dx["G_tot"], G_tot_Y=dy["G_tot"], dG_tot_rel=_rel(dx["G_tot"], dy["G_tot"]),
        hotspot_X=dx["xy_Gii_max_interp"], hotspot_Y=dy["xy_Gii_max_interp"],
        dhotspot_um=float(np.hypot(dx["xy_Gii_max_interp"][0] - dy["xy_Gii_max_interp"][0],
                                   dx["xy_Gii_max_interp"][1] - dy["xy_Gii_max_interp"][1])),
        X_warm_source=dx["warm_source"], Y_warm_source=dy["warm_source"],
        X_certified=dx["certified"], Y_certified=dy["certified"],
    )


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
        rest = argv[3:]
        maxo, run_id = MAX_OUTER_CAP, None
        i = 0
        while i < len(rest):
            if rest[i].isdigit():
                maxo = int(rest[i])
            elif rest[i] == "--run-id" and i + 1 < len(rest):
                run_id = rest[i + 1]; i += 1
            i += 1
        run_node(Nx, Ny, max_outer=maxo, run_id=run_id)
    elif argv[0] == "--family":
        name = argv[1].upper()
        run_family(name, include_fourth=("--include-4th" in argv))
    else:
        sys.exit("usage: --list | --node Nx Ny [maxouter] | --family X|Y [--include-4th]")
