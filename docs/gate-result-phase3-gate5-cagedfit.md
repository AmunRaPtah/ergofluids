# Gate result: Gate 5 (model-based caged-diffusion fit, same digitized data as Gate 4)

Date: 2026-07-31. Criteria and parameters locked in `docs/BUILD_PLAN.md` ("Gate 5" section) and
`repo/scripts/run_gate5.py` (docstring) before this script was run at full scale. Script:
`repo/scripts/run_gate5.py`, seed 20260731, 2000-draw bootstrap.

## Why this gate exists

Gate 4 (`docs/gate-result-phase3-realdata.md`) tested whether a local log-log slope, compared
between a fixed early window and a fixed late window of the digitized S14a MSD curve, measurably
decreased for the composite hyaluronan-collagen network. It did not, on its own pre-registered
primary criterion (95% CI of the early-late slope difference included zero). That write-up's "What
would change this result" section named two untried follow-ups: raw trajectory data from the
arXiv:1909.05091 authors, or a model-based fit of an explicit caged-diffusion functional form to the
whole curve, which might detect a plateau shape that a two-window slope comparison misses.

Author outreach was drafted (`docs/author-outreach-draft.md`, addressed to the corresponding
author, Prof. Gijsje Koenderink) and sent; as of 2026-07-31 no response has been received. With that
path currently exhausted, this gate tests the second, still-open option: the same S14a digitized
data (composite, hyaluronan, collagen_1mg curves, unchanged from Gate 4), fit with a genuinely
different functional form and comparison method, rather than new data.

## Model and method (as pre-registered in `docs/BUILD_PLAN.md`, restated here)

Two two-parameter models, fit by weighted nonlinear least squares (weights = `1/sigma_i^2`,
`sigma_i = sqrt(reported_error_i^2 + digitization_error_i^2)`, the same combined-in-quadrature
error Gate 4 used) on each curve's full digitized range, no early/late windowing:

- **Confined diffusion** (the caging hypothesis): `MSD(t) = P * [1 - exp(-t / tau)]`, the standard
  confined/restricted-diffusion form from the single-particle-tracking literature, originating in
  Kusumi, Sako & Yamamoto, *Biophys. J.* 65:2021-2040 (1993), restated in later SPT methods papers
  (e.g. Fujiwara et al., *Mol. Biol. Cell* 27:1101-1119, 2016). `P` is the MSD plateau, `tau` the
  confinement relaxation time.
- **Global power law** (the null used implicitly by Gate 0/1/4): `MSD(t) = A * t^alpha`.

Both have 2 free parameters, so AICc (`chi^2 + 2k + 2k(k+1)/(n-k-1)`, `k=2`) compares them without
either being penalized more for flexibility. Propagated via a 2000-draw Gaussian-perturbation
bootstrap on `y` (seed 20260731), recording `delta_AICc = AICc_powerlaw - AICc_confined` (positive
means confined is preferred, since lower AICc is better) and, for the confined model, `tau`, per
draw. All 2000 draws converged for all three curves (0 dropped for any curve).

**Pass criterion**, locked before running:
- (A) Composite: 95% CI of `delta_AICc` entirely positive AND 95% CI of `tau`'s lower bound below
  the curve's own max digitized `Delta t`.
- (B) Hyaluronan and collagen_1mg: (A)'s two parts do NOT both hold.

**Known risk, stated before running**: Gate 4 already found the composite curve may not extend far
enough in `Delta t` to show visible flattening. If so, `tau` might come out unconstrained (pushed
far past the data range in most bootstrap draws), which the `tau`-CI part of criterion (A) was
designed to catch.

## Result

| curve | n points | max Delta t | delta_AICc (powerlaw − confined) [95% CI] | confined preferred in all 2000 draws | tau [95% CI] | tau CI lower bound < max Delta t | criterion |
|---|---|---|---|---|---|---|---|
| composite | 118 | 10.727 | -109.340 [-149.145, -69.690] | NO | 1.430 [1.199, 1.658] | YES | (A) **FAIL** |
| hyaluronan | 119 | 1.071 | -557.752 [-621.878, -494.394] | NO | 0.136 [0.107, 0.171] | YES | (B) PASS |
| collagen_1mg | 113 | 1.062 | -320.114 [-376.011, -263.517] | NO | 0.300 [0.265, 0.335] | YES | (B) PASS |

**Gate 5 verdict: FAIL** (criterion A fails for composite).

## Reading the result honestly

The "known risk" did not materialize: `tau`'s 95% CI for composite is [1.199, 1.658], comfortably
inside the observed `Delta t` range (max 10.727), not pinned against the upper numerical bound
(`1e4 * max(t)`) the fit was permitted to explore. The confined model got a fair, well-determined
fit to the composite curve's shape, not a degenerate one, and still lost decisively: the power-law
model's AICc is lower by roughly 70 to 149 across the full bootstrap distribution, an order of
magnitude past the conventional "strong support" threshold of `|delta AICc| > 10`. Both pure
component curves show the same pattern, power law preferred, even more decisively (`delta_AICc`
in the hundreds), consistent with the expectation that they should not show a confinement signature.

This is a different, and in one respect more informative, negative result than Gate 4's. Gate 4's
CI included zero, ambiguous, consistent with either "no effect" or "underpowered to detect a real
effect." Gate 5's CI for composite sits entirely and substantially on the "power law wins" side,
positive evidence that a global power law describes this curve's shape better than a model with a
built-in plateau, not merely an absence of evidence for a plateau. Combined, the two gates now agree
in the same direction from two independent statistical angles, a fixed-window local-slope
comparison and a whole-curve nonlinear model comparison, that within the digitized `Delta t` range
of Supplementary Figure S14a (roughly 0.09 to 10.7 s for composite), there is no detectable sign of
the MSD-level flattening that a caged-particle interpretation of the paper's own reported dynamics
would predict.

This does not contradict the paper's own qualitative finding, or Gate 4's own secondary,
non-locked ISF check (composite's intermediate scattering function does plateau well above the pure
networks', a real, statistically supported effect on that separate panel). It specifically means
the caging signature, in the data actually available to this project, is visible in the ISF panel's
incomplete decay but not in the MSD panel's local shape over the digitized range, a distinction
Gate 4 already raised and this gate's result reinforces rather than resolves.

## What this does and does not establish

**Does not overturn or retest Gate 4.** Gate 4's own verdict, method, and result stand unchanged;
this is a separate, additional test, reported alongside it, not a replacement.

**Removes the model-based refit as an open follow-up.** `docs/gate-result-phase3-realdata.md` and
`docs/publication-angle.md` both named this as an untried option that "might detect the plateau
earlier in the accessible range." It has now been tried, pre-registered, and did not find one; the
open-question language in those documents needs to change to reflect that, not stay phrased as if
this were still untested (see updates to `HANDOFF.md`, `docs/publication-angle.md`,
`docs/ip-product-angle.md`, `docs/manuscript-draft.md` made alongside this gate).

**Leaves raw trajectory data as the only remaining concrete path.** With author outreach sent and
unanswered as of 2026-07-31, and the model-based refit now also run and negative, no further
analysis of the existing digitized summary curves is expected to resolve this differently; the
paper's own S14a panel most plausibly does not extend far enough in `Delta t` to show flattening at
all, a property of the published figure's range, not of which statistical test is applied to it.

**Explicitly not tested here**: the Mori-Zwanzig memory kernel remains untested against any real
data, unchanged from Gate 4's own scope note; this gate is a refit of the exponent/caging question
only, using the same two derived summary curves, not new data of a shape MZMD could use.

**Per `docs/BUILD_PLAN.md`'s phase sequencing rule**, Phase 4 (IP and venture material) still does
not open on this result. See memory `ergofluids-ip-gating-discipline` for why this gating is upheld
regardless of how much investigative effort has gone into trying to clear it.
