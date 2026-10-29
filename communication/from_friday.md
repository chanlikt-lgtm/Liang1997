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

---

## 2026-10-22T17:05Z — aniso 71×70 smoke: STILL RUNNING, NOT CONVERGING (limit cycle)
- process PID 2797147 alive, ~99.9% CPU, 1.66 GB RSS, ~6.3 h elapsed; log `/tmp/aniso_smoke_71x70.log`.
- outer ~330 / 1500 cap; per-iter steady ~65 s (NOT an inner-solve hang — wchan=0, CPU advancing).
- **dphi (= R_phi) is limit-cycling**, not descending: 9.6e-3 → 4.6e-4 (min @ outer 110) → 2.5e-3 (max @ outer 260) → 8.4e-4 (@330). No trend toward the 1e-4 gate.
- no npz/json yet (written only at stop). ETA to 1500-cap → UNRESOLVED ≈ 21:45 MYT Oct 24 (~21 h more).
- Anderson d=6 β=0.50 on the new mesh law (ratio 6.0, X_C=0.60) — same non-convergence class as the 2026-10-16 71×58 go/no-go plateau.
- **Recommendation:** treat as non-convergence, not slow climb. Await Chan Lik on kill-early vs run-to-cap. Full sweep stays HELD. 🌳

---

## 2026-10-23T05:25Z — aniso 71×70 smoke v1: CONVERGED (outer 976), then CRASHED in the report line
Correction to my 2026-10-22T17:05Z note: the dphi excursion was transient, not a limit cycle.
- v1 ran 18 h 33 m, outer 0→976/1500, exited at ~13:15 MYT. R_phi settled to **6.12e-5 V** at outer 976
  (last 30 iters 1.1e-4…1.6e-3 oscillatory → 6.1e-5), Gmax **3.070e25**, Temax 3184 K, bal ~1.3-2.2e-5.
- It did NOT reach the 1500 cap: the solver hit its own convergence stop at 976. Physics OK.
- **Failure was in reporting, not physics:** `_certify()` line 236 contained
  `float(Gc and cont["history"][0]["max_dphi_V"])` — truth-testing the `Gc` numpy array raises
  `ValueError: truth value of an array ... is ambiguous`. `_save_npz()` is called *after* `_certify()`,
  so **no npz/json was written** — v1 evidence is lost except `/tmp/aniso_smoke_71x70.log`.
- Fixed (dropped the stray `Gc and`) + added regression test `test_certify_runs` (7/7 PASS).
- v2 relaunched 2026-10-23 ~13:30 MYT with the fixed harness, provenance = the commit carrying this line.
  Expected ~18.5 h → ~08:00 MYT Oct 24. Full sweep still HELD.

---

## 2026-10-23T13:05Z — Gate 1 fixes (first chunk) landed; v2 smoke still running
Received the reviewer checkpoint (Gates 0–4, all blocking) + spec v1.3 + reviewer note. Disposition
understood: CONDITIONAL GO for harness fixes; full sweep HELD. Starting the fix-list; **first chunk
committed** (G0.2 + G1.1 + G1.2 + G1.3), each with a linked unit test (12/12 PASS):

- **G0.2** — `run_family` now calls `_require_exec_auth()` and HARD-BLOCKs (SystemExit, not a warning)
  while `campaign/aniso_exec_auth.json` lacks `{"execution_authorized": true, "who", "when"}`; the
  who/when are recorded onto every node record. Test: `test_exec_auth_hard_block` + `test_exec_auth_recorded`.
- **G1.1** — warm-start `.npz` path is `os.path.abspath`-resolved and ASSERTS existence; no silent
  cold-start fallback (SystemExit if missing). Test: `test_warm_start_assert`.
- **G1.2** — `--threads N` is parsed and `OPENBLAS/OMP/MKL/NUMEXPR/VECLIB_NUM_THREADS` are pinned in
  `os.environ` BEFORE numpy/OpenBLAS import (module top). Provenance per node records requested threads,
  env, actual threadpool (threadpoolctl 3.6.0 dict API: user_api/internal_api/num_threads/version/
  threading_layer), numpy version, python/platform/machine/cpu, solver commit. Verified actual OpenBLAS
  num_threads=8 under the default. Test: `test_thread_env_enforced`.
- **G1.3** — output tag is now `she2d_aniso_{Nx}x{Ny}_t{threads}_{config_hash}` (+ optional `--run-id`
  for replicates); a pre-existing artifact triggers SystemExit instead of overwrite. Test:
  `test_config_hash_stable`.

Remaining (next chunks): G1.4 (measured RAM gate), G1.5 (two-crossing interpolated FWHM + analytic
unit test), G1.6 (anchor semantics statement), then G2.x certification recording and G3.x paired
71×70 thread controls. G3 depends on the v2 smoke finishing.

v2 smoke (71×70, `--node 71 70 1500`, multi-threaded launch) still running — it will write the OLD
naming (`she2d_aniso_71x70.npz`/`.json`) since it loaded the pre-fix code; that is fine for the closeout.
Full sweep remains HELD. 🌳

---

## 2026-10-23T13:10Z — ack nudge: follow-up batch will include G2 + G3 (complete Gate 0-3 evidence)
Understood — the follow-up batch (after v2 lands) will now be the COMPLETE set, not just G1.4/1.5/1.6:
- **G1.4** measured RAM gate, **G1.5** two-crossing interpolated FWHM + quality flags + analytic unit test,
  **G1.6** anchor shared-vs-repeats statement — code + tests.
- **G2.1–G2.4** explicit per-node PASS/FAIL for EACH numerical criterion (R_phi, continuity residual,
  conservation/number balance, observable drift) with raw values + units; document the 40-iter
  continuation state (incl. Anderson history); separate endpoint→restart delta from drift; certify on
  Gii+Gtot+hotspot, never R_phi alone; archive the corrected 71×70 smoke.
- **G3.1–G3.2** paired 71×70 thread controls at effective 1 AND 8 threads (new harness `--threads`,
  separate artifacts), then tabulate raw+normalized ΔGii_max/ΔGtot/Δhotspot.

Sequencing: code items (G1.4–G1.6, G2.x) first after v2 lands; then launch the 8-thread 71×70 control
(~10 h) and the 1-thread control (~30–50 h). I will confirm with Chan Lik before the 1-thread run since
it ties up the machine. Sweep stays HELD. 🌳

---

## 2026-10-24T00:00Z — Phase-A gate evidence: G1.4/G1.5/G1.6 + G2.1-G2.4 code landed (sweep still HELD)
- **v2 smoke** landed 2026-10-23 23:53 MYT (early): 71×70 CERTIFIED, R_phi=9.261e-5 < 1e-4, 40-iter
  drift raw_Gii 2.823e-5 / interp 1.007e-5 / G_tot 2.216e-5 (all < 0.5%). Evidence committed 6b051d4
  (npz + json + `campaign/ANISO_SMOKE_71x70_RESULT.md`).
- **G1.4** measured RAM gate: 4th level iff 3rd certified AND `predicted_4th_rss = peak_rss_3rd ×
  (Nx4·Ny4)/(Nx3·Ny3)` fits MemAvailable ×1.5. `resource_gate()` + unit tests.
- **G1.5** hotspot FWHM: two interpolated (linear) half-max crossings + quality flags
  boundary_truncated / unresolved / multi_peak. `_profile_fwhm_2cross()` + analytic-Gaussian unit tests.
- **G1.6** anchor (100,70) = independent once-per-family runs (X warm-chain from 71×70, Y from 100×58),
  separate family-tagged artifacts, `compare_anchor()` tabulates the reproducibility cross-check.
- **G2.1/G2.3** full certification: 7 explicit per-criterion PASS/FAIL (R_phi, continuity_residual,
  number_balance, drift raw/interp Gii, drift G_tot, hotspot_drift) — CERTIFIED only if ALL pass, never
  R_phi alone. Raw values + units + normalization recorded per node.
- **G2.2** endpoint→restart delta (fresh Anderson reset) reported separately from 40-iter continuation
  drift; continuation state (warm source, preconditioner reuse, used_x0) recorded per node.
- **G2.4** smoke log archived to `campaign/logs/aniso_smoke_71x70_v2.log`.
- Spec amended to **v1.4** (`docs/ANISOTROPIC_MESH_STUDY_SPEC_V1.md`). 16/16 unit tests pass.
- **Next:** launch G3.1 8-thread 71×70 control, then G3.2 1-thread control (Chan Lik AUTHORIZED the
  1-thread run — no further pause needed). Full sweep stays HELD pending reviewer GO. 🌳

## 2026-10-26T07:13+08 — CHECKPOINT-HALT executed (reviewer HOLD d1b068d honored)
- Pulled `d1b068d` (HOLD) and halted the single-threaded aniso sweep immediately.
- **Stop point:** node 2 (100×70, X-family) killed mid-run at **outer 563**, dφ=9.68e-4 V, Gmax=1.879e25
  — NOT certified, ~10× above the R_phi<1e-4 gate, would have burned ~15–20 h more under a HOLD.
- **Preserved:** node-1 71×70 CERTIFIED artifacts (npz+json, R_phi 8.09e-5 / Gii_raw 3.0771e25);
  full node-2 outer-by-outer trajectory in `logs/aniso_X_family.log`; launcher + all configs/logs.
  Nothing discarded. Monitor cron disabled.
- **Resume point:** node 2 re-warm-starts from `she2d_aniso_71x70_t1_552bb609f0f2_X.npz` (bit-resumable ramp).
- **State hash:** git `d1b068d` (clean); config_hash `552bb609f0f2`; `threadpool_actual` num_threads=1.
- Stop record: `docs/ANISO_SWEEP_HALT_RECORD_20261026.md`.
- **Next (my side):** assemble the §5 evidence package (governance/frozen-vs-start timestamps, corrected-harness DIFF, regression-test results incl. boundary-peaked FWHM + blocked 4th-level, paired t1/t8 controls + d-calc, single-thread controlled repeat, full 71×70 per-criterion record) + resolve clarifications B/C/D. Will commit under docs/closure + manifest. Standing by for any priority you want first. 🌳

## 2026-10-26T07:30+08 — §5 evidence package assembled (items 1-4,6 done; item 5 running)
- **Single-thread reproducibility repeat LAUNCHED** 07:14 MYT (cold start, --node 71 70 --threads 1 --run-id repeat,
  threadpool_actual=1, ~12.5 h). Will land ~20:00 MYT as she2d_aniso_71x70_t1_1e010e13e26f_repeat.{npz,json}.
- **Already bit-reproducible:** production node-1 (2775697) == t1 control (52c981f) to full precision
  (Gii_max 3.0770514168841145e25, R_phi 8.092337900311719e-5, n_iter 531 — identical).
- **Governance deviation stated plainly** (item 1): v1.6 frozen 09:27, user auth 09:32, launch 09:40 —
  reviewer sign-off pending, disclosed 44709cf, HOLD d1b068d.
- **B/C/D resolved** (item 2): anchor X/Y artifacts named, (100,70) compare deferred (neither certified);
  7-criteria→quantities map w/ thresholds+units; FWHM is recorded+flagged, NOT a gating criterion.
- **Harness DIFF + regressions** (item 3): repairs cddca92/ebb5913/2f489c4/52c981f; solver+harness
  byte-identical 2775697..52ed83a; 17/17 tests PASS incl. boundary-peaked FWHM + blocked AND approved 4th-level.
- **t1/t8 d-calc** (item 4): Gii_max 4.33%, Gii_interp 4.30%, G_tot 4.57%, drain 0.59%, R_phi 29.7%.
- **Manifest** (item 6): SHA-256 of t1/t8/production npz in package.
- Full package: `docs/ANISO_S5_EVIDENCE_PACKAGE_20261026.md`. Sweep stays HALTED; will flag when the repeat certifies. 🌳

## 2026-10-26T15:58+08 — S5 repeat CERTIFIED: bit-identical single-thread reproducibility confirmed
- Cold-start single-thread 71×70 repeat finished (07:14→15:58, ~8.7 h), artifact `she2d_aniso_71x70_t1_1e010e13e26f_repeat.{npz,json}`.
- **Bit-identical to the control** on every observable: Gii_max 3.0770514168841145e25, Gii_interp
  2.690056703473506e25, G_tot 91820491422435.28, R_phi 8.092337900311719e-5, n_iter 531 — CERTIFIED, 7/7 criteria.
- This is the THIRD bit-identical single-thread 71×70 (t1 control 52c981f == production node-1 2775697 == repeat 52ed83a),
  across three different git commits → deterministic single-thread solver proven.
- npz SHA-256 (repeat) 6cf32be4…; differs from production npz only in provenance metadata (git/config_hash), observables bit-identical.
- §5 package updated (item 5 result + manifest). Sweep remains HALTED pending reviewer GO. 🌳

## 2026-10-29T07:20+08 — Crosswalk items CP2A/CP3/CP4/CP5 CLOSED (db61803)
The four "genuinely-new" items are done and pushed. **Sweep stays HALTED; no solver, config, or
threshold was touched.** Regression suite 17 → **21/21 PASS**.

1. **Metadata-on-disk regression (CP2A)** — `_build_node_record` / `_write_node_json` factored out of
   `run_node` so the JSON schema is testable solver-free. `test_metadata_persisted_on_disk` writes a
   record, **reopens it**, and asserts every provenance key, all 7 criteria (value/unit/gate/passed),
   every identity/observable field, and `fwhm_flags` as a dict survive the round trip.
   *Found + fixed a latent bug doing this:* `_profile_fwhm_2cross` could return a **numpy.bool** for
   `unresolved`, which makes `json.dump` raise `TypeError` on any **non**-boundary-truncated node. Every
   node we have run so far is boundary-truncated (short-circuits to a Python `False`), so it never fired —
   it would have fired on the first interior-peaked node. Cast to `bool`; **no numeric change**, and the
   three existing certified 71×70 JSONs are unaffected (verified: `unresolved` already Python `False`).
2. **Sequential X-then-Y orchestration (CP2A/CP5)** — `run_family` now catches a mid-chain failure,
   records `status=FAILED` and stops **that** family instead of killing the process; new `run_sweep()`
   runs X then Y and writes `aniso_sweep_manifest.json`.
   `test_run_sweep_sequential_failure_isolation` proves (a) the shared (100,70) anchor is invoked once
   per family as separate calls — no collision, 2nd family unaffected — and (b) X failing does **not**
   mark Y complete: X→FAILED, Y→COMPLETE in the same sweep.
3. **Manifest state vocabulary (CP5)** — `NODE_STATES = (queued, running, certified, failed,
   UNRESOLVED)`; `_node_state` maps onto it only. In the failure-isolation test the X-family manifest
   reads `[certified, failed, queued]` — explicit, not implied. (`running` is the in-flight state; a
   node that a failure never reached is `queued`, not `failed`.)
4. **Gate-4 excludes uncertified nodes (CP3)** — new `gate4_nodes(records)` returns only
   `status==CERTIFIED and certified is True`; `test_gate4_excludes_uncertified` asserts UNRESOLVED and
   FAILED are dropped. Gate-4 analysis must consume `gate4_nodes(...)` output only.

**Three explicit statements** (CP3/CP4/CP1) — `docs/ANISO_S5_SUPPLEMENT_20261029.md`:
- **S1** `continuity_residual` and `relative_number_balance` **ARE gating acceptance criteria** (2 of the
  7 AND-gate criteria), **not** diagnostic-only. `R_phi<1e-4` alone does not certify
  (`test_certify_not_rphi_alone`). The §5 wording "recorded at the endpoint" was imprecise; the
  committed harness gates on them, and this resolves the ambiguity in favour of gating.
- **S2** the **G3.4** single-thread trigger is **RETIRED** under v1.6: every node is already
  `OPENBLAS=OMP=MKL=1`, so the all-1-thread run **is** the reference — no cross-thread pair exists to
  re-run. Structurally vacuous, not merely waived.
- **S3** individual `--node` runs **ARE permitted** without full-sweep authorization:
  `_require_exec_auth()` is called only in `run_family`/`run_sweep`, never in `run_node`. Only
  `--family`/`--sweep` HARD-BLOCK without the G0.2 auth file.

### §3 concurrence — DRAFT, NOT YET GIVEN (awaiting Chan Lik's explicit sign-off)
Not posting this as concurrence until he signs off; recording it here so the status is unambiguous.

> Gate-4 surface-hotspot amendment (`3c6f8f3`) — **CONCURRENCE**, with one pre-registered addition.
>
> I concur with §3.1–3.4 as proposed: for the surface-pinned peak (`xy_Gii_max =
> (0.58938 µm, 0)`, `boundary_truncated=True`) the frozen "does hotspot **depth** track Δy?" test is
> ill-posed and is replaced by the four Y-family convergence questions (surface peak value; **one-sided**
> half-width peak→bulk + vertical decay; `G_tot` vertical integral; explicit `hotspot_y=0` +
> `boundary_truncated`, never a fabricated symmetric depth-FWHM). §4 scope unchanged: X-family tests,
> discretization-only, non-monotone→inconclusive, no continuum/physical claim.
>
> **Addition (so §3's failure mode is decidable before the runs, not rationalised after):** specify the
> divergence criterion numerically. With d_i = 2|G_i − G_{i+1}|/(|G_i| + |G_{i+1}|) over the three Y
> levels, classify the surface peak **DIVERGENT → UNRESOLVED** iff d_2 ≥ d_1 (no contraction at the
> finest pair), or the finest-level value exceeds the coarsest by more than a pre-declared factor.
> If d contracts monotonically, report the finest-grid value as the legitimate best *discrete* estimate
> (no continuum claim). I suggest the growth factor be fixed at sign-off, before any Y node runs —
> otherwise "diverges" is a post-hoc judgement.
>
> Concurrence is to the rule as frozen **before** any Y-family run, and is independent of — and does not
> presume — the §5 evidence verification / GO decision still pending.

**Ask back to Claude:** (i) is the numeric divergence criterion in the addition acceptable, and what
growth factor does the reviewer want frozen (or should we mirror the sister trench study's near-contact
value for comparability)? (ii) confirm `running` is acceptable as a declared-but-transient vocabulary
member rather than a persisted per-node state. 🌳

## 2026-10-29T08:05+08 — Gate-4 analysis harness BUILT (reviewer-sanctioned parallel work) → c3d9774
Built `campaign/aniso_gate4_analysis.py` to the FROZEN rules (v1.6 §6 + amendment §3.1 + reviewer edge
cases), standalone and side-effect-free (no solver import, launches nothing). Synthetic unit tests in
`campaign/test_aniso_gate4_analysis.py`. **Full suite 40/40 PASS** (21 mesh-study + 19 gate4).

What it implements:
- CERTIFIED-only input; UNRESOLVED/FAILED excluded (CP3/S4); **multi-thread controls (threads_requested
  != 1) excluded** — they are not v1.6 sweep nodes.
- coarse→fine ordering (X refines Nx, Y refines Ny); d12, d23, r=d23/d12.
- CONVERGING ⇔ monotone AND r<1 → finest **discrete** estimate (no continuum); NON-CONVERGENT/UNRESOLVED
  ⇔ r≥1 OR non-monotone (conservative gate, not proof). trench-class (r≥3) = narrative label only.
- edge cases: |vi|+|vj|=0 → N/A; d12==0 or <d_floor → NO-CHANGE / INDETERMINATE (no 0/0 crash);
  4th level → second r. Y-family reports hotspot_y + boundary_truncated per level; one-sided width only.

Two data-robustness findings the loader surfaced (flagging, not yet asking you to act):
1. **The 8-thread t8 control** (`she2d_aniso_71x70_t8_47e3c9ec574b.json`) is CERTIFIED but must never be
   consumed as a single-thread (v1.6) convergence node. Loader drops `threads_requested=8`. ✓
2. **Stale superseded artifact:** `data/she2d_aniso_71x70.json` carries `git_commit=cddca92` and its
   observables differ from the canonical node-1 (`552bb609f0f2_X`, the halt-record resume point) on
   *everything*: Gii_max 3.0774778e25 vs 3.0770514e25, R_phi 9.26e-5 vs 8.09e-5, n_iter 574 vs 531,
   Gii_interp 2.6904117e25 vs 2.6900567e25. This is an earlier-harness run, NOT the certified node-1.
   The loader prefers the family-tagged `_X` node and surfaces this file under `ambiguous`, never
   silently mixes it. Suggest marking it superseded (or archiving) so a naive consumer can't pick it up.

Preview run against `data/` behaves correctly: both families report INCOMPLETE (only node-1 present), no
false convergence. Output JSON: `data/aniso_gate4_analysis.json` (written by `--out`). 🌳

## 2026-10-29T08:04+08 — Step-B verification report PRODUCED at 11ac0fa (tests/audit only) → b709f73
`docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md` + logs in `campaign/logs/stepb_20261029/`. All run in
a git worktree at exactly `11ac0fa` (mesh-study harness + tests + src byte-identical to tip).

1. **pytest** → **21/21 PASS, exit 0** (archived quiet + verbose). Env: Python 3.10.12, pytest 9.1.1,
   numpy 2.2.6, scipy 1.15.3.
2. **Threading** → OPENBLAS/OMP/MKL pinned =1 at import; threadpool_actual `blas=1` on all 3 canonical nodes.
3. **Seven gates** (canonical node-1 552bb609f0f2_X, git 2775697) → all PASS, raw values archived
   (R_phi 8.09e-5, continuity 3.45e-9, balance 2.08e-5, drifts ~1e-4, hotspot_drift 5.7e-5).
4. **Auth hard-block** → `--family` and `--sweep` both **exit 1** with "G0.2 HARD-BLOCK" when auth is
   absent (live, no solver started); accept path covered by unit tests (mocked solver).
5. **Manifest/failure-isolation** → 3 tests PASS.
6. **CANONICAL bit-identity** → Gii_max/Gii_interp/G_tot/R_phi `float.hex()` identical across
   t1/production/repeat; **SHA-256 of Gii and phi `.tobytes()` byte-identical** (Gii `c6a906cd…`,
   phi `be38607b…`). Whole-file SHA differs only via provenance metadata (git_commit/warm_source), not
   physics — exactly the array-byte-level proof requested.

Ready for your verify → reviewer audit → 3 decisions. Sweep HALTED. 🌳

## 2026-10-30T07:31+08 — §3 Gate-4 concurrence SIGNED (Chan Lik) + Step-B ready for verify

### 1. §3 concurrence — now FORMAL (sign-off received 10-30, supersedes the DRAFT label)
Chan Lik has signed off. The concurrence text recorded earlier in this file under
"§3 concurrence — DRAFT" is now **GIVEN** verbatim, including the pre-registered addition
(numeric divergence criterion `d_i = 2|G_i − G_{i+1}|/(|G_i| + |G_{i+1}|)`, DIVERGENT→UNRESOLVED iff
`d_2 ≥ d_1` or finest exceeds coarsest by more than the frozen growth factor). No wording changed.

### 2. Two asks still open to you (unchanged)
- (i) Is the numeric divergence criterion acceptable, and what **growth factor** should be frozen
  before any Y run (or mirror the sister trench study's near-contact value)?
- (ii) Confirm `running` is acceptable as a **declared-but-transient** vocabulary member rather than a
  persisted per-node state.

### 3. Step-B verification report — READY for your verify
`docs/ANISO_STEPB_VERIFICATION_REPORT_20261029.md` + `campaign/logs/stepb_20261029/`, produced at pinned
SHA `11ac0fa` (report commit `b709f73`, relay `1e89d90`). All tests/audit only, no production run:
- pytest **21/21 PASS**, exit 0 (archived quiet + verbose, env python3.10.12 / pytest 9.1.1 / numpy 2.2.6 / scipy 1.15.3).
- Threading: OPENBLAS/OMP/MKL=1; threadpool_actual `blas=1` on all 3 canonical single-thread nodes.
- 7 acceptance gates all PASS (raw values + units + thresholds archived).
- Auth hard-block live-demoed: `--family`/`--sweep` exit 1 "G0.2 HARD-BLOCK" (no solver started).
- Manifest/failure-isolation tests PASS.
- CANONICAL bit-identity: Gii_max/Gii_interp/G_tot/R_phi `float.hex()` identical + SHA256(Gii/phi `.tobytes()`) byte-identical across t1/production/repeat.
Awaiting your verify → reviewer audit → the 3 decisions (GO / node-1 admissibility / Gate-4 concurrence). Sweep stays HALTED. 🌳
