# Gate result: Gate 6 (does HODMD's diagnosed bias generalize across other DMD-family methods?)

Date: 2026-07-31. Criteria and parameters locked in `docs/BUILD_PLAN.md` ("Gate 6" section) before
this script was run. Script: `repo/scripts/run_gate6.py`, seed 20260731.

## Why this gate exists

Gate 0/0b (`docs/gate-result-phase1-synthetic.md`) diagnosed a systematic bias in HODMD (this
project's original `dmd` estimator) when reconstructing power-law-in-time MSD curves: HODMD
forward-simulates from a fitted eigenvalue decomposition, which compounds error for a signal that
is not itself a finite sum of exponentials in real time. The fix used (`ssa`) abandons
eigenvalue-based reconstruction entirely, replacing it with denoising-only Hankel-SVD projection.

That leaves a real question open: is the bias specific to HODMD's own implementation, or a general
property of DMD-family methods that reconstruct via a fitted eigenvalue decomposition? Answering
this generalizes the diagnosis from "we found and fixed a problem in one class" to "here is which
established methods in this family share the problem and which don't."

## Candidates and method (as pre-registered, restated here)

Three established, published, PyDMD-implemented methods (installed version 2025.8.1), chosen for
mechanistic diversity, none built for this project:

1. **`HODMD(forward_backward=True)`**: the identical HODMD configuration Gate 0 tested (`d=10,
   svd_rank=6, opt=True`), plus forward-backward operator averaging (Dawson, Hemati, Williams &
   Rowley, arXiv:1507.02264). Isolates whether this specific, minimal, established bias-correction
   technique fixes HODMD's bias while keeping eigenvalue-based dynamic reconstruction, unlike `ssa`.
2. **`BOPDMD`** (Bagging, Optimized DMD; Askham & Kutz, *SIAM J. Appl. Dyn. Syst.* 17, 2018,
   variable-projection fitting; Sashidhar & Kutz, arXiv:2107.10878, 2021, bootstrap-aggregated
   bagging across sub-samples of snapshots). A modern, actively recommended noise/uncertainty-robust
   variant, mechanistically distinct from HODMD.
3. **`SubspaceDMD`** (Takeishi, Kawahara & Yairi, *Phys. Rev. E* 96, 033310, 2017): a
   subspace-identification estimator, a different theoretical foundation from regression-based DMD.

`BOPDMD` and `SubspaceDMD` do not natively delay-embed a scalar signal, so both were fit on the
identical Hankel-matrix construction `ssa_denoise_exponent` already uses (window=20, rank=4),
reconstructed via each method's own `reconstructed_data`, and reassembled to a 1D curve by the same
anti-diagonal averaging `ssa` uses, isolating "which reconstruction algorithm is applied to the same
delay-embedded matrix" as the only variable against `ssa`. `HODMD(forward_backward=True)` keeps
HODMD's own native delay embedding unchanged from the original `dmd` estimator, isolating
forward-backward averaging as the only variable against `dmd`.

Protocol identical to Gate 0 in every other respect: `generate_2d_trajectories` (150 particles, 80
steps, 2D fractional Brownian motion), `alpha_true` in {0.5, 0.7, 1.0}, 20 independent realizations
per condition, 150-resample percentile bootstrap CI per realization, pass bar 18/20 coverage at
nominal 90%. Seed 20260731 (independent random stream from Gate 0's own 20260722 run).

**Numerical instrumentation note**: the pre-registration committed to reporting `loglog`-fallback
counts (each estimator falls back to `loglog_fit_exponent` on any fit exception or non-finite
reconstruction). The first run of this script (not reported as a result, an internal QA step) was
found to be missing the counting instrumentation despite the fallback logic itself already being
present; this was fixed (added `FALLBACK_COUNTS` tracking in `exponent.py`, reset/read per condition
in `run_gate6.py`) and the identical script, seed, and protocol re-run before any result was
finalized or reported. The re-run reproduced numerically identical coverage and bias values to the
uninstrumented run, confirming determinism; only the fallback-count visibility changed. The result
below is from the instrumented, final run.

## Result

| alpha_true | hodmd_fb coverage | hodmd_fb mean bias | bopdmd coverage | bopdmd mean bias | subspace coverage | subspace mean bias |
|---|---|---|---|---|---|---|
| 0.5 | 15/20 | -0.0644 | 18/20 | -0.0154 | 20/20 | +0.0055 |
| 0.7 | 12/20 | -0.0994 | 20/20 | -0.0067 | 20/20 | +0.0367 |
| 1.0 | 15/20 | -0.1013 | 20/20 | -0.0019 | 19/20 | +0.0818 |

Required: 18/20 at every `alpha_true`. `loglog`-fallback triggers: 0 out of 27,180 total estimator
calls (3 candidates x 3 conditions x 3,020 calls each, 1 point estimate + 150 bootstrap resamples
per repeat x 20 repeats) for every candidate. The numerical note's concern (occasional
variable-projection convergence warnings observed in pre-registration smoke testing) did not
translate into any actual fallback event at full scale.

**Verdict: `hodmd_fb` FAILS at all three conditions. `bopdmd` and `subspace` both PASS at all three
conditions.** No candidate landed at exactly 17/20 at any condition, so the pre-registered
power-follow-up trigger (a Gate 0c-style 100-repeat re-test, reserved for an exact 17/20) does not
apply to any of the three; `hodmd_fb`'s failures are decisive (12-15 out of 20), not borderline.

## Reading the result

**`hodmd_fb` did not just fail to fix the bias, it made it measurably worse.** Its mean bias
(-0.064 to -0.101) is larger in magnitude than plain `dmd` (HODMD without forward-backward
averaging)'s diagnosed bias (-0.026 to -0.054, from Gate 0/0b). Its coverage at `alpha_true=0.7`
(12/20) is worse than plain `dmd` scored at the same condition in either of its two runs (17/20 in
the original Gate 0, 18/20 in the Gate 0b re-run with a different bootstrap draw order): a swing of
this size (5-6 counts) is well outside the 1-2 count swing plain `dmd`/`loglog` showed between their
own two independent 20-repeat runs (Gate 0 vs Gate 0b, both already documented as ordinary Monte
Carlo variation), so this reads as a real effect of adding forward-backward averaging, not noise.

**`bopdmd` and `subspace` both cleanly avoid the bias**, with mean bias close to zero (`bopdmd`:
-0.015 to -0.002) or small and one-directional but still inside calibrated coverage (`subspace`:
+0.006 to +0.082, growing with `alpha_true`).

This is not simply "HODMD's bias generalizes to the whole DMD family" (two of three candidates
avoid it) nor "any bias-correction technique fixes it" (the one candidate built by minimally
patching HODMD itself does not, and gets worse). It sharpens the mechanistic account from Gate 0/0b:
forward-backward averaging is a technique developed for a different problem, correcting
eigenvalue bias from sensor/measurement noise in the original DMD estimation procedure (Dawson et
al.'s stated motivation). It does not address the specific structural mismatch diagnosed here,
forward-simulating a fitted eigenvalue decomposition on a signal that is not a finite sum of
real-time exponentials, so it is not surprising in hindsight that applying it to the same underlying
HODMD procedure leaves that mismatch intact, or makes the fit less stable in a way that widens
apparent bias further. `BOPDMD` and `SubspaceDMD` both avoid the problem via a route that does not
reuse HODMD's own two-stage delay-embed-then-forward-simulate estimation procedure: `BOPDMD` fits
the eigenvalue decomposition by directly optimizing (variable projection) against the whole
reconstruction window rather than a two-step linear regression followed by forward propagation, and
`SubspaceDMD` estimates dynamics through subspace identification, a different theoretical route
entirely. This project's own `ssa` fix (denoising only, no dynamic reconstruction at all) is
therefore not the only way to avoid HODMD's bias, but the two other things that do avoid it also do
not rely on HODMD's own specific estimation route, which is consistent with, not a coincidence
alongside, the original diagnosis.

**What this does not establish**: this is still a synthetic-data-only test (fractional Brownian
motion, known ground truth), like Gate 0/1/2/3; it says nothing new about the real-data result
(Gates 4, 5). It does not test every DMD variant PyDMD implements, only three chosen for mechanistic
diversity; other variants (for example plain `OptDMD`, `FbDMD` without HODMD's delay embedding,
`PiDMD` under various structural constraints) remain untested and are not claimed to behave either
way.

## Bearing on the project

Per `docs/BUILD_PLAN.md`'s phase sequencing rule, this does not reopen Phase 4 (IP/venture material)
or change the verdict of any real-data gate. It strengthens the HODMD bias diagnosis, described in
`docs/publication-angle.md` as the project's most broadly useful and citable finding, from "we found
and fixed a problem in one class" to a more general, more specific claim about which established
methods in the same family share the problem and which don't, and a more precise account of why.
