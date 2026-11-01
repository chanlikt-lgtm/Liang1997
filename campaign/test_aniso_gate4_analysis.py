"""Unit tests for the Gate-4 analysis harness -- SYNTHETIC sequences only (no real sweep data yet).

Covers the frozen section-3.1 criterion: known contraction ratios, converging / diverging / non-monotone
series, and every pre-specified edge case (zero denominator, below-noise-floor, 4-level second-r,
certified-only input exclusion, family level ordering, one-sided Y flags).
"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import aniso_gate4_analysis as g4


def _series(ds):
    return g4.analyze_series(ds, d_floor=0.0)


def test_rel_diff_symmetric():
    assert g4.rel_diff(1.0, 1.0) == 0.0
    assert g4.rel_diff(1.0, 2.0) == 2.0 / 3.0
    assert abs(g4.rel_diff(2.0, 1.0) - 2.0 / 3.0) < 1e-15


def test_rel_diff_both_zero_is_none():
    assert g4.rel_diff(0.0, 0.0) is None
    assert g4.rel_diff(0.0, 1.0) == 2.0  # not both zero -> finite


def test_converging_monotone_r_lt_1():
    # v=[1, 1.05, 1.055]: d12=0.04878, d23=0.004751, r~0.0974
    r = _series([1.0, 1.05, 1.055])
    assert r["monotone"] is True
    assert r["status"] == "CONVERGING"
    assert r["r"] < 1.0
    assert r["finest_discrete_estimate"] == 1.055


def test_diverging_r_ge_1():
    # v=[1, 1.05, 1.11]: d12=0.04878, d23=0.05556, r~1.139 > 1
    r = _series([1.0, 1.05, 1.11])
    assert r["monotone"] is True
    assert r["r"] >= 1.0
    assert r["status"] == "NON-CONVERGENT/UNRESOLVED"
    assert "r>=1" in r["reason"]


def test_non_monotone_is_unresolved():
    r = _series([1.0, 1.05, 1.02])
    assert r["monotone"] is False
    assert r["status"] == "NON-CONVERGENT/UNRESOLVED"
    assert r["reason"] == "non-monotone"


def test_decreasing_converging_series():
    # monotone decreasing, contracting: [1.11, 1.05, 1.001]
    r = _series([1.11, 1.05, 1.001])
    assert r["monotone"] is True
    assert r["status"] == "CONVERGING"


def test_zero_denominator_edge_case():
    r = _series([0.0, 0.0, 0.0])
    assert r["status"] == "N/A"
    assert "zero denominator" in r["reason"]


def test_below_noise_floor_indeterminate():
    # d12 tiny -> indeterminate, r not computed
    r = g4.analyze_series([1.0, 1.0 + 1e-12, 2.0], d_floor=1e-6)
    assert r["status"] == "INDETERMINATE"
    assert r["r"] is None


def test_noise_floor_zero_allows_tiny_d12():
    # d_floor=0 (default for bit-identical Gii): even a small d12 is judged by r
    r = _series([1.0, 1.0 + 1e-9, 1.0 + 1e-9 + 1e-12])
    assert r["status"] == "CONVERGING"


def test_trench_class_narrative_flag():
    # r >= 3 -> trench_class label, but verdict is still just UNRESOLVED (not a threshold)
    r = _series([1.0, 1.01, 1.05])  # d12=0.00995, d23=0.0388, r~3.9
    assert r["r"] >= 3.0
    assert r["trench_class"] is True
    assert r["status"] == "NON-CONVERGENT/UNRESOLVED"


def test_four_level_second_r():
    # 4 levels -> two contraction ratios; converging iff all r < 1 and monotone
    r = g4.analyze_series([1.0, 1.05, 1.055, 1.057])
    assert r["n_levels"] == 4
    assert len(r["ratios"]) == 2
    assert r["status"] == "CONVERGING"


def test_insufficient_levels():
    r = _series([1.0, 2.0])
    assert r["status"] == "INSUFFICIENT"


# ---- certified-only input + family ordering ---------------------------------
def _node(Nx, Ny, Gii, x=0.5, status="CERTIFIED", certified=True, fwhm_flags=None, G_tot=1.0,
          width=0.002, family=None):
    return dict(Nx=Nx, Ny=Ny, family=family, status=status, certified=certified,
                Gii_interp=Gii, Gii_max=Gii * 1.1,
                xy_Gii_max_interp=[x, 0.0], avalanche_y_fwhm=width,
                fwhm_flags=fwhm_flags or dict(boundary_truncated=True), G_tot=G_tot)


def test_load_certified_excludes_uncertified():
    td = tempfile.mkdtemp()
    paths = []
    specs = [(71, 70, "CERTIFIED", True), (100, 70, "UNRESOLVED", False),
             (141, 70, "FAILED", False), (200, 70, "CERTIFIED", True)]
    for Nx, Ny, st, cert in specs:
        p = os.path.join(td, "n_%dx%d.json" % (Nx, Ny))
        json.dump(_node(Nx, Ny, 1.0, status=st, certified=cert), open(p, "w"))
        paths.append(p)
    nodes, skipped, ambiguous = g4.load_certified_nodes(paths)
    assert set(nodes) == {(None, 71, 70), (None, 200, 70)}
    assert len(skipped) == 2
    assert ambiguous == []


def test_load_certified_excludes_multithread_control():
    # v1.6 is single-thread: an 8-thread control at the same level must NOT be treated as a sweep node
    td = tempfile.mkdtemp()
    p1 = os.path.join(td, "n_t1.json")
    p8 = os.path.join(td, "n_t8.json")
    d1 = _node(71, 70, 2.690, fwhm_flags=dict(boundary_truncated=True))
    d8 = _node(71, 70, 2.576, fwhm_flags=dict(boundary_truncated=True))
    d1["provenance"] = dict(threads_requested=1)
    d8["provenance"] = dict(threads_requested=8)
    json.dump(d1, open(p1, "w"))
    json.dump(d8, open(p8, "w"))
    nodes, skipped, ambiguous = g4.load_certified_nodes([p1, p8])
    assert set(nodes) == {(None, 71, 70)}
    assert nodes[(None, 71, 70)]["Gii_interp"] == 2.690
    assert any("multi-thread" in why for _, why in skipped)


def test_load_certified_separates_xy_anchor():
    """F2: the shared (100,70) anchor must be kept as SEPARATE X- and Y-family records, and each
    family's analysis must read its OWN anchor -- never substitute one for the other."""
    td = tempfile.mkdtemp()
    px = os.path.join(td, "x_anchor.json")
    py = os.path.join(td, "y_anchor.json")
    dx = _node(100, 70, 2.00, family="X"); dx["provenance"] = dict(threads_requested=1)
    dy = _node(100, 70, 3.00, family="Y"); dy["provenance"] = dict(threads_requested=1)
    json.dump(dx, open(px, "w"))
    json.dump(dy, open(py, "w"))
    nodes, skipped, ambiguous = g4.load_certified_nodes([px, py])
    # both anchors survive, keyed by family
    assert nodes[("X", 100, 70)]["Gii_interp"] == 2.00
    assert nodes[("Y", 100, 70)]["Gii_interp"] == 3.00
    assert ambiguous == []
    # each family's analysis reads its OWN anchor, not the other's
    x_nodes = {("X", 71, 70): _node(71, 70, 1.80, family="X"),
               ("X", 100, 70): nodes[("X", 100, 70)],
               ("X", 141, 70): _node(141, 70, 2.10, family="X")}
    y_nodes = {("Y", 100, 58): _node(100, 58, 2.80, family="Y"),
               ("Y", 100, 70): nodes[("Y", 100, 70)],
               ("Y", 100, 85): _node(100, 85, 3.10, family="Y")}
    fam_x = g4.analyze_family("X", x_nodes, g4.OBSERVABLES["X"], g4.FAMILIES["X"]["levels"])
    fam_y = g4.analyze_family("Y", y_nodes, g4.OBSERVABLES["Y"], g4.FAMILIES["Y"]["levels"])
    x_vals = fam_x["observables"]["Gii_interp"]["values"]   # (71,70),(100,70),(141,70)
    y_vals = fam_y["observables"]["Gii_interp"]["values"]   # (100,58),(100,70),(100,85)
    assert x_vals[1] == 2.00   # X-family reads its own (100,70) anchor
    assert y_vals[1] == 3.00   # Y-family reads its own (100,70) anchor


def test_family_level_ordering_coarse_to_fine():
    # X refines Nx -> order (71,70),(100,70),(141,70); Y refines Ny -> (100,58),(100,70),(100,85)
    x = g4._sort_levels("X", [(100, 70), (141, 70), (71, 70)])
    assert x == [(71, 70), (100, 70), (141, 70)]
    y = g4._sort_levels("Y", [(100, 85), (100, 58), (100, 70)])
    assert y == [(100, 58), (100, 70), (100, 85)]


def test_analyze_gate4_y_reports_flags_and_converges():
    # synthetic Y-family: surface peak converging, one-sided width, G_tot -- all with real variation
    nodes = {
        ("Y", 100, 58): _node(100, 58, 2.60, G_tot=90.0, width=0.0024,
                               fwhm_flags=dict(boundary_truncated=True), family="Y"),
        ("Y", 100, 70): _node(100, 70, 2.66, G_tot=91.0, width=0.0021,
                               fwhm_flags=dict(boundary_truncated=True), family="Y"),
        ("Y", 100, 85): _node(100, 85, 2.68, G_tot=91.4, width=0.00195,
                               fwhm_flags=dict(boundary_truncated=True), family="Y"),
    }
    rep = g4.analyze_gate4(nodes, d_floor=0.0)
    fam = rep["families"]["Y"]
    assert fam["observables"]["Gii_interp"]["status"] == "CONVERGING"
    assert fam["observables"]["G_tot"]["status"] == "CONVERGING"
    assert fam["observables"]["onesided_width"]["status"] == "CONVERGING"
    # per-level flags report hotspot_y + boundary_truncated (amendment item 4)
    assert all("hotspot_y" in f and "boundary_truncated" in f for f in fam["flags"])
    assert all(f["boundary_truncated"] is True for f in fam["flags"])


def test_flat_series_no_change():
    # all three identical -> no resolvable change, not a division-by-zero crash
    r = _series([1.0, 1.0, 1.0])
    assert r["status"] == "NO-CHANGE"
    assert r["finest_discrete_estimate"] == 1.0
    # coarse pair identical but a finer pair moves -> indeterminate (r undefined), no crash
    r2 = _series([1.0, 1.0, 1.1])
    assert r2["status"] == "INDETERMINATE"
    assert r2["r"] is None


def test_analyze_gate4_missing_node_is_incomplete():
    nodes = {("Y", 100, 58): _node(100, 58, 2.6, family="Y"),
             ("Y", 100, 70): _node(100, 70, 2.66, family="Y")}
    rep = g4.analyze_gate4(nodes, d_floor=0.0)
    fam = rep["families"]["Y"]
    assert fam["missing"] == [(100, 85)]
    assert fam["observables"]["Gii_interp"]["status"] == "INCOMPLETE"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ok = 0
    for fn in fns:
        try:
            fn()
            print("PASS  %s" % fn.__name__)
            ok += 1
        except Exception:
            print("FAIL  %s" % fn.__name__)
            traceback.print_exc()
    print("\nRESULT: %d/%d PASS" % (ok, len(fns)))
    sys.exit(0 if ok == len(fns) else 1)
