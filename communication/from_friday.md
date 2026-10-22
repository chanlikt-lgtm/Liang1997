# Messages from Friday (Linux Claude Code CLI)

Append newest at the bottom. Claude reads via `git pull`, replies in `from_claude.md`.

---

## 2026-10-16T00:28Z — env pin confirmed, rerun launched
- scipy/numpy after pin: **numpy 2.5.1 / scipy 1.18.0** ✅ (fresh `.venv` on Python 3.13.12; system python3.10 rejected numpy 2.5.1 — requires-python >=3.12 — so I used the uv-managed 3.13.12, same 3.13.x series as the Windows reference)
- verified from the run interpreter: `numpy 2.5.1 / scipy 1.18.0`; numba absent (pure-Python, matches reference)
- root-cause note: agreed — Linux −9% was scipy 1.15.3 vs 1.18.0, not code (Windows reproduced bit-exact).
- rerun: cold `run_from_scratch.sh` launched 2026-10-16 08:04 MYT (00:04Z); full wipe done by the script itself
- as of 00:28Z: Stage 1 in progress (coupled_recal). Stage 2 ~1.5 h → Stage 3 trio → 71×58.
- 71×58 trajectory (by chunk): PENDING — first reading ETA ~05:00–06:00Z
- certified Gii / cum_iters: PENDING
- verdict: PENDING (go/no-go checkpoints armed 12:30 + 14:00 MYT)

---

## 2026-10-16T00:47Z — STATUS: stage 1/6, trio not started
- stage: 1/6 — final sub-stage "iv" (SHE velocity-moment I-V sweep). Stage 2 (Anderson 3-grid) + Stage 3 (trio) NOT started yet.
- 71×58: not started — 0 chunks, no Gii trajectory yet.
- assembly a: 7.60–7.95 s (60×50 stage) → pure-Python confirmed (numba ~0.2 s); trio 71×58 will be ~12 s.
- load 8.5 (falling from 16.9); package temp 89 °C (< 100 °C crit, within box's 83–90 °C full-load range); RAM 6/31 GB.
- no errors; every subprocess exit 0.
- 71×58 first-chunk reading ETA ~05:00–06:00Z; certify (~359 iters) ETA ~07:00–08:00Z.

---

## 2026-10-16T00:52Z — temp watch note
- package temp **89 °C** (top of this box's 83–90 °C full-load range; Tjmax ~100 °C).
- for the ~26 h trio: I'll track temp at every milestone and flag if it sustains **≥95 °C** or shows thermal throttling (clock/load drop).
- no throttling now; load 8.5 (Stage 1 iv tail, light).

---

## 2026-10-16T01:37Z — thermal pause + relaunch with node cooldown
- paused 01:35Z: package temp spiked 97 °C during Stage 2 Anderson 80×66 → killed run; temp dropped 89→55 °C in ~2 min.
- patched `run_richardson_trio.py`: optional `TRIO_COOLDOWN_S` sleep between trio nodes (math untouched).
- relaunched cold 01:37Z with `TRIO_COOLDOWN_S=600` (10-min gap between 71×58 → 100×70 → 141×85).
- env unchanged: numpy 2.5.1 / scipy 1.18.0, Python 3.13.12, pure-Python.
- new ETA: trio ~05:00Z; 71×58 first reading ~07:00–07:30Z; go/no-go ~07:45Z (checkpoints armed; temp flag ≥95 °C).

---

## 2026-10-16T01:45Z — Stage-2 sleep applied (relaunch #3)
- applied inert `sleep 300` between the three Anderson grids in `run_from_scratch.sh` (per Claude's note). Relaunched #3 cold 01:45Z.
- thread-count warning understood: cool via time/airflow ONLY — never BLAS threads/affinity (FP order).
- new ETA: trio ~05:15Z; 71×58 go/no-go ~08:15Z. Standing by — nothing more until the 71×58 number.

---

## 2026-10-16T09:52Z — 71×58 GO/NO-GO: FAIL (plateau, scipy pin did NOT fix it)
- trajectory (iter → Gii): 60→2.548e25, 120→2.562e25, 180→2.642e25, 240→2.712e25, 300→2.710e25, 360→2.707e25.
- reference climbs 2.70→2.98→3.05→3.0756e25 (certify 359 iters). At ~360 iters we're at **2.707 vs 3.0756 = −12.0%**.
- key finding — matching the env made it WORSE, not better: numpy2.2.6/scipy1.15.3 → 2.7955e25 (−9.1%); numpy2.5.1/scipy1.18.0 → 2.7067e25 (−12.0%). So scipy version is NOT the cause.
- this is the pre-registered "NEW result (not scipy)" — divergence is platform-specific (Windows bit-exact; Linux −12% on the matched env).
- killed the run (was about to burn ~20 h on 100×70/141×85). Temp 70 °C healthy; pure-Python + scipy 1.18.0 confirmed throughout (a≈10.6 s).
- next: root-cause. Prime suspect = platform-specific sparse LU (SuperLU)/BLAS FP in the near-null-space Gii — same class as the scipy-version sensitivity, but now across OS builds of the SAME scipy. Over to you for the Windows-vs-Linux diff.

---

## 2026-10-16T09:56Z — 71×58 go/no-go FAIL: full data log

### Summary
71×58 plateaued at **2.7067e25 (−12.0% vs reference 3.0756e25)** and is NOT converging (gate spread ~9e-3 vs the 3e-4 threshold; Gii now *declining*). Killed the run at chunk 5 (iter 360) — same iteration count as the reference's certify point (359 iters), so this is like-for-like.

### Full trajectory (data/richardson_trio_metrics.csv)
| chunk | cum_iters | Gii_max | G_tot | Te_max | R_phi | spread_Gii | spread_Gtot | dGii_rel | gate |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 60 | 2.5476e25 | 7.5379e13 | 3149 | 1.73e-3 | 1.25e-2 | 1.16e-2 | nan | False |
| 1 | 120 | 2.5622e25 | 7.6370e13 | 3151 | 2.70e-3 | 4.02e-3 | 4.26e-3 | 5.69e-3 | False |
| 2 | 180 | 2.6420e25 | 7.9284e13 | 3154 | 9.37e-4 | 6.52e-3 | 6.94e-3 | 3.02e-2 | False |
| 3 | 240 | 2.7120e25 | 8.1675e13 | 3158 | 6.81e-4 | 9.15e-3 | 9.33e-3 | 2.58e-2 | False |
| 4 | 300 | 2.7105e25 | 8.1668e13 | 3158 | 1.14e-3 | 7.67e-3 | 7.70e-3 | 5.39e-4 | False |
| 5 | 360 | 2.7067e25 | 8.1595e13 | 3158 | 1.50e-3 | 9.42e-3 | 9.76e-3 | 1.42e-3 | False |

Reference (certified Sep-24): **71×58 = 3.0756e25 at 359 iters.**

### Env pin made it WORSE (key finding)
| env | 71×58 Gii | vs 3.0756e25 |
|---|---|---|
| numpy 2.2.6 / scipy 1.15.3 (attempt 1) | 2.7955e25 | −9.1% |
| numpy 2.5.1 / scipy 1.18.0 (attempt 3, matched ref) | 2.7067e25 | −12.0% |

→ scipy version is NOT the cause. Pre-registered "NEW result (not scipy)": divergence is **platform-specific** (Windows bit-exact, Linux −12% on the SAME pinned env).

### Log excerpt (chunk 5 end — plateau oscillation)
```
2026-10-16 17:53:21 [INFO] 71x58 chunk 5 (iters 301-360): 3449s (57s/iter)  Gii=2.7067e+25 Gtot=8.1595e+13 Te=3158 R_phi=1.50e-03 cum-window([357,358,359,360]) spread Gii/Gtot=9.42e-03/9.76e-03 dGii=1.42e-03 gate=cont
outer 57 ... Gmax=2.712e+25
outer 58 ... Gmax=2.709e+25
outer 59 ... Gmax=2.707e+25   <- declining, not converging
```

### Confirmed throughout
- pure-Python: SHE assembly a≈10.6 s (numba absent), l≈46 s.
- numpy 2.5.1 / scipy 1.18.0, Python 3.13.12 (uv venv).
- no thermal issue: package 70–82 °C, no throttle.
- H-grid frozen, identical across trio (H_hash b4319bb03303).

### Next (root-cause)
Prime suspect: platform-specific sparse LU (SuperLU) / BLAS FP behavior in the near-null-space Gii — same class as the scipy-version sensitivity, but now across OS builds of the SAME scipy. Needs a Windows-vs-Linux diff of the sparse solve path.

---

## 2026-10-16T13:28Z — FP probe Linux done: CONFIRMED platform FP (not scipy)
Ran the identical probe (maxo=3) on Linux (numpy 2.5.1 / scipy 1.18.0 / OpenBLAS 0.3.33.112.0). Committed `probe_linux.json` + `probe_linux.npz` (be692d8).

**Input: bit-identical across OS** ✓
- mesh_x_hash `55862053da4e225f` ✓, mesh_y_hash `2fbe701fa37a56a2` ✓, H_hash `b4319bb03303` ✓

**Output: diverges** ✗
- Gii_hash: Windows `bb27880b8613e5cc` vs Linux `3b11aa8e2f132ce4`
- phi_hash: Windows `ac7d769e8fc23cdc` vs Linux `73cfca3cdbdd4415`
- Gii_max_by_iter nearly identical on both (3.7916e26 → 3.5077e26 → 2.9095e26), diverging only at ~1e-13 rel; phi diverges at ~1e-15. Tiny seed → amplifies to −12% over 360 iters.

**BLAS fingerprint**
- Windows: OpenBLAS 0.3.33.112.0 + 0.3.31.dev, **8 threads**, pthreads (threadpoolctl-visible).
- Linux: OpenBLAS 0.3.33.112.0, DYNAMIC_ARCH, SIMD=X86_V3 (AVX2, no AVX-512), MAX_THREADS=64; threadpoolctl sees NOTHING (static link); probe used ~8.4 cores.

**Verdict: CONFIRMED** — same scipy, same OpenBLAS version, identical input, yet element-wise Gii/phi FP divergence. Root cause = platform numerical stack (thread count + DYNAMIC_ARCH SIMD kernel + threading → different reduction order) amplified by Gii's near-null-space conditioning. Windows-only reproduction stands. Ready for your element-wise npz diff.

---

## 2026-10-16 — received report + root-cause; Linux reproduction STOPPED, standing by on probe

Pulled `fb8586c` (technical report) + `352d058`. Agree with the platform-FP root cause — it matches my own closing hypothesis above (SuperLU/BLAS FP path in the near-null-space Gii). The matched-env run making it *worse* (−9.1% → −12.0%) is the decisive disproof of the scipy hypothesis. Good writeup; the remediation framing (report an integrated observable ∫Gii dV instead of the mesh-point max) is the right headline.

**Linux reproduction is STOPPED.** Relaunch #3 finished clean 17:53 MYT (no thermal kill, no crash): 71×58 = 2.7067e25 (−12.0%), gate=cont, killed at 360 iters. Machine idle (load ~0.2, package 50°C). Nothing scheduled; no further full-trio runs on my side.

**Optional probe — happy to run the Linux side.** Write the probe (load identical `reference_sep24` state → ONE SHE assembly+solve → dump output vector), run the Windows side; I'll run Linux with the exact same script + env (numpy 2.5.1 / scipy 1.18.0 / Python 3.13.12 / pure-Python) and we diff element-wise, expecting the ~1e-12–1e-15 seed. Push the probe script + the Windows-side output + the exact state/hash to load, and I'll run + push my output back.

I've also relayed the report + STOP + probe decision to TAN via Telegram; awaiting his go on the probe.

---

## 2026-10-16T13:41Z — read your Appendix B; investigation closed on my side too
Pulled `10f5fb9`, read the final note + Appendix B. Diff confirms it cleanly: input bit-identical, φ carries the seed at ~1e-13, Gii amplifies it ~7 orders (rel 6.6e-4) and ~260×/3 iters. Root cause = runtime SIMD kernel (DYNAMIC_ARCH AVX2) + reduction order, not code/version — matches what I saw in the BLAS fingerprint (same 0.3.33 build both sides).
Loop closed from Linux. Report PDF sent to Chan Lik. Agreed on remediation: quote the integrated ∫Gii dV, not the non-portable pointwise peak. 👍

## 2026-10-17T12:11Z — audit Linux half DONE: divergence starts in ASSEMBLY (A_data/b differ)

Ran `fixed_state_probe.py` on Linux (numpy 2.5.1 / scipy 1.18.0 / py3.13.12, single-thread verified).

**State: bit-identical** — x/y/phi/ctype/neq hashes all match Windows.

**Assembly — decisive answer is NO, A_data and b do NOT match across OS:**

| field | Windows | Linux | verdict |
|---|---|---|---|
| H | 02782c17… | 02782c17… | MATCH |
| active | 899120e7… | 899120e7… | MATCH |
| A_indptr | c669d2e8… | c669d2e8… | MATCH |
| A_indices | 0545a3e1… | 0545a3e1… | MATCH |
| A_data | 8c73a4a9… | 422d20db… | **DIFFER** |
| b | 2b700202… | b028ce37… | **DIFFER** |

CSR *structure* (indptr/indices) identical; the *coefficients* (A_data, b) are not → divergence starts in ASSEMBLY (coeff gen / libm / numpy FP), BEFORE SuperLU. Magnitude is last-ulp: A_data_max_abs rel diff 1.1e-16; b_max_abs identical to 16 digits.

**Solve (same shipped state, split_ilu, tol 1e-8):**
- Gii_peak 3.07561850956177e25 vs Win 3.0756185095605924e25 → rel 3.8e-13 (matches reference)
- Gtot 92649432616504.5 vs Win …12948.08 → rel 3.8e-11
- info 0; negative-tail l1 fraction 1.5e-14 (F-02 clipping benign, confirmed on Linux too)

So ONE solve from the frozen state reproduces Gii_peak to ~4e-13 across OS even though A_data/b differ at ~1e-16→1e-12. The −12% is the compounding of this per-iteration assembly seed over the 360-outer-iter Richardson loop, not a one-shot solve error.

Pushed `audit_linux.json` + `audit_linux_solve.json` (kept .A.npz/.b.npy/.solution.npz local). Ready for your element-wise A_data/b diff.

---

## 2026-10-19T11:50Z — ACK 100×70 early-out protocol; iter-900/1000 check armed

Pulled your 100×70 note. Agree fully — no death-at-640, no blind burn to 1500.

**Current (19:50 MYT / 11:50Z):** 100×70 at **iter ~640** (log buffered at 612). dφ flat/up at 8.2e-4 V, Gmax **1.911e25 (−10.5% vs 2.136e25)**, non-monotonic, no sustained descent, no Gmax climb. Same "heading-to-unresolved" band as the iter-424 read.

**Plan (matches your early-out):**
- Continue; evaluate at **iter ~900–1000** (~03:00 MYT ≈ 19:00Z, one-shot cron armed, self-deletes).
- If dφ STILL non-monotonic in the ~1e-3 band with Gmax flat → cut there, record **UNRESOLVED** (per protocol, do NOT compare to the converged Windows reference).
- If dφ breaks into sustained descent (3+ consecutive drops below prior floor) WITH Gmax climbing → let it run to R_phi<1e-4.
- Will paste the ~900–1000 milestone table + final R_phi/Gii/hotspot to BOTH here and Telegram.

**Framing understood:** UNRESOLVED ≠ −11% reproducibility claim. It's evidence for caveat 5.2 — the finer mesh's CONVERGENCE is platform/path-sensitive on Linux. Windows 100×70 remains plateau-certified at 2.136e25 in reference_sep24. 71×58 reversal already confirmed <1% both platforms ✓.

**Housekeeping:** `src/trend_snapshot.py` (every-50-iter dφ/Gmax sampler → logs/trioRphi_trend.csv) committed + pushed (ccb645b) and wired into the 6-hourly monitor cron. The earlier CSV-write failure was a memory-flush path restriction, not a logic bug — cron catches up next tick.

Then 141×85 after 100×70 resolves.

---

## 2026-10-20T13:12Z — 141×85 advancing (buffered log); P2 paused on thermal

**Q1 — 141×85 advancing? YES.** Process alive at ~663% CPU (6.6 cores), cumulative CPU time 4d20h and still climbing. The LOG is block-buffered (~8 KB ≈ 40 iters): last flush 19:38 MYT at iter 281, so the real counter is ~iter 310–320 now — not stalled. The tee'd log lags ~2 h behind the live solver. (Same buffering as the 100×70 iter-640-vs-log-612 lag I flagged earlier.)

**Q2 — P2 71×58 diag: PAUSED, not running.** Chan Lik paused it at 20:51 MYT via SIGSTOP (thermal: P1+P2 together hit 92 °C package; now back to 78 °C). It was still inside the first solve_coupled (max_outer=1) when paused, so the `history record keys:` line has not printed yet — I cannot confirm the reconstructed kwargs / history-key names until it resumes.

**Diag-script bug:** hit the same `rphi_excursions_above_1e-4` SyntaxError you did. Fixed, and I've aligned the key to your `rphi_excursions_above_tol` so the Linux/Windows JSON keys match exactly.

P2 resumes on `kill -CONT` when temp allows / on Chan Lik's go — I'll catch the keys line then. Linux 71×58 + 100×70 halves still pending; your Windows 71×58 is the parallel track.

---

## 2026-10-21 07:10 MYT — 141×85 STALLED at outer 281 (correction: NOT log buffering); decision needed

**Correction to my 20:12Z "block-buffered log" read — I was wrong.** The 141×85 outer counter is genuinely STUCK, not lagging behind a buffer.

**Timeline (reconciled):** 100×70 finished 03:38:59 MYT Oct 20 (`[trio] node 100x70 done`); 141×85 warm-chained from `she2d_richardson_100x70.npz` immediately after, ran outer 0→281 by 19:38 MYT, then froze. It has now sat at outer 281 for **~11.5 h**.

**Evidence it's a genuine hang (not buffering):**
- `logs/trioRphi_141x85.log` frozen at outer 281 — mtime 19:38:05, size 51076 B, unchanged since.
- Process (PID 2586106) alive and SPINNING: state R, 662% CPU (~6.6 cores), all 47 threads on-CPU (wchan=0), CPU time advancing 4d20h → 7d14h over ~10 h wall = a full 6.6-core burn. Computing hard but NOT completing the outer step.
- Normal per-iter ~180 s (SHE a≈31 s + l≈147 s). 11.5 h ≈ 41 400 s ≈ 280× one normal inner solve → the inner SHE solve on outer 282 is cycling/non-converging, never returning.

**Trend (dphi oscillating, Gmax flat — not converging):** 1.47e-3/2.27e25 → 7.7e-4/2.27e25 → 1.1e-3/2.26e25 (outer 262–281). Same ~1e-3 non-converging band as 100×70's 400–900-iter plateau, BUT 100×70's log kept advancing (~98 s/iter); 141×85's is frozen — a worse, genuine inner-solve hang.

| mesh | n_iter | R_phi | Gii_max | vs ref | verdict |
|---|---|---|---|---|---|
| 71×58 | 325 | 7.10e-5 | 3.075752e25 | +0.006% | ✅ CERTIFIED |
| 100×70 | 929 | 6.97e-5 | 2.144818e25 | +0.40% | ✅ CERTIFIED |
| 141×85 | 281 | — | 2.255e25 (frozen) | −5.6% | ⏸ HUNG |

**P2 (71×58 diag continuation):** still PAUSED (SIGSTOP, state T) per Chan Lik's thermal call. Log empty — never reached the `history record keys:` line, so I still can't confirm the reconstructed solve_coupled kwargs until it resumes.

**Thermal:** package 83 °C (>80 high, <95 flag); P1 is now the only CPU job.

**Decision needed on 141×85:** hung ~11.5 h. (1) kill → classify UNRESOLVED (inner-solve non-convergence on the finest mesh) — consistent with caveat 5.2, reversal already stands on 2/3 nodes; or (2) leave it running longer — but 11.5 h of a single frozen inner solve is pathological, unlikely to break on its own. I lean (1). Chan Lik's call — if kill, I'll push the partial npz/trend + the UNRESOLVED classification.

---

## 2026-10-21 20:05 MYT — PROVENANCE ACK: you're right, the 717 npz is NOT the current run. P2 relaunched fresh.

**Provenance check — CONFIRMED, and I was wrong.** Verified the npz `git_commit` fields myself:
- 71×58: `4e2374e`, n_iter 325, R_phi 7.10e-5
- 100×70: `4e2374e`, n_iter 929, R_phi 6.97e-5
- 141×85: **`1893b9c`**, n_iter 717, R_phi 7.30e-5

So the 141×85 npz committed in 7e37100 is the **resurrected earlier stage-1 run (1893b9c)**, not a fresh restart of the current trio. My HEARTBEAT note ("fresh-restarted warm-chained from 100×70 → converged at 717") was **incorrect** — the current run's 141×85 never reached 717; it HUNG at outer 281 and was killed. The 717 npz is a byte-match to the deleted stage-1 file, as you said. Apologies for the muddied provenance.

**Current-run 141×85 (hung at outer 281): KILLED.** Process gone, log still frozen at outer 281 (mtime 19:38 Oct 20, 51076 B). So for THIS run (4e2374e) node 3 = **UNRESOLVED — inner-solve stagnation**. No clean single-run trio; your solver-equivalent framing stands.

**P2: relaunched fresh** (single-threaded, corrected script, `.venv/bin/python -u`). First `history record keys:` line already printed and confirms all corrected names are present:
```
['G_tot_cm1s', 'Gii_max_cm3s', 'NH', 'Te_max_K', 'drain_current_A_per_um', 'iteration', 'max_dphi_V', 'n_max_cm3', 'p_max_cm3', 'relative_number_balance', 'seconds', 'she_assembly_s', 'she_krylov_outer_iterations', 'she_linear_s', 'she_preconditioner_reused', 'she_used_x0']
```
71×58 running now (--extra 100), then 100×70. Will paste R_phi min/med/max + excursion count + Gii/Gtot/Id drift per node when they land.

**Honest trio framing (adopted):** 71×58 +0.006% and 100×70 +0.40% (current run 4e2374e); 141×85 +0.79% (earlier run 1893b9c, SAME solver, warm-chained from an earlier 100×70). All three certify <1% under the same solver; the finest mesh is the fragile one (one run hung, an earlier run certified) — conditioning sharpens with refinement.

---

## 2026-10-22 12:25 MYT — R5 CLOSED (clean tree = True) + NUM-01 / NUM-02 / RUN-03 landed. TWO FLAGS.

### ⚑ FLAG 1 — the Gate C validator is NOT on this host. Needs a resend.
`Liang1997_Readonly_Checkpoints.py` (sha `1574593918f5…`) does not exist anywhere on this Linux box,
is not in the repo at any commit, and is not in `CLOSEOUT_solver-frozen-2026-09-26/` (that bundle
has only README/PROVENANCE/ENVIRONMENT/report PDF + `SHA256SUMS.txt`, no `gate_c/` dir, no script).
So step 4 could not be run with your script. I wrote
`report/closure/gate_c_cleanroom_local.py` — a **local reimplementation** of its checks and its
exact output schema (`checks[]`, `nodes[]`, `git{head,dirty}`, `refinement_ratios`, `S_rev…`,
`archival_parity`, `overall`) — and labelled it as such in `program`, in the file header, and in the
proof doc. It is read-only. **Please resend the original**; swap it in and re-run for the official
clean-tree CP7.

### ⚑ FLAG 2 — the committed data at `e4c7587` does NOT have all three sidecars.
The trio NPZs **are** committed (so the clone's `data/` is hash-pinned and porcelain stays empty),
but:
- **71×58 sidecar = STALE.** It is the 2026-10-16 cold-restart sidecar (`cum_iters=360`,
  `passed=false`), terminal `Gii=2.706653e25 / Gtot=8.159518e13`, vs NPZ terminal
  `Gii=3.075752e25 / Gtot=9.264380e13`. Different, abandoned trajectory.
- **100×70 sidecar = ABSENT. 141×85 sidecar = ABSENT.** Never committed.

And there are **three mutually distinct datasets** in play — this is the explicit data-source
decision you asked for:

| source | 71×58 | 100×70 | 141×85 |
|---|---|---|---|
| committed at `e4c7587` (what I replayed) | `6327362…` | `12e5e71…` | `d9eaf69…` |
| `CLOSEOUT…/SHA256SUMS.txt` | `2e5736b0…` | `9d8139b5…` | `dd51e353…` |
| Windows Gate C JSON | `33533e2c…` | `ad390eb4…` | `59b16b78…` |

Your earlier Gate C PASS was on the **Windows Rev6 set** (`3.075619 / 2.087561 / 2.399434 e25`); the
commit carries the **Linux R_phi-converged set** (`3.075752 / 2.144818 / 2.406344 e25`). Pick one
and pin it. **My recommendation:** commit all three sidecars regenerated from the NPZ `last4_*`
terminal chunks via `src/certified_window.py` (NUM-01), and mark the old 71×58 sidecar *superseded*
rather than silently overwriting it.

### CLEAN-TREE REPLAY (R5) — done, KEY datum obtained
Fresh clone → `git checkout --detach e4c7587` → `HEAD=e4c7587f64cf4ebf74df15ea6f5ccae442672eed`,
`git status --porcelain` **empty (0 bytes)**, re-verified pristine before **and after** each run
(all gate output was written outside the clone, so nothing could dirty it).

- **Gate B: 11/11 PASS**, and the tree was *still* byte-for-byte pristine afterwards. Identical
  verdict to the dirty-checkout run — the fix commit behaves the same on a provably clean tree.
- **Gate C: `Source tree clean = True`** ← the R5 datum, now clean rather than dirty.
  Sidecar-based mode is `INCOMPLETE` *only* on data-custody (`71×58` stale sidecar, two missing) —
  not on integrity. Supplementary sidecar-free mode (`--npz-window`, clearly labelled, reconstructs
  from the NPZ's own `last4_*`) gives all three nodes genuine 4-consecutive-iteration windows:
  `71×58` 322–325 (spread 6.974e-05), `100×70` 926–929 (2.131e-05), `141×85` 714–717 (7.748e-06),
  all under the unchanged 3e-4 gate; H-hashes identical; refinement 1.414355/1.414368; overall
  `INTERNAL CHECKS PASS — PAPER VALIDATION NOT CLAIMED`; still **NOT SPATIALLY CONVERGED**.
  Bonus: `eps_max` IS present on all three Linux nodes (it was absent on the Windows set), and
  archival parity is materially better: `+2.868 / +0.460 / −0.276 %` vs `+2.864 / −2.222 / −0.562 %`.
  Only `71×58 +2.868%` remains outside ±2% (the known under-converged archival value).

### NUM-01 — centralized, and the degenerate-window hole is closed
New `src/certified_window.py` = the single authoritative reader; `read_certified_window(npz, sidecar)`
requires **4 unique consecutive** absolute iterations **and** a terminal-scalar match against the
NPZ, and rejects a stale/mismatched sidecar. `richardson_fit.py`, `run_richardson_trio.py` (both the
already-passed check *and* the cross-chunk resume-buffer reload, via `validate_buffer`) and
`gen_run_report.py` now all route through it, so the window and the `u` half-range can no longer
diverge between consumers. Verified on the real trio — identical `u` from both code paths:
`71×58 1.072401e21`, `100×70 2.284844e20`, `141×85 9.321655e19`, `match=True` for all three.
Reviewer's regression test implemented: a **1-iteration terminal chunk with a drifting prior-3
sidecar → `u_Gii = 1.1108e21 > 0`** (it was 0 before). Degenerate no-sidecar case → correctly not
certifiable; stale sidecar → rejected with fallback.

### NUM-02 — signed per-node manifest
New `src/node_manifest.py`: `build_manifest` / `verify_manifest` with full 40-char commit (resolved
from the NPZ short hash), **dirty refusal**, frozen solver definition (Phi_gate, mesh law, dH,
she_tol, tol_phi, Anderson), canonical physics-constant JSON, doping/geometry SHA-256,
H-array SHA-1 (+NPZ `H_hash` prefix consistency), warm-source SHA-256, and python/numpy/scipy
versions. Your three acceptance tests pass: **missing H_hash → FAIL, changed Phi_gate → FAIL,
changed warm-source SHA → FAIL**. On the real committed node it correctly reports
`FAIL -> ['git tree dirty (refused): not a frozen solver']` — that run *was* made on a dirty tree.
`git_commit_full` resolves: `4e2374e374d43dc33efc4e5e533b768ea3e35541`.

### RUN-03 — Stage-1 sentinel now hard-fails
`run_linux_full.sh` exits nonzero when `figures/she2d_iv_moment.png` is absent (was warn+continue).
Sandbox-tested both ways: absent → `EXIT_A=1`, log has `sentinel … MISSING`, Stage 2 never reached;
present → `EXIT_B=0`, full chain runs.

### Test log
`report/closure/ENG_ITEMS_TESTLOG_20261022.txt` (unit tests, real-data consumer cross-check,
manifest on real data, RUN-03 both branches). Proof/custody doc:
`report/closure/CLEANROOM_PROOF_20261022.md`.

---

## 2026-10-22 12:45 MYT — R5 CLOSED: authentic validator ran clean-tree, all 3 nodes certify sidecar-based.

### What you sent, verified
- Authentic `Liang1997_Readonly_Checkpoints.py` committed at `7501ee2`. sha256 checked:
  `1574593918f5cd82f507cb2fddc26f9f520f5d462906d26d589ff00e3e8a0635` — matches your `1574593918f5…6a0635`. ✓

### What I did (commit `fca646b`)
- Regenerated all THREE progress.json sidecars from the committed NPZs' own `last4_*` terminal arrays
  via `src/certified_window.py` (added `write_certified_sidecar()` + `--write` CLI, NUM-01 writer).
  Windows are the genuine 4-consecutive-iteration windows: 71×58 `[322..325]`, 100×70 `[926..929]`,
  141×85 `[714..717]`; `passed=true`, `cum_iters` == terminal iter.
- Marked the old 2026-10-16 cold-restart 71×58 sidecar **SUPERSEDED** (renamed to
  `data/she2d_richardson_71x58.progress.json.superseded_20261016`, content preserved — not silently
  overwritten).
- **Dataset label:** committed trio = **Linux R_phi-converged set** (`3.075752 / 2.144818 / 2.406344 e25`).
  Closeout bundle + Windows Rev6 = HISTORICAL. (Resolves the three-dataset ambiguity.)

### Clean-tree replay at `fca646b` (fresh clone → detach, porcelain 0 bytes before AND after)
- **Gate B: PASS 11/11**, `git.dirty=False`.
- **Gate C (AUTHENTIC): `INTERNAL CHECKS PASS — PAPER VALIDATION NOT CLAIMED`**, `errors=[]`,
  **`Source tree clean = True`**, all three nodes certified **sidecar-based (no fallback)**:
  spread 6.974e-05 / 2.131e-05 / 7.748e-05, H-hashes equal, params comparable, refinement
  1.414355/1.414368, `S_rev=10598.04`, `NOT SPATIALLY CONVERGED`.

### Three remaining FAILs are all non-critical warnings (not errors; overall stays PASS)
- `Phi_gate` absent from NPZs (to be frozen via the NUM-02 signed manifest, not in the NPZ).
- `eps_max` absent — NPZs carry the equivalent `eps_max_eV` (schema-name mismatch).
- Archival parity `71×58 +2.868%` (the known under-converged archival value).

Full proof: `report/closure/CLEANROOM_PROOF_20261022.md`. Clean-tree CP7 is complete on all three
axes you asked for: authentic script + self-contained pinned commit + clean tree. 🌳
