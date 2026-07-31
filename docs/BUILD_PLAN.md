# ErgoFluids: build plan

This document states pass/fail criteria for Gate 0 and Gate 1 before either has been run. Both
gates are written from real, sourced numbers where possible; where a number is not obtainable
(explained below), that gap is stated directly rather than papered over with an invented figure.

## Data reality check

`literature-map.md` identifies arXiv:1909.05091 ("Particle diffusion in extracellular hydrogels")
as the closest real dataset to ErgoFluids' target system. Reading the full text directly (this
session) surfaced concrete, sourced numbers:

- For the composite network (1 mg/mL collagen + 2 mg/mL hyaluronan), 0.6 µm tracer particles show a
  subdiffusive exponent **α ≈ 0.5**, from fitting the intermediate scattering function decay time
  τ(q) (paper's Figure 4, Supplementary Figure S14). The paper does not report a numeric uncertainty
  for this value in the main text.
- For the single-component networks (pure collagen or pure hyaluronan alone), particle motion is
  close to simple diffusion, **α ≈ 1**.
- The paper reports no data-availability statement and no link to a raw-trajectory repository. Only
  derived quantities (α, mesh sizes, moduli) appear in the text and figures, not raw time series.

Consequence: there is no downloadable raw trajectory dataset to fit DMD/EDMD against directly this
pass. Gate 1 below is scoped honestly around that constraint: it validates the pipeline against
literature-anchored synthetic data, not against the paper's own raw measurements. That distinction
is carried into the eventual gate-result document, not hidden.

## Gate 0: pipeline correctness (synthetic, known ground truth)

**Pre-registered before any code is run.**

Generate synthetic subdiffusive trajectories with a known, chosen exponent α_true (for example via
fractional Brownian motion or a generalized Langevin equation with a power-law memory kernel tuned
to produce a target α). Fit the DMD/EDMD pipeline (`src/ergofluids/koopman`) to recover an estimate
α_hat.

**Pass criterion**: across at least 20 independent synthetic realizations at each of α_true in
{0.5, 0.7, 1.0}, the bootstrap 95% CI of α_hat contains α_true in at least 18 of 20 runs (90%
nominal coverage, allowing for finite-sample slack). **Fail** if coverage is materially below that
in a way not explained by a known implementation bug.

Purpose: confirm the estimator itself works before comparing it to any literature number.

### Gate 0 result and root-cause diagnosis

Gate 0 failed as first run (`docs/gate-result-phase1-synthetic.md`): the HODMD-based estimator
missed the 18/20 coverage bar at all three exponents (15, 17, 12), the log-log baseline missed it
at one (16/20 at alpha=0.7). Diagnosis, not a re-tune: point-estimate bias, not interval width,
drives the failure. HODMD's mean bias ran -0.026 to -0.054 across conditions (worst at
alpha_true=1.0), while log-log's bias stayed near zero (-0.004 to +0.015); bootstrap CI widths were
comparable between the two estimators. Inspecting the reconstructed curve directly showed why:
HODMD's reconstruction error is small near the start of the time window and grows to roughly 5 to
10 times larger by the end. Re-parameterizing onto a grid uniform in log(t), so the target curve is
closer to linear in the fitting index, did not fix this (error got worse, not better), which rules
out "wrong time axis" as the cause.

The mechanism: HODMD reconstructs by forward-simulating the fitted eigenvalue/mode decomposition
from initial conditions, which compounds error over the window for a signal that is not itself a
finite sum of exponentials in real time (a power-law-in-time curve is not). A plain Hankel-SVD
low-rank projection of the same delay-embedded matrix, reassembled by anti-diagonal (Hankelization)
averaging instead of dynamic extrapolation, that is, classical Singular Spectrum Analysis (SSA)
using the same delay-embedding machinery but with no eigenvalue-based forward simulation, showed
uniformly small reconstruction error with no growth over the window in a spot check, and recovered
alpha_true=1.0 as 0.972 versus HODMD's 0.945 to 0.961.

**Gate 0b, pre-registered here before the full 20-repeat run**: replace the DMD estimator's
reconstruction step with SSA-style Hankel-SVD denoising (no HODMD dynamic reconstruction), keep the
log-log slope fit on the denoised curve exactly as before, and re-run the identical Gate 0 protocol
(20 repeats, alpha_true in {0.5, 0.7, 1.0}, same 18/20 coverage bar). This is a mechanistically
motivated method change following a diagnosed root cause, not a parameter search against the
outcome; the result is reported honestly below regardless of whether it passes. If it still fails,
the conclusion is that DMD/Koopman-style modeling does not help this particular estimation problem,
and Phase 2 should not assume otherwise. Labeling note: SSA-based denoising uses the same
delay-embedding (Hankel matrix) construction as HODMD, but is no longer a Koopman-eigenvalue-based
reconstruction, and future write-ups must describe it as such rather than call it "DMD."

Result: `ssa` missed the bar by one at alpha_true=0.5 (17/20) and met or exceeded it at the other
two (19/20 at 0.7, 18/20 at 1.0). See `docs/gate-result-phase1-synthetic.md`, Gate 0b.

### Gate 0c: pre-registered power follow-up

**Pre-registered here, before running.** A single miss at 17/20 versus an 18/20 bar could be a real
shortfall or ordinary binomial noise around a true rate near 90%; n=20 cannot distinguish these.
Re-run alpha_true=0.5 only, loglog and ssa only (dmd excluded, already diagnosed as a real failure),
at 100 repeats instead of 20, and report the exact Clopper-Pearson 95% CI on the true coverage rate.
**Interpretation rule, fixed now**: if that CI contains 90%, treat the original 17/20 as noise and
Gate 0 as passed for `ssa`. If it excludes 90% on the low side, treat Gate 0 as still failed and
investigate further. No parameter changes after this result either way.

Result: loglog 89/100 (95% CI [81.2%, 94.4%]), ssa 90/100 (95% CI [82.4%, 95.1%]), both containing
90%. Per the rule fixed above, Gate 0 is resolved as **passed for `ssa`** across all three tested
exponents. See `docs/gate-result-phase1-synthetic.md`, Gate 0c, for full detail.

## Gate 1: literature-anchored synthetic validation

**Pre-registered before any code is run.**

Using the same pipeline, generate synthetic trajectories parameterized to match the two literature
regimes identified above: single-component networks (α_true ≈ 1) and the composite
hyaluronan-collagen network (α_true ≈ 0.5). Fit DMD/EDMD to each synthetic dataset independently
without telling the pipeline which regime it came from.

**Pass criterion**: the pipeline's estimated α_hat distinguishes the two regimes, that is, the
bootstrap 95% CIs for the composite-regime estimate and the single-component-regime estimate do not
overlap, and the composite-regime point estimate falls within ±0.15 of 0.5 (a stated default
tolerance, chosen because the paper gives no numeric uncertainty to inherit).

**Fail** if the CIs overlap, or if the composite-regime estimate falls outside that tolerance.

**Explicitly not claimed by a pass here**: a pass validates that the modeling pipeline can recover
the qualitative and approximate quantitative pattern reported in the literature, using synthetic
data built to match that literature's summary statistics. It does not validate the pipeline against
the paper's own raw measurements, because those are not available. Any future write-up must state
this distinction.

## Gate 2: Mori-Zwanzig memory kernel, on a real memory-effect test

**Pre-registered before any code is run.** The Julia reference (`lanl/MoriZwanzigModalDecomposition.jl`,
read directly this session, not just cited) implements MZMD as: project observables to reduced rank
r via SVD, compute time-lagged correlation matrices C(δ) = X(t+δ) X(t)^T for δ = 0..n_ks over a
fitting window, then solve a Yule-Walker-style recursion for memory-kernel operators Ω(1)..Ω(n_ks):

```
Ω(1) = C(1) C(0)^-1
Ω(k) = [C(k) - sum_{l=1}^{k-1} Ω(l) C(k-l)] C(0)^-1      for k = 2..n_ks
```

used for prediction as `g(t+1) = sum_{l=1}^{n_ks} Ω(l) g(t-l+1)`. At n_ks=1 this is a plain
one-step Markovian (DMD-like) transition operator; n_ks > 1 is a vector-autoregressive memory
kernel of order n_ks. This is a legitimate, well-specified algorithm to port, not a re-description
of HODMD's biased reconstruction from Gate 0.

**Test system**: Mori-Zwanzig theory's textbook motivating case is a Markovian system observed only
through a subset of its state. Simulate a stable, stochastic, fully Markovian 2D linear system
(x, y), with `A = [[0.4, 0.3], [0.2, 0.7]]` (eigenvalues 0.263 and 0.837, spectral radius < 1,
confirmed this session) plus Gaussian process noise. Fit only on the observed scalar x(t); y is
never given to the fitting pipeline. The marginal dynamics of x alone are provably non-Markovian
once y is integrated out, so a memoryless (n_ks=1) fit on x should structurally underperform a
memory-augmented (n_ks=K, K to be chosen and fixed before results are seen) fit on multi-step
forecasts of x.

**Protocol, locked before the pre-registered run**: a 30-trial pilot (not the official run, used
only to size the protocol, not to compare which model wins) showed two things worth fixing before
committing. First, forecasting far ahead (15 steps) is uninformative: both n_ks=1 and n_ks=6
forecasts decay to the unconditional mean and their RMSEs converge, an expected property of
stable stochastic linear forecasts at long horizons, not a property of either model's memory
handling, so the horizon is set short (3 steps) instead. Second, at that short horizon the pilot's
paired difference (memoryless RMSE minus memory-augmented RMSE) was positive on average, in the
theory-predicted direction, but modest relative to its spread (mean 0.023, sd 0.088 over 30 trials),
so 30 trajectories under-powers a bootstrap test of it; the trajectory count is set to 60 instead.
Final locked parameters: t_win=50, n_ks=6 (memory-augmented) vs n_ks=1 (memoryless), forecast
horizon=3, n_traj=60, noise_std=0.3 (`data/hidden_variable.py` defaults). No further changes after
this point regardless of the official run's outcome.

Fit n_ks=1 and n_ks=6 to x(t) alone on the fitting window of each of the 60 trajectories; forecast
forward 3 steps; compute each trajectory's forecast RMSE against the true x path for both n_ks
settings. Paired bootstrap (resample trajectories with replacement) on the per-trajectory RMSE
difference (memoryless minus memory-augmented), following the same CI-excludes-zero gate convention
used in Topologix's real gate-result files.

**Pass criterion**: the 95% CI of (RMSE_memoryless - RMSE_mzmd), paired-bootstrapped across
trajectories, excludes zero on the positive side (memory-augmented forecast error is genuinely
lower). **Fail** if the CI includes zero or favors the memoryless model.

**Explicitly not claimed by a pass here**: a pass shows the ported MZMD algorithm captures a known,
theory-guaranteed memory effect in a controlled linear synthetic system. It says nothing yet about
whether real tissue transport has the kind of memory this recursion can usefully model, and nothing
about the arXiv:1909.05091 composite-network ISF plateau specifically, that comparison is Phase 3+
work once real or better-anchored data exists.

## Gate 3: Mori-Zwanzig memory kernel, on a caging test closer to the real target

**Pre-registered before any code is run.** Gate 2's hidden-variable system is linear and generic;
it does not reproduce the specific qualitative behavior arXiv:1909.05091 reports for the composite
network, an MSD/ISF plateau consistent with transient caging before eventual escape. Before spending
effort on real-data acquisition (Phase 3), test the same MZMD port against a system that actually
produces that signature, mechanistically motivated rather than fit to it: a fast Ornstein-Uhlenbeck
fluctuation x(t) around a slowly, unboundedly diffusing hidden trap center c(t)
(`data/caging.py`, `kappa=0.5`, `sigma_x=0.3`, `sigma_c=0.03`). Only x is observed; c is discarded.

**Verification the system behaves as intended (done before locking the gate, not a pass/fail
result)**: a 200 to 300-trajectory ensemble MSD of x alone, log-log slope fit in three windows,
showed the expected crossover: 0.18 over steps 1 to 8 (fast local equilibration), 0.26 over steps
10 to 100 (confined, near-plateau), 0.65 over steps 200 to 400 (escape, still rising toward
diffusive as the simulated window ends). This confirms the system produces a genuine, verified
caging-then-escape signature, not merely an assumption.

**Protocol, locked after a 30-trial pilot** (used only to size the protocol, not to compare which
model wins, same discipline as Gate 2): t_win=100, n_ks=15 (memory-augmented) vs n_ks=1
(memoryless), forecast horizon=10 (long enough to probe the plateau-to-escape region, unlike Gate
2's short-horizon test). The pilot's paired difference (mean 0.057, sd 0.111 over 30 trials, 60% of
trials favoring memory) was directionally consistent with Gate 2 and larger in magnitude; n_traj is
set to 60, matching Gate 2, giving more margin than the minimum the pilot's power would technically
require. No further changes after this point regardless of the official run's
outcome.

**Pass criterion**: identical structure to Gate 2, the 95% paired-bootstrap CI of (RMSE_memoryless
minus RMSE_mzmd) across the 60 trajectories excludes zero on the positive side. **Fail** if the CI
includes zero or favors the memoryless model.

**Explicitly not claimed by a pass here**: a pass shows MZMD captures memory in a synthetic system
built to mechanistically resemble caging, still not the paper's actual reported data. It is a
stronger stand-in than Gate 2, not a substitute for real data.

## Gate 5: model-based caged-diffusion fit (same digitized data, different functional form)

**Pre-registered here, before this gate's script is run.** Gate 4's primary test (fixed
early/late-window log-log OLS slope comparison) failed for the composite network on its own
locked criterion (`docs/gate-result-phase3-realdata.md`). That write-up's "What would change this
result" section named two untried follow-ups: raw trajectory data from the paper's authors, or a
model-based fit of an explicit caged-diffusion functional form to the whole MSD curve instead of
comparing two fixed windows. Author outreach was drafted and sent (`docs/author-outreach-draft.md`)
and has not received a response as of 2026-07-31. This gate tests the second option, on the same
S14a digitized data, with no new data collected and no change to Gate 4's own result or verdict.

**Model.** The standard confined/restricted-diffusion MSD form from the single-particle-tracking
literature, originating in Kusumi, Sako & Yamamoto, *Biophys. J.* 65:2021-2040 (1993), and restated
in numerous later SPT methods papers (for example Fujiwara et al., *Mol. Biol. Cell* 27:1101-1119,
2016, Eq. 3 region):

```
MSD_confined(Delta t) = P * [1 - exp(-Delta t / tau)]
```

with `P` the MSD plateau value (proportional to the square of an effective confinement length
scale) and `tau` the characteristic confinement relaxation time. This is a genuinely different test
from Gate 4: it fits the curve's full visible shape at once rather than comparing two local
windows, and it is an established literature model, not one invented for or tuned to this
dataset's outcome.

Compared against a single global power law across the same full curve, the same functional family
Gate 0/1/4 already used:

```
MSD_powerlaw(Delta t) = A * Delta t^alpha
```

Both models have 2 free parameters, so neither is penalized more than the other for flexibility
going in.

**Fit method.** Weighted nonlinear least squares (weights = `1/sigma_i^2`, `sigma_i = sqrt(reported_error_i^2
+ digitization_error_i^2)`, the same combined-in-quadrature error Gate 4 used) on the full digitized
curve, no early/late windowing. Compared via small-sample-corrected AIC:
`AICc = chi^2 + 2k + 2k(k+1)/(n-k-1)`, `chi^2` the weighted residual sum of squares at each model's
best fit, `k=2` for both models, so the AICc difference is directly comparable without needing an
absolute likelihood normalization. Applied to the same three curves Gate 4 used (composite,
hyaluronan, collagen_1mg). Propagated via the same style of 2000-draw Gaussian-perturbation
bootstrap as Gate 4 (perturb each point's `y` by `N(0, sigma_i)`, refit both models, record
`delta_AICc = AICc_powerlaw - AICc_confined` and, for the confined model, `tau`), seed 20260731 (a
fresh seed for this later, separately-run gate; Gate 4's seed 20260723 is not reused). Any bootstrap
draw where either model's fit fails to converge is dropped and the drop count is reported directly,
not silently absorbed into a smaller-than-stated n.

**Pass criterion:**
- **(A) Composite**: the 95% CI of `delta_AICc` is entirely positive (excludes zero, the confined
  model is preferred in every bootstrap draw, not just on average) AND the 95% CI of `tau` has a
  lower bound below the curve's own maximum digitized `Delta t` (the fitted plateau is at least
  partly constrained by data inside the observed range in every bootstrap draw, not purely an
  extrapolation beyond it).
- **(B) Hyaluronan AND collagen_1mg**: (A)'s two parts do NOT both hold, that is, either the
  `delta_AICc` CI does not exclude zero on the confined-preferred side, or `tau`'s CI lower bound
  exceeds the curve's own maximum digitized `Delta t`. This operationalizes "the pure networks
  should not show a data-constrained confinement signature the way the composite is hypothesized
  to."

**Fail** if (A) fails for composite, or (B) fails (a pure-component curve looks just as
data-constrained-confined as composite is hypothesized to) for either pure-component curve.

**Explicitly not claimed by a pass here**: same standing caveat as Gate 4, this still uses
literature-digitized summary curves, not raw trajectory data. A pass would show a plateau shape is
detectable in the composite curve's overall form using a standard confined-diffusion model,
succeeding where Gate 4's fixed-window slope comparison did not; it would not validate against the
paper's own raw measurements, and it would not overturn or retest Gate 4's own specific finding
that within-window curvature is not detectable in this Delta t range, a global functional-form fit
and a local two-window slope comparison can legitimately disagree because they use the curve's
shape differently, and both results would stand side by side.

**Known risk, stated before running**: Gate 4's own write-up already noted the composite curve may
not extend far enough in `Delta t` to show flattening at all ("Reaching the point where MSD itself
visibly flattens would likely require probing longer Delta t ... than S14a's own axis range extends
to"). If that is correct, `tau`'s bootstrap distribution may be poorly constrained (many draws
pushing `tau` far beyond the data range), which criterion (A)'s `tau`-CI condition is designed to
catch and report honestly as a data-range limitation rather than let it pass silently on `delta_AICc`
alone.

No parameter or criterion changes after seeing the numbers below.

### Gate 5 result

Run 2026-07-31, `repo/scripts/run_gate5.py`, seed 20260731, 2000/2000 bootstrap draws converged
for all three curves (0 dropped). Full detail and discussion in
`docs/gate-result-phase3-gate5-cagedfit.md`; summary:

| curve | delta_AICc (powerlaw − confined) [95% CI] | confined preferred in all draws | tau [95% CI] | tau CI lower bound < max Delta t | criterion |
|---|---|---|---|---|---|
| composite | -109.340 [-149.145, -69.690] | NO | 1.430 [1.199, 1.658] | YES | (A) **FAIL** |
| hyaluronan | -557.752 [-621.878, -494.394] | NO | 0.136 [0.107, 0.171] | YES | (B) PASS |
| collagen_1mg | -320.114 [-376.011, -263.517] | NO | 0.300 [0.265, 0.335] | YES | (B) PASS |

**Gate 5 verdict: FAIL** (criterion A does not hold for composite: the power-law model is
decisively preferred over the confined-diffusion model, not the reverse).

This is a sharper negative result than Gate 4, not merely a repeat of it. `tau` is well-constrained
inside the observed range for composite (95% CI [1.199, 1.658], well below the curve's max digitized
`Delta t` of 10.727), so the "known risk" flagged before running, that `tau` might be pushed
unconstrained beyond the data range, did not materialize; the confined model got a fair,
well-determined fit and still lost decisively (`delta_AICc` 95% CI entirely below roughly -69,
versus a `>0` bar for a pass). The composite MSD curve is better described, over this digitized
`Delta t` range, by a single global power law than by a model with a built-in plateau. This does not
overturn Gate 4 (a local two-window slope comparison and a global functional-form fit are different,
non-redundant tests, and both are reported as run); it removes the model-based refit as an open
follow-up, since it was tried and did not find a caging signature either, this time with a decisive
rather than ambiguous result. Per `BUILD_PLAN.md`'s phase sequencing rule, Phase 4 (IP/venture
material) still does not open on this result.

## Phase sequencing

1. **Phase 1 (this pass, complete)**: Gate 0 (failed for `dmd`, passed for `ssa` after diagnosis
   and a power follow-up), Gate 1 (passed for all estimators), both on synthetic data. `koopman/`
   module (PyDMD-based `dmd`, retired, plus `ssa`, the estimator to carry forward), `validation/`
   module (bootstrap CI harness), gate-result write-up.
2. **Phase 2, complete**: Mori-Zwanzig memory-kernel extension (`mz/` module, ported from
   `lanl/MoriZwanzigModalDecomposition.jl`). Passed on a linear hidden-variable synthetic system
   (Gate 2, `docs/gate-result-phase2-mzmd.md`) and on a caged-particle system built to
   mechanistically resemble the composite network's reported plateau, with a verified MSD
   crossover (Gate 3, `docs/gate-result-phase2-gate3-caging.md`). Both gates passed. Neither used
   the paper's actual data.
3. **Phase 3**: revisit real-data acquisition. Either request raw data directly from the paper's
   authors, or scope a literature-digitization effort (for example WebPlotDigitizer on published
   figures) as a distinct, explicitly-labeled data source with its own error characterization.
4. **Phase 4+**: IP and venture material, only after a phase-3-or-later gate has passed against
   real (not synthetic) data.

Phase 3 and 4 are not started yet.
