# Audit closure — Gate A (source identity) + follow-up remediation

Response to the independent follow-up review (2026-10-22). Your blocking item was **Gate A: the
public raw files still showed the old behavior**, so the seven fixes could not be confirmed. This
resolves that.

## Gate A — the fixes ARE on `main`; verify at a pinned commit (not floating `main`)

The follow-up fetched floating `main` through the raw CDN and saw stale content (indexing/cache lag,
exactly the "stale indexed snapshot" possibility you noted). The fixes landed in commit
**`a01524ef6abc0127ae44607e483274ffac8fa533`** (audited base = its parent
`0741874b38387b96bb3b225df84615b30f9ca45b`), plus this follow-up commit hardening RUN-02.

**Verify at the immutable commit SHA (bypasses the branch cache):**
```
https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/<FIX_SHA>/src/gen_run_report.py
https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/<FIX_SHA>/src/archive_run.py
https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/<FIX_SHA>/trio_launch.sh
https://raw.githubusercontent.com/chanlikt-lgtm/Liang1997/<FIX_SHA>/reproduce_all.py
```
(`<FIX_SHA>` = the HEAD commit of `main` recorded alongside this file; see `git rev-parse HEAD`.)

The complete audited→fix diff is committed at
[`report/closure/gate_a_fix_diff_vs_audited.patch`](closure/gate_a_fix_diff_vs_audited.patch)
(`git diff 0741874 -- src/gen_run_report.py src/archive_run.py trio_launch.sh reproduce_all.py`).

### Markers you can grep at the fix commit
- `gen_run_report.py`: `# RUN-01`, `r.returncode`, no `--enable-installer`; `u = [(sp[i] * G[i] / 2.0) ...]` (NUM-01); `__MISSING_H_HASH__` sentinel + `hash_ok = (len(hashes) == 1) and ("__MISSING_H_HASH__" not in hashes)` (NUM-02).
- `archive_run.py`: `*.progress.json` pattern, `sha256_file`, `SHA-256 (relative`, and the RUN-02 fail-closed `sys.exit(4)`.
- `trio_launch.sh`: `set -euo pipefail`, `TRIO_AUTOPUSH`.
- `reproduce_all.py`: `sys.exit(1)` on failed stages; `raise RuntimeError(...recalibration output missing...)`.

## Follow-up remediation in this commit

- **RUN-02 hardened (your flagged gap):** a missing acceptance sidecar is now **fail-closed** —
  `archive_run.py` exits nonzero (code 4) unless `--exploratory` is passed, which instead labels the
  snapshot `_UNCERTIFIED`. A certified archive without sidecars is no longer possible.
- **NUM-02 (your point 2 — the all-node-missing case):** already covered. Because every node maps to
  the sentinel `__MISSING_H_HASH__` when its key is absent, the all-missing case yields the set
  `{"__MISSING_H_HASH__"}` whose presence check fails `hash_ok` (cardinality-one does **not** pass).
  Single-node, all-node, and changed-hash omissions all fail. We will additionally add the explicit
  `all("H_hash" in node)` form and the H-array byte-digest check with the signed manifest (queued).

## Still queued (acknowledged partial — unchanged from the response)

- **NUM-01 full:** route `richardson_fit.py` and `run_richardson_trio.py` through one shared
  `read_certified_window()` (only `gen_run_report.py` is rewired so far).
- **NUM-02 signed manifest:** per-node exact-schema manifest (source-tree hash + dirty refusal,
  physics/doping/geometry digests, H-array bytes SHA, warm-source SHA, versions) enforced vs the
  frozen run definition.
- **RUN-03 (`run_linux_full.sh`):** hard-fail on a missing Stage-1 sentinel.

## Gate B–D evidence (being assembled separately)

- **Gate B** — the seven fault-injection negative tests (failing-before / passing-after, with exit
  codes and scripts).
- **Gate C** — your `Liang1997_Readonly_Checkpoints.py` run against the real archived NPZs + sidecars,
  with JSON output and all hashes. (Clarifying which dataset is the certified set, since the repo's
  working `data/` holds both reference and interim artifacts.)
- **Gate D** — the 100-iteration per-observable histories (from the diagnostic continuation) as CSV,
  reported separately from the 4-sample `3e-4` plateau spread — these are distinct axes, as you note.

## Scientific status (unchanged, agreed)

SCI-01 remains a **BLOCKER**: the non-monotone trio establishes no continuum `G_ii`. The archival
+2.86% is retained as a **deprecated historical-baseline** comparison, not a live accuracy test; a new
immutable reference will be set only after independent verification. SCI-02/03 remain open and
accepted. No continuum or full-paper-reproduction claim is made.
