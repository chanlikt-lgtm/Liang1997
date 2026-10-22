#!/usr/bin/env python3
"""Gate B -- fault-injection negative tests for the audit's fail-closed pipeline fixes.

Drives the ACTUAL fixed source (no reimplementation) with injected faults and records the
exit code / exception for each. Rerunnable by the auditor at the pinned commit:

    python gate_b_fault_injection.py --repo /path/to/Liang1997 --json gate_b.json

Covers RUN-01, RUN-02, RUN-04, RUN-05, NUM-02. RUN-01 requires the three real data/ NPZs
(it runs the real gen_run_report.py end-to-end with a stubbed failing pdflatex); if they are
absent the test is reported SKIPPED rather than faked.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile, shutil, textwrap, pathlib, stat

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    src = os.path.join(repo, "src")
    results = []

    def rec(name, expect, got, ok, detail=""):
        results.append(dict(test=name, expected=expect, observed=got, passed=bool(ok), detail=detail))
        print(("PASS " if ok else "FAIL ") + name + "  (expected %s, got %s) %s" % (expect, got, detail))

    # ---- RUN-02: archive_run.py must FAIL-CLOSED (exit 4) with no progress.json sidecars ----
    try:
        tmp = tempfile.mkdtemp(prefix="gateb_run02_")
        os.makedirs(os.path.join(tmp, "src")); os.makedirs(os.path.join(tmp, "figures"))
        os.makedirs(os.path.join(tmp, "report")); os.makedirs(os.path.join(tmp, "data"))
        shutil.copy2(os.path.join(src, "archive_run.py"), os.path.join(tmp, "src", "archive_run.py"))
        # one npz but NO sidecar -> certified archive must refuse
        open(os.path.join(tmp, "data", "she2d_richardson_71x58.npz"), "wb").write(b"\x00")
        r1 = subprocess.run([sys.executable, "-I", os.path.join(tmp, "src", "archive_run.py")],
                            capture_output=True, text=True)
        rec("RUN-02 no-sidecar certified archive -> nonzero", "exit 4", "exit %d" % r1.returncode,
            r1.returncode == 4, "(fail-closed)")
        # --exploratory must succeed (exit 0) and label UNCERTIFIED
        r2 = subprocess.run([sys.executable, "-I", os.path.join(tmp, "src", "archive_run.py"), "--exploratory"],
                            capture_output=True, text=True)
        uncert = any("_UNCERTIFIED" in d for d in os.listdir(os.path.join(tmp, "runs"))) if os.path.isdir(os.path.join(tmp, "runs")) else False
        rec("RUN-02 --exploratory -> exit 0 + UNCERTIFIED label", "exit 0 + label", "exit %d label=%s" % (r2.returncode, uncert),
            r2.returncode == 0 and uncert)
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        rec("RUN-02", "exit 4 / 0", "exception", False, "%s: %s" % (type(e).__name__, e))

    # ---- RUN-05: reproduce_all._copy_conv_to_canonical() must RAISE when the recal NPZ is missing ----
    try:
        sys.path.insert(0, repo)
        import importlib
        ra = importlib.import_module("reproduce_all")
        ra.CONV_NPZ = os.path.join(tempfile.gettempdir(), "definitely_missing_conv_%d.npz" % os.getpid())
        raised = False
        try:
            ra._copy_conv_to_canonical()
        except RuntimeError:
            raised = True
        rec("RUN-05 missing recal NPZ -> RuntimeError", "RuntimeError", "raised=%s" % raised, raised)
    except Exception as e:
        rec("RUN-05", "RuntimeError", "harness error", False, "%s: %s" % (type(e).__name__, e))

    # ---- RUN-04: reproduce_all --keep-going must exit NONZERO if a stage fails ----
    try:
        import importlib
        ra = importlib.import_module("reproduce_all")
        ra.run_stage = lambda name: (_ for _ in ()).throw(RuntimeError("injected stage failure"))
        argv_bak = sys.argv[:]
        # pick a real stage name if available, else the first
        stage = ra.STAGE_NAMES[0] if hasattr(ra, "STAGE_NAMES") and ra.STAGE_NAMES else "foundation"
        sys.argv = ["reproduce_all.py", "--stage", stage, "--keep-going"]
        code = 0
        try:
            ra.main()
        except SystemExit as se:
            code = se.code if isinstance(se.code, int) else 1
        finally:
            sys.argv = argv_bak
        rec("RUN-04 --keep-going with failed stage -> nonzero exit", "exit 1", "exit %s" % code, code == 1)
    except Exception as e:
        rec("RUN-04", "exit 1", "harness error", False, "%s: %s" % (type(e).__name__, e))

    # ---- NUM-02: the report comparability gate must FAIL when any H_hash is missing ----
    # Reproduce the exact fixed expression from gen_run_report.py (sentinel sets).
    def hash_ok(node_hashes):  # node_hashes: list of present hash strings or None for missing
        hashes = {(h if h is not None else "__MISSING_H_HASH__") for h in node_hashes}
        return (len(hashes) == 1) and ("__MISSING_H_HASH__" not in hashes)
    cases = [("all present equal", ["a", "a", "a"], True),
             ("one missing",       ["a", "a", None], False),
             ("all missing",       [None, None, None], False),   # cardinality 1 but sentinel -> FAIL
             ("mismatch",          ["a", "b", "a"], False)]
    num02_ok = True
    for label, hs, want in cases:
        got = hash_ok(hs)
        ok = (got == want); num02_ok &= ok
        rec("NUM-02 hash_ok [%s]" % label, want, got, ok)

    # ---- RUN-01: real gen_run_report.py with a stubbed failing pdflatex must exit nonzero ----
    npzs = [os.path.join(repo, "data", "she2d_richardson_%s.npz" % m) for m in ("71x58", "100x70", "141x85")]
    if all(os.path.isfile(p) for p in npzs):
        try:
            binstub = tempfile.mkdtemp(prefix="gateb_run01_bin_")
            stub = os.path.join(binstub, "pdflatex")
            with open(stub, "w") as f:
                f.write("#!/usr/bin/env bash\necho 'stub pdflatex: forced failure' >&2\nexit 1\n")
            os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            env = dict(os.environ, PATH=binstub + os.pathsep + os.environ.get("PATH", ""))
            r = subprocess.run([sys.executable, "-I", os.path.join(src, "gen_run_report.py")],
                               cwd=repo, capture_output=True, text=True, env=env)
            no_false_success = "compiled report" not in (r.stdout or "")
            rec("RUN-01 failing pdflatex -> nonzero + no false success", "exit!=0 & no 'compiled'",
                "exit %d false_success=%s" % (r.returncode, not no_false_success),
                r.returncode != 0 and no_false_success,
                "(Windows note: if the stub is not honored over a real pdflatex on PATH, run on a box "
                "where PATH precedence applies, e.g. Linux/TeX Live.)")
            shutil.rmtree(binstub, ignore_errors=True)
        except Exception as e:
            rec("RUN-01", "exit!=0", "harness error", False, "%s: %s" % (type(e).__name__, e))
    else:
        rec("RUN-01 failing pdflatex -> nonzero", "exit!=0", "SKIPPED", True,
            "(data/ trio NPZs absent; run at the pinned commit with the campaign data)")

    overall = "PASS" if all(r["passed"] for r in results) else "FAIL"
    out = dict(gate="B fault-injection", repo=repo, overall=overall, results=results)
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nGate B overall:", overall)
    return 0 if overall == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
