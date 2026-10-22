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
    label = ("_" + sys.argv[1]) if len(sys.argv) > 1 else ""
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

    # Fail-closed: the per-node progress sidecars carry the certified acceptance buffer; without them
    # the archive cannot be re-certified (audit RUN-02).
    archived_sidecars = [p for p in dat if p.endswith(".progress.json")]
    print("archived %d plots + %d reports + %d data/logs (%d sidecars) -> %s"
          % (len(png), len(rep), len(dat), len(archived_sidecars), os.path.relpath(run, ROOT)))
    if not archived_sidecars:
        sys.stderr.write("WARNING (RUN-02): no she2d_richardson_*.progress.json archived -- "
                         "this snapshot cannot reproduce its own plateau certificate.\n")

if __name__ == "__main__":
    main()
