"""
aniso_gate4_analysis.py -- Gate-4 (mesh-convergence) analysis harness. PRE-REGISTERED, FROZEN rules.

Reads CERTIFIED per-node json artifacts (and/or synthetic series) ONLY. Does NOT launch any run,
does NOT alter the frozen acceptance rules, and does NOT substitute for reviewer concurrence on the
Gate-4 amendment -- it is the analysis tool that will consume the sweep results when they exist.

Frozen rules implemented (spec v1.6 section 6 + docs/ANISO_GATE4_SURFACE_HOTSPOT_AMENDMENT_20261027.md,
incl. section 3.1 contraction criterion and the reviewer's 2026-10-28 edge cases):

  - Input = CERTIFIED nodes only; UNRESOLVED / FAILED / uncertified nodes are EXCLUDED (CP3 / S4).
  - Within each family, levels are ordered coarse -> fine (X refines Nx, Y refines Ny).
  - For each observable, adjacent relative differences d12, d23, contraction ratio r = d23/d12.
  - CONVERGING   <=> monotone AND r < 1   -> report finest as the best DISCRETE estimate (NO continuum).
  - NON-CONVERGENT / UNRESOLVED <=> r >= 1 OR non-monotone.  r >= 1 is a conservative gate, NOT proof
    of divergence; r < 1 is evidence CONSISTENT WITH convergence, NOT proof of a continuum.
  - Edge cases (frozen): |v_i|+|v_j| = 0 -> "N/A (both zero)"; d12 < d_floor -> r indeterminate,
    judged by absolute change against the observable noise floor (d_floor = measured run-to-run
    reproducibility; ~0 for the bit-identical Gii family).
  - "trench-class" (r >= 3) is a NARRATIVE comparison label (sister trench near-contact ~3.4-3.5),
    NOT a threshold.  Never part of the verdict.

Usage:
  python campaign/aniso_gate4_analysis.py [--data-dir ../data] [--out ../data/aniso_gate4_analysis.json]

Unit tests (synthetic sequences, known r / converging / diverging / all edge cases):
  python3 -m pytest campaign/test_aniso_gate4_analysis.py -q
"""
import os, sys, json, argparse

# ---- Frozen family geometry (mirrors the pre-registered spec; do NOT alter after seeing results) ----
FAMILIES = {
    "X": {"direction": "x-only (refine drain-x)", "fixed": "Ny=70",
          "levels": [(71, 70), (100, 70), (141, 70)]},
    "Y": {"direction": "y-only (refine depth-y)", "fixed": "Nx=100",
          "levels": [(100, 58), (100, 70), (100, 85)]},
}

# Refined axis per family: X refines Nx (axis 0), Y refines Ny (axis 1).
_REFINE_AXIS = {"X": 0, "Y": 1}


def _sort_levels(family, levels):
    ax = _REFINE_AXIS[family]
    return sorted(levels, key=lambda lv: lv[ax])


# ---------------------------------------------------------------------------
# Pure convergence functions (no I/O) -- the frozen section 3.1 criterion
# ---------------------------------------------------------------------------
def rel_diff(a, b):
    """Frozen relative difference d = 2|a-b|/(|a|+|b|).  None when both are zero (edge case)."""
    denom = abs(a) + abs(b)
    if denom == 0.0:
        return None
    return 2.0 * abs(a - b) / denom


def _monotone(values):
    """True iff the series never reverses direction (all nonzero successive diffs share one sign)."""
    diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    signs = {1 if d > 0 else (-1 if d < 0 else 0) for d in diffs}
    return not ({1, -1} <= signs)


def analyze_series(values, d_floor=0.0, name="series"):
    """Apply the frozen section-3.1 convergence/divergence criterion to a coarse->fine series (>=3).

    Returns a dict with values, monotone, d12/d23, r (and all ratios), status, reason, and (when
    converging) the finest discrete estimate.  Edge cases are reported explicitly, never guessed.
    """
    values = [float(v) for v in values]
    n = len(values)
    out = dict(name=name, values=values, n_levels=n, monotone=_monotone(values),
               d12=None, d23=None, diffs=None, r=None, ratios=None,
               trench_class=False, status=None, reason=None, finest_discrete_estimate=None)
    if n < 3:
        out["status"] = "INSUFFICIENT"
        out["reason"] = "need >= 3 levels (got %d)" % n
        return out
    ds = [rel_diff(values[i], values[i + 1]) for i in range(n - 1)]
    out["d12"] = ds[0]
    out["d23"] = ds[1]
    out["diffs"] = ds
    if any(d is None for d in ds[:2]):
        out["status"] = "N/A"
        out["reason"] = "zero denominator (both values zero in a pair)"
        return out
    # noise-floor / flat-coarse-pair edge case: d12 == 0 (identical coarse values) or below d_floor
    # means the contraction ratio r = d23/d12 is undefined / meaningless.
    if ds[0] < d_floor or ds[0] == 0.0:
        if all(d == 0.0 for d in ds):
            out["status"] = "NO-CHANGE"
            out["reason"] = "all levels identical (no resolvable change)"
            out["finest_discrete_estimate"] = values[-1]
        else:
            out["status"] = "INDETERMINATE"
            out["reason"] = ("coarse pair shows no resolvable change (d12=%.3g <= d_floor=%.3g); "
                              "cannot screen contraction" % (ds[0], d_floor))
        return out
    rs = [ds[i + 1] / ds[i] for i in range(n - 2)]
    out["r"] = rs[0]
    out["ratios"] = rs
    out["trench_class"] = any(r >= 3.0 for r in rs)
    if out["monotone"] and all(r < 1.0 for r in rs):
        out["status"] = "CONVERGING"
        out["finest_discrete_estimate"] = values[-1]
        out["reason"] = "monotone and r<1 (successive differences shrink)"
    elif not out["monotone"]:
        out["status"] = "NON-CONVERGENT/UNRESOLVED"
        out["reason"] = "non-monotone"
    else:
        out["status"] = "NON-CONVERGENT/UNRESOLVED"
        out["reason"] = "contraction ratio r>=1 (finer step moves >= coarser)"
    return out


# ---------------------------------------------------------------------------
# Observable definitions (frozen; per family)
# ---------------------------------------------------------------------------
# X-family (drain-x): peak value + hotspot x-location.
X_OBSERVABLES = [
    ("Gii_interp", "peak value (interpolated)", lambda r: r["Gii_interp"]),
    ("Gii_max",    "peak value (raw)",          lambda r: r["Gii_max"]),
    ("hotspot_x",  "hotspot x-location (um)",   lambda r: r["xy_Gii_max_interp"][0]),
]
# Y-family (depth-y, surface-pinned): surface-peak value, ONE-SIDED width (never symmetric FWHM), G_tot.
Y_OBSERVABLES = [
    ("Gii_interp", "surface peak value (interpolated)", lambda r: r["Gii_interp"]),
    ("Gii_max",    "surface peak value (raw)",          lambda r: r["Gii_max"]),
    ("onesided_width", "one-sided half-width (um, peak->bulk)", lambda r: r["avalanche_y_fwhm"]),
    ("G_tot",      "vertical integral G_tot",           lambda r: r["G_tot"]),
]
OBSERVABLES = {"X": X_OBSERVABLES, "Y": Y_OBSERVABLES}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_certified_nodes(paths, require_single_thread=True):
    """Read node JSONs from disk; return (nodes keyed by (Nx,Ny), skipped, ambiguous).

    CERTIFIED only.  When require_single_thread is True, nodes with an explicit
    threads_requested != 1 are EXCLUDED (they are multi-thread controls, not v1.6 sweep nodes).
    When several single-thread candidates share a (Nx,Ny), the family-tagged one wins and the
    alternates are surfaced in `ambiguous` (never silently mixed)."""
    nodes, skipped, ambiguous = {}, [], []
    by_level = {}
    for p in paths:
        try:
            with open(p) as fh:
                d = json.load(fh)
        except (OSError, ValueError) as e:
            skipped.append((p, "unreadable: %s" % e))
            continue
        if d.get("status") != "CERTIFIED" or d.get("certified") is not True:
            skipped.append((p, "status=%s certified=%s" % (d.get("status"), d.get("certified"))))
            continue
        prov = d.get("provenance") or {}
        thr = prov.get("threads_requested")
        if require_single_thread and thr is not None and thr != 1:
            skipped.append((p, "multi-thread control (threads_requested=%s)" % thr))
            continue
        lv = (int(d["Nx"]), int(d["Ny"]))
        by_level.setdefault(lv, []).append((p, d))
    for lv, cands in by_level.items():
        cands.sort(key=lambda pd: (pd[1].get("family") is not None, pd[1].get("family") or "", pd[0]))
        keep = cands[-1]
        nodes[lv] = keep[1]
        for p, d in cands[:-1]:
            ambiguous.append((p, "duplicate %dx%d; kept family=%s, ignored family=%s"
                              % (lv[0], lv[1], keep[1].get("family"), d.get("family"))))
    return nodes, skipped, ambiguous


# ---------------------------------------------------------------------------
# Family / gate analysis
# ---------------------------------------------------------------------------
def analyze_family(family, nodes, observables, levels, d_floor=0.0):
    """Analyze one family: order coarse->fine, run each observable through the frozen criterion,
    and attach per-level physical flags (hotspot location / boundary_truncated for Y)."""
    ordered = _sort_levels(family, levels)
    recs, missing = [], []
    for lv in ordered:
        if lv in nodes:
            recs.append(nodes[lv])
        else:
            missing.append(lv)
    fam = dict(family=family, direction=FAMILIES[family]["direction"],
               fixed=FAMILIES[family]["fixed"], levels=ordered, missing=missing, observables={})
    # per-level flags (reported explicitly, per the amendment item 4)
    flags = []
    for lv, r in zip(ordered, recs):
        f = dict(level="%dx%d" % lv)
        if family == "Y":
            f["hotspot_y"] = r["xy_Gii_max_interp"][1]
            f["boundary_truncated"] = bool(r["fwhm_flags"].get("boundary_truncated"))
        else:
            f["hotspot_x"] = r["xy_Gii_max_interp"][0]
        flags.append(f)
    fam["flags"] = flags
    if missing:
        for key, desc, fn in observables:
            fam["observables"][key] = dict(name=key, description=desc, status="INCOMPLETE",
                                           reason="missing nodes: %s" % missing)
        return fam
    for key, desc, fn in observables:
        vals = [fn(r) for r in recs]
        fam["observables"][key] = analyze_series(vals, d_floor=d_floor, name=key)
        fam["observables"][key]["description"] = desc
    return fam


def analyze_gate4(nodes, d_floor=0.0, families=None):
    """Full Gate-4 analysis over all families. Returns a report dict (discretization-only)."""
    families = families or FAMILIES
    report = dict(schema="aniso_gate4_analysis", version=1,
                  note="discretization-only; no continuum/physical claim; r<1 = consistent-with-"
                       "convergence, r>=1 = conservative UNRESOLVED gate (not proof)",
                  d_floor=d_floor, families={})
    for name, fam in families.items():
        report["families"][name] = analyze_family(name, nodes, OBSERVABLES[name], fam["levels"],
                                                  d_floor=d_floor)
    return report


def render(report):
    """Human-readable table per family per observable (coarse->fine d12/d23/r/monotone/verdict)."""
    lines = []
    lines.append("Gate-4 analysis (frozen rules, discretization-only).  d_floor = %s" % report["d_floor"])
    for name, fam in report["families"].items():
        lines.append("\n[%s-family] %s  (fixed %s)  levels=%s" %
                     (name, fam["direction"], fam["fixed"], ["%dx%d" % lv for lv in fam["levels"]]))
        if fam["missing"]:
            lines.append("  MISSING: %s" % fam["missing"])
        for f in fam["flags"]:
            lines.append("  flag %s" % f)
        for key, o in fam["observables"].items():
            if o["status"] == "INCOMPLETE":
                lines.append("  %-16s %-24s -> INCOMPLETE (%s)" % (key, o.get("description", ""), o.get("reason")))
                continue
            trench = " [trench-class]" if o.get("trench_class") else ""
            lines.append("  %-16s %-24s d12=%-9.3g d23=%-9.3g r=%-9s monotone=%-5s -> %s%s"
                         % (key, o.get("description", ""), o["d12"], o["d23"],
                            ("%.3g" % o["r"]) if o["r"] is not None else "n/a",
                            o["monotone"], o["status"], trench))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate-4 mesh-convergence analysis (frozen rules).")
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--out", default=None, help="write report JSON here (default: data-dir/aniso_gate4_analysis.json)")
    ap.add_argument("--d-floor", type=float, default=0.0, help="observable noise floor (default 0)")
    args = ap.parse_args(argv)

    # Gather node JSONs that match any pre-registered level.
    wanted = {lv for fam in FAMILIES.values() for lv in fam["levels"]}
    candidates = []
    for fn in sorted(os.listdir(args.data_dir)):
        if not fn.endswith(".json"):
            continue
        candidates.append(os.path.join(args.data_dir, fn))
    nodes, skipped, ambiguous = load_certified_nodes(candidates)
    nodes = {lv: r for lv, r in nodes.items() if lv in wanted}
    report = analyze_gate4(nodes, d_floor=args.d_floor)
    report["skipped"] = skipped
    report["ambiguous"] = ambiguous

    print(render(report))
    if ambiguous:
        print("\nAMBIGUOUS (duplicate certified artifacts at one level):")
        for p, why in ambiguous:
            print("  - %s  (%s)" % (p, why))
    if skipped:
        print("\nSKIPPED (%d):" % len(skipped))
        for p, why in skipped[:20]:
            print("  - %s  (%s)" % (p, why))
    out = args.out or os.path.join(args.data_dir, "aniso_gate4_analysis.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=2)
    print("\nWrote %s" % out)
    return report


if __name__ == "__main__":
    main()
