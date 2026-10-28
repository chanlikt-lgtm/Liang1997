"""
test_aniso_mesh_study.py -- unit tests for the anisotropic mesh-study harness.

Covers the reviewer's three build requirements:
  1. mesh law unchanged vs the frozen driver for a shared (Nx,Ny)  (byte-identical reuse)
  2. refuses nothing (no self-similar SEQUENCE guard -- accepts non-self-similar nodes)
  3. writes the identical npz schema (plus the new interpolated-peak + certification fields)
Plus a sub-cell interpolated-peak sanity test (reviewer adj. 2).
Run:  python campaign/test_aniso_mesh_study.py
"""
import os, sys, ast, tempfile, io, json
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
    """_certify must not crash on a converged-looking node (regression: 'Gc and' array-truth bug),
    and must emit a full per-criterion PASS/FAIL report (G2.1)."""
    obs = dict(R_phi=1e-5, Gii_interp=3.0, history_Gii=np.array([3.0, 3.0]),
               history_Gtot=np.array([2.0, 2.0]), xy_Gii_max_interp=[0.4, 0.05],
               h_rep=0.005, continuity_residual=1e-9, relative_number_balance=1e-5)
    Ny, Nx = 70, 71
    x = np.linspace(0.0, 0.8, Nx); y = np.linspace(0.0, 0.7, Ny)
    Gii = np.full((Ny, Nx), 3.0)
    hist = [dict(Gii_max_cm3s=3.0 + 1e-6 * (k % 3), G_tot_cm1s=2.0, max_dphi_V=1e-5) for k in range(40)]
    cont = dict(history=hist, Gii=Gii, x=x, y=y)
    certified, status, detail, report = aniso._certify(obs, cont)
    assert status in ("CERTIFIED", "UNRESOLVED")
    assert isinstance(report["cont_R_phi_band"], list) and len(report["cont_R_phi_band"]) == 2
    assert all(np.isfinite(float(v)) for v in report["cont_R_phi_band"])
    # G2.1: explicit PASS/FAIL for every numerical criterion, with raw value + unit + gate
    assert len(report["criteria"]) == 7
    names = {c["name"] for c in report["criteria"]}
    assert names == {"R_phi", "continuity_residual", "number_balance", "drift_raw_Gii",
                     "drift_interp_Gii", "drift_G_tot", "hotspot_drift"}
    for c in report["criteria"]:
        assert isinstance(c["passed"], bool) and "value" in c and "unit" in c and "gate" in c
    # G2.2: restart delta and continuation-state doc are present
    assert "restart_delta_raw_Gii" in report and "continuation_state" in report


def test_certify_not_rphi_alone():
    """G2.3: a node that passes R_phi but fails another criterion must NOT be CERTIFIED."""
    obs = dict(R_phi=1e-6, Gii_interp=3.0, history_Gii=np.array([3.0, 3.0]),
               history_Gtot=np.array([2.0, 2.0]), xy_Gii_max_interp=[0.4, 0.05],
               h_rep=0.005, continuity_residual=1e-3,   # FAILS the 1e-6 continuity gate
               relative_number_balance=1e-5)
    Ny, Nx = 70, 71
    x = np.linspace(0.0, 0.8, Nx); y = np.linspace(0.0, 0.7, Ny)
    Gii = np.full((Ny, Nx), 3.0)
    hist = [dict(Gii_max_cm3s=3.0, G_tot_cm1s=2.0, max_dphi_V=1e-6) for _ in range(40)]
    cont = dict(history=hist, Gii=Gii, x=x, y=y)
    certified, status, detail, report = aniso._certify(obs, cont)
    assert status == "UNRESOLVED" and certified is False
    ccont = [c for c in report["criteria"] if c["name"] == "continuity_residual"][0]
    assert ccont["passed"] is False


def test_fwhm_2cross_gaussian():
    """G1.5: two-crossing FWHM recovers 2.3548*sigma for a well-resolved Gaussian within 5%."""
    x = np.linspace(0.0, 1.0, 201)
    x0, sigma = 0.5, 0.08
    profile = np.exp(-((x - x0) ** 2) / (2 * sigma ** 2))
    info = aniso._profile_fwhm_2cross(profile, x)
    expected = 2.3548200450309493 * sigma
    assert info["fwhm"] is not None
    assert abs(info["fwhm"] - expected) / expected < 0.05
    assert not info["boundary_truncated"] and not info["unresolved"] and not info["multi_peak"]
    assert x[0] <= info["left_x"] < info["right_x"] <= x[-1]


def test_fwhm_2cross_flags():
    """G1.5: quality flags -- boundary-truncated, multi-peak, and unresolved profiles."""
    x = np.linspace(0.0, 1.0, 101)
    # boundary-truncated: peak at the left edge, monotonically decreasing rightward
    mono = np.exp(-((x - x[0]) ** 2) / (2 * 0.05 ** 2))
    assert aniso._profile_fwhm_2cross(mono, x)["boundary_truncated"]
    # multi-peak: two separated Gaussians above half-max
    two = (np.exp(-((x - 0.3) ** 2) / (2 * 0.04 ** 2))
           + np.exp(-((x - 0.7) ** 2) / (2 * 0.04 ** 2)))
    assert aniso._profile_fwhm_2cross(two, x)["multi_peak"]
    # unresolved: a single-cell spike
    spike = np.zeros_like(x); spike[50] = 1.0
    assert aniso._profile_fwhm_2cross(spike, x)["unresolved"]


def test_resource_gate():
    """G1.4: resource gate blocks an infeasible case and approves a feasible one."""
    ok, d_ok = aniso.resource_gate(1e8, (141, 70), (200, 70))   # ~142 MB predicted -> fits
    assert ok is True and d_ok["approved"] is True
    no, d_no = aniso.resource_gate(1e15, (141, 70), (200, 70))  # absurd -> must block
    assert no is False and d_no["approved"] is False
    assert "reason" in d_ok and "reason" in d_no and "cell_ratio" in d_ok


def test_parse_node_rest_threads():
    """Regression: `--threads N` after `--node` must NOT corrupt the max_outer parse (G3 launch path)."""
    assert aniso._parse_node_rest(["1500"]) == (1500, None)
    assert aniso._parse_node_rest(["1500", "--threads", "8"]) == (1500, None)
    assert aniso._parse_node_rest(["1500", "--threads", "1"]) == (1500, None)
    assert aniso._parse_node_rest(["300", "--run-id", "rep2", "--threads", "1"]) == (300, "rep2")


def test_config_hash_stable():
    """G1.3: config hash is deterministic (same frozen config -> same 12-char hash)."""
    h1, h2 = aniso._config_hash(), aniso._config_hash()
    assert h1 == h2 and len(h1) == 12


def test_thread_env_enforced():
    """G1.2: thread env vars are pinned to THREADS_REQUESTED at import time."""
    assert aniso.THREADS_REQUESTED in (1, 8) or aniso.THREADS_REQUESTED >= 1
    for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        assert os.environ.get(v) == str(aniso.THREADS_REQUESTED)


def test_exec_auth_hard_block():
    """G0.2: run_family must HARD-BLOCK (SystemExit), not warn, when authorization is absent."""
    saved = aniso.AUTH_FILE
    aniso.AUTH_FILE = os.path.join(tempfile.gettempdir(), "aniso_exec_auth_absent_%d.json" % os.getpid())
    if os.path.exists(aniso.AUTH_FILE):
        os.remove(aniso.AUTH_FILE)
    try:
        try:
            aniso.run_family("X")
            raised = False
        except SystemExit:
            raised = True
        assert raised, "run_family must hard-block without execution authorization"
    finally:
        aniso.AUTH_FILE = saved


def test_exec_auth_recorded():
    """G0.2: a valid auth file is accepted and its who/when is surfaced."""
    saved = aniso.AUTH_FILE
    aniso.AUTH_FILE = os.path.join(tempfile.gettempdir(), "aniso_exec_auth_ok_%d.json" % os.getpid())
    with open(aniso.AUTH_FILE, "w") as fh:
        json.dump({"execution_authorized": True, "who": "Chan Lik", "when": "2026-10-23T00:00:00Z"}, fh)
    try:
        a = aniso._require_exec_auth()
        assert a["execution_authorized"] is True and a["who"] == "Chan Lik"
    finally:
        aniso.AUTH_FILE = saved


def _build_full_record(Nx=71, Ny=70, family="X", status="CERTIFIED", certified=True):
    """Build a realistic node record via the real _build_node_record path (no solver run)."""
    r = _mock_r(Ny, Nx)
    x, y, dx, dys, dyd = aniso.build_mesh(Nx, Ny)
    obs = aniso._extract_observables(r, x, y)
    hist = [dict(Gii_max_cm3s=1.0 + 1e-6 * (k % 3), G_tot_cm1s=2.0, max_dphi_V=1e-5) for k in range(40)]
    cont = dict(history=hist, Gii=r["Gii"], x=x, y=y)
    _c, _s, detail, report = aniso._certify(obs, cont)
    prov = aniso._provenance()
    cfg = aniso._config_hash()
    npz_path = "/tmp/nonexistent_%dx%d_%s.npz" % (Nx, Ny, family)
    json_path = "/tmp/nonexistent_%dx%d_%s.json" % (Nx, Ny, family)
    rec = aniso._build_node_record(Nx, Ny, family, "", status, certified, detail, cfg, prov,
                                   "0123456789ab", dx, dys, dyd, obs, report,
                                   npz_path, json_path, "/tmp")
    return rec, json_path


def test_metadata_persisted_on_disk():
    """CP2A: a node record written to disk and REOPENED must retain every provenance + criteria field
    (the JSON, not the in-memory dict, is what a third party reads)."""
    import shutil
    rec, json_path = _build_full_record()
    # overwrite into a temp dir so we actually persist + reload a real file
    td = tempfile.mkdtemp()
    try:
        json_path = os.path.join(td, "node.json")
        aniso._write_node_json(rec, json_path)
        assert os.path.exists(json_path)
        with open(json_path) as fh:
            reopened = json.load(fh)
        # provenance block persisted (not just in memory)
        prov = reopened["provenance"]
        for k in ("threads_requested", "threads_env", "numpy_version", "python", "platform",
                  "machine", "cpu", "git_commit", "git_dirty", "threadpool_actual"):
            assert k in prov, "provenance key missing on disk: %s" % k
        # all 7 criteria persisted with their value/unit/gate/passed
        assert len(reopened["criteria"]) == 7
        names = {c["name"] for c in reopened["criteria"]}
        assert names == {"R_phi", "continuity_residual", "number_balance", "drift_raw_Gii",
                         "drift_interp_Gii", "drift_G_tot", "hotspot_drift"}
        for c in reopened["criteria"]:
            assert isinstance(c["passed"], bool) and "value" in c and "unit" in c and "gate" in c
        # certification / status / identity fields persisted
        for k in ("status", "certified", "certification", "git_commit", "git_dirty", "H_hash",
                  "config_hash", "warm_source", "drain_dx", "surface_dy", "dy_depth", "ref_depth",
                  "Gii_max", "Gii_interp", "G_tot", "xy_Gii_max", "xy_Gii_max_interp",
                  "avalanche_y_fwhm", "drain_current_A_per_um", "R_phi", "dGii_tail",
                  "relative_number_balance", "continuity_residual", "n_iter", "h_rep",
                  "fwhm_flags", "restart_delta_raw_Gii", "restart_delta_G_tot",
                  "hotspot_drift_um", "hotspot_drift_cells", "continuation_state",
                  "drift_raw_Gii", "drift_interp_Gii", "drift_G_tot", "cont_n_iter",
                  "cont_R_phi_band"):
            assert k in reopened, "node field missing on disk: %s" % k
        # a boundary-truncated fwhm flag survives serialization as a dict, not a string
        assert isinstance(reopened["fwhm_flags"], dict)
        assert "boundary_truncated" in reopened["fwhm_flags"]
    finally:
        shutil.rmtree(td, ignore_errors=True)


def test_gate4_excludes_uncertified():
    """CP3: Gate-4 analysis input must EXCLUDE uncertified/UNRESOLVED/failed nodes."""
    records = [
        dict(status="CERTIFIED", certified=True),
        dict(status="UNRESOLVED", certified=False),
        dict(status="FAILED", certified=False),
        dict(status="CERTIFIED", certified=True),
    ]
    kept = aniso.gate4_nodes(records)
    assert len(kept) == 2 and all(r["status"] == "CERTIFIED" for r in kept)


def test_node_state_vocabulary():
    """CP5: _node_state maps records onto the frozen manifest vocabulary only."""
    assert aniso._node_state(dict(status="CERTIFIED")) == "certified"
    assert aniso._node_state(dict(status="UNRESOLVED")) == "UNRESOLVED"
    assert aniso._node_state(dict(status="FAILED")) == "failed"
    assert aniso._node_state(None) == "failed"
    assert set(aniso.NODE_STATES) == {"queued", "running", "certified", "failed", "UNRESOLVED"}


def test_run_sweep_sequential_failure_isolation():
    """CP2A/CP5: a clean sequential X-then-Y dry run -- the shared (100,70) anchor does not make the
    2nd family fail, and one family failing must NOT mark the other complete."""
    import shutil
    calls = []
    def _fake_run_node(Nx, Ny, max_outer=1500, warm_npz=None, verbose=True, outdir=None, run_id=None,
                       family=None):
        calls.append((Nx, Ny, family))
        if family == "X" and (Nx, Ny) == (100, 70):
            raise SystemExit("synthetic X-family mid-chain failure")
        return dict(Nx=Nx, Ny=Ny, family=family, status="CERTIFIED", certified=True,
                    npz="/tmp/fake_%dx%d_%s.npz" % (Nx, Ny, family))
    saved_node = aniso.run_node
    saved_auth = aniso.AUTH_FILE
    aniso.AUTH_FILE = os.path.join(tempfile.gettempdir(), "aniso_exec_auth_sweep_%d.json" % os.getpid())
    with open(aniso.AUTH_FILE, "w") as fh:
        json.dump({"execution_authorized": True, "who": "Chan Lik", "when": "2026-10-29T00:00:00Z"}, fh)
    aniso.run_node = _fake_run_node
    td = tempfile.mkdtemp()
    try:
        manifest, results = aniso.run_sweep(outdir=td)
        # X-family: (71,70) ran, then (100,70) failed -> X is FAILED
        assert results["X"]["status"] == "FAILED"
        # Y-family ran independently to completion despite X failing (failure isolation)
        assert results["Y"]["status"] == "COMPLETE"
        y_nodes = results["Y"]["nodes"]
        assert all(n["state"] == "certified" for n in y_nodes)
        # the shared (100,70) anchor ran in BOTH families as separate calls
        anchor = [(nx, ny, f) for (nx, ny, f) in calls if (nx, ny) == (100, 70)]
        assert len(anchor) == 2 and {a[2] for a in anchor} == {"X", "Y"}
        # manifest emits the full state vocabulary + per-family status
        assert set(manifest["vocabulary"]) == {"queued", "running", "certified", "failed", "UNRESOLVED"}
        assert manifest["families"]["X"]["status"] == "FAILED"
        assert manifest["families"]["Y"]["status"] == "COMPLETE"
        # X-family node states: certified (71,70), failed (100,70), queued (141,70)
        x_states = [n["state"] for n in manifest["families"]["X"]["nodes"]]
        assert x_states == ["certified", "failed", "queued"]
        # manifest file actually written to disk
        assert os.path.exists(manifest["_path"])
    finally:
        aniso.run_node = saved_node
        aniso.AUTH_FILE = saved_auth
        shutil.rmtree(td, ignore_errors=True)


def test_warm_start_assert():
    """G1.1: a missing warm-start npz must raise, never silently cold-start."""
    missing = os.path.join(tempfile.gettempdir(), "does_not_exist_%d.npz" % os.getpid())
    try:
        aniso._solve(71, 70, 1500, warm_npz=missing)
        raised = False
    except SystemExit:
        raised = True
    assert raised, "missing warm-start npz must HARD-FAIL (no silent cold-start fallback)"


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
