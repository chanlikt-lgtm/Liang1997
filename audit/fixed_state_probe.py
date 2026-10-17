#!/usr/bin/env python3
"""Fixed-state reproducibility diagnostics for Liang1997 SHE-BTE.

Run OUTSIDE the frozen solver tree; no source edits are required.

1) On the canonical/reference machine, freeze the archived phi and contact state:
   python SHE_BTE_fixed_state_probe.py freeze --repo Liang1997 \
       --source Liang1997/data/she2d_richardson_71x58.npz \
       --state audit_state_71x58.npz

2) Copy the SAME audit_state_71x58.npz to both machines. On each, set
   OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1, MKL_NUM_THREADS=1,
   SHE2D_DISABLE_NUMBA=1 BEFORE Python starts. Then:
   python SHE_BTE_fixed_state_probe.py measure --repo Liang1997 \
       --state audit_state_71x58.npz --prefix audit_windows --save-matrix
   python SHE_BTE_fixed_state_probe.py measure --repo Liang1997 \
       --state audit_state_71x58.npz --prefix audit_linux --save-matrix

3) Compare JSON diagnostics and, if saved, CSR matrix dumps:
   python SHE_BTE_fixed_state_probe.py compare audit_windows.json audit_linux.json

Only after assembly agrees sufficiently, repeat measure with --solve to
compare the same A,b through LGMRES/spilu and its impact-ionization moments.
The script creates NEW sidecar files; it does not overwrite archived results.

Prepared from public source at closeout commit 930dd86. THIS IS AN UNRUN
DIAGNOSTIC HARNESS in this environment, not a claim of numerical validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np


def digest(x):
    a = np.ascontiguousarray(x)
    return hashlib.sha256(a.tobytes()).hexdigest()


def put_repo_on_path(repo):
    root = Path(repo).expanduser().resolve()
    if not (root / "src" / "she2d.py").exists():
        raise FileNotFoundError(f"Expected source at {root / 'src' / 'she2d.py'}")
    sys.path.insert(0, str(root / "src"))
    return root


def versions():
    import scipy
    d = {
        "python": platform.python_version(), "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "env": {k: os.environ.get(k) for k in (
            "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "SHE2D_DISABLE_NUMBA")},
    }
    try:
        from threadpoolctl import threadpool_info
        d["threadpool_info"] = threadpool_info()
        d["single_thread_verified"] = all(
            int(t.get("num_threads", -1)) == 1 for t in d["threadpool_info"])
    except ImportError:
        d["threadpool_info"] = "UNVERIFIED: install threadpoolctl"
        d["single_thread_verified"] = False
    return d


def freeze(args):
    put_repo_on_path(args.repo)
    from device import DeviceParams, build_doping
    from poisson import Poisson2D
    from dd import DDSolver
    with np.load(args.source, allow_pickle=False) as archive:
        x = np.asarray(archive["x"], dtype=np.float64).copy()
        y = np.asarray(archive["y"], dtype=np.float64).copy()
        phi = np.asarray(archive["phi"], dtype=np.float64).copy()
    if phi.shape != (len(y), len(x)):
        raise ValueError("Archived potential does not match x and y")
    dev = DeviceParams()
    X, Y = np.meshgrid(x, y)
    _nd, _na, nnet = build_doping(dev, X, Y)
    ps = Poisson2D(x, y, nnet, dev, Phi_gate=-0.74)
    dd = DDSolver(ps)
    ctype = np.asarray(ps.contact_type, dtype=np.int32)
    neq = np.asarray(dd.n_eq, dtype=np.float64)
    state = Path(args.state)
    state.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(state, x=x, y=y, phi=phi, ctype=ctype, neq=neq)
    out = {
        "source": str(args.source), "state": str(state),
        "shape": list(phi.shape),
        "sha256": {k: digest(v) for k, v in {
            "x": x, "y": y, "phi": phi, "ctype": ctype, "neq": neq}.items()},
        "note": "Copy this exact state file to both platforms; do not rebuild independently."
    }
    Path(str(state) + ".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


def fv_area_cm2(x, y):
    dx = np.empty(len(x), dtype=float)
    dy = np.empty(len(y), dtype=float)
    dx[1:-1] = 0.5 * (x[2:] - x[:-2]); dx[0] = 0.5*(x[1]-x[0]); dx[-1] = 0.5*(x[-1]-x[-2])
    dy[1:-1] = 0.5 * (y[2:] - y[:-2]); dy[0] = 0.5*(y[1]-y[0]); dy[-1] = 0.5*(y[-1]-y[-2])
    return np.outer(dy, dx) * 1e-8


def measure(args):
    put_repo_on_path(args.repo)
    from she2d import SHE2D
    import scipy.sparse as sp
    with np.load(args.state, allow_pickle=False) as state:
        x = np.asarray(state["x"], dtype=np.float64)
        y = np.asarray(state["y"], dtype=np.float64)
        phi = np.asarray(state["phi"], dtype=np.float64)
        ctype = np.asarray(state["ctype"], dtype=np.int32)
        neq = np.asarray(state["neq"], dtype=np.float64)
    if phi.shape != (len(y), len(x)) or neq.shape != phi.shape or ctype.shape != phi.shape:
        raise ValueError("Invalid frozen-state shapes")
    she = SHE2D(x, y, phi, ctype, neq, dHi_eV=0.0125,
                include_impact_ionization=True, absorbing_top=True,
                phi_span_H=(-0.60, 3.65))
    A, b = she.assemble(backend=args.backend)
    A = A.tocsr(copy=False)
    A.sum_duplicates()
    A.sort_indices()
    out = {
        "source_state": str(args.state), "repo": str(Path(args.repo).resolve()),
        "environment": versions(), "backend": she.assembly_backend,
        "Ndof": int(she.Ndof), "NH": int(she.NH), "nnz": int(A.nnz),
        "n_orphans": int(she.n_orphans),
        "state_sha256": {k: digest(v) for k, v in {
            "x": x, "y": y, "phi": phi, "ctype": ctype, "neq": neq}.items()},
        "assembly_sha256": {k: digest(v) for k, v in {
            "H": she.H, "active": she.active,
            "A_indptr": A.indptr, "A_indices": A.indices,
            "A_data": A.data, "b": b}.items()},
        "A_data_max_abs": float(np.max(np.abs(A.data))),
        "b_max_abs": float(np.max(np.abs(b))),
    }
    prefix = Path(args.prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    if args.save_matrix:
        sp.save_npz(str(prefix) + ".A.npz", A, compressed=True)
        np.save(str(prefix) + ".b.npy", b)
    if args.solve:
        she.solve(method=args.method, tol=args.tol)
        _n, _te, Gii = she.moments()
        raw = she.f_raw
        Fraw = np.zeros_like(she.eps, dtype=np.float64)
        Fraw[she.active] = raw
        G_raw = np.trapezoid(she.Z * Fraw * she.ii_rate, she.H, axis=2) * 1e-6
        eactive = she.eps[she.active]
        from scattering import II_ETH
        from constants import eV
        tail = eactive >= II_ETH*eV
        neg = raw < 0
        raw_abs_sum = float(np.sum(np.abs(raw)))
        neg_tail_abs = float(np.sum(np.abs(raw[neg & tail])))
        out["solve"] = {
            "method": args.method, "tol": args.tol, "info": int(she.info),
            "negative_count": int(np.count_nonzero(neg)),
            "negative_tail_count": int(np.count_nonzero(neg & tail)),
            "negative_l1_fraction": float(np.sum(np.abs(raw[neg])) / max(raw_abs_sum, 1e-300)),
            "negative_tail_l1_fraction_of_total": float(neg_tail_abs / max(raw_abs_sum, 1e-300)),
            "scaled_raw_residual_inf": float(she.scaled_raw_residual_inf),
            "scaled_clipped_residual_inf": float(she.scaled_residual_inf),
            "Gii_peak_cm3_s": float(Gii.max()),
            "Gii_raw_peak_cm3_s": float(G_raw.max()),
            "Gtot_cm_inv_s": float(np.sum(Gii*fv_area_cm2(x, y))),
            "Gii_hash": digest(Gii), "raw_f_hash": digest(raw),
            "clipped_f_hash": digest(she.f),
        }
        np.savez_compressed(str(prefix) + ".solution.npz", f_raw=raw, f= she.f,
                            Gii=Gii, Gii_raw=G_raw)
    Path(str(prefix) + ".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


def compare(args):
    from scipy.sparse import load_npz
    a = json.loads(Path(args.left).read_text(encoding="utf-8"))
    b = json.loads(Path(args.right).read_text(encoding="utf-8"))
    result = {}
    for family in ("state_sha256", "assembly_sha256"):
        keys = set(a.get(family, {})) | set(b.get(family, {}))
        result[family] = {k: a.get(family, {}).get(k) == b.get(family, {}).get(k)
                          for k in sorted(keys)}
    for k in ("Ndof", "NH", "nnz", "n_orphans", "backend"):
        result[k] = {"left": a.get(k), "right": b.get(k)}
    Ap = (Path(args.left).with_suffix(""))
    Bp = (Path(args.right).with_suffix(""))
    apath = Path(str(Ap) + ".A.npz")
    bpath = Path(str(Bp) + ".A.npz")
    if apath.exists() and bpath.exists():
        A = load_npz(apath); B = load_npz(bpath)
        structure_equal = (A.shape == B.shape and np.array_equal(A.indptr, B.indptr)
                           and np.array_equal(A.indices, B.indices))
        result["matrix_structure_equal"] = bool(structure_equal)
        if structure_equal:
            error = np.max(np.abs(A.data - B.data)) if A.nnz else 0.0
            scale = np.max(np.abs(A.data)) if A.nnz else 1.0
            result["A_data_max_abs_difference"] = float(error)
            result["A_data_max_scaled_difference"] = float(error/max(scale,1e-300))
    pa, pb = Path(str(Ap) + ".b.npy"), Path(str(Bp) + ".b.npy")
    if pa.exists() and pb.exists():
        av, bv = np.load(pa), np.load(pb)
        if av.shape == bv.shape:
            result["b_max_scaled_difference"] = float(
                np.max(np.abs(av-bv))/max(np.max(np.abs(av)), 1e-300))
    sa, sb = Path(str(Ap) + ".solution.npz"), Path(str(Bp) + ".solution.npz")
    if sa.exists() and sb.exists():
        with np.load(sa) as left, np.load(sb) as right:
            vals = {}
            for k in ("f_raw", "f", "Gii", "Gii_raw"):
                l, r = left[k], right[k]
                if l.shape != r.shape:
                    vals[k] = "shape mismatch"
                    continue
                dif = np.abs(l-r)
                vals[k] = {"relative_inf": float(np.max(dif)/max(np.max(np.abs(l)),1e-300)),
                           "absolute_inf": float(np.max(dif))}
            result["solutions"] = vals
    print(json.dumps(result, indent=2))
    if not all(result.get("state_sha256", {}).values()):
        print("STATE DIFFERENCE: do not attribute any later differences to sparse solving.")
    elif not all(result.get("assembly_sha256", {}).values()):
        print("ASSEMBLY DIFFERENCE: isolate mesh/coefficients/CSR/b before diagnosing Krylov.")
    else:
        print("IDENTICAL ASSEMBLY: downstream solver, clipping, and moments are next.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("freeze", help="Freeze the reference state once, then copy its bytes to every OS")
    p.add_argument("--repo", required=True); p.add_argument("--source", required=True)
    p.add_argument("--state", required=True); p.set_defaults(func=freeze)
    p = sub.add_parser("measure", help="Assemble/solve from exactly the same frozen input")
    p.add_argument("--repo", required=True); p.add_argument("--state", required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--backend", choices=("python", "numba"), default="python")
    p.add_argument("--save-matrix", action="store_true")
    p.add_argument("--solve", action="store_true")
    p.add_argument("--method", choices=("split_ilu", "direct", "legacy_ilu"), default="split_ilu")
    p.add_argument("--tol", type=float, default=1e-8)
    p.set_defaults(func=measure)
    p = sub.add_parser("compare", help="Compare two platform result files")
    p.add_argument("left"); p.add_argument("right"); p.set_defaults(func=compare)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
