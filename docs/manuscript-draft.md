# Diagnosing and testing a Koopman/Mori-Zwanzig subdiffusion estimator: a pre-registered gate sequence from synthetic validation to a literature-digitized real-data test

**Short title:** Pre-registered validation of a Koopman/Mori-Zwanzig subdiffusion estimator

**Author:** Eniola Olutogun

**Affiliation:** Hasso Plattner Institute, University of Potsdam, Potsdam, Germany

Corresponding author: ennyolutogun@gmail.com

**Status:** first full draft, 2026-07-23; updated 2026-07-31 to add the Gate 5 model-based refit, the
Gate 6 DMD-generality test, and the Gate 7 digitization-accuracy test. Target venue: PLOS ONE, chosen
because its published criteria for publication (journals.plos.org/plosone/s/criteria-for-publication)
require technical/methodological soundness rather than novelty or impact, and explicitly state
negative and null results are considered; both fit this paper's mixed-result, pre-registered-gate
structure.
All results below are taken directly from `docs/gate-result-phase1-synthetic.md`,
`docs/gate-result-phase2-mzmd.md`, `docs/gate-result-phase2-gate3-caging.md`,
`docs/gate-result-phase3-realdata.md`, `docs/gate-result-phase3-gate5-cagedfit.md`,
`docs/gate-result-gate6-dmd-generality.md`, and `docs/gate-result-gate7-digitization-accuracy.md`;
nothing here should be edited without also updating (or checking against) those source documents.

## Abstract

We test whether Koopman-operator and Mori-Zwanzig-based methods recover known subdiffusive signatures
in macromolecular transport through extracellular hydrogels, using a pre-registered sequence of
validation gates. Three exponent estimators (log-log fitting, Higher-Order Dynamic Mode Decomposition
[HODMD], and a Hankel-SVD/SSA variant) were calibrated on synthetic data, a Mori-Zwanzig memory-kernel
extension was tested on two synthetic systems with known memory effects, and the pipeline was then
tested against literature-digitized real data. Synthetic calibration revealed a systematic HODMD bias
when reconstructing power-law-in-time curves, traced to its forward-simulation step and fixed with a
denoising-only SSA variant. A further synthetic test found this bias is not shared by two other
DMD-family methods (Bagging, Optimized DMD and Subspace DMD), while a minimal established
bias-correction technique applied to HODMD itself (forward-backward averaging) made the bias
measurably worse, sharpening rather than broadening the original diagnosis. For the real-data test,
we digitized two published figures from a hyaluronan-collagen composite hydrogel study, tracking
reported and digitization error separately, and applied a pre-registered criterion for detecting the
composite network's caging signature. The estimators did not detect a statistically significant local
slope decrease in the digitized MSD curve within propagated uncertainty, the primary, locked
criterion, though a secondary check on the intermediate scattering function showed the expected
qualitative plateau. A follow-up test fit an explicit confined-diffusion model against a global power
law by AICc; the power law was decisively preferred for the composite network even though the
confined model's characteristic time was well-constrained within the observed range, a sharper
negative result. We report this as a mixed result, discuss why the digitized figure's time range
likely falls short of the plateau region, and describe a digitization methodology independently
validated against synthetic ground truth with both pre-registered accuracy checks passing well inside
threshold, making it reusable for extracting quantitative data from published figures.

## 1. Introduction

Hyaluronan-collagen hydrogels are a widely used biomimetic model for the extracellular matrix [1]
that macromolecular drugs must cross in dense tissue, including tumor stroma [2]. Particle transport
through these gels is often subdiffusive [3], and the specific exponent and its dependence on
network composition carries information about pore size, crosslinking, and caging behavior.
Koopman-operator methods, including Dynamic Mode Decomposition (DMD) and its variants, are
increasingly used to extract dynamical structure, including scaling exponents, from time-series data
[4,5], and Mori-Zwanzig formalisms [6,7] offer a principled way to add memory effects that plain
Markovian DMD misses. Applying these tools to macromolecular transport in tissue-like gels is, to our
knowledge, untested. We
report a pre-registered gate sequence built to test that application honestly: synthetic validation
first, then a test against the closest available real (if indirect, literature-digitized) data, with
the pass/fail criteria fixed before the data was digitized.

## 2. Methods

### 2.1 Exponent estimators

We tested three estimators for the subdiffusive scaling exponent alpha, defined via mean-squared
displacement (MSD) proportional to Delta t^alpha. `loglog` performs ordinary least-squares
regression of log(MSD) on log(Delta t). `dmd` applies Higher-Order Dynamic Mode Decomposition
(HODMD [8]), via the PyDMD implementation [9,10], to a delay-embedded trajectory and recovers alpha from the fitted eigenvalue spectrum
via forward reconstruction. `ssa` uses the same delay-embedding matrix as `dmd` but replaces
HODMD's eigenvalue-based forward simulation with Hankel-SVD low-rank projection and anti-diagonal
averaging (Singular Spectrum Analysis-style denoising), with the exponent then read off the
denoised curve by log-log fit. All three were implemented in `src/ergofluids/koopman/exponent.py`.

### 2.2 Mori-Zwanzig memory kernel

We ported the Mori-Zwanzig Mode Decomposition (MZMD) algorithm described by Woodward et al. [11]
from its reference Julia implementation to Python (`src/ergofluids/mz/mzmd.py`). The kernel order
n_ks controls the number of memory terms retained; n_ks = 1 reduces the method to a memoryless
(Markovian) fit.

### 2.3 Synthetic validation protocol

Gates 0 and 1 used 2D fractional Brownian motion [12] trajectories (150 particles, 80 time steps,
150 percentile-bootstrap resamples per estimate [13]). Gate 0 tested bootstrap interval calibration
(target: 18/20 coverage at nominal 90%, at alpha_true in {0.5, 0.7, 1.0}). Gate 1 tested whether the
estimators separate two literature-anchored exponent regimes (single-component, alpha ~ 1.0;
hyaluronan-collagen composite, alpha ~ 0.5), with a pre-registered pass criterion of non-overlapping
95% CIs and a composite-regime point estimate within +/-0.15 of 0.5.

Gates 2 and 3 tested the MZMD kernel on synthetic systems with a theory-guaranteed or
mechanistically-motivated memory effect: a linear 2D hidden-variable system (Gate 2, 60
trajectories, n_ks = 1 vs. 6) and a caged-particle system, a fast Ornstein-Uhlenbeck fluctuation
around a slowly diffusing hidden trap center, verified independently to reproduce a
plateau-then-escape MSD crossover (Gate 3, 60 trajectories, n_ks = 1 vs. 15). Both used paired
bootstrap (2000 resamples) on the per-trajectory forecast RMSE difference between memoryless and
memory-augmented fits.

### 2.4 Real-data acquisition and digitization

No public per-trajectory or raw ensemble dataset exists for the target system. We therefore
digitized two published figures from Burla et al. [14]: Figure 4a (intermediate
scattering function, ISF, vs. tq^2, for 0.6 micron tracers in composite, hyaluronan-only, and
collagen-only networks) and Supplementary Figure S14a (ensemble MSD vs. Delta t for the same
systems). Figures were rendered from the source PDF at 400 DPI, cropped to the panel region, and
calibrated to data coordinates using an affine transform derived from tick-mark pixel positions
(residuals <1 pixel across 6-8 independent tick checks per axis after correcting a small
frame-line offset). Curve data were extracted by color-thresholding each curve's marker color and
column-binning (4 px bins), yielding 97-148 points per curve. Two independent error columns were
tracked per point: `reported_error` (half the vertical pixel spread within a column bin, reflecting
the paper's own plotted error bars) and `digitization_error` (a fixed pixel-uncertainty term
reflecting calibration/rendering uncertainty only). Three extraction artifacts, frame-line,
legend-swatch, and tick-mark pixel contamination, all sharing color with genuine curve pixels, were
identified by comparing extracted ranges against the source images and corrected with tightened
crop margins, legend-box exclusion, and a maximum-row-span sanity filter.

### 2.5 Real-data test protocol (pre-registered)

For each of three curves present in both panels (composite, hyaluronan, collagen), we fit a local
log-log slope in an early window (bottom 40% of that curve's log(Delta t) range) and a late window
(top 40%), for both `loglog` and `ssa` (`dmd` excluded, per its Gate 0 failure). Digitized errors
were propagated via a 2000-draw Gaussian-perturbation bootstrap. Pass criteria, fixed before the
result was computed:

- **(A)** for the composite curve, the 95% CI of (slope_early - slope_late) excludes zero for both
  estimators;
- **(B)** for both pure-component curves, the 95% CI lower bound of slope_late exceeds 0.5 for both
  estimators.

A secondary, non-pass/fail descriptive check compared late-window mean ISF between composite and
each pure component on the Figure 4a panel.

### 2.6 Model-based caged-diffusion refit protocol (Gate 5, pre-registered)

Gate 4's primary test compares two fixed windows of a single curve; it does not ask whether the
curve's overall shape is better described by a model with a built-in plateau. As a follow-up,
pre-registered separately (`docs/BUILD_PLAN.md`, "Gate 5") after Gate 4's result and before this
script was run, we fit two two-parameter models to each curve's full digitized range by weighted
nonlinear least squares (weights = 1/sigma_i^2, sigma_i the same combined reported/digitization
error used in Gate 4): a global power law, `MSD(t) = A t^alpha`, and the standard confined-diffusion
form from the single-particle-tracking literature [15], restated in later methods papers, e.g. [16],
`MSD(t) = P[1 - exp(-t/tau)]`. The two were compared by
small-sample-corrected AIC (AICc) [17], propagated through the
same style of 2000-draw Gaussian-perturbation bootstrap Gate 4 used (fresh seed, not reused from
Gate 4). The pre-registered pass criterion required, for the composite curve, that the confined
model be preferred (95% CI of `delta_AICc = AICc_powerlaw - AICc_confined` entirely positive) with
`tau` constrained inside the observed Delta t range (95% CI lower bound below the curve's maximum
digitized Delta t, ruling out a pass driven by an unconstrained, effectively-extrapolated plateau);
and, for both pure-component curves, that this same combination not hold.

### 2.7 DMD-generality test protocol (Gate 6, pre-registered)

Gate 0/0b diagnosed HODMD's bias but tested only one fix (`ssa`, which abandons eigenvalue-based
dynamic reconstruction entirely). As a separate, later-pre-registered follow-up
(`docs/BUILD_PLAN.md`, "Gate 6"), independent of the real-data gates, we asked whether the bias is
specific to HODMD or shared by other established DMD-family methods, using three PyDMD-implemented
candidates chosen for mechanistic diversity: `HODMD(forward_backward=True)` (forward-backward
operator averaging [18], applied to the identical HODMD configuration
Gate 0 tested), `BOPDMD` (Bagging, Optimized DMD [19,20]), and `SubspaceDMD` [21]. `BOPDMD` and
`SubspaceDMD` do not natively delay-embed a scalar signal, so both were fit on the identical
Hankel-matrix construction `ssa` uses and reassembled to a 1D curve the same way, isolating "which
reconstruction algorithm is applied to the same delay-embedded matrix" as the only variable against
`ssa`. Protocol otherwise identical to Gate 0: fBm trajectories, `alpha_true` in {0.5, 0.7, 1.0}, 20
repeats per condition, 150-resample bootstrap CI, 18/20 coverage bar. Each estimator falls back to
`loglog_fit_exponent` on any fit exception or non-finite reconstruction, with fallback counts
tracked and reported per condition rather than absorbed silently.

### 2.8 Digitization pipeline validation protocol (Gate 7, pre-registered)

Section 2.4's digitization procedure has no independent ground truth to validate against on the real
PDF panels. As a separate, later-pre-registered test (`docs/BUILD_PLAN.md`, "Gate 7"), we built a
synthetic log-log panel with known `(x, y, error)` values, 30 points, `y = 2.0 * Delta t^0.65` plus
fixed-seed multiplicative lognormal jitter (sigma = 0.04, an exponent and coefficient chosen
arbitrarily and unrelated to any value reported elsewhere in this study), each with a known
error-bar half-length of 10% of `y`, joined by a straight line in log-log space to match the
continuous-curve style of the real panels. The panel was rendered through the same PDF-to-PNG path
used for the real figures (`pdftoppm` at 400 DPI), and its axis calibration was computed
analytically from the known plot limits and the verified pixel-scale relationship between the
figure's point-space and the render resolution, rather than hand-read from the image, so this test
isolates the extraction machinery (color masking, column binning, pixel-to-data conversion) given a
*correct* calibration; it does not test whether the real panels' hand-read tick-mark pixel positions
were themselves correct, since no independent ground truth exists for that step on the real pages.
The identical, unmodified curve-extraction function used by both real digitization scripts was then
run on the synthetic panel. Two checks were pre-registered: (1) across every extracted bin along the
curve, recovered `y` compared against the known log-log-interpolated ground-truth value at that
bin's `x` (pass: median relative error < 2%, 95th-percentile < 8%); (2) at the 30 known vertices,
where error-bar whiskers are drawn, recovered `reported_error` compared against the known true
half-length (pass: median relative error < 15%, Pearson correlation with ground truth > 0.8).

## 3. Results

### 3.1 Estimator calibration and the HODMD bias (Gate 0/0b/0c)

At n = 20 repeats per condition, no estimator cleared the pre-registered 18/20 coverage bar at all
three tested exponents in the initial run (Table 1a): `loglog` reached 18/16/19 and `dmd` reached
15/17/12 (alpha = 0.5/0.7/1.0). Root-cause analysis attributed `dmd`'s shortfall to a systematic bias
(-0.026 to -0.054, worst at alpha_true = 1.0) arising because HODMD forward-simulates from its
fitted eigenvalue decomposition, and a power-law-in-time signal is not a finite sum of exponentials
in real time; reconstruction error grew 5-10x from the start to the end of the fitting window.
Replacing dynamic reconstruction with Hankel-SVD denoising only (`ssa`, no forward simulation, same
delay embedding) reduced this bias. `loglog` and `dmd` were re-run alongside the new `ssa` estimator
in a single combined run (Table 1b); `loglog` and `dmd`'s per-condition counts shift slightly between
Tables 1a and 1b because a new estimator changes the bootstrap random-number draw order, ordinary
Monte Carlo variation between two independent 20-repeat runs at a true rate near 90%, not a change in
either estimator. `ssa` reached 17/19/18 in this re-run, still missing the bar by one at alpha = 0.5.
A pre-registered 100-repeat follow-up at that condition (Table 1c) found true coverage of 89.0% (95%
CI [81.2%, 94.4%]) for `loglog` and 90.0% (95% CI [82.4%, 95.1%]) for `ssa`, confirming the earlier
17/20 was sampling noise rather than genuine miscalibration. Gate 0 passes for `ssa`; `dmd`/HODMD is
retired from the pipeline.

**Table 1a. Gate 0, initial run (n = 20 repeats per condition, seed 20260722; `ssa` did not exist
yet).**

| alpha_true | loglog | dmd (HODMD) | required |
|---|---|---|---|
| 0.5 | 18/20 | 15/20 | 18/20 |
| 0.7 | 16/20 | 17/20 | 18/20 |
| 1.0 | 19/20 | 12/20 | 18/20 |

**Table 1b. Gate 0b, re-run after the SSA fix (n = 20 repeats per condition, all three estimators
fit together in one run; see note above on why `loglog`/`dmd` counts differ slightly from Table
1a).**

| alpha_true | loglog | dmd (HODMD) | ssa | required |
|---|---|---|---|---|
| 0.5 | 18/20 | 17/20 | 17/20 | 18/20 |
| 0.7 | 19/20 | 18/20 | 19/20 | 18/20 |
| 1.0 | 19/20 | 13/20 | 18/20 | 18/20 |

**Table 1c. Gate 0c, power follow-up at alpha_true = 0.5 only (n = 100 repeats).**

| estimator | coverage | 95% CI on true rate | 90% target |
|---|---|---|---|
| loglog | 89/100 (89.0%) | [81.2%, 94.4%] | inside |
| ssa | 90/100 (90.0%) | [82.4%, 95.1%] | inside |

### 3.2 Regime separation (Gate 1)

All three estimators cleanly separated the single-component (alpha_true = 1.0) and composite
(alpha_true = 0.5) regimes, with non-overlapping 95% CIs and composite-regime point estimates
(loglog: 0.522; dmd: 0.482; ssa: 0.521) within 0.03 of the literature-anchored target. Gate 1 passes
for all three estimators.

### 3.3 Memory-kernel validation (Gate 2/3)

On the linear hidden-variable system, the memory-augmented fit (n_ks = 6) reduced forecast RMSE from
0.344 to 0.315 (paired difference 0.0294, 95% CI [0.0132, 0.0458]). On the caged-particle system,
n_ks = 15 reduced RMSE from 0.399 to 0.364 (paired difference 0.0350, 95% CI [0.0112, 0.0587]). Both
gates pass: the ported MZMD kernel captures memory effects a memoryless fit misses, on a generic
linear system and on a system built to mechanistically resemble the target material's reported
caging behavior. Neither test used the paper's real data or was fit to its reported figures.

### 3.4 Real-data test (Gate 4)

The primary criterion failed for the composite network under both estimators (Table 2): the 95% CI
of the early-late slope difference included zero for both `loglog` (-0.077, [-0.741, 0.608]) and
`ssa` (-0.084, [-0.943, 0.704]); the point estimate was, if anything, slightly negative (late-window
slope marginally higher than early-window). Both pure-component curves passed criterion (B) under
both estimators (slope_late 95% CI lower bounds of 0.646 and 0.729, both above the 0.5 threshold).

**Table 2. Gate 4 primary test (S14a MSD curves).**

| curve | estimator | slope_early [95% CI] | slope_late [95% CI] | early - late [95% CI] | criterion |
|---|---|---|---|---|---|
| composite | loglog | 0.436 [0.237, 0.600] | 0.513 [-0.138, 1.145] | -0.077 [-0.741, 0.608] | (A) FAIL |
| composite | ssa | 0.419 [0.201, 0.598] | 0.502 [-0.260, 1.300] | -0.084 [-0.943, 0.704] | (A) FAIL |
| hyaluronan | loglog | 0.320 [0.260, 0.381] | 0.721 [0.646, 0.794] | -0.401 [-0.493, -0.305] | (B) PASS |
| hyaluronan | ssa | 0.312 [0.249, 0.375] | 0.722 [0.646, 0.799] | -0.410 [-0.509, -0.311] | (B) PASS |
| collagen (1 mg/mL) | loglog | 0.661 [0.609, 0.715] | 0.794 [0.729, 0.857] | -0.133 [-0.217, -0.050] | (B) PASS |
| collagen (1 mg/mL) | ssa | 0.664 [0.608, 0.717] | 0.797 [0.729, 0.863] | -0.133 [-0.222, -0.041] | (B) PASS |

The secondary descriptive check on the ISF panel showed a clear separation: composite's late-window
mean ISF (0.419, [0.399, 0.440]) sat well above hyaluronan's (0.093, [0.084, 0.102]) and collagen's
(0.140, [0.131, 0.149]), with both pairwise differences excluding zero. This matches the paper's own
qualitative framing of the composite network retaining a non-decaying caged fraction.

### 3.5 Model-based caged-diffusion refit (Gate 5)

The confined-diffusion model was not preferred for any curve; the power-law model won decisively in
all three cases (Table 3). For composite, `tau`'s 95% CI ([1.199, 1.658]) sat comfortably inside the
observed range (maximum digitized Delta t = 10.727), so this was a well-determined fit, not one
where the confined model was starved of the curvature it needed, and it still lost to the power law
by 70-149 AICc points, an order of magnitude past the conventional `|delta AICc| > 10` "strong
support" threshold. Both pure-component curves showed the same pattern more strongly still
(hundreds of AICc points). Gate 5 fails on its pre-registered criterion.

**Table 3. Gate 5 model comparison (S14a MSD curves, 2000/2000 bootstrap draws converged for every
curve).**

| curve | max Delta t | delta_AICc (powerlaw - confined) [95% CI] | tau [95% CI] | criterion |
|---|---|---|---|---|
| composite | 10.727 | -109.340 [-149.145, -69.690] | 1.430 [1.199, 1.658] | (A) FAIL |
| hyaluronan | 1.071 | -557.752 [-621.878, -494.394] | 0.136 [0.107, 0.171] | (B) PASS |
| collagen (1 mg/mL) | 1.062 | -320.114 [-376.011, -263.517] | 0.300 [0.265, 0.335] | (B) PASS |

![Digitized composite-network MSD curve (blue points, error bars combine reported and digitization
error in quadrature) with the two pre-registered Gate 5 fits overlaid: a power law (orange, solid)
and a confined-diffusion model (green, dashed). The power law tracks the data across the full
range; the confined-diffusion fit systematically deviates, overshooting at short Delta t,
undershooting mid-range, and flattening before the data does, the same result Table 3 reports as
a decisive AICc preference for the power law.](figures/fig1_composite_msd_fits.png)

**Fig 1. Composite-network MSD: digitized data against two pre-registered model fits (Gate 5).**
Digitized composite MSD (blue points; error bars combine reported and digitization error in
quadrature) against a power law fit (orange, solid) and a confined-diffusion fit (green, dashed).
The power law tracks the data across the full range; the confined-diffusion fit deviates
systematically, overshooting at short Delta t, undershooting mid-range, and flattening before the
data does. Point estimates: power law alpha = 0.49; confinement time tau = 1.42 s. See Table 3 for
the AICc comparison and bootstrap confidence intervals.

### 3.6 DMD-generality test (Gate 6)

`hodmd_fb` failed at all three conditions (Table 4); `bopdmd` and `subspace` both passed cleanly at
all three. Zero `loglog`-fallback triggers occurred across 27,180 total estimator calls for any
candidate. `hodmd_fb`'s mean bias (-0.064 to -0.101) is larger in magnitude than plain HODMD's
diagnosed bias (-0.026 to -0.054, Section 3.1), and its coverage at alpha_true = 0.7 (12/20) is
worse than plain HODMD scored at the same condition in either of its two Gate 0 runs (17/20 and
18/20): forward-backward operator averaging did not fix HODMD's bias, and measurably worsened it.
`bopdmd` and `subspace` both avoided the bias, with mean bias close to zero (`bopdmd`) or small and
growing but still inside calibrated coverage (`subspace`).

**Table 4. Gate 6 coverage and mean point-estimate bias (n = 20 repeats per condition; required
18/20).**

| alpha_true | hodmd_fb coverage | hodmd_fb bias | bopdmd coverage | bopdmd bias | subspace coverage | subspace bias |
|---|---|---|---|---|---|---|
| 0.5 | 15/20 | -0.0644 | 18/20 | -0.0154 | 20/20 | +0.0055 |
| 0.7 | 12/20 | -0.0994 | 20/20 | -0.0067 | 20/20 | +0.0367 |
| 1.0 | 15/20 | -0.1013 | 20/20 | -0.0019 | 19/20 | +0.0818 |

![Bootstrap-CI coverage out of 20 repeats, across all six exponent estimators tested in this
project, at each true exponent value, against the 18/20 pass bar (dashed). loglog, dmd (HODMD),
and ssa are Gate 0b; hodmd_fb, bopdmd, and subspace are Gate 6. hodmd_fb sits below the bar at
every condition, most severely at alpha_true = 0.7; bopdmd and subspace clear it at every
condition.](figures/fig2_coverage_comparison.png)

**Fig 2. Bootstrap-CI coverage across six subdiffusion-exponent estimators.** Coverage out of 20
repeats per estimator at three true exponent values, against the 18/20 pass bar (dashed). loglog,
dmd (HODMD), and ssa are from Gate 0b; hodmd_fb, bopdmd, and subspace are from Gate 6. hodmd_fb
falls below the bar at every condition, most severely at alpha_true = 0.7; bopdmd and subspace
clear it at every condition.

### 3.7 Digitization pipeline accuracy (Gate 7)

Both pre-registered checks passed, well inside threshold (Table 5). The extraction machinery
recovered 449 points from a 1796-pixel-wide plot interior; curve-following median relative error
(0.35%) was roughly six times tighter than the 2% bar, and error-bar recovery correlated with ground
truth at r = 0.991 against a 0.8 bar.

**Table 5. Gate 7 accuracy checks against synthetic ground truth.**

| check | metric | result | threshold | pass |
|---|---|---|---|---|
| 1: curve-following (n = 449 bins) | median relative error | 0.35% | < 2% | yes |
| 1: curve-following (n = 449 bins) | 95th-percentile relative error | 0.53% | < 8% | yes |
| 2: error-bar recovery (n = 30 vertices) | median relative error | 1.15% | < 15% | yes |
| 2: error-bar recovery (n = 30 vertices) | Pearson r | 0.991 | > 0.8 | yes |

### 3.8 External real-figure validation (Gate 8)

Gate 7 validates the extraction machinery against a synthetic panel with an analytically known
calibration; it does not test the tick-mark calibration step itself, since no independent ground
truth exists for that step on a real page. As a separate check, the digitization pipeline was
generalized into a config-driven tool and tested on a real, external figure never otherwise used in
this study: Fig. 1b of Zhao et al. [22], which labels its own 7%-coverage EA-MSD curve's fitted
slope as 0.85. The pipeline, including programmatic tick-mark detection, recovered an exponent of
0.852 (Table 6), a difference of 0.002 from the paper's own stated value.

This test also surfaced a limitation the synthetic case could not: unlike the panels used elsewhere
in this study, this figure has no plotted per-point error bars, and a slope-reference annotation
line crossing the curve inflated `reported_error` in the region it crosses, producing a wide,
asymmetric confidence interval despite the accurate point estimate. The `y` values themselves were
unaffected. We report this as a scoped limitation of the uncertainty quantification for bare-marker
figures, not of the extraction itself.

**Table 6. Gate 8: real-figure exponent recovery.**

| quantity | value |
|---|---|
| recovered exponent (ssa) | 0.852 |
| 95% CI | [0.079, 0.869] |
| paper's own stated value | 0.85 |
| absolute difference | 0.002 |

A second, independent real-figure test followed, on a different curve, color, and target value in
the same paper: Fig. 1d's blue `<TA-MSD>` curve at the same 7% coverage, labeled 0.98. A first attempt
recovered 0.653, a large miss, traced to the panel's own same-colored slope-reference label text
being binned as curve data; generalizing the tool's single legend-exclusion box into a list of
exclusion boxes resolved it. The corrected run recovered 0.918 (95% CI [0.844, 1.345]), a difference
of 0.062 from the paper's stated value. That the two targets (0.85 and 0.98) are far apart rules out
the pass being an artifact of the estimator drifting toward one particular number.

## 4. Discussion

The two halves of this study point in different directions on the same question, and we report both
rather than foreground the one that reads more favorably. The synthetic gate sequence (Gates 0-3)
supports the estimator pipeline on its own terms: once HODMD's forward-simulation step is replaced
with denoising-only reconstruction, the resulting `ssa` estimator is calibrated at the nominal 90%
level, separates literature-anchored exponent regimes cleanly, and, via the Mori-Zwanzig extension,
captures memory effects that a memoryless fit misses, on both a generic linear system and one built
to mechanistically resemble the target material's caging behavior. None of this, however, was tested
against anything real; it is a statement about the pipeline's internal consistency, not about
macromolecular transport.

The real-data test (Gate 4) is the point where that gap was addressed, and it did not confirm the
target signature on its pre-registered primary criterion. The composite network's digitized MSD
curve shows no statistically significant local slope decrease between an early and late Delta t
window; if anything the point estimate runs slightly the wrong way. Read alongside the secondary ISF
check, which does show a large, well-supported difference between composite and the pure networks,
the most likely explanation is not that the caging signature is absent from this data, but that
Supplementary Figure S14a's own Delta t range does not extend far enough to capture the MSD-level
flattening directly. The composite curve's global exponent (approximately 0.48) does sit below both
pure components' (approximately 0.55-0.75), and the ISF panel shows the expected non-decaying caged
fraction; the specific operationalization tested here, a local within-window slope decrease, is
simply a narrower and stricter claim than either of those, and it is the one that was pre-registered
as primary. We see this as a property of the accessible digitized range and the chosen test
statistic, not evidence against the underlying phenomenon.

A second contributor is a known measurement artifact rather than a modeling failure: DDM/particle-
tracking MSD curves commonly show apparent sub-diffusive curvature at the shortest accessible lag
times from localization and dynamic-error effects unrelated to the material's true long-time
exponent. The hyaluronan curve's early-window slope (approximately 0.31-0.32) is, on its face, more
surprising than composite's (approximately 0.42-0.44) under a naive "pure networks look diffusive"
expectation; a short-lag noise floor is the more parsimonious explanation, and it plausibly inflates
the early-window slope comparison's noise for all three curves. We did not attempt to correct for it,
to avoid introducing a post-hoc adjustment tuned to this dataset's outcome.

Gate 5's model-based refit, run as a direct follow-up to Gate 4's ambiguous result, sharpens rather
than overturns it. Where Gate 4's confidence interval simply included zero, consistent with either
"no effect" or "underpowered to detect one," Gate 5 found positive evidence in the other direction:
a well-constrained confined-diffusion fit (tau's interval sat inside the data range, not pushed
past it) still lost decisively to a plain power law. Two different statistical approaches, a local
two-window slope comparison and a whole-curve nonlinear model comparison, now agree that no
MSD-level flattening is detectable within Supplementary Figure S14a's digitized Delta t range. Read
together with the ISF-panel check, which does show the expected effect on an independent panel of
the same figure, the most parsimonious explanation remains the one Gate 4 already suggested: the
panel's own Delta t range most likely ends before the composite network's MSD curve visibly
flattens, a property of the published figure, not of which test is applied to the digitized points
within it.

The HODMD bias diagnosis (Gate 0/0b) stands independently of the real-data result and is, we think,
the most broadly useful finding here: HODMD's eigenvalue-based forward reconstruction introduces a
systematic, growing bias when applied to power-law-in-time signals, because such signals are not a
finite sum of exponentials in real time. This is a specific, mechanistic, falsifiable failure mode
for a widely used DMD variant, and the fix (denoising-only reconstruction via the same delay
embedding) is simple enough to adopt directly.

Gate 6 sharpens this finding rather than merely broadening it. A minimal, established
bias-correction technique, forward-backward operator averaging, applied to the exact same HODMD
configuration, did not fix the bias and made it measurably worse: coverage at alpha_true = 0.7 fell
to 12/20 from HODMD's own 17-18/20 in its two prior runs, and mean bias grew in magnitude beyond
HODMD's own. Two mechanistically different established methods, BOPDMD (variable-projection
optimized fitting with bootstrap aggregation) and SubspaceDMD (subspace-identification-based
estimation), both avoided the bias cleanly. The pattern is informative precisely because it does not
split along a simple "eigenvalue methods fail, others succeed" line: `hodmd_fb` is still
eigenvalue-based and failed; `bopdmd` is also eigenvalue-based, via a different fitting route, and
passed. The more specific reading is that forward-backward averaging targets a different problem,
correcting eigenvalue bias from sensor or measurement noise in the original DMD estimation procedure
(the problem it was developed for), not the structural mismatch diagnosed here, forward-simulating a
fitted eigenvalue decomposition on a signal that is not a finite sum of real-time exponentials. The
two methods that did avoid the bias both estimate their eigenvalue decomposition through a route
that does not reuse HODMD's own two-stage delay-embed-then-forward-simulate procedure: BOPDMD by
directly optimizing against the whole reconstruction window (variable projection) rather than a
linear regression followed by forward propagation, and SubspaceDMD through subspace identification,
a different theoretical foundation entirely. `ssa`'s original fix (denoising only, no dynamic
reconstruction at all) is therefore not the only way to avoid HODMD's bias, but the two other things
that do avoid it also do not rely on HODMD's own specific estimation route, consistent with, not
incidental to, the original diagnosis.

The digitization methodology, tick-calibrated pixel
extraction with two independently tracked error sources, and three documented, caught-and-fixed
contamination bugs, is offered as a reusable procedure for anyone needing to extract quantitative
data from published figures where raw data is unavailable, independent of what this particular
application concluded. Gate 7 (Section 3.7) gives this claim a quantified basis rather than a
qualitative one: given correct axis calibration, the shared extraction machinery recovers known
ground truth to well under 1% median error, both along a continuous curve and at discrete error-bar
locations. This does not validate the real panels' hand-read tick-mark calibration itself, which has
no independent ground truth to check against, but it does narrow where residual uncertainty in the
real digitized curves can plausibly come from: calibration and rendering precision (already carried
through every downstream gate as `digitization_error`), not an undiagnosed flaw in the extraction
code.

Since generalized into a config-driven tool, the pipeline was also tested end to end on a real,
external figure it had never seen (Gate 8, Section 3.8), recovering the paper's own stated exponent
to within 0.002 while surfacing a genuine, now-documented limitation in uncertainty quantification
for figures without plotted error bars. We regard this as a second, independent line of support for
the digitization methodology as a reusable contribution, alongside the honest record of where it
currently falls short.

## 5. Limitations

No raw single-particle trajectory data for the target system is publicly available. The
Mori-Zwanzig memory kernel was validated only on synthetic data (Gates 2-3); digitized ensemble summary curves
cannot supply the per-trajectory time series the method requires, so this is a structural gap that
more digitization effort cannot close. The collagen-family curves in both digitized figures share
color with the plot frame, tick marks, and legend text, the same failure mode that produced three
caught contamination bugs elsewhere; we cannot rule out smaller, harder-to-spot residual
contamination of the same kind. The short-lag-time noise floor discussed above was not corrected
for. This study tests a single literature target; the estimator pipeline's behavior on other
subdiffusive systems remains untested. We did test a second operationalization of "caging" on this
same target, an explicit caged-diffusion functional-form fit rather than two-window slope comparison
(Gate 5, Section 3.5), pre-registered separately to avoid retroactively building a criterion around
this dataset's specific outcome; it also did not detect the target signature, more decisively than
the first test. With that avenue closed on the existing digitized data, raw trajectory data from the
original authors is the only remaining concrete path to a sharper real-data test. Separately, Gate 6
tested only three DMD-family methods, chosen for mechanistic diversity, not an exhaustive survey of
PyDMD's implemented variants; other variants (for example plain `OptDMD`, `FbDMD` without HODMD's
delay embedding, or `PiDMD` under various structural constraints) remain untested and are not
claimed to behave either way. Gate 7's synthetic validation of the digitization pipeline (Section
3.7) is scoped to the extraction machinery given correct axis calibration; it does not and cannot
independently confirm that the two real panels' hand-read tick-mark pixel positions were themselves
correct, since no ground truth exists for that step on the real PDF pages.

## 6. Conclusion

We report a pre-registered, mixed-outcome test of Koopman/Mori-Zwanzig-based subdiffusion estimators
against literature-digitized real data, followed by two further pre-registered tests: a second
real-data test using a genuinely different statistic, and a synthetic-only generality test of the
original HODMD bias diagnosis. The estimator pipeline and memory-kernel extension are internally
validated on synthetic data, including a diagnosed and fixed bias in a commonly used DMD variant;
neither real-data test confirmed the target caging signature on its primary, locked criterion (a
local two-window slope comparison, and a whole-curve confined-diffusion model fit compared by AICc),
though a secondary descriptive check on an independent panel of the same figure did show the
expected qualitative signature. We report this as an honest mixed result rather than reframe it as a
validation. With the model-based refit now also run and negative, raw trajectory data from the
original authors is the one remaining concrete path to a sharper real-data test. Separately, the
HODMD bias diagnosis itself was strengthened: a minimal, established bias-correction technique
applied to HODMD's own procedure did not fix the bias and made it worse, while two mechanistically
different established methods avoided it cleanly, a more specific and more generalizable finding
than the original diagnosis alone supported. The digitization methodology was validated against
synthetic ground truth for the first time in this work, and passed both pre-registered accuracy
checks well inside threshold, giving the reusable-procedure claim a quantified basis alongside the
documented extraction-bug history.

## Competing interests

The author declares no competing interests.

## Data availability

All data, code, and analysis scripts underlying this study are publicly available in the GitHub
repository AmunRaPtah/ergofluids (https://github.com/AmunRaPtah/ergofluids), pinned to commit
a2b8246 for this submission. Digitized figure data are in `repo/data/digitized/`; pre-registered gate
criteria are in `docs/BUILD_PLAN.md`; gate scripts are in `repo/scripts/` (`run_gate0.py` through
`run_gate7.py`).

## References

1. Amorim S, Reis CA, Reis RL, Pires RA. Extracellular matrix mimics using hyaluronan-based
biomaterials. Trends Biotechnol. 2021;39(1):90-104.

2. Netti PA, Berk DA, Swartz MA, Grodzinsky AJ, Jain RK. Role of extracellular matrix assembly in
interstitial transport in solid tumors. Cancer Res. 2000;60(9):2497-2503.

3. Höfling F, Franosch T. Anomalous transport in the crowded world of biological cells. Rep Prog
Phys. 2013;76(4):046602.

4. Schmid PJ. Dynamic mode decomposition of numerical and experimental data. J Fluid Mech.
2010;656:5-28.

5. Brunton SL, Budišić M, Kaiser E, Kutz JN. Modern Koopman theory for dynamical systems. SIAM Rev.
2022;64(2):229-340.

6. Zwanzig R. Memory effects in irreversible thermodynamics. Phys Rev. 1961;124(4):983-992.

7. Mori H. Transport, collective motion, and Brownian motion. Prog Theor Phys. 1965;33(3):423-455.

8. Le Clainche S, Vega JM. Higher order dynamic mode decomposition. SIAM J Appl Dyn Syst.
2017;16(2):882-925.

9. Demo N, Tezzele M, Rozza G. PyDMD: Python Dynamic Mode Decomposition. J Open Source Softw.
2018;3(22):530.

10. Ichinaga SM, Andreuzzi F, Demo N, Tezzele M, Lapo K, Rozza G, et al. PyDMD: A Python Package for
Robust Dynamic Mode Decomposition. J Mach Learn Res. 2024;25.

11. Woodward M, Lin YT, Tian Y, Hader C, Fasel H, Livescu D. Mori-Zwanzig mode decomposition:
Comparison with time-delay embeddings. arXiv:2311.09524 [Preprint]. 2023.

12. Mandelbrot BB, Van Ness JW. Fractional Brownian motions, fractional noises and applications.
SIAM Rev. 1968;10(4):422-437.

13. Efron B, Tibshirani RJ. An Introduction to the Bootstrap. New York: Chapman & Hall; 1993.

14. Burla F, Sentjabrskaja T, Pletikapic G, van Beugen J, Koenderink GH. Particle diffusion in
extracellular hydrogels. arXiv:1909.05091 [Preprint]. 2019.

15. Kusumi A, Sako Y, Yamamoto M. Confined lateral diffusion of membrane receptors as studied by
single particle tracking (nanovid microscopy). Effects of calcium-induced differentiation in
cultured epithelial cells. Biophys J. 1993;65(5):2021-2040.

16. Fujiwara TK, Iwasawa K, Kalay Z, Tsunoyama TA, Watanabe Y, Umemura YM, et al. Confined diffusion
of transmembrane proteins and lipids induced by the same actin meshwork lining the plasma membrane.
Mol Biol Cell. 2016;27(7):1101-1119.

17. Hurvich CM, Tsai CL. Regression and time series model selection in small samples. Biometrika.
1989;76(2):297-307.

18. Dawson STM, Hemati MS, Williams MO, Rowley CW. Characterizing and correcting for the effect of
sensor noise in the dynamic mode decomposition. Exp Fluids. 2016;57(3):42.

19. Askham T, Kutz JN. Variable projection methods for an optimized dynamic mode decomposition. SIAM
J Appl Dyn Syst. 2018;17(1):380-416.

20. Sashidhar D, Kutz JN. Bagging, optimized dynamic mode decomposition (bop-dmd) for robust,
stable forecasting with spatial and temporal uncertainty-quantification. arXiv:2107.10878
[Preprint]. 2021.

21. Takeishi N, Kawahara Y, Yairi T. Subspace dynamic mode decomposition for stochastic Koopman
analysis. Phys Rev E. 2017;96(3):033310.

22. Zhao Y, Chen H, Hu M, Xu WS, Wang D. Diffusional aging at water/oil interfaces laden with charged
nanoparticles studied by single-molecule tracking. Nat Commun. 2026;17:7149.
