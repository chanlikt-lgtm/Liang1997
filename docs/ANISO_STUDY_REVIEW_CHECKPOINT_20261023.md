# Anisotropic Mesh Study — Reviewer Checkpoint

**Project:** Liang1997  
**Review ID:** SCI-01 / ANISO v1.2  
**Checkpoint date:** 2026-10-23  
**Current disposition:** **CONDITIONAL GO** for harness correction and validation; **HOLD** for the full anisotropic sweep.  
**Scope:** Numerical reliability, reproducibility, threading controls, certification, and defensible convergence claims.  

## Source documents

- [Reviewer note (2026-10-23)](https://github.com/chanlikt-lgtm/Liang1997/blob/main/docs/ANISO_STUDY_REVIEWER_NOTE_20261023.md)
- [Anisotropic mesh study specification v1](https://github.com/chanlikt-lgtm/Liang1997/blob/main/docs/ANISOTROPIC_MESH_STUDY_SPEC_V1.md)
- [Study harness](https://github.com/chanlikt-lgtm/Liang1997/blob/main/campaign/aniso_mesh_study.py)

> **Status rule:** An unchecked item is **not verified**, not necessarily proven defective. Mark items complete only after linking evidence. This document records review checkpoints, not results of newly executed solver tests.

## Gate 0 — Policy and authorization

- [ ] **G0.1 — Resolve amendment approval status.** Identify separately: proposal acceptance, scientific-review sign-off, and authorization to execute the full sweep. Remove or explain the apparent conflict between the note's pending sign-off and the spec's approved wording.
  - **Evidence:** `________________`
- [ ] **G0.2 — Enforce execution authorization.** Prevent accidental full-sweep launch when authorization is absent (not just a console warning). Record who authorized it and when.
  - **Evidence:** `________________`
- [ ] **G0.3 — Freeze experiment definitions.** Record Git commit, config hash, mesh family, parameters, tolerances, threading policy, and planned analysis rules before inspecting sweep results.
  - **Evidence:** `________________`

**Gate 0 status:** [ ] PASS  [ ] HOLD  

## Gate 1 — Harness integrity (blocking)

- [ ] **G1.1 — Warm-start path correctness.** Resolve warm-start `.npz` paths relative to the output directory (or use absolute paths). Assert that every intended warm-start file exists; do not silently fall back to a cold start.
  - **Acceptance:** A two-node dry run records the actual warm-start path, successful load, and the receiving mesh.
  - **Evidence:** `________________`
- [ ] **G1.2 — Thread count enforcement and provenance.** Set/check the effective BLAS/OpenMP thread configuration before numerical work begins. Persist actual thread-pool information, backend/library versions, CPU/platform, and solver commit per node.
  - **Acceptance:** Logs show one-thread and eight-thread controls actually ran with the requested effective thread configuration.
  - **Evidence:** `________________`
- [ ] **G1.3 — Collision-free output naming.** Include mesh, thread count, replicate/run ID, and configuration identifier in result paths. Never overwrite a previous control artifact.
  - **Acceptance:** One-thread and eight-thread runs on the same mesh coexist and have distinct checksums/metadata.
  - **Evidence:** `________________`
- [ ] **G1.4 — Fourth-level RAM gate.** Define and implement a measured peak-memory/resource feasibility rule before any optional fourth-level refinement; record approval and resource measurement.
  - **Acceptance:** An infeasible test case is blocked, and a feasible case records its resource decision.
  - **Evidence:** `________________`
- [ ] **G1.5 — Hotspot FWHM implementation.** Calculate physical width from two interpolated half-maximum crossings; distinguish a boundary-truncated, unresolved, or multi-peak profile from a valid full width.
  - **Acceptance:** Unit tests on analytic/synthetic peaks recover known widths within a documented tolerance.
  - **Evidence:** `________________`
- [ ] **G1.6 — Shared-anchor repeat semantics.** State whether `(100,70)` is one shared computation or independent X/Y repeats. If repeats support reproducibility claims, retain independent files and compare them.
  - **Evidence:** `________________`

**Gate 1 status:** [ ] PASS  [ ] HOLD  

## Gate 2 — Numerical certification (blocking)

- [ ] **G2.1 — Complete certification criteria.** Predefine tolerances and normalizations for potential residual `R_phi`, continuity residual, conservation/number balance, and observable drift; do not report the latter metrics without using them when claiming certification.
  - **Acceptance:** Every node has explicit PASS/FAIL for each numerical criterion, with raw values and units.
  - **Evidence:** `________________`
- [ ] **G2.2 — Continuation/restart diagnostic.** Document exactly what solver state is carried over when continuing for 40 iterations, including any acceleration/history state.
  - **Acceptance:** Separate endpoint-to-restart change from subsequent continuation drift; report both.
  - **Evidence:** `________________`
- [ ] **G2.3 — Observable stability.** Evaluate at least peak `G_ii`, integrated `G_tot`, and hotspot `(x,y)` using predefined absolute/relative tolerances appropriate to their scales.
  - **Acceptance:** No node is certified from `R_phi` alone.
  - **Evidence:** `________________`
- [ ] **G2.4 — Smoke test certification.** Complete corrected `71×70` smoke test and archive solver logs, `.json`/`.npz`, convergence traces, and certification decisions.
  - **Acceptance:** All required checks pass; any remaining failures are disclosed and resolved before full sweep.
  - **Evidence:** `________________`

**Gate 2 status:** [ ] PASS  [ ] HOLD  

## Gate 3 — Threading comparability (blocking)

- [ ] **G3.1 — Paired thread controls.** Run `71×70` at effective 1 and 8 threads with identical frozen physics, solver settings, and initialization; retain separate artifacts.
  - **Evidence:** `________________`
- [ ] **G3.2 — Quantify per-observable differences.** Tabulate absolute and normalized differences for `G_ii,max`, `G_tot`, and hotspot coordinates (and widths if used in claims). Report raw values as well as percentages.
  - **Evidence:** `________________`
- [ ] **G3.3 — Exact fallback trigger.** Pre-register a comparison rule for close neighboring-mesh observables; e.g., for positive nonzero quantities, `d(a,b)=2|a-b|/(|a|+|b|)<0.01`, with separate absolute tolerances for near-zero values and coordinate shifts. Treat 1% as an operational trigger, **not** a proven uncertainty bound.
  - **Evidence:** `________________`
- [ ] **G3.4 — Apply controls to implicated mesh pairs.** Whenever an adjacent pair is used for a near-convergence or asymptotic-order claim and meets the pre-registered trigger, rerun **both** members single-threaded and compare the inferred mesh trend.
  - **Evidence:** `________________`
- [ ] **G3.5 — Limit interpretation.** Do not generalize the `71×70` measured thread difference as a rigorous noise bound for every mesh.
  - **Evidence:** `________________`

**Gate 3 status:** [ ] PASS  [ ] HOLD  

## Gate 4 — Directional-convergence interpretation

- [ ] **G4.1 — X-only/Y-only isolation.** Verify the non-refined mesh direction and all physics remain frozen within each family; report exact mesh coordinates/local spacings.
  - **Evidence:** `________________`
- [ ] **G4.2 — Hotspot quality flags.** Report physical hotspot position, interpolation quality, boundary proximity, peak multiplicity, and displacement relative to local mesh spacing.
  - **Evidence:** `________________`
- [ ] **G4.3 — Apparent order vs. asymptotic convergence.** Use actual effective spacings (including unequal refinement ratios) when estimating directional apparent order. Three monotone levels permit an *apparent* order but do not alone establish the asymptotic regime.
  - **Evidence:** `________________`
- [ ] **G4.4 — Nonmonotone or uncertified outcomes.** Predeclare that such sequences will be reported as inconclusive; do not extrapolate them into claimed continuum-limit agreement.
  - **Evidence:** `________________`
- [ ] **G4.5 — Preserve the scientific boundary.** Present conclusions as discretization-convergence evidence, not physical validation or agreement with Liang (1997) unless separately established.
  - **Evidence:** `________________`

**Gate 4 status:** [ ] PASS  [ ] HOLD  

## Release checkpoint — Full sweep authorization

**Blocking prerequisites:** Gate 0, Gate 1, Gate 2, and Gate 3 must each be marked PASS with linked artifacts before full-sweep authorization. Gate 4 analysis rules must be frozen before results are interpreted.

| Checkpoint | Current status | Evidence / reviewer note |
|---|---|---|
| G0: Policy and authorization | NOT VERIFIED | |
| G1: Harness integrity | NOT VERIFIED | |
| G2: Numerical certification | NOT VERIFIED | |
| G3: Threading comparability | NOT VERIFIED | |
| G4: Directional analysis rules pre-registered | NOT VERIFIED | |

**Full-sweep disposition:** [x] **HOLD**  [ ] GO  
**Reason:** Evidence of completed fixes, smoke certification, and thread controls has not been verified in this checkpoint.  

**Reviewer:** `________________`  
**Review timestamp (UTC):** `________________`  
**Git commit / configuration hash:** `________________`  
**Artifact directory or immutable run manifest:** `________________`  
**Approver / authorization record:** `________________`  

### Decision history

| Date (UTC) | Commit / manifest | Decision | Reviewer | Reason / evidence |
|---|---|---|---|---|
| 2026-10-23 | Pending | CONDITIONAL GO for fixes; HOLD full sweep | Pending | Initial review checkpoint; verification pending |

## Reporting template for each executed mesh

| Field | Value |
|---|---|
| Run ID / family | |
| Mesh `(Nx, Ny)` and local spacing | |
| Git commit, config hash | |
| Threads requested / effective | |
| BLAS backend and environment | |
| Initialization source | |
| `R_phi` / continuity residual / conservation error | |
| Continuation and restart deltas | |
| `G_ii,max` / `G_tot` | |
| Hotspot `(x, y)` and quality flags | |
| FWHM and validity flag | |
| Certification PASS/FAIL | |
| Output artifact links and checksums | |

---

**Checkpoint principle:** No unchecked item becomes a PASS solely because the code appears plausible. Attach reproducible evidence, and preserve the pre-registered decision rules when new results become available.
