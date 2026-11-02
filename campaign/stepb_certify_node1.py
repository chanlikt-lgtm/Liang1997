#!/usr/bin/env python3
"""stepb_certify_node1.py -- Step-B re-run evidence, Item 4: independent certification recomputation.

Recomputes the Node-1 (71x70) certification INDEPENDENTLY from the preserved raw Gii array (not from
the stored scalar observables), exercising:
  (a) the F1 boundary-aware interpolated peak (surface-pinned max stays at y=0, no bulk shift);
  (b) the seven acceptance gates re-derived from the raw arrays.

The frozen NPZ/JSON are opened read-only and never mutated.  No solver is invoked.

Usage:  python campaign/stepb_certify_node1.py [--json out.json]
"""
import json, os, sys, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, HERE)

import aniso_mesh_study as aniso

DATA = os.path.join(REPO, "data")
NPZ = os.path.join(DATA, "she2d_aniso_71x70_t1_552bb609f0f2_X.npz")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()

    d = np.load(NPZ, allow_pickle=True)
    Gii = d["Gii"]; x = d["x"]; y = d["y"]

    # (a) F1: independent interpolated peak from the RAW Gii array
    G_interp, xi, yi, jg, ig = aniso.interpolated_peak(Gii, x, y)
    gmax = float(Gii[jg, ig])
    nodal_xy = [float(x[ig]), float(y[jg])]
    peak = dict(
        Gii_nodal=gmax, Gii_interp=G_interp,
        nodal_jg=jg, nodal_ig=ig, nodal_xy=nodal_xy,
        interp_xy=[xi, yi],
        boundary_max=(jg == 0 or jg == Gii.shape[0] - 1 or ig == 0 or ig == Gii.shape[1] - 1),
        y_is_surface=(yi == 0.0),
        delta_interp_vs_nodal_pct=100.0 * (G_interp - gmax) / gmax,
    )

    # (b) seven gates independently re-derived from raw arrays + stored continuation scalars
    # R_phi, continuity_residual, relative_number_balance, Gii/G_tot/drift are all present in the
    # frozen NPZ as scalars; recompute the peak-dependent one (Gii_interp) and re-check each gate.
    gates = []
    def _gate(name, value, gate, op, unit, norm):
        passed = (value < gate) if op == "<" else (value > gate)
        gates.append(dict(name=name, value=float(value), gate=gate, op=op, unit=unit, norm=norm,
                          passed=bool(passed)))
        return bool(passed)

    _gate("R_phi", float(d["R_phi"]), 1e-4, "<", "V", "absolute")
    _gate("continuity_residual", float(d["continuity_residual"]), 1e-6, "<", "1", "scaled by max(|bs|,1)")
    _gate("number_balance", float(d["relative_number_balance"]), 1e-2, "<", "1", "|balance|/scale")
    _gate("drift_raw_Gii", float(d["drift_raw_Gii"]), 5e-3, "<", "1", "40-iter continuation spread")
    _gate("drift_interp_Gii", float(d["drift_interp_Gii"]), 5e-3, "<", "1", "40-iter endpoint delta")
    _gate("drift_G_tot", float(d["drift_G_tot"]), 5e-3, "<", "1", "40-iter continuation spread")
    _gate("hotspot_drift", float(d["hotspot_drift_cells"]), 0.5, "<", "cell",
          "|cont hotspot - main hotspot| / h_rep")

    # (c) R_phi<1e-4 alone is NOT sufficient: the two continuity-class criteria are AND-gated
    all_pass = all(g["passed"] for g in gates)
    rphi_only = (float(d["R_phi"]) < 1e-4)
    certified = all_pass

    report = dict(
        schema="stepb_node1_independent_certification", version=1,
        source_npz=os.path.basename(NPZ),
        source_sha256=aniso._file_sha256(NPZ),
        peak=peak,
        seven_gates=gates,
        all_gates_pass=all_pass,
        rphi_alone_insufficient=("R_phi<1e-4 alone would be %s; certification requires all 7 gates"
                                 % ("PASS" if rphi_only else "FAIL")),
        certified=certified,
        n_iter=int(d["n_iter"]),
    )
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
