"""
certified_window.py -- NUM-01 single authoritative reader for a node's certified
cumulative-window plateau evidence.

The Rev-6 trio certifies each node on the LAST FOUR REAL *cumulative* outer iterations,
spanning driver chunks. This module is the ONE place that:

  * reconstructs that 4-sample window -- persisted sidecar `plateau_buffer` first (the
    genuine cross-chunk window), else the NPZ terminal chunk (`last4_*`),
  * VALIDATES it (4 unique CONSECUTIVE absolute iterations, and the window's terminal
    Gii/G_tot/R_phi matching the NPZ terminal scalars), and
  * returns the certification quantities (mean_Gii / u_Gii / mean_Gtot / u_Gtot /
    Rphi_last) plus provenance.

Consumers (richardson_fit.py, run_richardson_trio.py, gen_run_report.py) all route through
read_certified_window() so the SAME window and the SAME u>0 half-range feed every downstream
verdict (Richardson S_rev, the trio scoreboard, and the auto report). Previously each
consumer reconstructed the window (or read the chunk-local last-4) independently, so a
degenerate 1-iteration terminal chunk could yield u=0 in one consumer and u>0 in another --
the exact inconsistency the reviewer's NUM-01 test targets.

Usage:
    import certified_window as cw
    w = cw.read_certified_window("data/she2d_richardson_71x58.npz",
                                 "data/she2d_richardson_71x58.progress.json")
    # w["valid"] is True iff a genuine 4-sample consecutive window was certified.
"""
import os
import json
import numpy as np
import plateau_gate as pg

WINDOW = 4
# Terminal-scalar match tolerance. The saved last4_*[-1] is bit-identical to Gii_max/G_tot/
# R_phi (same npz write) and a valid sidecar round-trips floats through JSON losslessly, so a
# tiny relative tolerance is ample; anything much looser would let a stale/mismatched sidecar
# (a genuinely different run, e.g. the pre-reversal 2.73e25 cold state) masquerade as current.
TERMINAL_RTOL = 1e-9


def _load(node_npz, node_progress):
    """Normalize node_npz (path or open NpzFile) -> (NpzFile, path, sidecar_path_or_None)."""
    if isinstance(node_npz, (str, os.PathLike)):
        path = os.fspath(node_npz)
        z = np.load(path, allow_pickle=True)
    else:
        z = node_npz
        path = getattr(node_npz, "path", None) or getattr(node_npz, "_file_name", None) or ""
    if node_progress is None and path:
        cand = os.path.splitext(path)[0] + ".progress.json"
        node_progress = cand if os.path.exists(cand) else None
    return z, path, node_progress


def validate_buffer(buffer, z):
    """Validate a rolling buffer (list of {abs_iter,Gii,Gtot,Rphi}) against the NPZ.

    Returns (ok, detail). Requires the abs_iters to be strictly increasing, unique, AND
    consecutive (diff==1), and the terminal sample to match the NPZ terminal scalars
    (Gii_max / G_tot / R_phi). Does NOT require 4 samples -- that is read_certified_window's
    job; this helper is also used to sanity-check an in-progress (<4-sample) resume buffer.
    """
    if not buffer:
        return False, "empty buffer"
    its = [int(b["abs_iter"]) for b in buffer]
    strictly_inc = all(its[i] < its[i + 1] for i in range(len(its) - 1))
    unique = len(set(its)) == len(its)
    consecutive = all(its[i + 1] == its[i] + 1 for i in range(len(its) - 1))
    if not (strictly_inc and unique):
        return False, "abs_iters not strictly increasing/unique: %s" % its
    if not consecutive:
        return False, "abs_iters not consecutive: %s" % its
    for key_src, key in (("Gii", "Gii_max"), ("Gtot", "G_tot"), ("Rphi", "R_phi")):
        if key not in z.files:
            continue
        if not np.isclose(buffer[-1][key_src], float(z[key]), rtol=TERMINAL_RTOL, atol=0.0):
            return False, ("terminal sample (%s=%.6e) != NPZ scalar (%s=%.6e)"
                           % (key_src, buffer[-1][key_src], key, float(z[key])))
    return True, "iters=%s" % its


def _validate_window(samples, z):
    """Validate a candidate window: >= WINDOW samples plus validate_buffer() on the last WINDOW."""
    if len(samples) < WINDOW:
        return False, "only %d real sample(s) (< %d)" % (len(samples), WINDOW)
    return validate_buffer(samples[-WINDOW:], z)


def _scalars(z):
    """Provenance scalars shared by the result dict."""
    return dict(
        H_hash=(str(z["H_hash"]) if "H_hash" in z.files else None),
        git_commit=(str(z["git_commit"]) if "git_commit" in z.files else None),
        git_dirty=(str(z["git_dirty"]) if "git_dirty" in z.files else None),
        warm_source=(str(z["warm_source"]) if "warm_source" in z.files else None),
    )


def read_certified_window(node_npz, node_progress=None):
    """Return the certified cumulative-window plateau evidence for one node.

    Returns a dict; `valid` is True only when a genuine 4-sample consecutive window could be
    certified. On any validation failure `valid=False` and `detail` explains why (callers must
    treat a non-valid window as NOT certifiable, never as u=0).
    """
    z, path, node_progress = _load(node_npz, node_progress)
    Nx = int(z["Nx"]); Ny = int(z["Ny"])
    node = "%dx%d" % (Nx, Ny)
    n_iter = int(z["n_iter"]) if "n_iter" in z.files else None

    # ---- candidate A: persisted sidecar plateau_buffer (authoritative cross-chunk window) ----
    sidecar_buf, sidecar_origin = None, None
    if node_progress and os.path.exists(node_progress):
        try:
            d = json.load(open(node_progress, encoding="utf-8"))
        except Exception:
            d = {}
        if isinstance(d, dict) and d.get("plateau_buffer"):
            sidecar_buf = list(d["plateau_buffer"])
            sidecar_origin = d.get("buffer_origin") or "persisted_sidecar"

    window, origin, rejected = None, None, None
    if sidecar_buf is not None:
        ok, det = _validate_window(sidecar_buf, z)
        if ok:
            window, origin = sidecar_buf[-WINDOW:], sidecar_origin
        else:
            rejected = "persisted_sidecar rejected: %s" % det

    # ---- candidate B: NPZ terminal chunk reconstruction (valid for a continuous run) ----
    if window is None:
        l4g = np.atleast_1d(np.asarray(z["last4_Gii_max"], float)) if "last4_Gii_max" in z.files else np.array([])
        l4t = np.atleast_1d(np.asarray(z["last4_G_tot"], float)) if "last4_G_tot" in z.files else np.array([])
        l4r = (np.atleast_1d(np.asarray(z["last4_R_phi"], float))
               if "last4_R_phi" in z.files else np.array([float(z["R_phi"])]))
        if l4g.size and l4t.size and l4r.size and n_iter is not None:
            try:
                npz_buf = pg.chunk_samples_from_last4(l4g, l4t, l4r, n_iter)
            except ValueError:
                npz_buf = []
            ok, det = _validate_window(npz_buf, z)
            if ok:
                window, origin = npz_buf[-WINDOW:], "npz_terminal_reconstruction"
            elif rejected is None:
                rejected = "npz_terminal_reconstruction rejected: %s" % det
        else:
            if rejected is None:
                rejected = "npz_terminal_reconstruction rejected: missing last4_*/n_iter"

    base = dict(valid=False, node=node, Nx=Nx, Ny=Ny, n_iter=n_iter, detail=rejected,
                sidecar_rejected=rejected, **_scalars(z))
    if window is None:
        base.update(dict(n_samples=0, window=[], iterations=[], buffer_origin=None,
                         mean_Gii=None, u_Gii=None, mean_Gtot=None, u_Gtot=None, Rphi_last=None,
                         spread_Gii=None, spread_Gtot=None))
        return base

    G = np.array([b["Gii"] for b in window], float)
    T = np.array([b["Gtot"] for b in window], float)
    R = np.array([b["Rphi"] for b in window], float)
    mean_G = float(G.mean()); u_G = float((G.max() - G.min()) / 2.0)
    mean_T = float(T.mean()); u_T = float((T.max() - T.min()) / 2.0)
    spread_G = float((G.max() - G.min()) / G.mean())
    spread_T = float((T.max() - T.min()) / T.mean())
    rphi_last = float(window[-1]["Rphi"])
    its = [int(b["abs_iter"]) for b in window]

    out = dict(valid=True, node=node, Nx=Nx, Ny=Ny, n_iter=n_iter, detail="certified",
               window=window, iterations=its, buffer_origin=origin, sidecar_rejected=rejected,
               n_samples=len(window),
               mean_Gii=mean_G, u_Gii=u_G, mean_Gtot=mean_T, u_Gtot=u_T, Rphi_last=rphi_last,
               spread_Gii=spread_G, spread_Gtot=spread_T, **_scalars(z))
    return out


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        print("usage: python certified_window.py <node.npz> [<node.progress.json>]")
        sys.exit(1)
    w = read_certified_window(args[0], args[1] if len(args) > 1 else None)
    print(json.dumps({k: w[k] for k in ("valid", "node", "detail", "buffer_origin",
          "iterations", "n_samples", "mean_Gii", "u_Gii", "mean_Gtot", "u_Gtot",
          "Rphi_last", "spread_Gii", "spread_Gtot", "H_hash", "git_commit", "warm_source",
          "sidecar_rejected")}, indent=2, default=str))
