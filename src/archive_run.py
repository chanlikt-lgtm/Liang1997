"""
archive_run.py -- snapshot every plot (and the run's key products) into a timestamped folder.

At the end of a run this copies all generated figures into runs/<YYYY-MM-DD_HHMMSS>/plots/ so each
run's plots are preserved instead of overwritten, alongside the run-results report, the trio data,
the per-node progress sidecars, the report source, and the convergence logs. Writes a MANIFEST.txt
(timestamp, git commit + dirty flag, environment versions, and a SHA-256 for every archived payload)
so the snapshot can be independently re-certified on another machine.
Usage: python archive_run.py [label]      (optional short label appended to the folder name)

Audit note (RUN-02): the archive MUST include she2d_richardson_*.progress.json (which persists the
corrected cumulative cross-chunk four-iteration acceptance buffer) and per-file SHA-256 hashes, or the
archived run alone cannot reproduce its own certificate.
"""
import os, sys, glob, shutil, subprocess, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "figures"); REP = os.path.join(ROOT, "report"); DATA = os.path.join(ROOT, "data")

def git(*a):
    try:
        return subprocess.check_output(["git", *a], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "?"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def copy_into(dst, patterns):
    """Copy every file matching patterns into dst; return the list of destination paths."""
    copied = []
    for pat in patterns:
        for src in glob.glob(pat):
            if os.path.isfile(src):
                d = os.path.join(dst, os.path.basename(src))
                shutil.copy2(src, d); copied.append(d)
    return copied

def env_versions():
    out = {}
    for mod in ("numpy", "scipy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "?"
    out["python"] = sys.version.split()[0]
    out["SHE2D_DISABLE_NUMBA"] = os.environ.get("SHE2D_DISABLE_NUMBA", "")
    return out

def main():
    # RUN-02 (hardened): a CERTIFIED archive must contain the per-node acceptance sidecars, or the
    # snapshot cannot reconstruct its own plateau certificate. Missing sidecars now FAIL CLOSED
    # (nonzero exit) unless the caller explicitly marks this an EXPLORATORY/uncertified archive.
    argv = [a for a in sys.argv[1:] if a != "--exploratory"]
    exploratory = "--exploratory" in sys.argv
    label = ("_" + argv[0]) if argv else ""
    if exploratory:
        label += "_UNCERTIFIED"

    # R1 (audit follow-up): validate node coverage from the SOURCE data/ dir BEFORE creating any run
    # folder, so a rejected certified archive leaves NO folder behind (an exit-code-ignoring publisher
    # cannot mistake a partial reject for a certified snapshot). The post-copy report below is retained.
    REQUIRED_NODES = ("71x58", "100x70", "141x85")
    def _src_nodes(suffix):
        return {os.path.basename(p)[len("she2d_richardson_"):-len(suffix)]
                for p in glob.glob(os.path.join(DATA, "she2d_richardson_*" + suffix))
                if os.path.basename(p).startswith("she2d_richardson_")}
    src_npz, src_sidecar = _src_nodes(".npz"), _src_nodes(".progress.json")
    pre_npz_without_sidecar = sorted(src_npz - src_sidecar)
    pre_missing_required = sorted(n for n in REQUIRED_NODES if n not in src_npz or n not in src_sidecar)
    if (pre_npz_without_sidecar or pre_missing_required) and not exploratory:
        det = []
        if pre_npz_without_sidecar: det.append("NPZ without sidecar: %s" % pre_npz_without_sidecar)
        if pre_missing_required:    det.append("required trio node(s) missing NPZ or sidecar: %s" % pre_missing_required)
        sys.stderr.write("ERROR (RUN-02/CLOS-01/R1): incomplete node coverage (%s) -- refusing to create a "
                         "certified archive folder. Re-run with complete sidecars, or pass --exploratory "
                         "for an uncertified archive.\n" % "; ".join(det))
        sys.exit(4)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run = os.path.join(ROOT, "runs", ts + label)
    plots = os.path.join(run, "plots")
    os.makedirs(plots, exist_ok=True)

    png = copy_into(plots, [os.path.join(FIG, "*.png"), os.path.join(FIG, "*.pdf")])
    rep = copy_into(run, [os.path.join(REP, "report_run_latest.pdf"),
                          os.path.join(REP, "report_run_latest.tex"),      # RUN-02: archive the report SOURCE
                          os.path.join(REP, "report_v6_full.pdf")])
    dat = copy_into(run, [os.path.join(DATA, "she2d_richardson_*.npz"),
                          os.path.join(DATA, "she2d_richardson_*.progress.json"),  # RUN-02: the acceptance buffer
                          os.path.join(DATA, "richardson_trio_run.log"),
                          os.path.join(DATA, "richardson_trio_metrics.csv"),
                          os.path.join(DATA, "richardson_*.log"),
                          os.path.join(DATA, "run_from_scratch.log")])

    all_payloads = png + rep + dat
    with open(os.path.join(run, "MANIFEST.txt"), "w", encoding="utf-8") as f:
        f.write("run snapshot: %s%s\n" % (ts, label))
        f.write("generated:    %s\n" % datetime.datetime.now().isoformat(timespec="seconds"))
        f.write("git commit:   %s (%s)\n" % (git("rev-parse", "HEAD"),
                                             "dirty" if git("status", "--porcelain") else "clean"))
        ev = env_versions()
        f.write("environment:  python %s, numpy %s, scipy %s, SHE2D_DISABLE_NUMBA=%s\n"
                % (ev["python"], ev["numpy"], ev["scipy"], ev["SHE2D_DISABLE_NUMBA"]))
        f.write("plots:        %d  (plots/)\n" % len(png))
        f.write("reports:      %d\n" % len(rep))
        f.write("data/logs:    %d\n\n" % len(dat))
        f.write("SHA-256 (relative path  hash):\n")
        for p in sorted(all_payloads):
            f.write("  %-48s  %s\n" % (os.path.relpath(p, run), sha256_file(p)))

    # Fail-closed (RUN-02 + CLOS-01): a CERTIFIED archive requires ONE-TO-ONE coverage -- every
    # archived node NPZ must have its matching progress.json sidecar, AND all three required trio
    # nodes (71x58, 100x70, 141x85) must be present. A partial trio (e.g. 3 NPZ but only 1 sidecar)
    # must NOT archive as certified; it exits nonzero unless --exploratory (then labelled UNCERTIFIED).
    REQUIRED_NODES = ("71x58", "100x70", "141x85")
    def basenames(suffix):
        return {os.path.basename(p)[len("she2d_richardson_"):-len(suffix)]
                for p in dat if os.path.basename(p).startswith("she2d_richardson_") and p.endswith(suffix)}
    npz_nodes = basenames(".npz")
    sidecar_nodes = basenames(".progress.json")
    archived_sidecars = [p for p in dat if p.endswith(".progress.json")]
    # every archived NPZ needs its sidecar; and the full required trio must be covered by both
    npz_without_sidecar = sorted(npz_nodes - sidecar_nodes)
    missing_required = sorted(n for n in REQUIRED_NODES if n not in npz_nodes or n not in sidecar_nodes)
    coverage_ok = (not npz_without_sidecar) and (not missing_required)
    print("archived %d plots + %d reports + %d data/logs (%d sidecars; npz_nodes=%s sidecar_nodes=%s) -> %s"
          % (len(png), len(rep), len(dat), len(archived_sidecars),
             sorted(npz_nodes), sorted(sidecar_nodes), os.path.relpath(run, ROOT)))
    if not coverage_ok:
        detail = []
        if npz_without_sidecar: detail.append("NPZ without sidecar: %s" % npz_without_sidecar)
        if missing_required:    detail.append("required trio node(s) missing NPZ or sidecar: %s" % missing_required)
        if exploratory:
            sys.stderr.write("WARNING (RUN-02/CLOS-01): incomplete node coverage (%s); labelled "
                             "UNCERTIFIED (exploratory archive).\n" % "; ".join(detail))
        else:
            sys.stderr.write("ERROR (RUN-02/CLOS-01): incomplete node coverage (%s) -- a certified trio "
                             "archive requires a matching progress.json for every node and all of %s. "
                             "Re-run with complete sidecars, or pass --exploratory for an uncertified "
                             "archive.\n" % ("; ".join(detail), list(REQUIRED_NODES)))
            sys.exit(4)

if __name__ == "__main__":
    main()
