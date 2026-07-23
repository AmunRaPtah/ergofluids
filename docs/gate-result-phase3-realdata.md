# Gate result: Phase 3, Gate 4 (real-data test, literature digitization)

Date: 2026-07-23. Criteria and parameters locked in `repo/scripts/run_gate4.py` (docstring)
before that script was run at full scale, following the digitization QC checks described below.
Script: `repo/scripts/run_gate4.py`, seed 20260723, 2000-draw bootstrap.

## Data source

No raw trajectory data for arXiv:1909.05091 (Burla et al., "Particle diffusion in extracellular
hydrogels") is publicly available; see `docs/BUILD_PLAN.md`'s "data reality check" and
`HANDOFF.md`. Phase 3 therefore digitizes two of the paper's own published figures instead of
using raw data:

- **Figure 4a** (PDF page 12): intermediate scattering function (ISF) vs tq^2, for 0.6 um tracer
  particles in composite (1 mg/mL collagen + 2 mg/mL hyaluronan, orange), 2 mg/mL hyaluronan
  (blue), and 1 mg/mL collagen (black) networks.
- **Supplementary Figure S14, panel (a)** (PDF page 32): ensemble MSD vs Delta t for the same
  0.6 um particles, in four networks: 1 mg/mL collagen (black), 2 mg/mL collagen (grey), 2 mg/mL
  hyaluronan (blue), composite (orange).

## Digitization method and honest quality assessment

`repo/scripts/digitize_fig4a.py` and `repo/scripts/digitize_s14a.py` (sharing helpers in
`repo/scripts/digitize_common.py`) do the following: render the source PDF page at 400 DPI via
`pdftoppm`, crop to a fixed sub-region around the target panel, locate the panel's frame and tick
marks by thresholding near-black pixels, derive a pixel-to-data affine calibration per axis from
those tick positions, then threshold each curve's distinctive marker color, bin matched pixels by
x-column, and convert each bin's pixel centroid and pixel spread to data units.

**Axis calibration confidence: high.** Both figures use tick marks at regular log-decade (x) and
either linear (Fig 4a y-axis, ISF in [0, 1]) or log-decade (S14a, both axes) spacing. For each
axis, 6 to 8 independent minor-tick pixel positions were checked against the calibration implied
by the major ticks; residuals were consistently under 1 pixel once a small, uniform offset in the
initial (frame-line-based) tick-center estimate was corrected. This is a substantially stronger
calibration check than "two points and hope"; the reported calibration is sub-pixel-consistent
across every tick used.

**Extraction bugs found and fixed during development, not papered over**: an early version of the
extraction mis-attributed pixels from (a) the plot's own axis frame lines near the crop margins,
(b) legend swatch lines (whose color matches a real curve's color, since legends reuse the same
color), and (c) x-axis tick marks near the bottom frame (whose black/grey color matches the
collagen curve) as if they were curve data. All three produced obviously wrong points: implausibly
large `reported_error` (spanning nearly the full plot height), or curve data appearing far beyond
where the actual plotted curve visibly ends. These were caught by inspecting the raw extracted
ranges against the source image, not assumed absent. Fixes: tightened pixel margins around the
plot frame, added legend-box exclusion for every curve's mask, and added a
`max_row_span_px = 200` sanity filter (any column bin whose matched-pixel vertical spread exceeds
that is dropped as likely frame/legend/tick contamination rather than a real marker plus error
bar). After these fixes, a full visual overlay of the digitized points against the source images
(`repo/scripts/_render/digitized_sanity_check.png`, produced during this session, not committed)
matched the published figures closely, including the composite curve's ISF plateau shape and its
late uptick in both panels.

**Point counts**: 97 to 148 points per curve (six curves total, two panels), after column-binning
at 4 pixels per bin. This is fewer than the paper's own underlying point density (its curves look
continuous at print resolution), but is a reasonable-resolution digitization, not a handful of
manually-clicked points.

**Two separate, non-merged error columns per point**, per the task's requirement:
- `reported_error`: half the vertical pixel spread of matched-color pixels in a column bin,
  converted to data units. In both figures the visible plotted error bars are far larger than the
  marker or line width, so this is dominated by the paper's own error bars, not by our pixel noise.
- `digitization_error`: a fixed, small pixel-uncertainty term (marker half-width plus half a bin
  width, ~3 to 5 px depending on axis and scale), independent of how large a given point's actual
  error bar is. This is deliberately much smaller than `reported_error` almost everywhere; it
  represents our own calibration/rendering uncertainty, not the paper's measurement uncertainty.

**Where I trust this least**: the collagen curves in both figures share their color family (black
or grey) with the plot frame, tick marks, and legend text, which is exactly the failure mode
described above; I fixed the specific instances I found by inspection, but do not have an
independent ground truth to confirm no residual contamination remains at a smaller, harder-to-spot
scale. The very short-Delta-t end of the S14a MSD curves (Delta t below about 0.02 s) shows
curvature that is a well-known DDM/particle-tracking noise-floor artifact at short lag times in
this kind of measurement, not necessarily the material's asymptotic exponent; I did not attempt to
correct for this, and it visibly affects the "early window" slope estimates in Gate 4 below
(see Result).

**Qualitative sanity check (done before locking Gate 4, not a pass/fail result on its own)**:
composite's digitized ISF plateaus at ISF approx 0.39 to 0.44 at late tq^2, versus approx 0.05 to
0.09 for hyaluronan and approx 0.12 to 0.18 for collagen, a large, visually obvious difference
matching the paper's own framing of the composite network as leaving a non-decaying caged
fraction. This confirmed the digitization was capturing the intended qualitative signature before
any statistical test was built around it.

## Gate 4 protocol (as pre-registered in `scripts/run_gate4.py`, restated here)

Three curves are used, present in both panels: composite, 2 mg/mL hyaluronan, and 1 mg/mL
collagen. Supplementary Figure S14a's fourth curve (2 mg/mL collagen) is excluded: it is not part
of Figure 4a's main-text three-way contrast, and the paper's own supplementary scatter (S14c/d)
reports an intermediate exponent for it that would confuse a test built around "composite vs the
two pure networks Figure 4a highlights."

**Primary test**, on the S14a MSD curves (the shape `loglog_fit_exponent` and
`ssa_denoise_exponent` from `src/ergofluids/koopman/exponent.py` are built for; `dmd` is excluded,
retired per Gate 0/0b/0c and not rehabilitated here): for each curve, fit a local log-log slope in
an EARLY window (bottom 40% of that curve's own log10(Delta t) range) and a LATE window (top 40%
of the same range), for both surviving estimators. Propagate the digitized error bars
(`reported_error` and `digitization_error`, combined in quadrature for this propagation step only;
the CSVs keep them as separate columns) via a 2000-draw Gaussian-perturbation bootstrap: perturb
each point's y by `N(0, sigma)`, refit, repeat, and take the 95% percentile CI.

Pass criterion:
- **(A) Composite**: the 95% CI of `(slope_early - slope_late)` is entirely positive (excludes
  zero) for BOTH `loglog` and `ssa`. Operationalizes "the local slope measurably flattens toward
  the plateau region."
- **(B) Hyaluronan AND 1 mg/mL collagen**: the 95% CI lower bound of `slope_late` exceeds 0.5, for
  BOTH `loglog` and `ssa`. Operationalizes "stays close to 1" as "does not drop into clearly
  subdiffusive territory," a looser bar than requiring the CI to sit inside `[0.9, 1.1]`, chosen
  because digitized data spanning at most about one decade of Delta t for these two curves is
  noisier than the synthetic curves Gate 0/1 used.

**Fail** if (A) fails for composite under either estimator, or (B) fails for either
pure-component curve under either estimator.

**Secondary, descriptive check** (not part of the pass/fail arithmetic: the exponent estimators
are built for power-law MSD curves, and ISF is a bounded, non-power-law quantity, so it is not run
through them): on the Fig 4a ISF curves, does composite's late-window (top 40% of
log10(tq^2)) mean ISF sit measurably above hyaluronan's and collagen's, within the same
error-propagated bootstrap? This directly probes the paper's own framing of the composite plateau
as a non-decaying caged fraction, distinct from the MSD slope test above.

No parameter or window changes were made after seeing the numbers below.

## Result

Primary test (MSD panel, S14a):

| curve | estimator | slope_early [95% CI] | slope_late [95% CI] | early-late [95% CI] | criterion |
|---|---|---|---|---|---|
| composite | loglog | 0.436 [0.237, 0.600] | 0.513 [-0.138, 1.145] | -0.077 [-0.741, 0.608] | (A) **FAIL** |
| composite | ssa | 0.419 [0.201, 0.598] | 0.502 [-0.260, 1.300] | -0.084 [-0.943, 0.704] | (A) **FAIL** |
| hyaluronan | loglog | 0.320 [0.260, 0.381] | 0.721 [0.646, 0.794] | -0.401 [-0.493, -0.305] | (B) PASS |
| hyaluronan | ssa | 0.312 [0.249, 0.375] | 0.722 [0.646, 0.799] | -0.410 [-0.509, -0.311] | (B) PASS |
| collagen (1 mg/mL) | loglog | 0.661 [0.609, 0.715] | 0.794 [0.729, 0.857] | -0.133 [-0.217, -0.050] | (B) PASS |
| collagen (1 mg/mL) | ssa | 0.664 [0.608, 0.717] | 0.797 [0.729, 0.863] | -0.133 [-0.222, -0.041] | (B) PASS |

Criterion (A) fails for composite under both estimators: the 95% CI of `(slope_early - slope_late)`
includes zero (indeed the point estimate is slightly negative, meaning the late-window slope point
estimate is a bit *higher* than the early-window one, not lower). Criterion (B) passes for both
pure-component curves under both estimators (`slope_late` CI lower bounds of 0.646 and 0.729,
both well above the 0.5 bar).

**Primary-test verdict: FAIL** (criterion A does not hold for composite).

Secondary, descriptive test (ISF panel, Fig 4a):

| curve | late-window mean ISF [95% CI] |
|---|---|
| composite | 0.419 [0.399, 0.440] |
| hyaluronan | 0.093 [0.084, 0.102] |
| collagen (1 mg/mL) | 0.140 [0.131, 0.149] |

composite - hyaluronan: 0.326 [0.304, 0.349] (CI excludes zero, composite higher)
composite - collagen: 0.280 [0.257, 0.302] (CI excludes zero, composite higher)

The descriptive ISF check shows a clear, statistically well-supported version of the paper's
caging signature: composite's ISF plateaus far above either pure component's, consistent with a
persistent non-decaying (caged) fraction of particles, while the pure networks' ISF decays close
to zero.

## Why the primary test failed while the secondary check did not

The composite MSD curve (S14a) does not show a *local, within-window* slope decrease over the
digitized Delta t range (about 0.09 to 10.6 s): its slope stays roughly flat, around 0.42 to 0.51,
across both the early and late windows, rather than starting near 1 and visibly curving downward
within that range. Looking directly at the source figure confirms this: composite (orange) in
S14a rises with a sustained, visibly shallower-than-diffusive slope throughout its visible range,
without an obvious flattening-then-plateau shape the way the ISF panel shows. The caging signature
here shows up as a *sustained low exponent* (global fit approx 0.48, well below both pure
components' global fits of approx 0.55 to 0.75) and, much more clearly, as an *incomplete ISF
decay*, not as detectable within-window curvature in the specific Delta t range this digitized
supplementary panel covers. Reaching the point where MSD itself visibly flattens would likely
require probing longer Delta t (or larger tq^2) than S14a's own axis range extends to; that is a
property of the published figure's own limited range, not something the digitization pipeline can
manufacture.

A secondary contributor: the early-window slope estimates for hyaluronan (0.31 to 0.32) sit well
below 1, arguably more surprising than composite's early-window slope (0.42 to 0.44), which
inverts the naive expectation that pure networks look purely diffusive throughout. This is
consistent with the short-lag-time noise-floor artifact flagged in the digitization write-up
above: DDM/particle-tracking MSD curves commonly show apparent sub-diffusive curvature at the
shortest accessible lag times, from localization and dynamic-error effects unrelated to the
material's true long-time exponent. This digitization did not attempt to correct for that
artifact, and it plausibly inflates the early-window slope comparison's noise for all three
curves, composite included.

## What this does and does not establish

This is the first Gate in this project run against literature-derived data rather than fully
synthetic data, and it is reported as a **fail on its pre-registered primary criterion**, not
reframed as a pass on a different one. The specific, narrow claim tested, "the digitized S14a MSD
curve shows a local log-log slope that measurably decreases from an early to a late window for the
composite network, but not for the two pure networks, within propagated digitization error," is
not supported by this data and this operationalization. The broader qualitative claim the paper
itself makes, that the composite network shows a caged-dynamics signature the pure networks do
not, is supported by the descriptive ISF-plateau check and by the global MSD exponent ordering,
but that is weaker evidence than a pre-registered primary-test pass would have been, and it was
explicitly not part of the locked pass/fail rule.

**Explicitly not tested here**: the Mori-Zwanzig memory kernel (`repo/src/ergofluids/mz`) is not
evaluated against this or any real data in this gate. No public per-trajectory time series exists
for arXiv:1909.05091, only the two derived, digitized summary curves used above, and MZMD requires
that shape of data (per-trajectory series, not an ensemble-averaged summary curve). The MZMD
memory-kernel result remains the synthetic-only finding from Gate 2 and Gate 3
(`docs/gate-result-phase2-mzmd.md`, `docs/gate-result-phase2-gate3-caging.md`); nothing in this
document extends, re-tests, or should be read as validating that result against real data.

**What would change this result**: raw single-particle trajectories (still not publicly available;
author contact remains the only path to those, per `docs/BUILD_PLAN.md`), or a longer-range
published MSD panel reaching further into the escape region, would let the local-slope test probe
the actual flattening region directly instead of only the front part of the subdiffusive stretch.
A model-based test (fitting an explicit caged-diffusion functional form to the MSD curve, rather
than comparing OLS slopes in two fixed windows) might also detect the plateau earlier in the
accessible range than a local-slope comparison does; that was not attempted here, to avoid
retroactively building a criterion around this specific dataset's outcome.
