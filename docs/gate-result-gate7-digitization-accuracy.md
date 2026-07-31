# Gate result: Gate 7 (digitization pipeline accuracy against synthetic ground truth)

Date: 2026-07-31. Criteria and parameters locked in `docs/BUILD_PLAN.md` ("Gate 7" section) before
this script was run. Script: `repo/scripts/run_gate7.py`, seed 20260731.

## Why this gate exists

`digitize_fig4a.py` and `digitize_s14a.py` both depend on shared machinery in `digitize_common.py`:
axis calibration (`LogAxis`/`LinearAxis`), color masking, and `extract_curve`'s column-binning and
per-bin centroid/spread estimation. Every gate that used the real digitized data (4, 5, and both
manuscript figures) depends on this machinery. Existing regression tests
(`repo/tests/test_digitization.py`) only check qualitative shape on the real, already-digitized
output (does the composite curve plateau, is its exponent below the pure components); no test has
ever compared digitized output against a case with known ground truth, because no ground truth
exists for the real PDF panels. This gate closes that gap using a synthetic panel built and rendered
the same way the real ones were read, where the true `(x, y, error)` values are known exactly because
they were generated.

## Scope, stated before running (restated here)

This tests the extraction machinery, color masking, column binning, and pixel-to-data conversion via
`extract_curve`, given a *correct* axis calibration. It does not and cannot test whether the two real
scripts' hand-read tick-mark pixel positions were themselves read correctly, since no independent
ground truth exists for that step on the real PDF pages. The synthetic panel's axis calibration is
instead computed analytically, isolating the one part of the pipeline that is independently
testable.

## Method (as pre-registered, restated here)

A synthetic log-log panel was built with matplotlib (`fig.dpi=72`, so `ax.transData` display pixels
equal PDF point-space positions directly). This pixel-scale relationship was verified empirically
before use, in a smoke test separate from the pre-registered run: predicted vs. detected axis-frame
pixel positions agreed to within 2px (the frame's own stroke width) on a throwaway test figure. The
panel was saved to PDF, then rendered through the project's own `digitize_common.render_page`
(`pdftoppm -r 400`), the same call the two real scripts use, so PDF rasterization is inside the
tested path, not bypassed. Axis calibration was computed analytically from the known `xlim`/`ylim`
via the verified pixel-scale relationship, not hand-read from the image. Curve extraction called
`extract_curve` imported unmodified from `digitize_common.py`, with default `bin_width`/
`marker_halfwidth`, exactly as the two real scripts call it.

**Ground truth**: 30 points, `x` log-spaced over 3 decades (1e-2 to 10, matching S14a's range),
`y = A * x^alpha` with `A=2.0`, `alpha=0.65` (arbitrary, distinct from any reported or estimated
exponent elsewhere in this project), plus fixed-seed multiplicative lognormal jitter (`sigma=0.04`)
so the panel is not a perfectly straight line. Each vertex carries a known error-bar half-length of
`0.10 * y_true`. Points are joined by a straight line in log-log space, matching how the real
S14a/Fig4a panels present continuous curves.

**Two pre-registered checks:**

1. Curve-following accuracy across all extracted bins: recovered `y` vs. the log-log-interpolated
   ground-truth value at that bin's `x`. Pass: median relative error < 2%, 95th-percentile < 8%.
2. Error-bar recovery at the 30 known vertices only: recovered `reported_error` vs. the known true
   half-length. Pass: median relative error < 15%, Pearson correlation > 0.8.

## Result

The rendered synthetic panel was visually inspected before trusting the numbers (a jittered orange
curve with visible vertical error-bar whiskers, not a degenerate straight line), confirming the test
was not accidentally trivial.

`extract_curve` recovered 449 points from a 1796px-wide plot interior.

| check | metric | result | threshold | pass |
|---|---|---|---|---|
| 1: curve-following (n=449 bins) | median relative error | 0.35% | < 2% | yes |
| 1: curve-following (n=449 bins) | 95th-percentile relative error | 0.53% | < 8% | yes |
| 2: error-bar recovery (n=30 vertices) | median relative error | 1.15% | < 15% | yes |
| 2: error-bar recovery (n=30 vertices) | Pearson r | 0.991 | > 0.8 | yes |

**Verdict: PASS on both checks, by a wide margin in both cases**, not a marginal pass. Curve-following
median error (0.35%) is roughly 6x tighter than the pre-registered threshold; error-bar recovery
correlation (0.991) is far above the 0.8 bar.

## Reading the result

The shared extraction machinery recovers known values accurately given correct axis calibration. The
margin (curve-following error under 1% at both the median and the 95th percentile) indicates the
column-binning/centroid logic is not a meaningful source of noise or bias in the digitized `y`
values relative to the `digitization_error` term already carried through every downstream gate,
which is dominated by the coarser calibration and marker-halfwidth pixel budgets baked into
`digitize_common.py`'s own error model, not by anything this test could have caught as a surprise.
Error-bar (`reported_error`) recovery is similarly tight and strongly correlated with ground truth,
supporting its use as a proxy for the paper's own plotted error bars.

**What this does and does not establish, stated before running, restated here.** A pass on both
checks, which is what happened, supports (does not prove beyond the stated scope) that the real
Fig4a/S14a digitizations are limited mainly by tick-reading precision, an already-documented, bounded
uncertainty carried as `digitization_error` in every downstream gate, rather than by an undiagnosed
flaw in the extraction code itself. It does not validate the two real scripts' hand-read tick-mark
pixel positions, since no independent ground truth exists for that step on the real PDF pages. It
does not touch or reopen Gate 4, Gate 5, or Phase 4 sequencing; those gates' own pass/fail verdicts
were about whether a caging signature is statistically detectable in the digitized curves, not about
whether the digitization itself is accurate, which is what this gate addresses.

## Bearing on the project

Fills the "contribution 3" gap named in `docs/publication-angle.md` (validating the digitization
methodology against synthetic ground truth, previously only supported qualitatively by
`test_digitization.py`'s shape checks). Strengthens the digitization-methodology write-up with a
quantified accuracy number rather than a qualitative "it looks right" claim. Does not change Phase
sequencing or any real-data gate's verdict.
