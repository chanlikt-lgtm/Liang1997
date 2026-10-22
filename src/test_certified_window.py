"""
test_certified_window.py -- unit tests for NUM-01 (certified_window.read_certified_window) and
NUM-02 (node_manifest.build_manifest / verify_manifest).

Reviewer acceptance tests:
  NUM-01  a 1-iteration terminal chunk whose prior 3 values drift -> u_Gii > 0 (and the same
             u via the spread*mean/2 derivation the report uses), i.e. a degenerate chunk-local
             last-4 (u=0) can no longer fake a finite reversal band. Consistent across the three
             consumers (richardson_fit, run_richardson_trio, gen_run_report) because they all
             route through read_certified_window.
  NUM-02  (1) missing H_hash -> FAIL, (2) changed Phi_gate -> FAIL, (3) changed warm-source
             SHA -> FAIL.

Run:  python src/test_certified_window.py     (exit 0 = all pass)
"""
import os
import sys
import json
import copy
import tempfile
import shutil
import hashlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import certified_window as cw
import plateau_gate as pg
import node_manifest as nm

FAIL = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("[%s] %s%s" % (tag, name, ("  -- " + detail) if detail else ""))
    if not cond:
        FAIL.append(name)


def _synthetic(tmp, tag, n_iter, last4_G, last4_T, last4_R, sidecar=None,
               H=None, H_hash="abc123def456", Nx=71, Ny=58):
    """Write a synthetic node NPZ (+ optional sidecar) and return (npz_path, sidecar_path)."""
    Gmax = float(last4_G[-1])
    Gtot = float(last4_T[-1])
    Rphi = float(last4_R[-1])
    arr = dict(
        Nx=Nx, Ny=Ny, n_iter=n_iter,
        ratio=6.0, W=0.09, X_C=0.60, dH_eV=0.0125, eps_max_eV=3.02, she_tol=1e-8, NH=591,
        Hmin=-3.7, Hmax=3.675, H_hash=H_hash,
        drain_dx=0.0038, surface_dy=0.00048,
        Gii_max=Gmax, G_tot=Gtot, R_phi=Rphi,
        last4_Gii_max=np.asarray(last4_G, float), last4_G_tot=np.asarray(last4_T, float),
        last4_R_phi=np.asarray(last4_R, float),
        git_commit="abcd1234", git_dirty="clean", warm_source="",
    )
    if H is not None:
        arr["H"] = np.asarray(H, dtype=np.float64)
    npz = os.path.join(tmp, "she2d_richardson_%s.npz" % tag)
    np.savez(npz, **arr)
    side = None
    if sidecar is not None:
        side = os.path.join(tmp, "she2d_richardson_%s.progress.json" % tag)
        json.dump(dict(plateau_buffer=sidecar, buffer_origin="persisted_sidecar"),
                  open(side, "w", encoding="utf-8"))
    return npz, side


def test_num01():
    print("\n== NUM-01 certified window ==")
    tmp = tempfile.mkdtemp(prefix="cwtest_")
    try:
        # The reviewer scenario: a node whose TERMINAL driver chunk contributed only ONE real
        # iteration (the tol_phi early-stop), but the prior 3 cumulative iterations drifted.
        term = 3.0757521592531657e25
        prior = [3.07553e25, 3.07560e25, 3.07570e25]          # drifting
        Tprior = [9.26430e13, 9.26440e13, 9.26450e13]
        Rprior = [2.0e-4, 1.9e-4, 1.8e-4]
        sidecar = [dict(abs_iter=58 + i, Gii=g, Gtot=t, Rphi=r)
                   for i, (g, t, r) in enumerate(zip(prior + [term], Tprior + [9.26438e13],
                                                     Rprior + [7.10e-5]))]
        # NPZ terminal chunk holds ONLY the 1 terminal sample (degenerate chunk-local last-4).
        npz, side = _synthetic(tmp, "71x58", n_iter=61, last4_G=[term], last4_T=[9.26438e13],
                               last4_R=[7.10e-5], sidecar=sidecar)

        w = cw.read_certified_window(npz, side)
        check("u_Gii > 0 (1-iter terminal chunk + drifting prior 3)", w["valid"] and w["u_Gii"] > 0,
              "u_Gii=%.4e" % (w["u_Gii"] if w["u_Gii"] is not None else -1))
        check("window uses the persisted sidecar", w["buffer_origin"] == "persisted_sidecar",
              w["buffer_origin"])
        check("window is 4 consecutive iters", w["iterations"] == [58, 59, 60, 61], str(w["iterations"]))
        check("mean_Gii == window mean", np.isclose(w["mean_Gii"], float(np.mean(prior + [term]))))
        check("u_Gii == (max-min)/2", np.isclose(w["u_Gii"], (max(prior + [term]) - min(prior + [term])) / 2.0))

        # Consistency: the report's derivation (u = spread * mean / 2) must equal the reader's u.
        ev = pg.evaluate(w["window"])
        check("spread_Gii * mean_Gii / 2 == u_Gii (gen_run_report derivation)",
              np.isclose(ev["spread_Gii"] * w["mean_Gii"] / 2.0, w["u_Gii"], rtol=1e-12))

        # Degenerate: SAME node but NO sidecar -> chunk-local 1-sample -> NOT certifiable.
        npz2, _ = _synthetic(tmp, "71x58b", n_iter=61, last4_G=[term], last4_T=[9.26438e13],
                             last4_R=[7.10e-5])
        w2 = cw.read_certified_window(npz2, None)
        check("degenerate no-sidecar terminal chunk -> not valid", w2["valid"] is False, w2["detail"])

        # Stale sidecar: terminal sample does NOT match the NPZ scalar -> rejected, fallback to NPZ.
        stale = [dict(abs_iter=357 + i, Gii=2.73e25, Gtot=8.16e13, Rphi=1.5e-3) for i in range(4)]
        npz3, side3 = _synthetic(tmp, "71x58c", n_iter=325,
                                 last4_G=[3.075537678965121e25, 3.075549e25, 3.075706e25, 3.0757521592531657e25],
                                 last4_T=[9.264317e13, 9.264350e13, 9.265654e13, 9.2643797265133e13],
                                 last4_R=[2.0e-4, 1.9e-4, 1.8e-4, 7.103532818497627e-05],
                                 sidecar=stale)
        w3 = cw.read_certified_window(npz3, side3)
        check("stale sidecar rejected", w3["sidecar_rejected"] is not None, w3["sidecar_rejected"])
        check("stale sidecar -> fallback to npz reconstruction", w3["valid"] and w3["buffer_origin"] == "npz_terminal_reconstruction",
              w3["buffer_origin"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_num02():
    print("\n== NUM-02 per-node manifest ==")
    tmp = tempfile.mkdtemp(prefix="nmtest_")
    old_git = nm._git
    nm._git = lambda *a: ""            # simulate a clean, fully-resolvable environment
    try:
        H = np.linspace(-3.7, 3.675, 591)
        H_prefix = hashlib.sha1(np.ascontiguousarray(H, dtype=np.float64).tobytes()).hexdigest()[:12]
        npz, _ = _synthetic(tmp, "71x58", n_iter=325,
                            last4_G=[3.075537678965121e25, 3.075549e25, 3.075706e25, 3.0757521592531657e25],
                            last4_T=[9.264317e13, 9.264350e13, 9.265654e13, 9.2643797265133e13],
                            last4_R=[2.0e-4, 1.9e-4, 1.8e-4, 7.103532818497627e-05], H=H, H_hash=H_prefix)

        m = nm.build_manifest(npz)
        ok, failures = nm.verify_manifest(m, npz)
        check("clean manifest verifies OK", ok, "; ".join(failures))

        # (1) missing H_hash -> FAIL
        npz_noh, _ = _synthetic(tmp, "71x58_noh", n_iter=325,
                                last4_G=[3.075537678965121e25, 3.075549e25, 3.075706e25, 3.0757521592531657e25],
                                last4_T=[9.264317e13, 9.264350e13, 9.265654e13, 9.2643797265133e13],
                                last4_R=[2.0e-4, 1.9e-4, 1.8e-4, 7.103532818497627e-05],
                                H=None, H_hash="abc123def456")
        m_noh = nm.build_manifest(npz_noh)
        ok, failures = nm.verify_manifest(m_noh, npz_noh)
        check("missing H_hash -> FAIL", not ok and any("H" in f for f in failures), "; ".join(failures))

        # (2) changed Phi_gate -> FAIL
        m_pg = copy.deepcopy(m)
        m_pg["frozen"]["Phi_gate"] = -0.75
        ok, failures = nm.verify_manifest(m_pg, npz)
        check("changed Phi_gate -> FAIL", not ok and any("frozen" in f for f in failures), "; ".join(failures))

        # (3) changed warm-source SHA -> FAIL
        warm_npz, _ = _synthetic(tmp, "71x58_warm", n_iter=325,
                                 last4_G=[3.075537678965121e25, 3.075549e25, 3.075706e25, 3.0757521592531657e25],
                                 last4_T=[9.264317e13, 9.264350e13, 9.265654e13, 9.2643797265133e13],
                                 last4_R=[2.0e-4, 1.9e-4, 1.8e-4, 7.103532818497627e-05], H=H, H_hash=H_prefix)
        # make a node whose warm_source points at a REAL file so build_manifest records a SHA
        z = dict(np.load(warm_npz, allow_pickle=True))
        z["warm_source"] = "she2d_richardson_71x58_warm.npz"
        warm2 = os.path.join(tmp, "she2d_richardson_100x70.npz")
        np.savez(warm2, **z)
        m_warm = nm.build_manifest(warm2)
        check("warm node records a warm-source SHA", m_warm["warm_source_sha256"] is not None)
        m_bad = copy.deepcopy(m_warm)
        m_bad["warm_source_sha256"] = "0" * 64
        ok, failures = nm.verify_manifest(m_bad, warm2)
        check("changed warm-source SHA -> FAIL", not ok and any("warm" in f for f in failures), "; ".join(failures))
    finally:
        nm._git = old_git
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_num01()
    test_num02()
    print("\nRESULT: %s" % ("ALL PASS" if not FAIL else "FAILURES: %s" % ", ".join(FAIL)))
    sys.exit(0 if not FAIL else 1)
