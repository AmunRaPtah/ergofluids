# Diagnosing and testing a Koopman/Mori-Zwanzig subdiffusion estimator: a pre-registered gate sequence from synthetic validation to a literature-digitized real-data test

**Author:** Eniola Olutogun

Corresponding author: ennyolutogun@gmail.com

**Status:** first full draft, 2026-07-23; updated 2026-07-31 to add the Gate 5 model-based refit and
the Gate 6 DMD-generality test. Target venue not yet selected. All results below are taken directly
from `docs/gate-result-phase1-synthetic.md`, `docs/gate-result-phase2-mzmd.md`,
`docs/gate-result-phase2-gate3-caging.md`, `docs/gate-result-phase3-realdata.md`,
`docs/gate-result-phase3-gate5-cagedfit.md`, and `docs/gate-result-gate6-dmd-generality.md`; nothing
here should be edited without also updating (or checking against) those source documents.

## Abstract

We test whether Koopman-operator and Mori-Zwanzig-based methods can recover known subdiffusive
signatures relevant to macromolecular transport through extracellular hydrogels. We use a
pre-registered sequence of validation gates: synthetic-data calibration and regime-separation tests
for three exponent estimators (log-log fitting, Higher-Order Dynamic Mode Decomposition, and a
Hankel-SVD/SSA variant), synthetic tests of a ported Mori-Zwanzig memory-kernel extension on a
linear hidden-variable system and a caged-particle system, and a final test against
literature-digitized real data. During synthetic calibration we diagnosed a systematic bias in
HODMD when reconstructing power-law-in-time curves, traced it to HODMD's forward-simulation step,
and fixed it with a denoising-only SSA variant; a pre-registered 100-repeat follow-up confirmed the
fix closed the gap. A further pre-registered synthetic test asked whether this bias generalizes to
other established DMD-family methods: a minimal, established bias-correction technique
(forward-backward operator averaging) applied to the same HODMD configuration did not fix the bias
and made it measurably worse, while two mechanistically different established methods (Bagging,
Optimized DMD and Subspace DMD) both avoided it cleanly, sharpening the diagnosis rather than simply
broadening it. For the real-data test, we digitized Figure 4a and Supplementary Figure S14a
from Burla et al. (2019), tracking reported and digitization error separately, and applied a
pre-registered pass/fail criterion for detecting the caging signature of a hyaluronan-collagen
composite network. The estimators did not detect a statistically significant local slope decrease
in the digitized MSD curve within propagated uncertainty (the primary, locked criterion), though a
secondary descriptive check on the intermediate scattering function did show the expected
qualitative plateau. A follow-up pre-registered test fit an explicit confined-diffusion functional
form to the same curve and compared it against a global power law by AICc; the power-law model was
decisively preferred for the composite network even though the confined model's characteristic time
was well-constrained within the observed range, a sharper negative result than the first test. We
report this as a mixed result rather than a validation, and discuss why the digitized figure's time
range likely falls short of the plateau region, alongside a digitization methodology that we believe
is independently reusable.

## 1. Introduction

Hyaluronan-collagen hydrogels are a widely used biomimetic model for the extracellular matrix that
macromolecular drugs must cross in dense tissue, including tumor stroma. Particle transport through
these gels is often subdiffusive, and the specific exponent and its dependence on network
composition carries information about pore size, crosslinking, and caging behavior. Koopman-operator
methods, including Dynamic Mode Decomposition (DMD) and its variants, are increasingly used to
extract dynamical structure, including scaling exponents, from time-series data, and Mori-Zwanzig
formalisms offer a principled way to add memory effects that plain Markovian DMD misses. Applying
these tools to macromolecular transport in tissue-like gels is, to our knowledge, untested. We
report a pre-registered gate sequence built to test that application honestly: synthetic validation
first, then a test against the closest available real (if indirect, literature-digitized) data, with
the pass/fail criteria fixed before the data was digitized.

## 2. Methods

### 2.1 Exponent estimators

We tested three estimators for the subdiffusive scaling exponent alpha, defined via mean-squared
displacement (MSD) proportional to Delta t^alpha. `loglog` performs ordinary least-squares
regression of log(MSD) on log(Delta t). `dmd` applies Higher-Order Dynamic Mode Decomposition
(HODMD; Le Clainche and Vega, 2017), via the PyDMD implementation (Demo et al., 2018; Ichinaga et
al., 2024), to a delay-embedded trajectory and recovers alpha from the fitted eigenvalue spectrum
via forward reconstruction. `ssa` uses the same delay-embedding matrix as `dmd` but replaces
HODMD's eigenvalue-based forward simulation with Hankel-SVD low-rank projection and anti-diagonal
averaging (Singular Spectrum Analysis-style denoising), with the exponent then read off the
denoised curve by log-log fit. All three were implemented in `src/ergofluids/koopman/exponent.py`.

### 2.2 Mori-Zwanzig memory kernel

We ported the Mori-Zwanzig Mode Decomposition (MZMD) algorithm described by Woodward et al. (2023)
from its reference Julia implementation to Python (`src/ergofluids/mz/mzmd.py`). The kernel order
n_ks controls the number of memory terms retained; n_ks = 1 reduces the method to a memoryless
(Markovian) fit.

### 2.3 Synthetic validation protocol

Gates 0 and 1 used 2D fractional Brownian motion trajectories (150 particles, 80 time steps, 150
bootstrap resamples per estimate). Gate 0 tested bootstrap interval calibration (target: 18/20
coverage at nominal 90%, at alpha_true in {0.5, 0.7, 1.0}). Gate 1 tested whether the estimators
separate two literature-anchored exponent regimes (single-component, alpha ~ 1.0;
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
digitized two published figures from Burla et al. (2019, arXiv:1909.05091): Figure 4a (intermediate
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
form from the single-particle-tracking literature (Kusumi, Sako & Yamamoto, 1993; restated in later
methods papers, e.g. Fujiwara et al., 2016), `MSD(t) = P[1 - exp(-t/tau)]`. The two were compared by
small-sample-corrected AIC (AICc), propagated through the
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
operator averaging, Dawson et al., arXiv:1507.02264, applied to the identical HODMD configuration
Gate 0 tested), `BOPDMD` (Bagging, Optimized DMD; Askham & Kutz, 2018; Sashidhar & Kutz,
arXiv:2107.10878, 2021), and `SubspaceDMD` (Takeishi, Kawahara & Yairi, 2017). `BOPDMD` and
`SubspaceDMD` do not natively delay-embed a scalar signal, so both were fit on the identical
Hankel-matrix construction `ssa` uses and reassembled to a 1D curve the same way, isolating "which
reconstruction algorithm is applied to the same delay-embedded matrix" as the only variable against
`ssa`. Protocol otherwise identical to Gate 0: fBm trajectories, `alpha_true` in {0.5, 0.7, 1.0}, 20
repeats per condition, 150-resample bootstrap CI, 18/20 coverage bar. Each estimator falls back to
`loglog_fit_exponent` on any fit exception or non-finite reconstruction, with fallback counts
tracked and reported per condition rather than absorbed silently.

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
application concluded.

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
claimed to behave either way.

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
than the original diagnosis alone supported.

## Competing interests

The author declares no competing interests.

## Data and code availability

All code, synthetic data generators, digitization scripts, and gate results are available at
https://github.com/AmunRaPtah/ergofluids. Digitized figure data (`repo/data/digitized/`) and the
pre-registered gate criteria (`docs/BUILD_PLAN.md`, `repo/scripts/run_gate4.py`,
`repo/scripts/run_gate5.py`, `repo/scripts/run_gate6.py`) are included.

## References

Askham, T., & Kutz, J. N. (2018). Variable projection methods for an optimized dynamic mode
decomposition. SIAM Journal on Applied Dynamical Systems, 17(1), 380-416.

Burla, F., Sentjabrskaja, T., Pletikapic, G., van Beugen, J., & Koenderink, G. H. (2019). Particle
diffusion in extracellular hydrogels. arXiv:1909.05091.

Dawson, S. T. M., Hemati, M. S., Williams, M. O., & Rowley, C. W. (2016). Characterizing and
correcting for the effect of sensor noise in the dynamic mode decomposition. Experiments in Fluids,
57(3), 42.

Demo, N., Tezzele, M., & Rozza, G. (2018). PyDMD: Python Dynamic Mode Decomposition. Journal of Open
Source Software, 3(22), 530.

Fujiwara, T. K., Iwasawa, K., Kalay, Z., Tsunoyama, T. A., Watanabe, Y., Umemura, Y. M., Murakoshi,
H., Suzuki, K. G. N., Nemoto, Y. L., Morone, N., & Kusumi, A. (2016). Confined diffusion of
transmembrane proteins and lipids induced by the same actin meshwork lining the plasma membrane.
Molecular Biology of the Cell, 27(7), 1101-1119.

Ichinaga, S. M., Andreuzzi, F., Demo, N., Tezzele, M., Lapo, K., Rozza, G., Brunton, S. L., & Kutz,
J. N. (2024). PyDMD: A Python Package for Robust Dynamic Mode Decomposition. Journal of Machine
Learning Research, 25.

Kusumi, A., Sako, Y., & Yamamoto, M. (1993). Confined lateral diffusion of membrane receptors as
studied by single particle tracking (nanovid microscopy). Effects of calcium-induced differentiation
in cultured epithelial cells. Biophysical Journal, 65(5), 2021-2040.

Le Clainche, S., & Vega, J. M. (2017). Higher order dynamic mode decomposition. SIAM Journal on
Applied Dynamical Systems, 16(2), 882-925.

Sashidhar, D., & Kutz, J. N. (2021). Bagging, optimized dynamic mode decomposition (bop-dmd) for
robust, stable forecasting with spatial and temporal uncertainty-quantification. arXiv:2107.10878.

Takeishi, N., Kawahara, Y., & Yairi, T. (2017). Subspace dynamic mode decomposition for stochastic
Koopman analysis. Physical Review E, 96(3), 033310.

Woodward, M., Lin, Y. T., Tian, Y., Hader, C., Fasel, H., & Livescu, D. (2023). Mori-Zwanzig mode
decomposition: Comparison with time-delay embeddings. arXiv:2311.09524.
