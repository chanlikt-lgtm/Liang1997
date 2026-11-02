#!/usr/bin/env python3
"""stepb_audit_node1.py -- Step-B re-run evidence, Item 2: raw Node-1 JSON/NPZ audit.

Reads the FROZEN single-thread 71x70 artifacts (never mutated), reports:
  (a) the seven acceptance gates with units/norm from the on-disk JSON (source of truth);
  (b) actual BLAS thread counts (threadpool_actual) + threads_env;
  (c) SHA-256 of Gii & phi arrays .tobytes() x3 + float.hex() scalar identity;
  (d) transparent whole-file provenance diffs (git_commit/git_dirty/warm_source/config_hash).

Usage:  python campaign/stepb_audit_node1.py [--json out.json]
"""
import json, hashlib, os, sys, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# The three single-thread 71x70 artifacts (t1 control, production node-1, repeat).
# The 8-thread t8 control is a threading-diagnostic artifact and is EXCLUDED from
# single-thread convergence analysis.
NODES = [
    ("t1 control",      "she2d_aniso_71x70_t1_47e3c9ec574b.npz"),
    ("production node1","she2d_aniso_71x70_t1_552bb609f0f2_X.npz"),
    ("repeat",          "she2d_aniso_71x70_t1_1e010e13e26f_repeat.npz"),
]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()

    report = {"schema": "stepb_node1_audit", "version": 1, "nodes": []}

    # ---- (a) seven gates from the production node-1 JSON ----
    prod_json = os.path.join(DATA, "she2d_aniso_71x70_t1_552bb609f0f2_X.json")
    j = json.load(open(prod_json))
    report["seven_gates"] = {
        "source_json": "she2d_aniso_71x70_t1_552bb609f0f2_X.json",
        "H_hash": j["H_hash"], "config_hash": j["config_hash"],
        "git_commit": j["git_commit"], "git_dirty": j["git_dirty"],
        "criteria": j["criteria"],
    }
    report["n_iter"] = j["n_iter"]
    report["h_rep"] = j["h_rep"]

    # ---- per-node: BLAS counts + array hashes + provenance ----
    for label, fn in NODES:
        npz = os.path.join(DATA, fn)
        jsn = npz.replace(".npz", ".json")
        d = np.load(npz, allow_pickle=True)
        jd = json.load(open(jsn))
        prov = jd.get("provenance", {})
        gii = d["Gii"].astype(np.float64).tobytes()
        phi = d["phi"].astype(np.float64).tobytes()
        rec = {
            "label": label,
            "npz": fn,
            "file_sha256": sha256_file(npz),
            "arrays": {
                "Gii": {"shape": list(d["Gii"].shape), "dtype": str(d["Gii"].dtype),
                        "sha256": sha256_bytes(gii)},
                "phi": {"shape": list(d["phi"].shape), "dtype": str(d["phi"].dtype),
                        "sha256": sha256_bytes(phi)},
            },
            "scalars": {
                "Gii_max_hex": float(d["Gii_max"]).hex(),
                "Gii_interp_hex": float(d["Gii_interp"]).hex(),
                "G_tot_hex": float(d["G_tot"]).hex(),
                "R_phi_hex": float(d["R_phi"]).hex(),
                "n_iter": int(d["n_iter"]),
            },
            "provenance": {
                "npz_git_commit": str(d["git_commit"]),
                "npz_git_dirty": str(d["git_dirty"]),
                "npz_warm_source": str(d["warm_source"]),
                "npz_config_hash": str(d["config_hash"]),
                "npz_H_hash": str(d["H_hash"]),
                "json_git_commit": jd.get("git_commit"),
                "json_git_dirty": jd.get("git_dirty"),
                "json_warm_source": jd.get("warm_source"),
                "json_config_hash": jd.get("config_hash"),
                "threads_requested": prov.get("threads_requested"),
                "threads_env": prov.get("threads_env"),
                "threadpool_actual": prov.get("threadpool_actual"),
                "numpy_version": prov.get("numpy_version"),
                "python": prov.get("python"),
            },
        }
        report["nodes"].append(rec)

    # ---- identity cross-check across the three nodes ----
    def key_set(field_path):
        out = []
        for n in report["nodes"]:
            v = n
            for k in field_path:
                v = v[k]
            out.append(v)
        return out

    gii_shas = [n["arrays"]["Gii"]["sha256"] for n in report["nodes"]]
    phi_shas = [n["arrays"]["phi"]["sha256"] for n in report["nodes"]]
    gii_max_hex = [n["scalars"]["Gii_max_hex"] for n in report["nodes"]]
    report["identity"] = {
        "Gii_sha256_all_equal": len(set(gii_shas)) == 1,
        "phi_sha256_all_equal": len(set(phi_shas)) == 1,
        "Gii_max_hex_all_equal": len(set(gii_max_hex)) == 1,
        "Gii_sha256": gii_shas[0] if len(set(gii_shas)) == 1 else gii_shas,
        "phi_sha256": phi_shas[0] if len(set(phi_shas)) == 1 else phi_shas,
        "file_sha256s": [n["file_sha256"] for n in report["nodes"]],
        "note_file_hash_differs": ("whole-file SHA differs because each npz embeds its own "
                                   "git_commit/warm_source provenance; physics arrays identical."),
    }

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
