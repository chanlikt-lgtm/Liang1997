"""
test_aniso_mesh_study.py -- unit tests for the anisotropic mesh-study harness.

Covers the reviewer's three build requirements:
  1. mesh law unchanged vs the frozen driver for a shared (Nx,Ny)  (byte-identical reuse)
  2. refuses nothing (no self-similar SEQUENCE guard -- accepts non-self-similar nodes)
  3. writes the identical npz schema (plus the new interpolated-peak + certification fields)
Plus a sub-cell interpolated-peak sanity test (reviewer adj. 2).
Run:  python campaign/test_aniso_mesh_study.py
"""
import os, sys, ast, tempfile, io
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "src"))

import aniso_mesh_study as aniso


# ---------------------------------------------------------------------------
# Extract the driver's build_mesh / dy_at / frozen constants via AST (the driver
# parses sys.argv at module level, so it cannot be imported directly).
# ---------------------------------------------------------------------------
def load_driver_mesh_defs():
    from device import DeviceParams
    path = os.path.join(REPO, "src", "coupled_drain_richardson.py")
    tree = ast.parse(open(path).read())
    keep = []
    def _target_names(node):
        names = []
        for t in node.targets:
            if isinstance(t, ast.Name):
                names.append(t.id)
            elif isinstance(t, ast.Tuple):
                names.extend(e.id for e in t.elts if isinstance(e, ast.Name))
        return names
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(n in {"RATIO", "W", "X_C", "REF_DEPTH"} for n in _target_names(node)):
                keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in ("build_mesh", "dy_at"):
            keep.append(node)
    mod = ast.Module(body=keep, type_ignores=[])
    ast.fix_missing_locations(mod)
    ns = {"np": np}
    p = DeviceParams(); ns["Lx"], ns["Ly"] = p.Lx, p.Ly
    exec(compile(mod, path, "exec"), ns)
    return ns


DRIVER = load_driver_mesh_defs()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_mesh_law_unchanged_vs_driver():
    """build_mesh must be byte-identical to the frozen driver for shared (Nx,Ny)."""
    for Nx, Ny in [(71, 70), (100, 70), (141, 85), (71, 58), (100, 58), (100, 85)]:
        xa, ya, dxa, dya_s, dya_d = aniso.build_mesh(Nx, Ny)
        xd, yd, dxd, dyd_s, dyd_d = DRIVER["build_mesh"](Nx, Ny)
        assert np.array_equal(xa, xd), "x mesh diverged at (%d,%d)" % (Nx, Ny)
        assert np.array_equal(ya, yd), "y mesh diverged at (%d,%d)" % (Nx, Ny)
        assert abs(dxa - dxd) == 0.0 and abs(dya_s - dyd_s) == 0.0 and abs(dya_d - dyd_d) == 0.0


def test_dy_at_unchanged_vs_driver():
    y = aniso.build_mesh(100, 70)[1]
    for depth in (0.0, 0.02, 0.05, 0.1, 0.35, 0.7):
        assert abs(aniso.dy_at(y, depth) - DRIVER["dy_at"](y, depth)) == 0.0


def test_refuses_nothing():
    """The harness drops the self-similar SEQUENCE guard: non-self-similar nodes build fine."""
    for Nx, Ny in [(71, 70), (100, 58), (100, 85), (200, 70), (100, 120), (141, 70)]:
        x, y, dx, dys, dyd = aniso.build_mesh(Nx, Ny)
        assert len(x) == Nx and len(y) == Ny
    # pre-registered families contain non-self-similar nodes
    assert (71, 70) in aniso.FAMILIES["X"]["levels"]
    assert (100, 58) in aniso.FAMILIES["Y"]["levels"]
    assert aniso.FAMILIES["X"]["fourth"] == (200, 70)
    assert aniso.FAMILIES["Y"]["fourth"] == (100, 120)


def test_interpolated_peak_subcell():
    """A smooth off-node peak must yield an interpolated value >= the nodal max, in-cell location."""
    x = np.linspace(0.0, 0.8, 71); y = np.linspace(0.0, 0.7, 70)
    X, Y = np.meshgrid(x, y)
    x0, y0, sx, sy = 0.4621, 0.0533, 0.015, 0.018
    G = np.exp(-((X - x0) ** 2) / (2 * sx ** 2) - ((Y - y0) ** 2) / (2 * sy ** 2))
    g_interp, xv, yv, jg, ig = aniso.interpolated_peak(G, x, y)
    assert np.isfinite(g_interp) and g_interp > 0.0
    assert g_interp >= G.max() - 1e-12, "interpolated peak must not fall below the nodal max"
    assert x[0] <= xv <= x[-1] and y[0] <= yv <= y[-1]
    # interpolated location is at least as close to the true peak as the nodal max
    jg_n, ig_n = np.unravel_index(int(np.argmax(G)), G.shape)
    assert abs(xv - x0) <= abs(x[ig_n] - x0) + 1e-12
    assert abs(yv - y0) <= abs(y[jg_n] - y0) + 1e-12


def test_interpolated_peak_degenerate():
    """Flat / uniform field falls back to the nodal max without error."""
    x = np.linspace(0.0, 0.8, 40); y = np.linspace(0.0, 0.7, 30)
    G = np.ones((30, 40))
    g_interp, xv, yv, _, _ = aniso.interpolated_peak(G, x, y)
    assert g_interp == 1.0


# ---------------------------------------------------------------------------
# npz schema test (no solver run): a minimal mock of solve_coupled's return dict
# ---------------------------------------------------------------------------
class _FakeSHE:
    NH = 5
    H = np.linspace(0.5, 2.5, 5) * 1.602176634e-19  # Joules (eV*e)


def _mock_r(Ny, Nx):
    Gii = np.zeros((Ny, Nx)); Gii[Ny // 2, Nx // 2] = 1.0
    Gii[Ny // 2 - 1, Nx // 2] = 0.9; Gii[Ny // 2 + 1, Nx // 2] = 0.9
    Gii[Ny // 2, Nx // 2 - 1] = 0.9; Gii[Ny // 2, Nx // 2 + 1] = 0.9
    hist = [dict(Gii_max_cm3s=1.0 + 0.001 * (k % 2), G_tot_cm1s=2.0 + 0.001 * (k % 2),
                 max_dphi_V=1e-5, relative_number_balance=1e-3, drain_current_A_per_um=1e-4)
            for k in range(8)]
    return dict(phi=np.zeros((Ny, Nx)), n=np.ones((Ny, Nx)) * 1e16, p=np.ones((Ny, Nx)) * 1e16,
                Te=np.full((Ny, Nx), 300.0), Gii=Gii,
                vx=np.zeros((Ny, Nx)), vy=np.zeros((Ny, Nx)),
                F3d=np.zeros((3, Ny * Nx), dtype=np.float32), H=_FakeSHE.H,
                Gamma_x_face=np.zeros((Ny, Nx + 1)), Gamma_y_face=np.zeros((Ny + 1, Nx)),
                history=hist,
                conservation=dict(scaled_linear_residual_inf=1e-8, relative_number_balance=1e-3,
                                  drain_current_A_per_um=1e-4),
                she=_FakeSHE())


def test_npz_schema_written():
    Nx, Ny = 71, 70
    r = _mock_r(Ny, Nx)
    x, y, dx, dys, dyd = aniso.build_mesh(Nx, Ny)
    obs = aniso._extract_observables(r, x, y)
    extra = dict(status="CERTIFIED", certified=True, max_outer=1500, tol_phi=1e-4,
                 cont_n_iter=40, drift_raw_Gii=1e-4, drift_interp_Gii=1e-4, drift_G_tot=1e-4,
                 cont_R_phi_band=np.array([1e-5, 1e-5]))
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "she2d_aniso_%dx%d.npz" % (Nx, Ny))
        aniso._save_npz(path, r, x, y, Nx, Ny, dx, dys, dyd, "", obs, extra)
        z = np.load(path)
        for key in ["x", "y", "phi", "n", "p", "Te", "Gii", "F3d", "H",
                    "Nx", "Ny", "ratio", "W", "X_C", "dH_eV", "eps_max_eV", "she_tol", "NH",
                    "H_hash", "common_phi_span", "n_iter", "git_commit", "git_dirty", "warm_source",
                    "drain_dx", "surface_dy", "dy_depth", "avalanche_y_fwhm",
                    "Gii_max", "Gii_interp", "G_tot", "xy_Gii_max", "xy_Gii_max_interp",
                    "drain_current_A_per_um", "continuity_residual", "relative_number_balance",
                    "R_phi", "dGii_tail", "last4_Gii_max", "last4_G_tot", "last4_R_phi",
                    "status", "certified", "drift_raw_Gii", "drift_interp_Gii", "drift_G_tot"]:
            assert key in z.files, "missing npz key: %s" % key
        assert float(z["Gii_interp"]) >= float(z["Gii_max"]) - 1e-12
        assert str(z["status"]) == "CERTIFIED"


def test_certify_runs():
    """_certify must not crash on a converged-looking node (regression: 'Gc and' array-truth bug)."""
    obs = dict(R_phi=1e-5, Gii_interp=3.0)
    Ny, Nx = 70, 71
    x = np.linspace(0.0, 0.8, Nx); y = np.linspace(0.0, 0.7, Ny)
    Gii = np.full((Ny, Nx), 3.0)
    hist = [dict(Gii_max_cm3s=3.0 + 1e-6 * (k % 3), G_tot_cm1s=2.0, max_dphi_V=1e-5) for k in range(40)]
    cont = dict(history=hist, Gii=Gii, x=x, y=y)
    certified, status, detail, drift = aniso._certify(obs, cont)
    assert status in ("CERTIFIED", "UNRESOLVED")
    assert isinstance(drift["cont_R_phi_band"], list) and len(drift["cont_R_phi_band"]) == 2
    assert all(np.isfinite(float(v)) for v in drift["cont_R_phi_band"])


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t(); print("PASS  %s" % t.__name__)
        except Exception:
            failed += 1
            print("FAIL  %s" % t.__name__)
            traceback.print_exc()
    print("\nRESULT: %d/%d PASS" % (len(tests) - failed, len(tests)))
    sys.exit(1 if failed else 0)
