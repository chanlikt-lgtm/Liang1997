# Gate-4 analysis-rule amendment — surface-pinned hotspot (reviewer note)

**Date:** 2026-10-27 · **Spec:** v1.6 §6 (analysis rules) · **Full sweep still HALTED (reviewer HOLD).**

Raising this **before** the Y-family runs so any change to the analysis rules is pre-registered, not
post-hoc. Requesting your concurrence on the amendment in §3.

## 1. The finding (from the one certified node, 71×70)

The certified 71×70 node places the peak G_ii **on the y = 0 surface**: `xy_Gii_max = (0.58938 µm, 0)`,
and the vertical FWHM is correctly flagged `boundary_truncated = True` (the profile has no lower
half-maximum crossing — the peak sits on the boundary). This is a **surface-pinned hotspot**, consistent
across the three bit-identical single-thread runs.

## 2. Why it affects the pre-registered Gate-4 test

The frozen headline grid-feature test was *"does the hotspot **depth** stop tracking Δy, or keep moving
with the mesh?"* That test implicitly assumed a **sub-surface** hotspot with a measurable depth and a
two-sided depth-FWHM. A **surface-pinned peak has no depth to track** and no symmetric depth-FWHM, so
that specific test is ill-posed as written. (The drain-**x** test is unaffected: the peak's x-location
and value under drain-x refinement are still well-defined.)

## 3. Proposed amendment (pre-registered; requesting concurrence)

For a surface-pinned peak, replace the "hotspot depth tracks Δy?" test with the following Y-family
(depth-y refinement, Nx fixed) convergence questions, all on the now-clean single-thread observables:

1. **Surface peak value:** does the interpolated peak G_ii at the surface converge under depth-y
   refinement (relative difference `d` shrinking across levels)?
2. **Near-surface vertical structure:** does the **one-sided** half-width (peak → into the bulk; report
   it as one-sided, never a fabricated symmetric FWHM) and the vertical decay converge?
3. **Integrated observable:** does `G_tot` (vertical integral) converge under depth-y refinement — the
   best-conditioned test of whether the surface layer is resolved?
4. **Report `hotspot_y` explicitly** (= 0 here) and the `boundary_truncated` flag for every node; do not
   report a two-sided depth-FWHM for a surface-pinned peak.

**Pre-declared failure mode (honest, by analogy to a known result):** if the surface peak value
**diverges** under near-surface vertical refinement — i.e. the first interior node's value keeps growing
as Δy→0 — classify it as a **non-convergent near-surface resolution layer at the abrupt surface contact**
and report it UNRESOLVED, *not* as a converged value. This is the same class as the near-contact
injection-layer non-convergence already documented in the sister trench study (ideal Dirichlet surface
contact → unbounded gradient as spacing→0), so we flag the possibility in advance rather than discover
it and rationalize it afterward.

## 3.1 Frozen numeric convergence/divergence criterion (pre-registered before any Y-run)

So "diverges" is objective, not a post-hoc judgement. Y-family levels `Ny ∈ {58, 70, 85}` (coarse→fine)
give values `v1,v2,v3` for each observable, with adjacent relative differences
`d12 = 2|v1−v2|/(|v1|+|v2|)`, `d23 = 2|v2−v3|/(|v2|+|v3|)`, and **contraction ratio `r = d23/d12`**.

- **CONVERGING** ⇔ the sequence is monotone AND `r < 1` (successive differences shrink). Report the
  finest-grid value as the legitimate best **discrete** estimate — no continuum claim.
- **NON-CONVERGENT / UNRESOLVED** ⇔ `r ≥ 1` (the finer step moves at least as much as the coarser — no
  approach to a limit), or non-monotone. Report UNRESOLVED, not a converged value.

The **gate is `r ≥ 1`** — parameter-free, nothing arbitrary to tune. We also **report `r` itself**, and
if `r ≳ 3` (comparable to the sister trench near-contact study's measured increment ratio ≈ 3.4–3.5)
additionally label it *"strong near-surface divergence (trench-class)"* — this is a **comparison
reference for narrative, NOT the divergence threshold** (so the verdict is never hostage to a chosen
factor). With 3 levels there is one `r`; a 4th level (if the resource gate permits) gives a second `r`
and a stronger monotonicity check. This criterion is frozen here, before any Y node runs.

## 4. What does not change

- The X-family (drain-x) tests: peak x-location and value convergence — unchanged.
- The discretization-only scope; the non-monotone→inconclusive discipline; no continuum/physical claim.
- All other Gate-4 rules in spec v1.6 §6.

## 5. Ask

Concurrence on the §3 amendment (or a preferred alternative) so the Y-family results are interpreted
under a rule frozen before they exist. This is independent of — and does not presume — the §5 evidence
verification / GO decision still pending on your side.
