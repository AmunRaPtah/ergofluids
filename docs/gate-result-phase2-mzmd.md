# Gate result: Phase 2, Gate 2 (Mori-Zwanzig memory kernel)

Date: 2026-07-22. Criteria and parameters locked in `docs/BUILD_PLAN.md` (Gate 2) before this
script was run at full scale, following a 30-trial pilot used only to size the protocol (horizon
and trajectory count), not to compare which model would win. Script: `repo/scripts/run_gate2.py`,
seed 20260725.

## What was tested

A stable, stochastic, fully Markovian 2D linear system (x, y), `A = [[0.4, 0.3], [0.2, 0.7]]`
(eigenvalues 0.263 and 0.837), simulated with Gaussian process noise (std 0.3). Only the scalar x
is given to the fitting pipeline; y is discarded. Mori-Zwanzig theory guarantees x's marginal
dynamics become non-Markovian once y is integrated out, so a memoryless (n_ks=1) fit should
structurally underperform a memory-augmented (n_ks=6) fit on short-horizon forecasts of x.

60 independent trajectories, fitting window 50 steps, 3-step-ahead forecast horizon. Both n_ks=1
and n_ks=6 memory kernels, ported from `lanl/MoriZwanzigModalDecomposition.jl` (source read
directly, `repo/src/ergofluids/mz/mzmd.py`), fit per trajectory; forecast RMSE computed against the
true held-out continuation; paired bootstrap (2000 resamples) on the per-trajectory RMSE difference.

## Result

| | mean RMSE |
|---|---|
| memoryless (n_ks=1) | 0.3442 |
| memory (n_ks=6) | 0.3148 |

Paired difference (memoryless minus memory): point estimate 0.0294, 95% CI [0.0132, 0.0458].

**Verdict: PASS.** The CI excludes zero on the positive side, meaning the memory-augmented fit's
forecast error is genuinely lower, not just lower by chance in this one sample. This is the first
result in this project where added model complexity (memory terms beyond n_ks=1) demonstrably
helped, unlike Gate 0's finding that HODMD's added complexity hurt.

## What this does and does not establish

This confirms the ported MZMD algorithm (`repo/src/ergofluids/mz/mzmd.py`) correctly captures a
real, theory-guaranteed memory effect on a controlled linear synthetic system with a known hidden
variable. It validates the port and the general approach, nothing more. It does not show that real
macromolecular tissue transport has memory of the specific linear, low-order kind tested here, and
it does not test the arXiv:1909.05091 composite network's reported ISF plateau (caged-particle,
likely nonlinear, dynamics) at all. That comparison needs either real trajectory data or a
purpose-built nonlinear synthetic analog, and is Phase 3+ work, not claimed here.

RMSE improves by about 9% (0.344 to 0.315) at this noise level and system size, a small effect
that a 30-trajectory pilot run could not bootstrap confidently. 60 trajectories was sized
specifically to resolve that, following the same power-before-trust discipline used for Gate 0c.
