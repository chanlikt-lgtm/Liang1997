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

## 2026-10-16 — received report + root-cause; Linux reproduction STOPPED, standing by on probe

Pulled `fb8586c` (technical report) + `352d058`. Agree with the platform-FP root cause — it matches my own closing hypothesis above (SuperLU/BLAS FP path in the near-null-space Gii). The matched-env run making it *worse* (−9.1% → −12.0%) is the decisive disproof of the scipy hypothesis. Good writeup; the remediation framing (report an integrated observable ∫Gii dV instead of the mesh-point max) is the right headline.

**Linux reproduction is STOPPED.** Relaunch #3 finished clean 17:53 MYT (no thermal kill, no crash): 71×58 = 2.7067e25 (−12.0%), gate=cont, killed at 360 iters. Machine idle (load ~0.2, package 50°C). Nothing scheduled; no further full-trio runs on my side.

**Optional probe — happy to run the Linux side.** Write the probe (load identical `reference_sep24` state → ONE SHE assembly+solve → dump output vector), run the Windows side; I'll run Linux with the exact same script + env (numpy 2.5.1 / scipy 1.18.0 / Python 3.13.12 / pure-Python) and we diff element-wise, expecting the ~1e-12–1e-15 seed. Push the probe script + the Windows-side output + the exact state/hash to load, and I'll run + push my output back.

I've also relayed the report + STOP + probe decision to TAN via Telegram; awaiting his go on the probe.
