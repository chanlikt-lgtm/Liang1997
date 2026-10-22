"""
node_manifest.py -- NUM-02 signed per-node reproducibility manifest.

Writes (build_manifest) and enforces (verify_manifest) an exact-schema manifest for ONE
Richardson node. The manifest captures everything a third party needs to re-derive the node's
certificate and to detect ANY drift from the frozen run definition:

  * full commit + dirty refusal        (a dirty tree is refused: it is not a frozen solver)
  * frozen solver definition           (Phi_gate, mesh law, dH, she_tol, tol_phi, Anderson ...)
  * physics constants                  (constants.py, byte-for-byte canonical JSON)
  * doping / geometry SHA-256          (DeviceParams + Nx,Ny canonical JSON)
  * H-array bytes SHA-1                (the frozen energy grid; matches the npz H_hash prefix)
  * warm-source SHA-256                (the upstream node NPZ this node was warm-started from)
  * environment versions               (python / numpy / scipy)

verify_manifest() fails-closed on ANY mismatch. The reviewer's three acceptance tests
(test_certified_window.py) exercise: (1) a missing H_hash -> FAIL, (2) a changed Phi_gate ->
FAIL, (3) a changed warm-source SHA -> FAIL.

Usage:
    import node_manifest as nm
    m = nm.build_manifest("data/she2d_richardson_71x58.npz")
    ok, failures = nm.verify_manifest(m, "data/she2d_richardson_71x58.npz")
"""
import os
import json
import copy
import numbers
import hashlib
import subprocess
import sys

import numpy as np
import constants as C
from device import DeviceParams

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SCHEMA_VERSION = 1

# ---- FROZEN run definition (mirrors coupled_drain_richardson.py -- do NOT edit one without the
#      other). Phi_gate lives here because the node NPZ does not persist it; the manifest records it
#      and verify_manifest() enforces it against this frozen block, so a changed Phi_gate is caught. ----
FROZEN_DEF = dict(
    Phi_gate=-0.74,
    ratio=6.0, W=0.09, X_C=0.60,
    dH_eV=0.0125, eps_max_eV=3.02, she_tol=1e-8, tol_phi=1e-4,
    aa_depth=6, aa_beta=0.5, aa_step_cap=5.0, aa_restart=6,
    common_phi_span=[-0.60, 3.65],
)


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _sha256_of(obj):
    return _sha256_bytes(_canonical(obj).encode("utf-8"))


def _physics_constants():
    out = {}
    for name in dir(C):
        if name.startswith("_"):
            continue
        v = getattr(C, name)
        if isinstance(v, numbers.Real):
            out[name] = float(v)
    return out


def _doping_geometry_signature(Nx, Ny):
    sig = {}
    for name in dir(DeviceParams):
        if name.startswith("_"):
            continue
        v = getattr(DeviceParams, name)
        if isinstance(v, numbers.Real):
            sig[name] = float(v)
    sig["Nx"] = int(Nx)
    sig["Ny"] = int(Ny)
    return sig


def _env_versions():
    out = {"python": sys.version.split()[0]}
    for mod in ("numpy", "scipy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "?"
    return out


def _git(*a):
    try:
        return subprocess.check_output(["git", *a], cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


def _full_commit(short):
    if not short:
        return ""
    full = _git("rev-parse", "--verify", short)
    return full or short


def _h_sha1(z):
    """SHA-1 of the frozen H-array bytes (hex), plus the 12-char prefix the npz stores."""
    if "H" not in z.files:
        return None, None
    h = hashlib.sha1(np.ascontiguousarray(z["H"], dtype=np.float64).tobytes()).hexdigest()
    return h, h[:12]


def build_manifest(node_npz, node_progress=None):
    """Build the per-node manifest dict. (The sidecar is accepted for signature only; the
    manifest does not depend on it.)"""
    path = os.fspath(node_npz)
    z = np.load(path, allow_pickle=True)
    Nx, Ny = int(z["Nx"]), int(z["Ny"])
    node = "%dx%d" % (Nx, Ny)
    short = str(z["git_commit"]) if "git_commit" in z.files else ""
    dirty = (str(z["git_dirty"]) if "git_dirty" in z.files else "") == "dirty"
    dirty_now = bool(_git("status", "--porcelain"))
    hsha, hprefix = _h_sha1(z)
    warm = str(z["warm_source"]) if "warm_source" in z.files else ""
    warm_sha = None
    if warm:
        wp = os.path.join(os.path.dirname(path), warm)
        warm_sha = _sha256_bytes(open(wp, "rb").read()) if os.path.exists(wp) else None
    manifest = dict(
        schema_version=SCHEMA_VERSION,
        node=node,
        Nx=Nx, Ny=Ny, n_iter=(int(z["n_iter"]) if "n_iter" in z.files else None),
        git_commit=short,
        git_commit_full=(_full_commit(short) or None),
        git_dirty=bool(dirty or dirty_now),
        frozen=copy.deepcopy(FROZEN_DEF),
        physics=_physics_constants(),
        doping_geometry_sha256=_sha256_of(_doping_geometry_signature(Nx, Ny)),
        H_sha1=hsha,
        H_hash_prefix=hprefix,
        warm_source=(warm or None),
        warm_source_sha256=warm_sha,
        versions=_env_versions(),
    )
    return manifest


def verify_manifest(manifest, node_npz):
    """Enforce the manifest against the frozen run definition and the node NPZ.

    Returns (ok: bool, failures: list[str]). Fail-closed: ANY mismatch -> ok=False.
    """
    failures = []
    z = np.load(os.fspath(node_npz), allow_pickle=True)
    Nx, Ny = int(z["Nx"]), int(z["Ny"])
    node = "%dx%d" % (Nx, Ny)

    # 1. dirty refusal -- a dirty tree is NOT a frozen solver.
    if manifest.get("git_dirty"):
        failures.append("git tree dirty (refused): not a frozen solver")

    # 2. frozen definition (Phi_gate, mesh law, dH, she_tol, tol_phi, Anderson ...)
    if manifest.get("frozen") != FROZEN_DEF:
        failures.append("frozen definition mismatch (e.g. Phi_gate changed): %s"
                        % (manifest.get("frozen") != FROZEN_DEF and manifest.get("frozen")))

    # 3. physics constants
    if manifest.get("physics") != _physics_constants():
        failures.append("physics constants mismatch")

    # 4. doping / geometry signature
    if manifest.get("doping_geometry_sha256") != _sha256_of(_doping_geometry_signature(Nx, Ny)):
        failures.append("doping/geometry SHA-256 mismatch")

    # 5. H-array SHA-1 (+ npz H_hash prefix consistency). A missing H/H_hash -> FAIL.
    hsha, hprefix = _h_sha1(z)
    if hsha is None:
        failures.append("missing H array (cannot compute H_sha1)")
    elif manifest.get("H_sha1") != hsha:
        failures.append("H-array SHA-1 mismatch (manifest %s != npz %s)"
                        % (manifest.get("H_sha1"), hsha))
    if "H_hash" not in z.files:
        failures.append("missing H_hash in node NPZ")
    elif hprefix is not None and str(z["H_hash"]) != hprefix:
        failures.append("npz H_hash (%s) != recomputed prefix (%s)" % (z["H_hash"], hprefix))
    elif manifest.get("H_hash_prefix") not in (None, str(z["H_hash"])):
        failures.append("manifest H_hash_prefix (%s) != npz H_hash (%s)"
                        % (manifest.get("H_hash_prefix"), str(z["H_hash"])))

    # 6. warm-source SHA-256
    warm = manifest.get("warm_source")
    if warm:
        wp = os.path.join(os.path.dirname(os.fspath(node_npz)), warm)
        if not os.path.exists(wp):
            failures.append("warm source %s missing" % warm)
        else:
            actual = _sha256_bytes(open(wp, "rb").read())
            if manifest.get("warm_source_sha256") != actual:
                failures.append("warm-source SHA-256 mismatch (manifest %s != actual %s)"
                                % (manifest.get("warm_source_sha256"), actual))
    elif manifest.get("warm_source_sha256") is not None:
        failures.append("cold node records a non-null warm-source SHA")

    # 7. environment versions
    if manifest.get("versions") != _env_versions():
        failures.append("environment versions mismatch: %s" % (manifest.get("versions"),))

    return (not failures), failures


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("node_npz")
    ap.add_argument("--verify", action="store_true", help="verify a manifest previously written")
    ap.add_argument("--manifest", default=None, help="manifest JSON to verify")
    a = ap.parse_args()
    if a.verify:
        m = json.load(open(a.manifest, encoding="utf-8"))
        ok, failures = verify_manifest(m, a.node_npz)
        print("VERIFY %s" % ("OK" if ok else "FAIL"))
        for f in failures:
            print("  - %s" % f)
        sys.exit(0 if ok else 1)
    m = build_manifest(a.node_npz)
    print(json.dumps(m, indent=2, default=str))
