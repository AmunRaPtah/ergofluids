# Gate result: Gate 9 (second external real-figure validation, different curve and color)

Date: 2026-08-04. Same weaker pre-registration form as Gate 8 (criterion fixed in conversation
immediately before running, not in a separate earlier session). Run via `scripts/digitize_cli.py`
against `scripts/_natcomm_fig1d_TAMSD.spec.json` (gitignored scratch config).

## Why this gate exists

Gate 8 tested the generalized tool on one real curve (grey squares, Zhao et al. Fig. 1b). A single
curve leaves open whether the tool generalizes across colors and figures, or happened to work once.
This gate tests a second, different curve in the same paper: Fig. 1d's bottom panel, the blue
`<TA-MSD>` curve at Phi = 7%, labeled directly on the plot as **0.98**, a very different target value
from Gate 8's 0.85, so a pass here cannot be explained by the estimator simply regressing toward the
same number twice.

## Method and first attempt (failed, diagnosed, fixed)

Axis calibration used the same programmatic tick-height detection as Gate 8, confirmed by checking
that minor-tick pixel spacing matched the expected log-scale pattern to within rounding (observed
minor-tick offsets from the major tick matched predicted log10-spaced offsets at a consistent
513.3 px/decade across 11 independent minor ticks). Marker fill color sampled directly: RGB
(1, 116, 184), a saturated blue distinct from the light blue-grey background band of individual
`TA-MSD` trajectories also drawn in this panel.

**First run**: point estimate 0.653 against a target of 0.98, a miss by 0.33, far outside the
pre-registered +/-0.15 tolerance. Diagnosis: the panel's own blue "proportional to t^0.98"
slope-label text sits inside both the target color range and the curve's pixel region, and got binned
as if it were curve data, corrupting several early bins by up to 3x.

**Fix**: the `FigureSpec` API's single `legend_box` was generalized to `exclude_boxes` (a list), so a
figure can exclude both a legend swatch and a same-colored annotation label in one spec, rather than
needing a workaround. Two tests added (`test_figurespec_json_multiple_exclude_boxes`, and the
existing legend_box test updated to check the backward-compatible single-box path still loads). Full
suite: 22 passing.

## Result (after the fix)

158 points extracted. `ssa` point estimate: **0.918** (95% CI: [0.844, 1.345], n_boot=2000) against
the paper's stated 0.98, a difference of 0.062, well inside the +/-0.15 tolerance. CI includes the
target. **PASS on both criteria.**

Some noise remains: 23 of 158 bins show `reported_error` above 0.08 (max 0.131,
versus Gate 8's contaminated-run max of 0.318 before its own fix), plausibly from this panel's grey
individual-trajectory background band sitting close to the blue curve, not a residual version of the
label-contamination bug (that region is now excluded). Not investigated further since the point
estimate and CI both already clear the pre-registered bar with margin.

## Bearing on the project

Second, independent real-figure pass, on a different curve, color, and target value than Gate 8,
strengthening the digitization methodology's generalization claim for both the PLOS ONE manuscript
and the tool's separate JOSS submission. Also produced a real API improvement (multi-box exclusion)
directly from a real failure, not a hypothetical one, consistent with how Gate 0's HODMD bias
diagnosis drove a real fix earlier in this project. Does not touch or reopen Gate 4, Gate 5, or
Phase 4 sequencing.
