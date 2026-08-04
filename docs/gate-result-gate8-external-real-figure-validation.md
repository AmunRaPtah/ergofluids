# Gate result: Gate 8 (external real-figure validation of the generalized digitization tool)

Date: 2026-08-04. Criteria fixed in conversation immediately before running (see the pre-registration
note in `docs/BUILD_PLAN.md`, "Gate 8" section. This is a weaker form of pre-registration than Gates
0-7, which were written into this repo's docs in a separate, earlier session, and is recorded as
such). Run via `scripts/digitize_cli.py` against `scripts/_natcomm_fig1b_7pct.spec.json` (gitignored
scratch config; the pipeline code it exercises, `src/ergofluids/digitize/{spec,exponent_fit}.py`, is
what's actually tracked).

## Why this gate exists

Gate 7 (`docs/gate-result-gate7-digitization-accuracy.md`) validated the shared extraction machinery
against a synthetic panel with an *analytically known* axis calibration. It deliberately isolates
the extraction math from the tick-reading step, and says so explicitly. It does not test whether the
newly generalized, config-driven tool (built 2026-08-04 out of the two hand-tuned scripts
`digitize_fig4a.py`/`digitize_s14a.py`) actually works end to end on a real, previously unseen PDF,
including the tick-mark calibration step a human (or agent) has to do by inspection. This gate closes
that gap.

## Scope, stated before running (restated here)

Tests the full pipeline: PDF render, tick-mark pixel-position detection, color-mask curve
extraction, and bootstrap exponent estimation. Against one real, external figure never used
anywhere else in this project. A single figure is not a generalization *guarantee*; it is a real,
previously-unseen test case, which is more than the tool had before. No claim is made here about
performance across figure styles broadly.

## Method (restated from BUILD_PLAN.md)

**Target**: Fig. 1b of Zhao et al., "Diffusional aging at water/oil interfaces laden with charged
nanoparticles studied by single-molecule tracking," *Nature Communications* 17:7149 (2026),
doi:10.1038/s41467-026-74008-w. Open-access, fetched directly from the publisher. EA-MSD vs. lag time
tau, log-log axes, three curves (NP surface coverage Phi = 0.15%/1%/7%, blue circle/orange
diamond/grey square). The paper labels the 7% curve's fitted slope directly on the panel as **0.85**
and cross-confirms the same number in panel d ("EA-MSD is proportional to t^0.85" at Phi = 7%),
giving an unambiguous, paper-stated ground truth to test against. Not a value inferred or eyeballed
by us.

**Calibration.** Fig. 1 renders on PDF page 3 at 400 DPI. Axis tick-mark pixel positions were found
programmatically: scan a strip near each frame edge for dark-pixel run lengths per column/row, and
flag local maxima taller than their neighbors as major ticks (this journal's style draws major ticks
visibly taller than minor ones). This located x-axis major ticks at pixel columns 736.5 (t=0.1s) and
1168.5 (t=1s), and y-axis major ticks at pixel rows 1321.5 (EA-MSD=1 mm^2) and 1679.0
(EA-MSD=0.1 mm^2), giving `LogAxis` calibrations for both axes. The 7% curve's marker fill color was
sampled directly from the rendered page (RGB 192,192,192, uniform and distinct from the near-black
frame/text/annotation pixels), matched with a `near_color` mask (tolerance 25). A legend-exclusion
box was set by visual inspection of the rendered panel, the same way `digitize_fig4a.py`'s original
`LEGEND_BOX` was set.

**Pipeline.** All of the above was expressed as a `FigureSpec` JSON and run through
`scripts/digitize_cli.py --estimate --estimator ssa`, i.e. through the same generalized API a future
user would use on any new figure. Not through bespoke code written for this specific panel.

**Pass criterion, fixed before running.** `ssa`'s point estimate within +/-0.15 of 0.85 (the paper's
own labeled value), OR its 95% bootstrap CI includes 0.85.

## Result

125 points extracted from the 7% curve (x range 0.047-1.06s, y range 0.033-0.45 mm^2, consistent by
inspection with the visible data range in the source figure).

| quantity | value |
|---|---|
| `ssa` point estimate | 0.852 |
| 95% CI | [0.079, 0.869] |
| paper's own labeled value | 0.85 |
| absolute difference (point estimate) | 0.002 |
| n_boot | 2000 |

**Verdict: PASS on both criteria.** The point estimate is essentially exact, and the CI (loosely)
contains the target.

## A finding this test surfaced that Gate 7 could not

The CI is wide and visibly asymmetric relative to how tight the point estimate is. Inspecting the
digitized CSV directly: 16 of 125 bins, concentrated at t approximately 0.42-0.76s, show
`reported_error` roughly an order of magnitude above the curve's median (up to 0.216 vs. a median of
0.012). That t-range is exactly where the paper's own black "0.85" slope-reference line and its short
diagonal guide segment cross the grey-square curve on the page. The most likely mechanism: thin
anti-aliased edge pixels of that black annotation, at intermediate grey values, fall inside the
grey-square color tolerance in that region, inflating the apparent within-bin vertical pixel spread
that `reported_error` is built to measure.

This matters because `reported_error`'s designed meaning is "the paper's own plotted uncertainty,"
per `digitize/common.py`'s module docstring. It assumes the figure has visible per-point error bars,
which the two figures Gate 0-7 were built around (Burla et al.) do. This figure does not: Fig. 1b
plots bare markers with a fitted line, no error whiskers. So for this figure, `reported_error` is not
measuring what its name says; it is measuring a mix of marker geometry and, in this specific
instance, contamination from a page annotation. The `y` centroid values themselves are not affected
(the point estimate's near-exact match to the paper's own number confirms this), but the CI built
from `reported_error` should not be read as calibrated the way Gate 7 demonstrated for figures with
real error bars.

**This is not a reason to distrust the point-estimate result.** It is a scoped, now-documented
limitation: the tool's uncertainty quantification is reliable when applied to figures with genuine
plotted error bars (Gate 7's design case, and the original Burla et al. figures), and needs either a
smarter contamination check or an honest "no calibrated uncertainty available" fallback for figures
without them. Worth fixing before any claim stronger than "the point estimate matched" is made about
a bare-marker figure.

## Bearing on the project

Strengthens `docs/publication-angle.md`'s "digitization methodology" contribution with a second,
independent, real-external-data validation beyond Gate 7's synthetic case. The first time the tool
has been tested on a figure neither it nor its authors had seen before. Also directly informs the
tool's separate software (JOSS) angle: demonstrates the generalized, config-driven API works
end-to-end on a real, unseen PDF, while surfacing a concrete, fixable limitation (the
annotation-contamination / no-error-bar case) that a JOSS submission's documentation should state
plainly rather than omit. Does not touch or reopen Gate 4, Gate 5, or Phase 4 sequencing.
